# Source this AFTER `conda activate lerobot-arena` to make env-local CUDA 12.8 toolchain win.
# Mirrors /mnt/robot/autosim_env.sh but for lerobot-arena env.
export CUDA_HOME=/mnt/robot/conda/envs/lerobot-arena
export PATH="$CUDA_HOME/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_HOME/lib:${LD_LIBRARY_PATH:-}"
export TORCH_CUDA_ARCH_LIST="8.0"   # A800 sm_80
export MAX_JOBS=4

# cuRobo uses setuptools_scm at IMPORT time to compute __version__. In
# lerobot-arena, isaacsim ships its own setuptools_scm copy in
# pip_prebundle/ that shadows the real one and fails to read the .git
# folder. Pin the version explicitly so `import curobo` works.
export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO="0.7.7.post1.dev5"

# cuRobo needs cuda.h in $CUDA_HOME/include but conda puts it in targets/x86_64-linux/include
if [ ! -f "$CUDA_HOME/include/cuda.h" ] && [ -f "$CUDA_HOME/targets/x86_64-linux/include/cuda.h" ]; then
  for h in "$CUDA_HOME/targets/x86_64-linux/include/"*.h; do
    name=$(basename "$h")
    [ -e "$CUDA_HOME/include/$name" ] || ln -sf "$h" "$CUDA_HOME/include/$name"
  done
  for d in "$CUDA_HOME/targets/x86_64-linux/include/"*/; do
    name=$(basename "$d")
    [ -e "$CUDA_HOME/include/$name" ] || ln -sf "$d" "$CUDA_HOME/include/$name"
  done
fi
