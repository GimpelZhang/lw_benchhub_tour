# CLAUDE.md — `/mnt/robot` 项目交接文档

> 本文件为 Claude Code / 其他 AI agent 在 new session 中拾起本项目工作的**权威入口**。
> 最后更新：2026-06-28（v6 整合，本文档已精简，移除 v1-v5 中间迭代记录）
> 项目阶段：Stage 1 已完成（SmolVLA 双臂 Piper 闭环仿真，40% 成功率）；Stage 2 v6 已完成（lerobot-arena 单 env 内 live isaaclab + cuRobo IK reach gate + SmolVLA 闭环，2 段视频，per-object IK 证据齐全）；Stage 3 待启动。

---

## 0. 给新 Agent 的第一段话（务必先读）

1. **本机是无显示器的云服务器**：Ubuntu 22.04 / A800-SXM4-40GB / CUDA 11.8（系统）+ 12.8（lerobot-arena env-local，仅 cuRobo 用）。所有渲染走 EGL 离屏。
2. **磁盘约束**：`/` 容量极小，**一切安装/下载/输出都写在 `/mnt/robot/` 下**；运行 `df -h` 自查。
3. **conda env 是唯一可用的 Python 环境**：`lerobot-arena`（Python 3.11.15）。Stage 1/2 v6 都在这里。绝大多数报错的根因是没激活它。
4. **numpy 必须永远锁在 `1.26.0`**：Isaac Sim 5.1.0 的 C 扩展硬绑这个版本。任何 `pip install` 都可能拉到 2.x，**必须在每条 `pip install` 之后立刻 `pip install --no-deps numpy==1.26.0` 验证回锁**。
5. **`CUDA_VISIBLE_DEVICES` 必须 `unset`**：否则 Isaac Sim 相机渲染会 Segfault。
6. **sudo 密码可能变化**：每次 session 用户会在开场指令中告知。新 session 若需要 sudo，先问。
7. **HF_TOKEN 已在 `/mnt/robot/headless_env.sh` 内**。模型下载若 timeout 可考虑 `HF_ENDPOINT=https://hf-mirror.com`。
8. **当前已跑通的事**：Stage 1 baseline（SmolVLA + DoublePiper-Abs，task: `L90K1PutTheBlackBowlOnThePlate`，10 episode 中 4 个成功）+ Stage 2 v6（LLM 生成 2 scene + live isaaclab/cuRobo per-object reach gate + SmolVLA OOD 闭环）。

---

## 1. 项目背景与总目标

用户基于 **光轮科技 LW-BenchHub + NVIDIA IsaacLab-Arena + HuggingFace lerobot** 这套栈，
跑通**具身智能 VLA 模型闭环仿真测试 demo**，并向 Stage 2 (LLM 驱动场景生成) 扩展。

| Stage | 目标 | 状态 |
|-------|------|------|
| Stage 1 | 跑通至少一个 VLA 模型的闭环仿真，输出视频 + 单帧 + 评测指标 | ✅ 已完成（SmolVLA，40% 成功率） |
| Stage 2 | 引入 LLM 自动生成场景配置 + cuRobo 可达性闸门 + 闭环评测 | ✅ v6 已完成（详见 §11） |
| Stage 3 | 真实 3DGS 场景重建 + VLA 闭环 | ⏳ 待启动（见 `Stage3_Plan.md`） |

### 关键计划与文档

| 文档 | 用途 |
|------|------|
| `Complete_Stage_1.md` | Stage 1 完整复现指南（9 个补丁全记录），用户交付物，**不要修改** |
| `Stage1_Plan*.md` / `Stage1_Patch.md` | 历史计划文档，参考用 |
| `Stage2_Plan.md` | Stage 2 原始计划 |
| `headless_env.sh` | Stage 1/SmolVLA 用环境变量脚本 |
| `lerobot_arena_curobo_env.sh` | Stage 2 v6 cuRobo + isaaclab 共存所需的额外 env 脚本 |
| `llm_env.sh` | DeepSeek API key（mode 600） |

