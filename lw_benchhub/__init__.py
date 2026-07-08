# v5 namespace-collision fix (CLAUDE.md §16):
#
# This outer __init__.py exists because /mnt/robot/lw_benchhub/ contains BOTH
# the project root AND an inner lw_benchhub/ Python package. When a tool runs
# with sys.path[0] = '' from /mnt/robot (or anywhere outside the project root),
# Python's path-based finder resolves `import lw_benchhub` to THIS file BEFORE
# the editable-install finder gets a chance to point at the real inner package.
#
# Historically this file was a `pkg_resources.declare_namespace(...)` stub,
# which (a) is deprecated and (b) does NOT merge attributes (like CONFIGS_PATH)
# from the inner package into this namespace. Result: `from lw_benchhub import
# CONFIGS_PATH` failed whenever the outer stub took precedence.
#
# v5 fix: shadow this module with the inner real package on first import,
# so the name `lw_benchhub` always resolves to /mnt/robot/lw_benchhub/lw_benchhub
# regardless of cwd / sys.path[0]. This keeps lerobot-eval (which historically
# worked by accident) green, AND lets scripts elsewhere on disk import
# lw_benchhub correctly.
import os
import sys
from importlib import util as _importlib_util

_inner_init = os.path.join(os.path.dirname(__file__), 'lw_benchhub', '__init__.py')
if os.path.isfile(_inner_init):
    _spec = _importlib_util.spec_from_file_location(
        __name__, _inner_init,
        submodule_search_locations=[os.path.join(os.path.dirname(__file__), 'lw_benchhub')],
    )
    _module = _importlib_util.module_from_spec(_spec)
    sys.modules[__name__] = _module
    _spec.loader.exec_module(_module)
