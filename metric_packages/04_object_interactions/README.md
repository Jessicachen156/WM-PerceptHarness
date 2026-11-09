# Object Interactions

本包只提供 Object Interactions：当前官方核心、项目运行入口、依赖和模型来源、参数示例。模型权重与实际视频需另行准备。

## 当前方案与修改

采用 T2V-CompBench 固定版本 `dd5eff7b93af0550b9efa2bdabbb21b3b017ceda`，裁判为 LLaVA-v1.6-34B，float16、未量化。官方先提取最多16个均匀帧，再取6张组成拼图；使用seed 0/1/2问答，原始三seed均分按 `(均分-1)/9` 归一化。

官方评分、提示、采样、解析和模型loader均未修改。`run.py` 是当前项目调用层：参数化路径、检查官方版本与源码、记录模型设备/dtype、检查输出覆盖。标准 `aggregate` 沿用官方有效行均值；另外提供 `complete_coverage_aggregate`，有无效行时为null，并保留失败计数。没有修改或修复裁判原始答案。

`official/LLaVA/` 是与该指标直接相关的官方源码子集，不是完整GPU环境；完整运行需要下述固定官方checkout。逐文件来源见 `SOURCES.json`，两份模型的revision、文件大小和hash指针见 `MODELS.json`。

## 运行

远程安装、下载、推理前先建立并验证持久会话：

```bash
tmux new-session -s object-interactions
test -n "$TMUX"
tmux display-message -p '#S'
```

分离：`Ctrl-b`后按`d`；恢复：`tmux attach -t object-interactions`。保留已有缓存、partial文件、目标路径、认证环境和下载后端。

准备完整源码：

```bash
git clone https://github.com/KaiyueSun98/T2V-CompBench.git
git -C T2V-CompBench checkout --detach dd5eff7b93af0550b9efa2bdabbb21b3b017ceda
```

已记录的推理环境为 Python 3.10.12、torch 2.10.0、transformers 4.37.2、accelerate 0.21.0。`requirements.txt` 是部分依赖记录，并非完整环境锁；torchvision/CUDA具体构建仍需匹配。先准备依赖，再在 LLaVA 目录按需执行 `pip install --no-deps --no-build-isolation -e .`，避免官方旧依赖自动替换当前Torch。

模型目录名必须保留 `llava-v1.6-34b`；CLIP-L/14-336准备在本地，并在完整checkout的LLaVA目录建立 `openai/clip-vit-large-patch14-336` 到权重目录的符号链接。入口不会自动下载模型。

准备独立输入目录，只放 `0001.mp4`、`0002.mp4`……；prompt JSON按顺序排列为 `[{"prompt":"冻结的任务文本"}, ...]`。复制并填写 `arguments.example.json`。模型、视频、prompt路径必须真实存在，输出和对应拼图目录使用新路径。执行：

```bash
python run.py --source-root /path/to/T2V-CompBench/LLaVA --arguments /path/to/arguments.json --check-only
python run.py --source-root /path/to/T2V-CompBench/LLaVA --arguments /path/to/arguments.json
```

第二条加载模型，需要足够GPU资源；通过 `CUDA_VISIBLE_DEVICES` 指定设备，官方 `device_map=auto` 分配模型。输出保留官方CSV、设备记录及 `project_scores.json`。

## 局限

项目仅对12对2–5秒短片做过试评。六帧可能漏动作，模型会混淆“对象存在”和“动作出现”，三个seed存在明显分歧。官方对象齐全分支即使交互很弱也可能给6/10，因此分数不是交互成功概率；不适合直接推广为长视频可靠裁判。

本次重新拆包未改评分逻辑，未重新运行GPU或验证新机完整安装。官方Apache-2.0许可证保留在 `official/LLaVA/LICENSE`。