---

## 2. 仓库与组件清单

| 组件 | 路径 | 版本 |
|------|------|------|
| Isaac Sim | conda env `lerobot-arena` 内 | **5.1.0** |
| Isaac Lab | `/mnt/robot/IsaacLab` | **v2.3.2** |
| IsaacLab-Arena | `/mnt/robot/IsaacLab-Arena` | `release/0.1.1` |
| LeRobot | `/mnt/robot/lerobot` | 0.5.1 |
| LW-BenchHub | `/mnt/robot/lw_benchhub` | 0.1.0（已打补丁，见 §3） |
| lightwheel-sdk | pip | **1.0.3** |
| pin (pinocchio cmeel wheel) | pip | **4.0.0**，不含 `pinocchio.casadi` |
| ffmpeg | conda-forge | 7.1.x |
| numpy | pip | **1.26.0**（永远锁住） |
| cuRobo（lerobot-arena env-local） | `/mnt/robot/AutoDataGen/dependencies/curobo` | 0.7.7.post1.dev5（editable, sm_80） |
| warp-lang（lerobot-arena） | pip | **1.8.1**（pin，见 §11.1） |
| cuda-toolkit（lerobot-arena env-local） | conda | 12.8.93（仅 cuRobo 编译/运行用） |

> **Isaac Lab 版本漂移**：实际安装的是 v2.3.2，但原计划文档写的是 v2.3.0。v2.3.x 系列**删除了** `DEVICE_MAP` / `RETARGETER_MAP` 常量，并**新增了** `XformPrimView` 的严格 xform op 顺序校验——这两点是 Complete_Stage_1.md 中 9 个补丁的主要来源。

---

## 3. 已修改的源码文件（关键 monkey-patches）

这些修改让 lw_benchhub 适配 IsaacLab v2.3.x + lightwheel_sdk 1.0.3 + cmeel pin 4.0.0 的实际环境，以及 Stage 2 v6 的跨 env 兼容。**不要回滚！**

### 3.1 `/mnt/robot/lw_benchhub/lw_benchhub/utils/monkey_patch.py`

- `patch_create_teleop_device()`：检测到 `DEVICE_MAP`/`RETARGETER_MAP` 缺失时**优雅跳过**。
- **新增** `patch_xform_prim_view_auto_standardize()`：override `XformPrimView.__init__` 强制 `validate_xform_ops=False`。

### 3.2 `/mnt/robot/lw_benchhub/lw_benchhub/core/tasks/base.py`

```python
try:
    from lightwheel_sdk.loader import ENDPOINT
except ImportError:
    from lightwheel_sdk.client import ENDPOINT  # SDK 1.0.3 把 ENDPOINT 从 .loader 挪到 .client
```

### 3.3 `/mnt/robot/lw_benchhub/lw_benchhub/utils/pinocchio_ik/piper_ik.py`

1. 拆分 try/except：把 `pinocchio` 和 `pinocchio.casadi` 分开 try。
2. lazy-stub `__init__`：缺 casadi 时不 raise，标记 `self._is_stub=True`。
3. stub-aware `reset()`：`if getattr(self, "_is_stub", False): return`。

> SmolVLA 输出关节角，不走 IK 路径，所以 stub 不影响闭环 eval；但任何 `solve_pose_to_joints()` 调用都会 raise。

### 3.4 `/mnt/robot/lw_benchhub/__init__.py`（v6 namespace fix）

原始是 `pkg_resources.declare_namespace(__name__)` 的 stub，导致 `from lw_benchhub import CONFIGS_PATH` 在 cwd 非 `/mnt/robot/lw_benchhub` 时 ImportError。

**v6 修复**：用 `importlib.util` shim 加载内部真实包 `/mnt/robot/lw_benchhub/lw_benchhub/__init__.py`，并把 `sys.modules['lw_benchhub']` 指向它。备份在 `__init__.py.bak_v5`。从任意 cwd 都能正确解析 `CONFIGS_PATH`，Stage 1 不受影响。

