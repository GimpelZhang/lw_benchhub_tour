# /mnt/robot/autosim_env.sh — env activation for the `autosim` conda env
# Source this BEFORE running anything that imports curobo / isaacsim / isaaclab inside this env.
# Pairs with conda activate /mnt/robot/conda/envs/autosim
#
# Usage:
#   source /home/vipuser/miniconda3/etc/profile.d/conda.sh
#   conda activate /mnt/robot/conda/envs/autosim
#   source /mnt/robot/autosim_env.sh
#
# Why each line matters (verified during Stage 2 cuRobo install, 2026-06-27):
#  - CUDA_HOME / PATH:           torch's cpp_extension picks up env's nvcc 12.8 (not system's 11.8)
#  - LD_LIBRARY_PATH:            conda's libstdc++ has CXXABI_1.3.15 needed by curobolib *.so;
#                                system libstdc++ lacks it → ImportError on bare `import curobo`
#  - TORCH_CUDA_ARCH_LIST=8.0:   A800 = sm_80; avoids JIT recompile for other archs
#  - unset CUDA_VISIBLE_DEVICES: Isaac Sim camera renderer segfaults when this is set
#  - UV_CACHE_DIR:               keeps wheel cache on /mnt (300G) not /home (small)

export CUDA_HOME=/mnt/robot/conda/envs/autosim
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib:$LD_LIBRARY_PATH
export TORCH_CUDA_ARCH_LIST="8.0"
unset CUDA_VISIBLE_DEVICES

# Builds + downloads
export UV_CACHE_DIR=/mnt/robot/conda/uv_cache
export UV_HTTP_TIMEOUT=600
export MAX_JOBS=4

# Headless rendering (consistent with /mnt/robot/headless_env.sh for lerobot-arena)
export DISPLAY=
export PYOPENGL_PLATFORM=egl
