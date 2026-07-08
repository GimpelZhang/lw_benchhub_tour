#!/usr/bin/env python3
"""§2 pre-check instrumentation patch (v2, correct replace semantics)."""
import shutil, sys
from pathlib import Path

PATH = Path("/mnt/robot/AutoDataGen/source/autosim_examples/autosim_examples/autosim/pipelines/doublepiper_kitchen_pnp/doublepiper_kitchen_pnp.py")
src = PATH.read_text()

if "_diag_skill_type" in src:
    print("ALREADY PATCHED — no-op."); sys.exit(0)

def replace(anchor, addition, label):
    global src
    assert anchor in src, f"[{label}] anchor not found"
    assert src.count(anchor) == 1, f"[{label}] anchor not unique ({src.count(anchor)})"
    src = src.replace(anchor, addition)
    print(f"[{label}] applied")

# 1: diag vars after head_view_frames
replace(
    "        self._head_view_frames: list[np.ndarray] = []\n",
    "        self._head_view_frames: list[np.ndarray] = []\n"
    "        # §2 pre-check diagnostic state (contact force + bowl movement during reach on bowl).\n"
    "        # Guarded: logging only; never alters pipeline behavior. Reused by Phase 2 tuning.\n"
    "        self._diag_skill_type: str | None = None\n"
    "        self._diag_target_object: str | None = None\n"
    "        self._diag_label: str = \"\"\n"
    "        self._diag_max_force: float = 0.0\n"
    "        self._diag_force_first_contact_step: int = -1\n"
    "        self._diag_bowl_start = None\n"
    "        self._diag_bowl_first_move_step: int = -1\n",
    "1 diag vars")

# 2: _log_diag_summary method before _make_pregrasp_goal
replace(
    "        except Exception:\n            pass\n\n    def _make_pregrasp_goal(self, goal, hover_z: float):\n",
    "        except Exception:\n            pass\n\n"
    "    def _log_diag_summary(self) -> None:\n"
    "        \"\"\"§2 pre-check: log max gripper contact force + bowl displacement for reach(bowl).\"\"\"\n"
    "        if self._diag_target_object != \"akita_black_bowl\" or self._diag_skill_type != \"reach\":\n"
    "            return\n"
    "        try:\n"
    "            bowl_disp = 0.0\n"
    "            bowl_end_str = \"n/a\"\n"
    "            try:\n"
    "                bowl_end = self._env.scene[\"akita_black_bowl\"].data.root_pos_w[self._env_id][:3].cpu()\n"
    "                bowl_end_str = [round(x, 3) for x in bowl_end.tolist()]\n"
    "                if self._diag_bowl_start is not None:\n"
    "                    bowl_disp = float(torch.linalg.norm(bowl_end - self._diag_bowl_start))\n"
    "            except Exception:\n"
    "                pass\n"
    "            self._logger.info(\n"
    "                f\"[diag summary {self._diag_label}] max_gripper_force={self._diag_max_force:.3f} N \"\n"
    "                f\"first_contact_step(>0.5N)={self._diag_force_first_contact_step} \"\n"
    "                f\"bowl_disp={bowl_disp:.4f} m bowl_first_move_step(>1cm)={self._diag_bowl_first_move_step} \"\n"
    "                f\"bowl_end={bowl_end_str}\"\n"
    "            )\n"
    "        except Exception as e:\n"
    "            self._logger.warning(f\"diag summary error: {e}\")\n\n"
    "    def _make_pregrasp_goal(self, goal, hover_z: float):\n",
    "2 summary method")

# 3: diag context after goal extraction
replace(
    "                goal = skill.extract_goal_from_info(skill_info, self._env, self._env_extra_info)\n\n"
    "                # Pre-grasp hover for the bowl: reach ABOVE the bowl first, then descend to the\n",
    "                goal = skill.extract_goal_from_info(skill_info, self._env, self._env_extra_info)\n\n"
    "                # §2 diagnostic context (label overridden for the hover reach below).\n"
    "                self._diag_skill_type = skill_info.skill_type\n"
    "                self._diag_target_object = skill_info.target_object\n"
    "                self._diag_label = skill_info.skill_type\n"
    "\n"
    "                # Pre-grasp hover for the bowl: reach ABOVE the bowl first, then descend to the\n",
    "3 diag context")