### 3.5 `/mnt/robot/AutoDataGen/dependencies/curobo/src/curobo/__init__.py`（v6 cuRobo version-detect fix）

cuRobo 在 import time 调 `setuptools_scm.get_version()`，被 isaacsim 自带的 prebundle 版本干扰。

**v6 修复**：在 setuptools_scm 路径之前**优先**读取 `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO` 环境变量，从 `lerobot_arena_curobo_env.sh` 注入。备份在 `__init__.py.bak_v6`。

### 3.6 完整补丁清单见 `Complete_Stage_1.md` 第 4 节（Stage 1 的 9 个坑，按时间顺序）

---

## 4. 运行 Stage 1 闭环仿真（黄金路径）

### 4.1 完整启动序列

```bash
# 1. 激活 conda + 注入环境变量
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES

# 2. 验证 numpy 还是 1.26.0
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"

# 3. 清理 + 启动
pkill -9 -f "isaacsim\|lerobot-eval\|kit/python" 2>/dev/null || true
mkdir -p /mnt/robot/eval_outputs_pathB_1
nohup bash /mnt/robot/pathB_logs/run_pathB.sh > /mnt/robot/pathB_logs/run_pathB.log 2>&1 &
echo $! > /mnt/robot/pathB_logs/run_pathB.pid

# 4. 监控
tail -F /mnt/robot/pathB_logs/run_pathB.log | \
  grep -E "EXIT_CODE|FINISHED|Traceback|Error:|running_success_rate|episode [0-9]+/"
```

### 4.2 启动脚本 `/mnt/robot/pathB_logs/run_pathB.sh` 关键参数

`lerobot-eval --policy.path=LightwheelAI/smolvla-double-piper-pnp ...`：
- `--env.state_dim=16`、`--env.action_dim=12`（DoublePiper）
- `--env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb`
- `--rename_map='{"observation.images.left_hand_camera_rgb": "observation.images.left_hand", ...}'`
- `--env.kwargs='{"config_path": "configs/envhub/example.yml"}'`（**相对路径，cwd 必须是 `/mnt/robot/lw_benchhub`**）
- `--trust_remote_code=true`、`--eval.batch_size=1`、`--eval.n_episodes=10`

### 4.3 Stage 1 baseline 输出

| 项 | 值 |
|----|----|
| 输出目录 | `/mnt/robot/eval_outputs_pathB_1/` |
| 视频 | `eval_outputs_pathB_1/videos/<env>/eval_episode_{0,1}.mp4`（默认只录前 2 个） |
| 任务 | `L90K1PutTheBlackBowlOnThePlate`（robocasa-libero-1-1 场景） |
| 成功率 | **40% (4/10)**，运行 10m39s |

要录全部 episode，加 `--eval.max_episodes_rendered=10`。

---

## 5. 故障排除速查

