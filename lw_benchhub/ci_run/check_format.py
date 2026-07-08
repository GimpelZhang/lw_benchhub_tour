#!/usr/bin/env python3
import os
import json
import shlex
import subprocess
import sys

if len(sys.argv) == 1:
    target_path = "."
else:
    target_path = sys.argv[1]


AUTOPEP8_CMD = (
    "autopep8 --diff --recursive "
    "--ignore=E501,E402 "
    "--exclude third_party "
    "--exit-code "
) + target_path

FLAKE8_CMD = (
    "flake8 "
    "--ignore E501,E402,F401,W503,E704,F841,F541,W504,W605,E266 "
    "--exclude third_party "

) + target_path


def run_cmd(cmd: str):
    try:
        proc = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True
        )
        return {
            "ok": proc.returncode == 0,
            "rc": proc.returncode,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip()
        }
    except FileNotFoundError:
        # command not found
        return {
            "ok": False,
            "rc": 127,
            "stdout": "",
            "stderr": f"Command not found: {cmd.split()[0]}"
        }
    except Exception as e:
        return {
            "ok": False,
            "rc": 2,
            "stdout": "",
            "stderr": f"Unexpected error running '{cmd}': {e}"
        }


def main():
    a = run_cmd(AUTOPEP8_CMD)
    f = run_cmd(FLAKE8_CMD)

    success = a["ok"] and f["ok"]

    # combine desc, put the stdout of both into it, for easy viewing of specific differences/alerts
    desc_parts = []
    desc_parts.append("=== autopep8 --diff output ===")
    desc_parts.append(a["stdout"] if a["stdout"] else "(empty)")
    desc_parts.append("\n=== flake8 output ===")
    desc_parts.append(f["stdout"] if f["stdout"] else "(empty)")
    desc = "\n".join(desc_parts).strip()

    # combine error: only summarize the stderr of the failed items
    err_parts = []
    if not a["ok"]:
        # if there is no stderr, but the return code is not 0, it is mostly because a fixable change was found
        if a["stderr"]:
            err_parts.append(f"[autopep8 rc={a['rc']}] {a['stderr']}")
        else:
            err_parts.append(f"[autopep8 rc={a['rc']}] Found formatting issues (see desc).")
    if not f["ok"]:
        if f["stderr"]:
            err_parts.append(f"[flake8 rc={f['rc']}] {f['stderr']}")
        else:
            err_parts.append(f"[flake8 rc={f['rc']}] Lint violations detected (see desc).")
    error = "\n".join(err_parts)

    result = {
        "success": success,
        "desc": desc,
        "error": error
    }
    print(desc)
    print(error)

    os.makedirs("/output", exist_ok=True)
    with open("/output/result.json", "w", encoding="utf-8") as fp:
        json.dump(result, fp, ensure_ascii=False, indent=4)

    # also print to the console, for easy viewing of CI logs
    # print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
