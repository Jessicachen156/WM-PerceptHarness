# 直接调用官方 CLIPScore

官方已提供 `compute_clip_score()`，无需自己重写。固定源码版本：`fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`。`official/vbench/` 收齐 `competitions/`、`vbench/`、`vbench2_beta_long/` 三个官方包及安装、说明、许可文件。这是与调用相关的官方源码集合，不是整个VBench-2.0仓库或已安装环境，不含模型权重。

## 官方接口和输入

从 `official/vbench/` 运行Python，或将该目录加入 `PYTHONPATH`：

```python
import torch
from competitions.clip_score import compute_clip_score

score, details = compute_clip_score(
    "/data/official_inputs.json", torch.device("cuda"), []
)
```

JSON使用官方格式，见 `examples/official_inputs.json`：

```json
[
  {
    "prompt_en": "A person opens a door.",
    "dimension": ["clip_score"],
    "video_list": ["/data/video.mp4"]
  }
]
```

可增加更多条目，一个prompt也可对应多个视频。使用真实的绝对视频路径，没有 `model` 字段，不要求预填哈希、帧数或窗口信息。每个视频与其整段目标文本配对，所有视频等权汇总；不同模型需要分别汇总时，分别提供输入文件。

`examples/call_official.py` 仅按正常import调用同一官方函数并保存结果，没有另外实现评分、抽帧、文本转换或汇总算法：

```bash
python examples/call_official.py \
  --input /data/official_inputs.json \
  --output /data/results/clipscore.json \
  --device cuda
```

官方 `clip_score.py` 本身没有 `__main__`，直接运行该文件不会执行评分；用上面的函数调用即可。

官方直接函数没有逐视频失败隔离或断点续跑：一个坏视频可能令本次调用整体抛错。调用示例只在全批成功后保存结果，拒绝覆盖同名文件。

## 环境与权重

官方competition文档使用Python3.9；请用独立且兼容的Python环境，先安装与机器匹配的一对PyTorch/TorchVision，再安装 `requirements-direct.txt`。该依赖文件是本包整理的直接导入依赖约束，不是作者完整环境锁，也尚未在新机器安装验收。原始官方requirements另行原样保留。

固定版官方 `setup.py` 会检查CUDA且仅接受部分旧版本；本路线按源码目录正常import，不必运行这个安装脚本。MoviePy 2没有旧代码需要的 `moviepy.editor`，所以使用 `moviepy<2`。其他维度的依赖和模型不在这份CLIP-only依赖说明范围。

远程安装、首次下载权重或推理前，先进入并验证持久会话：

```bash
tmux new-session -A -s clipscore
test -n "$TMUX"
# 已准备配套torch/torchvision后，在本指标包根目录：
python -m pip install -r requirements-direct.txt
python examples/call_official.py --input /data/official_inputs.json --output /data/results/clipscore.json --device cuda
```

分离：`Ctrl-b`后按`d`；重连：`tmux attach -t clipscore`。保留下载缓存、partial文件、目标路径、认证环境及下载后端。

官方函数调用 `clip.load("ViT-B/32")`，使用CLIP自身的缓存，缺权重时可能联网下载；可提前准备缓存。官方导入链涉及RAFT代码，但CLIP-only评分不加载RAFT权重。调用示例也接受 `--device cpu`；本轮没有做CPU或GPU数值推理验收。

## 官方命令行

在 `official/vbench/` 下，官方入口是：

```bash
python competitions/run_eval.py \
  --video_path /data/videos \
  --output_path /data/results \
  --prompt_file /data/short_prompt_list.txt \
  --dimension text_alignment
```

这个分组同时运行 `overall_consistency` 和 `clip_score`，需要该分组额外的依赖及权重；`requirements-direct.txt`仅针对前面的CLIP-only函数调用。不要改成不存在的 `--dimension clip_score`。官方脚本按提示词文件名中的 `short_prompt_list` / `long_prompt_list` 选择分支；逐行提示词须与排序后的视频对应。只需要CLIPScore时，优先用官方函数及JSON明确绑定视频路径。

## 与项目封装的区别

`modified/run_clipscore.py` 仅用于已有Wan/Dense实验：提取实际输入文字、按生成帧窗口切视频、记录哈希与日志等。其白名单用于选择项目专用映射，不是官方算法限制。它和 `modified/official_runtime.py` 在本次交付中保持原字节。

官方直接调用按提供的整段视频评分，不自动做Dense JSON转换或项目切窗。将原分窗输入改为整段视频时，输入与分数可能变化；复现原实验应继续使用项目入口。

两条路线均使用官方CLIP ViT-B/32、每输入视频8个区间中间帧、归一化图文特征余弦相似度。8帧不是8fps；77位置长度限制与 `truncate=True` 保留。分数不等于动作成功率或物理正确性。

## 来源与验证边界

[官方函数](https://github.com/Vchitect/VBench/blob/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/competitions/clip_score.py)、[官方competition说明](https://github.com/Vchitect/VBench/blob/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/competitions/README.md)。新增官方文件逐一核对固定Git提交的blob哈希；来源及SHA256见 `OFFICIAL_MANIFEST.json`。本次没有修改官方源码或运行真实视频评分，不把文件检查当作完整环境验收。