| 症状 | 根因 | 一行修复 |
|------|------|---------|
| `FileNotFoundError: configs/envhub/example.yml` | cwd 错 | `cd /mnt/robot/lw_benchhub` |
| `cannot import name 'DEVICE_MAP'` | IsaacLab v2.3.x 移除 | monkey_patch.py 已修，确认未被回滚 |
| `cannot import name 'ENDPOINT' from 'lightwheel_sdk.loader'` | SDK 1.0.3 API 漂移 | `base.py` 的 dual-import shim |
| `ImportError: pinocchio is required` | `pin` 包未装 | `pip install pin==4.0.0` 然后立即 `pip install --no-deps numpy==1.26.0` |
| `cannot import name 'casadi' from 'pinocchio'` | cmeel wheel 不含 casadi 绑定 | `piper_ik.py` 的 lazy-stub 已修 |
| `is not a xformable prim with standard transform operations` | USD prim op 顺序非标准 | `patch_xform_prim_view_auto_standardize` 已修 |
| `'PiperPinocchioIK' object has no attribute '_model'` | env.reset() 调到 stub | `reset()` 内的 `_is_stub` 守卫 |
| Isaac Sim Segfault on 相机 | `CUDA_VISIBLE_DEVICES` 被设 | `unset CUDA_VISIBLE_DEVICES` |
| `numpy != 1.26.0` | 某次 pip 升级了 numpy | `pip install --no-deps numpy==1.26.0` |
| HF 下载 timeout | 网络问题 | 试 `HF_ENDPOINT=https://hf-mirror.com` |
| `from lw_benchhub import CONFIGS_PATH` ImportError | namespace stub 抢占 | §3.4 v6 patch 已修 |
| `module 'warp.types' has no attribute 'array'` | warp-lang 1.14.0 与 isaacsim 5.1 不兼容 | §11.1 `pip install --no-deps warp-lang==1.8.1` |
| cuRobo `setuptools-scm was unable to detect version` | isaacsim prebundle 干扰 | §3.5 v6 patch + `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO` |

完整 Stage 1 9 坑详解 → `Complete_Stage_1.md` §4。

---

## 6. 目录速览

```
/mnt/robot/
├── CLAUDE.md                         ← 本文件
├── Complete_Stage_1.md               ← Stage 1 复现指南（用户成品）
├── Stage1_Plan*.md / Stage1_Patch.md / Stage2_Plan.md
├── headless_env.sh                   ← Stage 1 env（必 source）
├── lerobot_arena_curobo_env.sh       ← Stage 2 v6 cuRobo env（v6 时 source）
├── llm_env.sh                        ← DeepSeek API key
├── pathB_logs/                       ← Stage 1 路径 B 日志与启动脚本
├── eval_outputs_pathB_1/             ← Stage 1 baseline 输出
├── stage2_logs/                     ← Stage 2 v6 日志、final_manifest.json、smoketest
├── eval_outputs_stage2_scene{1,2}/  ← Stage 2 v6 视频
├── stage2_final_deliverables/       ← v6 summary.md + snapshot PNG
├── lw_benchhub/configs/envhub/generated/  ← v6 LLM 生成的场景 yml
├── generate_scenes_with_live_reach.py  ← v6 LLM 生成 + reach gate
├── validate_scene_objects_reach.py     ← v6 实际调用的 IK validator
├── verify_stage2.py
├── v5_install_logs/, v6_install_logs/  ← 安装日志
├── AutoDataGen/                      ← cuRobo 仓库（submodule 已 init）
├── IsaacLab/                         ← Isaac Lab v2.3.2 源码
├── IsaacLab-Arena/                   ← release/0.1.1
├── lerobot/                          ← HuggingFace lerobot
├── lw_benchhub/                      ← 光轮 BenchHub（已打补丁，见 §3）
├── conda/envs/lerobot-arena          ← 主 env（含 env-local cuda-toolkit 12.8）
├── models/                           ← 本地缓存的模型权重
└── .omc/                             ← OMC orchestrator state（不要碰）
```

> v1-v5 的输出目录（`eval_outputs_stage2_v{1..5}*`、`pathB_logs_v{2..5}`、`stage2_*final_deliverables`、`lw_benchhub/configs/envhub/generated{_v3,_v4}` 等）仍存在硬盘上但已不重要，可在需要空间时清理。

---

## 7. 给新 Agent 的协作约定