# 4: hover label
replace(
    "                    pre_goal = self._make_pregrasp_goal(goal, hover_z=0.15)\n"
    "                    pre_success, pre_steps, pre_done = self._execute_single_skill(skill, pre_goal)\n",
    "                    pre_goal = self._make_pregrasp_goal(goal, hover_z=0.15)\n"
    "                    self._diag_label = \"reach_hover\"\n"
    "                    pre_success, pre_steps, pre_done = self._execute_single_skill(skill, pre_goal)\n",
    "4 hover label")

# 5: reset accumulators before the step loop
replace(
    "        steps = 0\n        while plan_success and steps < self.cfg.max_steps:\n",
    "        steps = 0\n"
    "        # §2 diagnostic: reset per-skill accumulators; capture bowl start position.\n"
    "        self._diag_max_force = 0.0\n"
    "        self._diag_force_first_contact_step = -1\n"
    "        self._diag_bowl_first_move_step = -1\n"
    "        try:\n"
    "            self._diag_bowl_start = self._env.scene[\"akita_black_bowl\"].data.root_pos_w[self._env_id][:3].detach().cpu()\n"
    "        except Exception:\n"
    "            self._diag_bowl_start = None\n"
    "        while plan_success and steps < self.cfg.max_steps:\n",
    "5 reset")

# 6: per-step instrumentation (replace the record_head_view + steps block)
replace(
    "            self._record_head_view_frame()\n\n            steps += 1\n",
    "            self._record_head_view_frame()\n\n"
    "            # §2 diagnostic: contact force + bowl movement during reach on bowl.\n"
    "            if self._diag_target_object == \"akita_black_bowl\" and self._diag_skill_type == \"reach\":\n"
    "                try:\n"
    "                    arm = self._current_arm\n"
    "                    body_names = self._robot.data.body_names\n"
    "                    gripper_links = ([\"gripper_base_l\", \"link7_l\", \"link8_l\"] if arm == \"left\"\n"
    "                                     else [\"gripper_base_r\", \"link7_r\", \"link8_r\"])\n"
    "                    max_force = 0.0\n"
    "                    for ln in gripper_links:\n"
    "                        if ln in body_names:\n"
    "                            idx = body_names.index(ln)\n"
    "                            f = float(torch.linalg.norm(\n"
    "                                self._robot.data.net_contact_forces[self._env_id, idx]).cpu())\n"
    "                            if f > max_force:\n"
    "                                max_force = f\n"
    "                    if max_force > self._diag_max_force:\n"
    "                        self._diag_max_force = max_force\n"
    "                    if self._diag_force_first_contact_step < 0 and max_force > 0.5:\n"
    "                        self._diag_force_first_contact_step = steps\n"
    "                    if self._diag_bowl_start is not None:\n"
    "                        bowl_now = self._env.scene[\"akita_black_bowl\"].data.root_pos_w[self._env_id][:3].detach().cpu()\n"
    "                        move = float(torch.linalg.norm(bowl_now - self._diag_bowl_start))\n"
    "                        if self._diag_bowl_first_move_step < 0 and move > 0.01:\n"
    "                            self._diag_bowl_first_move_step = steps\n"
    "                    if steps % 10 == 0 or max_force > 0.5:\n"
    "                        self._logger.info(\n"
    "                            f\"[diag {self._diag_label}] step={steps} max_force={max_force:.3f} N \"\n"
    "                            f\"(run_max={self._diag_max_force:.3f})\"\n"
    "                        )\n"
    "                except Exception as e:\n"
    "                    self._logger.warning(f\"diag instrumentation error: {e}\")\n\n"
    "            steps += 1\n",
    "6 per-step")

# 7: summary before the two early returns
replace(
    "            if bool((terminated[self._env_id] | truncated[self._env_id]).item()):\n"
    "                return True, steps, True\n"
    "            if output.done:\n"
    "                return True, steps, False\n",
    "            if bool((terminated[self._env_id] | truncated[self._env_id]).item()):\n"
    "                self._log_diag_summary()\n"
    "                return True, steps, True\n"
    "            if output.done:\n"
    "                self._log_diag_summary()\n"
    "                return True, steps, False\n",
    "7 early returns")

# 8: summary before the final return
replace(
    "                )\n\n        return False, steps, False\n",
    "                )\n\n        self._log_diag_summary()\n        return False, steps, False\n",
    "8 final return")

PATH.write_text(src)
print("ALL PATCHES APPLIED")
