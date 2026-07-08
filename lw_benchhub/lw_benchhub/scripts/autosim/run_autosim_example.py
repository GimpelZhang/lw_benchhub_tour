"""Script to run autosim example."""


import argparse
from isaaclab.app import AppLauncher
import traceback


# add argparse arguments
parser = argparse.ArgumentParser(description="run autosim example pipeline.")
parser.add_argument("--pipeline_id", type=str, default=None, help="Name of the autosim pipeline.")
parser.add_argument("--robot_profile", type=str, default=None, help="Name of the robot profile.")
parser.add_argument("--num_runs", type=int, default=1, help="Number of runs to run.")

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


def main():
    pipeline = make_pipeline(args_cli.pipeline_id, robot_profile=args_cli.robot_profile)
    for i in range(args_cli.num_runs):
        print(f"====== Running autosim pipeline [{i+1}/{args_cli.num_runs}] ======")
        try:
            pipeline.run()
        except Exception as e:
            print(f"Error: {e}")
            print(traceback.format_exc())
            continue


if __name__ == '__main__':
    main()