1. **不要修改 `Complete_Stage_1.md`**——用户交付物，按用户意图保持原样。
2. **新尝试请用新输出目录**：`/mnt/robot/eval_outputs_<your_label>/`，不要覆盖 `eval_outputs_pathB_1` 或 v6 输出。
3. **修改 lw_benchhub 源码前先记录**：在本文件的 §3 追加一行说明。
4. **后台长跑用 `nohup ... &` + PID 文件**：见 `pathB_logs/run_pathB.pid` 模式。
5. **跑大模型前先 `nvidia-smi`**：确认 40 GB 显存空闲。残留进程用 `pkill -9 -f "isaacsim\|lerobot-eval\|kit/python"`。
6. **凡是动了 `pip`，最后一步永远是 `pip install --no-deps numpy==1.26.0` + `python -c "import numpy; print(numpy.__version__)"` 验证**。
7. **OMC autopilot/ralph/team 等模式开启后**，正常结束时记得 `/oh-my-claudecode:cancel` 清理 state。

---

## 8. 已知遗留问题

1. **Stage 1 成功率仅 40%**：episode 数 10 个，波动大。加 `--eval.n_episodes=50` 可得更稳统计。
2. **只录前 2 个 episode 视频**：默认 `max_episodes_rendered=2`，加 `--eval.max_episodes_rendered=10` 全录。
3. **pinocchio.casadi 缺失**：cmeel wheel 限制。若要恢复完整 IK（teleop 数据采集），需 `conda install -c conda-forge pinocchio` 安装带 casadi 的版本，然后回滚 `piper_ik.py` lazy-stub。conda-forge 安装曾出现 solver 卡 15+ 分钟死锁，记得加 `--strict-channel-priority` 或限制 channel。
4. **lw_benchhub 的 `pyproject.toml` 依赖声明不完整**：`tyro / vuer[all]==0.0.70 / pyzmq / qpsolvers==4.8.1 / flask / mediapy / zmq / num2words / casadi / lazy-import` 都需手动 `pip install`。
5. **IsaacLab 版本漂移**：实际 v2.3.2，所有 monkey-patch 围绕 2.3.x。升级到 v2.4+ 要重新测。
6. **dual-arm IK 仍是单臂 kinematics 镜像**（v6 reach gate 中）：左右臂用同一份 `piper_curobo.yml` 加 ±15 cm lateral offset 模拟，没有合成双臂 12-DoF URDF。
7. **SmolVLA OOD 闭环 0% 成功率**：模型只在 `libero-1-1/L90K1PutTheBlackBowlOnThePlate` fine-tune。Stage 2 跑任何别的 task 都 OOD。要拿非 0 成功率得 fine-tune 跨 task 泛化的 VLA，或专门挑分布接近的 task。

---

## 9. 快速健康检查脚本

新 session 启动后跑一遍能省 1 小时排错：

```bash
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
unset CUDA_VISIBLE_DEVICES

python - <<'PY'
import sys
print("Python:", sys.version)
import numpy; assert numpy.__version__ == "1.26.0", f"BAD numpy {numpy.__version__}"
print("numpy:", numpy.__version__, "OK")
import torch; print("torch:", torch.__version__, "cuda:", torch.cuda.is_available())
import isaacsim, isaaclab, isaaclab_arena, lerobot, lw_benchhub
print("isaaclab:", isaaclab.__version__ if hasattr(isaaclab,'__version__') else 'n/a')
import pinocchio; print("pinocchio:", pinocchio.__version__)
try:
    from pinocchio import casadi
    print("pinocchio.casadi: AVAILABLE")
except ImportError:
    print("pinocchio.casadi: MISSING (expected; lazy-stub in effect)")
from lightwheel_sdk.client import ENDPOINT
print("lightwheel_sdk.client.ENDPOINT:", ENDPOINT[:50] if ENDPOINT else "(empty)")
from lw_benchhub import CONFIGS_PATH
print("lw_benchhub.CONFIGS_PATH:", CONFIGS_PATH)
print("ALL GREEN")
PY

nvidia-smi --query-gpu=memory.free --format=csv,noheader
ls /mnt/robot/lw_benchhub/configs/envhub/example.yml && echo "config OK"
```

要验证 v6 cuRobo 链路（可选）：

