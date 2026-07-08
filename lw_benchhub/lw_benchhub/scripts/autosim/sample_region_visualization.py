"""Visualize object placement sample regions directly in the IsaacSim viewport (3D).

This script loads an autosim pipeline, resets the environment, and draws colored 3D
line boxes in the IsaacSim viewport showing:

  - Reset Region  (blue)        : the full valid surface area on the fixture where the
                                   object can physically land, as returned by
                                   fixture.get_all_valid_reset_region().
  - Sample Region (orange)      : the narrower rectangle actually used for random
                                   sampling, derived from the obj_cfg placement fields
                                   (size / pos / margin).  Corresponds directly to the
                                   x_ranges / y_ranges stored in the UniformRandomSampler.
  - Object Positions (green +)  : small cross markers at each reset's actual object
                                   landing position (only with --show_object_pos).
All coordinates are in the world frame.

Must be run WITHOUT --headless so the viewport is visible.

Usage
# Basic draw regions only:
python lw_benchhub/scripts/autosim/sample_region_visualization.py \\
    --pipeline_id <PIPELINE_ID> \\
    --obj_name obj

# With object position markers (30 resets):
python lw_benchhub/scripts/autosim/sample_region_visualization.py \\
    --pipeline_id <PIPELINE_ID> \\
    --obj_name obj \\
    --show_object_pos --num_resets 30
"""


import argparse
from isaaclab.app import AppLauncher


# add argparse arguments
parser = argparse.ArgumentParser(description="Sample region visualization in IsaacSim viewport.")
parser.add_argument("--pipeline_id", type=str, default=None, help="Name of the autosim pipeline.")
parser.add_argument("--obj_name", type=str, default="obj", help="Object name to visualize placement regions for.")
parser.add_argument("--show_object_pos", action="store_true", help="Draw cross markers at object positions across multiple resets.")
parser.add_argument("--num_resets", type=int, default=20, help="Number of resets used to collect object positions (only used with --show_object_pos).")

# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli = parser.parse_args()

app_launcher_args = vars(args_cli)

# launch omniverse app
app_launcher = AppLauncher(app_launcher_args)
simulation_app = app_launcher.app


import lw_benchhub.autosim

from autosim import make_pipeline
from lw_benchhub.utils.math_utils.transform_utils.numpy_impl import rotate_2d_point
from lw_benchhub.utils.ui_utils import draw_line, clear_debug_drawing


Z_LIFT = 0.001  # raise lines slightly above surfaces to avoid z-fighting


def rect_to_world(cx_local, cy_local, w, d, fixture_pos, fixture_rot):
    """Convert a rectangle in fixture-local frame to world-coordinate corner points.

    Args:
        cx_local: x center of rectangle in fixture local frame
        cy_local: y center of rectangle in fixture local frame
        w: width (x extent)
        d: depth (y extent)
        fixture_pos: fixture world position [x, y, z]
        fixture_rot: fixture yaw angle in radians

    Returns:
        list of 4 [x, y] world-coordinate corners (closed polygon order)
    """
    half_w, half_d = w / 2, d / 2
    corners_local = [
        (cx_local - half_w, cy_local - half_d),
        (cx_local + half_w, cy_local - half_d),
        (cx_local + half_w, cy_local + half_d),
        (cx_local - half_w, cy_local + half_d),
    ]
    corners_world = []
    for (lx, ly) in corners_local:
        wx, wy = rotate_2d_point([lx, ly], rot=fixture_rot)
        corners_world.append([wx + fixture_pos[0], wy + fixture_pos[1]])
    return corners_world


def xrange_to_world(x_range, y_range, reference_pos, reference_rot):
    """Convert a sampler x_range/y_range rectangle to world-coordinate corner points.

    x_ranges/y_ranges are already in fixture-local frame (offset + intra_offset applied).
    reference_pos and reference_rot are the fixture's world pose used by the sampler.

    Args:
        x_range: [min_x, max_x] in fixture local frame
        y_range: [min_y, max_y] in fixture local frame
        reference_pos: sampler.reference_pos (fixture world pos at region z)
        reference_rot: sampler.reference_rot (fixture yaw)

    Returns:
        list of 4 [x, y] world-coordinate corners (closed polygon order)
    """
    corners_local = [
        (x_range[0], y_range[0]),
        (x_range[1], y_range[0]),
        (x_range[1], y_range[1]),
        (x_range[0], y_range[1]),
    ]
    corners_world = []
    for (lx, ly) in corners_local:
        wx, wy = rotate_2d_point([lx, ly], rot=reference_rot)
        corners_world.append([wx + reference_pos[0], wy + reference_pos[1]])
    return corners_world


