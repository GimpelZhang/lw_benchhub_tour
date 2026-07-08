#!/usr/bin/env python3
"""Phase 2 Task 2.2 — insert `descend` into the bowl-reach skill chain + add _execute_descend.

Modifies doublepiper_kitchen_pnp.py:
  1. In execute_skill_sequence: after the reach_hover block for akita_black_bowl, call _execute_descend
     (Cartesian linear descent from hover to grasp pose via cuRobo IK per waypoint), then `continue`
     to skip the original lateral grasp reach.
  2. Add _execute_descend method (20-step linear interpolation, cuRobo IKSolver per waypoint,
     warm-started; writes actions via the adapter's _apply_descend).

DEPENDS ON: patch_piper_adapter_descend.py (Task 2.1) applied first (_get_ik_solver + _apply_descend).
Idempotent: no-op if already patched. Backs up to .bak_patch01_descend.

NOTE: §2 pre-check found gripper force = 0N during hover reach (bowl movement is settling, not
gripper contact). This strongly suggests descend will NOT fix the grasp failure. Apply only if
Gate A fails AND the all-link scan (extend_section2_alllink.py) confirms a gripper/contact issue.
"""
import shutil, sys
from pathlib import Path

PATH = Path("/mnt/robot/AutoDataGen/source/autosim_examples/autosim_examples/autosim/pipelines/doublepiper_kitchen_pnp/doublepiper_kitchen_pnp.py")
src = PATH.read_text()

if "_execute_descend" in src:
    print("ALREADY PATCHED — no-op."); sys.exit(0)

BAK = PATH.with_suffix(".py.bak_patch01_descend")
if not BAK.exists():
    shutil.copyfile(PATH, BAK)

# 1: insert descend call after the hover block, before the grasp reach.
old1 = ('                    if not pre_success:\n'
        '                        raise ValueError("Pre-grasp hover reach failed.")\n'
        '\n'
        '                success, steps, episode_done = self._execute_single_skill(skill, goal)\n')
new1 = ('                    if not pre_success:\n'
        '                        raise ValueError("Pre-grasp hover reach failed.")\n'
        '\n'
        '                    # === Phase 2: Cartesian linear descent (replaces lateral grasp reach) ===\n'
        '                    self._diag_label = "descend"\n'
        '                    descend_success, descend_steps, descend_done = self._execute_descend(\n'
        '                        goal.target_pose, hover_z=0.15, n_steps=20\n'
        '                    )\n'
        '                    self._logger.info(f"Descend executed.({descend_steps} steps, success={descend_success})")\n'
        '                    self._log_object_positions(after_skill="descend")\n'
        '                    if descend_done:\n'
        '                        return PipelineOutput(success=self._check_task_success(), generated_actions=self._generated_actions)\n'
        '                    if not descend_success:\n'
        '                        raise ValueError("Descend to grasp pose failed.")\n'
        '                    continue  # skip the original lateral grasp reach; next skill is grasp()\n'
        '\n'
        '                success, steps, episode_done = self._execute_single_skill(skill, goal)\n')
assert src.count(old1) == 1, f"old1 count={src.count(old1)}"
src = src.replace(old1, new1)
print("[1 descend insertion] applied")

# 2: add _execute_descend method (insert before _build_world_state)
old2 = "    def _build_world_state(self) -> WorldState:\n"
new2 = '''    def _execute_descend(self, grasp_pose, hover_z: float = 0.15, n_steps: int = 20):
        """Phase 2: Cartesian linear descent from hover to grasp pose via cuRobo IK per waypoint.

        Replaces the lateral cuRobo reach(grasp) for the bowl with a vertical straight-line
        descent, eliminating the lateral component that (per the original hypothesis) pushes the
        bowl. NOTE: §2 pre-check found gripper force = 0N during hover — the bowl movement is
        mostly settling, so this fix is UNCERTAIN to help.
        """
        import torch
        from curobo.types.math import Pose
        arm = self._current_arm
        solver, tdtype = self._action_adapter._get_ik_solver(arm)
        # Build hover + grasp poses (robot-root frame; grasp_pose is goal.target_pose).
        hover_pose = grasp_pose.clone()
        hover_pose[0, 2] = hover_pose[0, 2] + hover_z
        # Linear interpolation of positions (n_steps+1 waypoints, including endpoints).
        t = torch.linspace(0, 1, n_steps + 1, device=grasp_pose.device).unsqueeze(1)
        waypoints_pos = t * (grasp_pose[0:1, :3] - hover_pose[0:1, :3]) + hover_pose[0:1, :3]
        waypoints_quat = hover_pose[0:1, 3:7].repeat(n_steps + 1, 1)  # constant orientation (top-down)
        # Solve IK per waypoint, warm-started from the previous solution.
        current_q = as_torch(self._robot.data.joint_pos)[self._env_id, :]
        plan_positions = []
        prev_q = None
        for i in range(n_steps + 1):
            pos = waypoints_pos[i:i+1]
            quat = waypoints_quat[i:i+1]
            target = Pose(position=pos, quaternion=quat)
            seed = prev_q.unsqueeze(0) if prev_q is not None else None
            result = solver.solve_single(target, seed_config=seed)
            if not result.success.item():
                self._logger.error(f"Descend IK failed at waypoint {i}/{n_steps}")
                return False, i, False
            q = result.position[0]
            plan_positions.append(q)
            prev_q = q
        # Execute each waypoint (write action, step, record).
        steps = 0
        for q in plan_positions:
            action = self._last_action.clone()
            adapter_result = self._action_adapter._apply_descend(q, self._env)
            action[self._env_id, :adapter_result.shape[0]] = adapter_result
            if self._record_dataset:
                self._record_dataset_frame(self._build_world_state(), action)
            _, _, terminated, truncated, _ = self._env.step(action)
            self._last_action = action
            self._generated_actions.append(action)
            self._record_head_view_frame()
            steps += 1
            if bool((terminated[self._env_id] | truncated[self._env_id]).item()):
                return True, steps, True
        return True, steps, False

    def _build_world_state(self) -> WorldState:
'''
assert src.count(old2) == 1, f"old2 count={src.count(old2)}"
src = src.replace(old2, new2)
print("[2 _execute_descend method] applied")

PATH.write_text(src)
print("PHASE 2 TASK 2.2 PATCH APPLIED:", PATH)