```bash
source /mnt/robot/lerobot_arena_curobo_env.sh
python -c "
import warp; assert hasattr(warp.types, 'array')
print('warp:', warp.__version__, 'warp.types.array OK')
import curobo
from curobo.wrap.reacher.ik_solver import IKSolver, IKSolverConfig
print('cuRobo import OK')
"
```

---

## 10. Stage 2 v6 — Single-env Live isaaclab + cuRobo Reach Gate（2026-06-27）

Stage 2 经过 v1-v5 多轮迭代（cuRobo 跳过 → workspace IK → AST literal IK → CSV-derived world IK → cross-env split → namespace/warp ABI fight），最终在 **v6** 收敛到：**在同一个 `lerobot-arena` env 内同时跑 isaaclab + cuRobo**，做真正的 live scene reach gate（启动 isaaclab 渲染场景 → 读 prim 世界位姿 → cuRobo IK 验可达 → 通过的 yml 进 SmolVLA 闭环）。本节是 Stage 2 当前唯一权威版本，v1-v5 的中间文档已在本次精简中移除。

### 10.1 关键交付物

```
/mnt/robot/
├── lerobot_arena_curobo_env.sh                  ← cuRobo + isaaclab 共存所需 env 脚本（必 source）
├── lw_benchhub/__init__.py                      ← namespace shim（§3.4）
├── AutoDataGen/dependencies/curobo/src/curobo/__init__.py  ← PRETEND_VERSION 优先（§3.5）
├── piper_curobo.yml                             ← Piper 单臂 kinematics 配置（6-DoF）
├── generate_scenes_with_live_reach.py        ← LLM 生成 + live reach gate（MAX_ROUNDS=5）
├── validate_scene_objects_reach.py           ← v6 实际复用的 IK validator
├── verify_stage2.py                          ← v6 deliverable 校验
├── stage2_logs/
│   ├── final_manifest.json                      ← 2 accepted scene + banned 列表 + 真实 init pose
│   ├── generate_scenes.log
│   ├── scene_reach_reports/scene_{1,2}_reach.json  ← per-object world_pos + IK err
│   ├── smoketest.json                        ← v6 link 端到端证据（chefmate_8_frypan reach）
│   ├── run_stage2_scene.sh / run_stage2_all.sh
│   └── run_stage2_scene{1,2}.log
├── lw_benchhub/configs/envhub/generated/scene_variation_{1,2}.yml
├── eval_outputs_stage2_scene{1,2}/           ← 各 2 mp4（video_length=1100, 22s 完整 episode）
└── stage2_final_deliverables/
    ├── stage2_summary.md
    └── scene_{1,2}_render_snapshot.png
```

### 10.2 v6 通过 reach gate 的 2 个场景（per-object 证据齐全）

| # | Layout / Task | Seed | n_obj | reach_ratio | SmolVLA SuccessRate |
|---|---|---|---|---|---|
| 1 | libero-1-1 / L10K3TurnOnTheStoveAndPutTheMokaPotOnIt | 12 | 1 (chefmate_8_frypan) | 1.0 ✅ | 0.0% (OOD) |
| 2 | libero-8-8 / LGPutTheBowlOnThePlate | 34 | **4** (plate, akita_black_bowl, wine_bottle, cream_cheese) | 1.0 ✅ | 0.0% (OOD) |

Scene 2 per-object IK 详情（v6 区别于 v3/v4 的关键证据）：

```
plate            world(2.25,-2.17,0.79)  left_err=0.0082  right_err=0.0012  ✅
akita_black_bowl world(2.48,-1.93,0.81)  left_err=0.0128  right_err=0.0013  ✅
wine_bottle      world(2.62,-1.95,0.90)  left_err=0.0296  right_err=0.0025  ✅
cream_cheese     world(2.08,-1.90,0.79)  left_err=0.0167  right_err=0.0031  ✅
```

所有 4 个物体右臂触达 < 1 cm。4 个 IK 误差来自 4 个独立 prim-collection 样本（不是 v4 风格的硬编码外推）。