def draw_rect_3d(corners_2d, z, color, thickness=3.0):
    """Draw a closed rectangle as 4 line segments at height z.

    Args:
        corners_2d: list of 4 [x, y] world-frame corner points (in order)
        z: height of the rectangle in world frame
        color: RGBA tuple, e.g. (1.0, 0.5, 0.0, 1.0)
        thickness: line thickness in pixels
    """
    n = len(corners_2d)
    for i in range(n):
        a = (*corners_2d[i], z)
        b = (*corners_2d[(i + 1) % n], z)
        draw_line(a, b, color, thickness)


def draw_point_3d(pos, color, arm=0.05, thickness=3.0):
    """Draw a small 3-axis cross at pos=[x, y, z].

    Args:
        pos: [x, y, z] world position
        color: RGBA tuple
        arm: half-length of each cross arm in meters
        thickness: line thickness in pixels
    """
    x, y, z = pos
    draw_line((x - arm, y, z), (x + arm, y, z), color, thickness)
    draw_line((x, y - arm, z), (x, y + arm, z), color, thickness)
    draw_line((x, y, z - arm), (x, y, z + arm), color, thickness)


def visualize_in_sim(reset_regions, fixture, sampler, obj_positions=None):
    """Draw all regions and markers in the IsaacSim viewport using debug lines.

    Color legend:
        Blue   : reset regions (full valid fixture surface)
        Orange : sample regions (actual sampling rectangle from obj_cfg)
        Green  : object positions from multiple resets (--show_object_pos)

    Args:
        reset_regions: list of reset_region dicts (offset, size) in fixture local frame
        fixture: Fixture object with .pos and .rot attributes
        sampler: UniformRandomSampler with x_ranges, y_ranges, reference_pos, reference_rot
        obj_positions: optional list of [x, y, z] arrays collected across multiple resets
    """
    clear_debug_drawing()

    # reset regions — blue
    for rr in reset_regions:
        z = fixture.pos[2] + rr["offset"][2] + Z_LIFT
        corners = rect_to_world(
            rr["offset"][0], rr["offset"][1],
            rr["size"][0], rr["size"][1],
            fixture.pos, fixture.rot
        )
        draw_rect_3d(corners, z, color=(0.3, 0.6, 1.0, 1.0), thickness=2.0)

    # sample regions — orange
    for x_range, y_range in zip(sampler.x_ranges, sampler.y_ranges):
        z = sampler.reference_pos[2] + Z_LIFT
        corners = xrange_to_world(
            x_range, y_range,
            sampler.reference_pos, sampler.reference_rot,
        )
        draw_rect_3d(corners, z, color=(1.0, 0.55, 0.0, 1.0), thickness=3.0)

    # object positions — green small cross
    if obj_positions:
        for p in obj_positions:
            draw_point_3d(p, color=(0.0, 0.9, 0.2, 1.0))


def main():
    # load the pipeline and env
    pipeline = make_pipeline(args_cli.pipeline_id)
    env = pipeline.load_env()
    env.reset()

    # get the task and object name
    task = env.cfg.isaaclab_arena_env.orchestrator.task
    obj_name = args_cli.obj_name

    # locate the target object config
    matching = [c for c in task.object_cfgs if c["name"] == obj_name]
    if not matching:
        raise ValueError(f"Object '{obj_name}' not found. Available: {[c['name'] for c in task.object_cfgs]}")
    obj_cfg = matching[0]

    # fixture object (already resolved to Fixture instance by _get_obj_cfgs)
    fixture = obj_cfg["placement"]["fixture"]

    # reset_region is written into obj_cfg by _get_placement_initializer (env_utils.py)
    # it is populated after the first env.reset() triggers sample_object_placements()
    reset_regions = obj_cfg.get("reset_region", [])
    if not reset_regions:
        raise RuntimeError(f"reset_region not found in obj_cfg for '{obj_name}'. Ensure env.reset() has been called at least once.")

    # placement_initializer is lazily created on first sample_object_placements() call (env_utils.py)
    sampler_name = f"{obj_name}_Sampler"
    if not hasattr(task, "placement_initializer") or sampler_name not in task.placement_initializer.samplers:
        raise RuntimeError(f"Sampler '{sampler_name}' not found. Ensure env.reset() has been called at least once.")
    sampler = task.placement_initializer.samplers[sampler_name]

    # collect object positions (xyz) across multiple resets
    obj_positions = []
    if args_cli.show_object_pos:
        for _ in range(args_cli.num_resets):
            env.reset()
            pos = env.scene.rigid_objects[obj_name].data.root_pos_w[0].cpu().numpy()
            obj_positions.append(pos.tolist())  # xyz three-dimensional

    visualize_in_sim(
        reset_regions=reset_regions,
        fixture=fixture,
        sampler=sampler,
        obj_positions=obj_positions if obj_positions else None,
    )

    # keep sim running so user can inspect the viewport
    while simulation_app.is_running():
        simulation_app.update()


if __name__ == "__main__":
    main()
