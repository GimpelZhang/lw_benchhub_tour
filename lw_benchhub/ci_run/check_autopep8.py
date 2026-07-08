#!/usr/bin/env python3
import os
import json
import shlex
import subprocess


def main():
    cmd = 'autopep8 --diff --recursive --ignore=E501,E402 --exclude third_party . --exit-code'
    # run command
    proc = subprocess.run(
        shlex.split(cmd),
        capture_output=True,
        text=True
    )

    success = (proc.returncode == 0)
    desc = (proc.stdout or "").strip()
    # only record stderr when failed, success will be empty
    error = (proc.stderr or "").strip() if not success else ""

    print(desc)
    print(error)

    result = {
        "success": success,
        "desc": desc,
        "error": error
    }

    os.makedirs("/output", exist_ok=True)
    with open("/output/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=4)

    # also print the result in the console, for local debugging/CI log viewing
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