Banned 列表（v6 reach gate 实际拒绝过的 (layout, task)）：
- `robocasakitchen-61-5 / ArrangeTableware` → `gym.NameNotFound`
- `libero-4-4 / L10S1PickUpTheBookAndPlaceItInTheBackCompartmentOfTheCaddy` → isaaclab boot hang（58 min CPU, 手动 kill）

闭环 SmolVLA 0% 成功率与 v1-v5 同因（SmolVLA OOD）。v6 的交付目标是"live reach gate + 闭环 pipeline 端到端打通"，不是 success_rate。

### 10.3 v6 关键技术决策

**§16.4 BLOCK 项的解法 = warp 版本 pin**：

根因：pip 默认 `warp-lang 1.14.0` 删除了 `warp.types.array`，而 isaacsim 5.1 的 `isaacsim/core/utils/warp/rotations.py:25` 依赖它；cuRobo 也 import warp。两者必须共用一个兼容版本。

证据：
- pip 默认: `warp-lang 1.14.0` → `hasattr(warp.types, "array")` False
- isaacsim 自带: `omni.warp.core 1.8.2+lx64` → 依赖 `warp.types.array`
- autosim env (无冲突): `warp 1.12.0`
- PyPI 上 1.8.2 不存在，但 1.8.1 存在且同 minor 系列

**修复**: `pip install --no-deps warp-lang==1.8.1` + 立即 `pip install --no-deps numpy==1.26.0` 回锁。
验证后:
- `warp 1.8.1`, `warp.types.array exists: True`
- numpy 1.26.0 锁住
- `import curobo` OK, `IKSolver/IKSolverConfig` 可导入
- `import lw_benchhub` OK
- Stage 1 §9 healthcheck 仍 all green

安装日志: `/mnt/robot/v6_install_logs/install_warp_pin_v2.log`。

**cuRobo __init__.py PRETEND_VERSION patch**: 见 §3.5。让 cuRobo 在 isaacsim 已加载后仍能跳过 setuptools_scm 自动检测。

**cuda-toolkit 12.8 inside lerobot-arena**: `conda install -y -c nvidia/label/cuda-12.8.1 cuda-toolkit` + 立即 numpy 回锁。env-local nvcc 12.8.93 通过 `lerobot_arena_curobo_env.sh` 的 PATH prepend 在 cuRobo 编译时生效；Stage 1 不 source 该脚本，所以 SmolVLA 看到的仍是系统 nvcc 11.8（无关，SmolVLA 不调 nvcc）。

**cuRobo 编译**: `cd /mnt/robot/AutoDataGen/dependencies/curobo && pip install -e . --no-build-isolation && pip install --no-deps numpy==1.26.0`. 装时 `lerobot_arena_curobo_env.sh` 必须 source（提供 `MAX_JOBS=4`、`TORCH_CUDA_ARCH_LIST=8.0`、`CUDA_HOME` 等）。安装日志：`/mnt/robot/v6_install_logs/install_curobo.log`。

### 10.4 v6 live-IK 工作流（实现细节）

```
generate_scenes_with_live_reach.py (lerobot-arena env)
    │
    ├─ DeepSeek 出 3 个 (overrides) JSON，CSV+whitelist 双重 schema 校验
    │
    └─ 每个 yml → 直接 import validate_scene_objects_reach._main(...)
                                                    │
        validate_scene_objects_reach (同进程 lerobot-arena env)
            ├─ export_env_for_envhub(...) → AppLauncher 启 Isaac Sim 5.1，加载 USD floorplan，env.reset()
            ├─ 读 env.scene.<rigid_object>.data.root_pos_w[0] —— 真实世界位姿
            ├─ 读 robot 的 root_state_w[0]（pos + quat → yaw）
            ├─ 加载 piper_curobo.yml → IKSolver, num_seeds=16, rotation_threshold=π, pos_threshold=0.01
            ├─ 对每个 object: world→arm_base = R_yaw.T @ (obj_world - arm_base_world)
            │   左/右臂 base 取 robot world pos ± 0.15 m lateral（绕 yaw 旋转后）
            └─ reach_ratio = (#either-arm pos_err < 1cm) / n_obj；threshold 0.50 → pass/fail
    │
    └─ 失败 (layout, task) → 加 banned；下一轮 prompt 里 LLM 避开；最多 5 轮
```

