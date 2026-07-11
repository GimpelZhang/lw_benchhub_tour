#!/usr/bin/env python3
"""Check whether the cuRobo gripper mesh collision actually loads.

Builds the CuroboPlanner's robot model from piper_curobo_left.yml + inspects:
  - mesh_link_names in the config
  - get_robot_link_meshes() — are the gripper meshes non-empty?
  - the collision checker's robot spheres/meshes

Pure cuRobo (no Isaac Sim)."""
from __future__ import annotations
import os, sys
os.environ.setdefault("SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO", "0.7.7.post1.dev5")

from curobo.types.base import TensorDeviceType
from curobo.util_file import load_yaml
from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig

CUROBO_CFG_DIR = "/mnt/robot/stage4_flywheel/curobo"
tdtype = TensorDeviceType()

cfg_dict = load_yaml(f"{CUROBO_CFG_DIR}/piper_curobo_left.yml")
kin = cfg_dict["robot_cfg"]["kinematics"]
print("config mesh_link_names:", kin.get("mesh_link_names"))
print("config collision_link_names:", kin.get("collision_link_names"))
print("config collision_spheres keys:", list(kin.get("collision_spheres", {}).keys()))

# Build the IK config (which builds the robot model).
ik_cfg = IKSolverConfig.load_from_robot_config(
    cfg_dict, None,
    rotation_threshold=3.14, position_threshold=0.01, num_seeds=4,
    self_collision_check=False, self_collision_opt=False,
    tensor_args=tdtype, use_cuda_graph=False,
)
solver = IKSolver(ik_cfg)

# Inspect the robot model's collision meshes.
robot_model = solver.robot_config.kinematics
print("\nrobot_model type:", type(robot_model).__name__)
print("robot_model.mesh_link_names:", getattr(robot_model, "mesh_link_names", "N/A"))

try:
    meshes = robot_model.get_robot_link_meshes()
    print(f"\nget_robot_link_meshes(): {len(meshes)} meshes")
    for i, m in enumerate(meshes):
        # Mesh object — try to inspect vertices/faces
        nv = getattr(m, "vertices", None)
        nf = getattr(m, "faces", None)
        name = getattr(m, "name", f"mesh_{i}")
        nv_count = len(nv) if nv is not None and hasattr(nv, "__len__") else "?"
        nf_count = len(nf) if nf is not None and hasattr(nf, "__len__") else "?"
        print(f"  mesh[{i}] name={name} vertices={nv_count} faces={nf_count}")
except Exception as e:
    print(f"\nget_robot_link_meshes() FAILED: {type(e).__name__}: {e}")

# Also check the collision checker's robot spheres.
try:
    cc = solver.robot_config
    print("\nrobot_config collision_checker_type:", getattr(cc, "collision_checker_type", "N/A"))
except Exception as e:
    print("cc inspect failed:", e)

# Phase 2 (Stage4_Patch_01 §4.3.4): report loaded collision spheres from the CudaRobotModel.
# solver.kinematics is the CudaRobotModel; total_spheres/robot_spheres reflect what cuRobo actually
# loaded (config collision_spheres are only active for links listed in collision_link_names).
km = solver.kinematics
print("\nPhase 2 sphere load check:")
print("  kinematics.total_spheres:", getattr(km, "total_spheres", "N/A"))
rs = getattr(km, "robot_spheres", None)
if rs is not None:
    print("  kinematics.robot_spheres.shape:", tuple(rs.shape))

print("\nDONE")
