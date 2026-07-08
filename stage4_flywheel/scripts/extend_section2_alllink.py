#!/usr/bin/env python3
"""§2 follow-up: extend the §2 instrumentation to an ALL-LINK contact-force scan.

The §2 finding showed gripper-link force = 0.0N during reach(bowl), yet the bowl moves.
This patch replaces the gripper-only force loop with a full-body scan that logs the
highest-force robot link each step. If NO link has force > 0.5N, the bowl movement is
settling (not contact) → Phase 2 (descend) is futile. If a non-gripper link contacts,
that identifies the real collision source.

Idempotent: re-running on an already-extended file is a no-op.
"""
import sys
from pathlib import Path

PATH = Path("/mnt/robot/AutoDataGen/source/autosim_examples/autosim_examples/autosim/pipelines/doublepiper_kitchen_pnp/doublepiper_kitchen_pnp.py")
src = PATH.read_text()

if "_diag_alllink_top" in src:
    print("ALREADY EXTENDED — no-op."); sys.exit(0)

# The gripper-only force loop to replace (exact match against the §2-patched file).
old = '''                    arm = self._current_arm
                    body_names = self._robot.data.body_names
                    gripper_links = (["gripper_base_l", "link7_l", "link8_l"] if arm == "left"
                                     else ["gripper_base_r", "link7_r", "link8_r"])
                    max_force = 0.0
                    for ln in gripper_links:
                        if ln in body_names:
                            idx = body_names.index(ln)
                            f = float(torch.linalg.norm(
                                self._robot.data.net_contact_forces[self._env_id, idx]).cpu())
                            if f > max_force:
                                max_force = f
                    if max_force > self._diag_max_force:
                        self._diag_max_force = max_force
                    if self._diag_force_first_contact_step < 0 and max_force > 0.5:
                        self._diag_force_first_contact_step = steps
                    if self._diag_bowl_start is not None:
                        bowl_now = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3].detach().cpu()
                        move = float(torch.linalg.norm(bowl_now - self._diag_bowl_start))
                        if self._diag_bowl_first_move_step < 0 and move > 0.01:
                            self._diag_bowl_first_move_step = steps
                    if steps % 10 == 0 or max_force > 0.5:
                        self._logger.info(
                            f"[diag {self._diag_label}] step={steps} max_force={max_force:.3f} N "
                            f"(run_max={self._diag_max_force:.3f})"
                        )'''

new = '''                    body_names = self._robot.data.body_names
                    # ALL-link scan: find which robot link (if any) has the highest contact force.
                    forces = self._robot.data.net_contact_forces[self._env_id]  # [num_bodies, 3]
                    force_mags = torch.linalg.norm(forces, dim=-1).detach().cpu().numpy()
                    max_idx = int(force_mags.argmax())
                    max_force = float(force_mags[max_idx])
                    max_link = str(body_names[max_idx])
                    if max_force > self._diag_max_force:
                        self._diag_max_force = max_force
                        self._diag_alllink_top = (max_link, max_force)
                    if self._diag_force_first_contact_step < 0 and max_force > 0.5:
                        self._diag_force_first_contact_step = steps
                    if self._diag_bowl_start is not None:
                        bowl_now = self._env.scene["akita_black_bowl"].data.root_pos_w[self._env_id][:3].detach().cpu()
                        move = float(torch.linalg.norm(bowl_now - self._diag_bowl_start))
                        if self._diag_bowl_first_move_step < 0 and move > 0.01:
                            self._diag_bowl_first_move_step = steps
                    if steps % 10 == 0 or max_force > 0.5:
                        import numpy as _np
                        top3 = _np.argsort(force_mags)[-3:][::-1]
                        top3_str = ", ".join(f"{body_names[i]}={float(force_mags[i]):.2f}N" for i in top3)
                        self._logger.info(
                            f"[diag {self._diag_label}] step={steps} max_force={max_force:.3f}N on {max_link} "
                            f"(run_max={self._diag_max_force:.3f}) top3: {top3_str}"
                        )'''

assert old in src, "gripper-only force block not found (file not §2-patched?)"
assert src.count(old) == 1
src = src.replace(old, new)

# Add the _diag_alllink_top instance var next to the other diag vars.
old_var = "        self._diag_bowl_first_move_step: int = -1\n"
new_var = ("        self._diag_bowl_first_move_step: int = -1\n"
           "        self._diag_alllink_top: tuple = (\"\", 0.0)  # (link_name, force) of run-max\n")
assert src.count(old_var) == 1
src = src.replace(old_var, new_var)

# Extend the summary to report the run-max link.
old_sum = '                f"bowl_end={bowl_end_str}"\n'
new_sum = ('                f"bowl_end={bowl_end_str} "\n'
           '                f"run_max_link={self._diag_alllink_top[0]} ({self._diag_alllink_top[1]:.3f}N)"\n')
assert src.count(old_sum) == 1
src = src.replace(old_sum, new_sum)

PATH.write_text(src)
print("ALL-LINK SCAN EXTENSION APPLIED")