### 10.5 v6 快速复现命令

```bash
source /home/vipuser/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source /mnt/robot/headless_env.sh
source /mnt/robot/lerobot_arena_curobo_env.sh
source /mnt/robot/llm_env.sh
unset CUDA_VISIBLE_DEVICES

# 1) LLM gen + live reach gate（一个 env，全程在 lerobot-arena）
python /mnt/robot/generate_scenes_with_live_reach.py

# 2) SmolVLA 闭环评测（同 env）
N_EPISODES=3 bash /mnt/robot/stage2_logs/run_stage2_all.sh

# 3) verify + 交付物
python /mnt/robot/verify_stage2.py
cat /mnt/robot/stage2_final_deliverables/stage2_summary.md
```

> v6 runners (`run_stage2_*.sh`) 用 `set +u`（不是 `set -u`），因为 conda 25 的 `~cuda-nvcc_activate.sh` 引用了未绑定的 `NVCC_PREPEND_FLAGS`，`set -u` 下会立刻 abort。

### 10.6 v6 已知遗留 / 可改进点（诚实声明）

1. **Scene 3 banning 不够优雅**：libero-4-4 boot hang 时只有手动 `pkill -9` 才能继续。validator 应加 5 min boot 超时。
2. **Round-1 gym registry mismatch** (`ArrangeTableware`)：CSV 有但 gym 未注册。validator 应识别 `gym.NameNotFound` 并立刻 ban，不烧一整轮 reach check。
3. **2 scene 而非 3 scene**：原计划 3 scene。v6 reach gate 严格性高，前 5 轮通过 2 个就停了。要凑 3 个把 `MAX_ROUNDS` 提到 8 再跑一轮即可。
4. **dual-arm IK 仍是单臂 kinematics 镜像**：±0.15 m lateral offset 假设。真正双臂需要 12-DoF URDF 或合成双臂模型。
5. **SmolVLA 0% OOD success rate**：v6 没尝试解，跟 v1-v5 同因。

### 10.7 Stage 1 仍然完全可用（regression-safe）

v6 的所有改动都不影响 Stage 1：

- §10.3 的 cuda-toolkit 与 cuRobo 安装：只在 `lerobot_arena_curobo_env.sh` 被 source 时进入 PATH；Stage 1 不 source 它。
- §3.4 namespace fix：严格改进，从任意 cwd 都能 import；Stage 1 不受影响。
- warp-lang 1.8.1 pin：替换了 pip 默认 1.14.0；isaacsim 5.1 本来就期望旧版本，SmolVLA 不受影响。

Stage 1 复现命令仍是 §4.1。

---

## 11. 进入 Stage 3 时的额外准备

参考 `Stage3_Plan.md`（如果存在）。Stage 3 目标是真实 3DGS 场景重建 + VLA 闭环，预计需要：

- 3DGS 训练管线（`gsplat` / `nerfstudio` / `splat-rt`）
- 从真实世界扫描数据 → USD 资产的转换工具
- 与 lw_benchhub 现有 layout/task 体系的对接

预期坑（基于 Stage 1/2 经验）：
- 3DGS 渲染可能与 Isaac Sim 5.1 EGL 模式冲突，需要 headless 兼容性测试
- numpy 1.26.0 锁仍然适用
- 若 3DGS 训练需要新版 PyTorch / CUDA，可能要新建独立 conda env（参照 v6 双 env 模式）

---

**End of CLAUDE.md** — 维护者：在每次重大改动后追加 §3 补丁记录、§8 遗留问题，或新增小节。保持本文档可执行、可复现。
