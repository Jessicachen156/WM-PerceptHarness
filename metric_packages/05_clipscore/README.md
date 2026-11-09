# CLIPScore：优先直接调用官方代码

**v3推荐：使用官方 `compute_clip_score()`。** 输入只需官方JSON中的目标提示词与视频路径，不限制视频来自哪个模型，不要求本项目的模型名称、哈希、帧数或分段字段。具体输入、运行命令及依赖见 [OFFICIAL_USAGE.md](OFFICIAL_USAGE.md)。

本次补齐固定版本下 `competitions/`、`vbench/`、`vbench2_beta_long/` 的官方源码，使官方函数能够按正常Python导入方式使用；逐文件原样核验。`examples/call_official.py` 只是调用官方函数并保存结果的最小示例，没有另写采样或评分算法。原项目两个封装文件保留原字节，仅用于复现特定实验协议。

下面的Wan/Dense限制只适用于这个可选的项目封装，不适用于推荐的官方入口。模型权重和外部依赖仍需准备；本次没有运行真实GPU/CPU推理或完成新机安装验收。

## 可选：项目实验封装

衡量生成视频与实际生成提示词的图文相似度。当前入口采用项目窗口协议，并调用固定 VBench 官方评分函数；它不是完整 VBench 数据集评测，也不是 Hessel CLIPScore 的同式实现。

## 方案与改动

- 官方核心：OpenAI CLIP ViT-B/32。每个输入窗口分成8个区间并取区间中间帧，求归一化图文特征余弦相似度均值。8帧不是8 fps。
- 项目输入：Wan 使用保存的 prompt；LingBot Dense 将 structured_caption.caption 紧凑序列化，保留空字段和 Unicode，不含外层 duration。窗口按从0开始、两端包含的最终视频帧区间切分，相邻窗口可共享边界帧。
- 裁窗使用无损编码，并核对采样RGB与原片一致。每视频各窗口等权，模型内各成功视频等权；失败独立记录，不填造分数。
- modified/run_clipscore.py 是当前入口。输入和输出路径均由参数/清单给出；official_runtime.py 直接加载经哈希核验的原评分和采样函数，函数体未改。

official/ 是选取源码，不是完整可安装仓库。VBench 固定于 fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490；LingBot 文本映射来源固定于 f348dca454c8f1e5707721614dbac10fa5290fed。逐文件来源及哈希见 OFFICIAL_MANIFEST.json。

## 环境与运行

Linux、Python 3.12，CUDA可用的 torch==2.10.0、torchvision==0.25.0，其余依赖见 requirements.txt。系统 PATH 中需 FFmpeg（含 libx264）和 ffprobe。这里不是新安装验收后的完整 lockfile。

提前准备 [官方 ViT-B/32 权重](https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt)，SHA-256 为 40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af。入口只接受已核验的本地文件，不自动下载。

远程安装、下载或评分前先进入并验证持久会话，再开始长任务：

    tmux new-session -A -s clipscore
    test -n "$TMUX"

在该会话内准备适合本机CUDA的Torch和TorchVision，进入本包目录，再运行：

    python -m pip install -r requirements.txt
    python modified/run_clipscore.py --manifest /data/manifests/clip.jsonl --checkpoint /data/checkpoints/ViT-B-32.pt --output-dir /data/results/clip_project_v1 --gpu 0

分离：Ctrl-b 后按 d；重新进入：tmux attach -t clipscore。保留已有下载缓存、目标和续传后端。

examples/clip_manifest.jsonl 仅为格式示例，必须替换视频路径、提示词、帧数及全零哈希。相对路径按清单目录解析；model 限 wan / lingbot-dense，sample_id 使用字母数字、下划线或连字符。可只提供单模型。

输出 protocol.json、results/<model>/<sample_id>.json、scores.csv 及进度文件；逐视频保留评分文本、截断后可见文本、采样位置和哈希。成功临时裁窗会清理，源视频不改动。清单、协议或代码变化时使用新输出目录；续跑核对已完成项的实际视频哈希。

## 局限与许可

保留官方 truncate=True 的77位置限制，正文通常最多75 token；JSON标签也占token。本包不缩写或补救长文本。不同模型的窗口数、文本结构和长度不同，分数不能直接视为任务完成率或公平的跨模型准确率。

本轮仅检查独立包源码路径、命令行帮助和评分函数一致性；未加载权重、运行GPU、重评分视频或验收新安装环境。

VBench、LingBot 各自 Apache-2.0 许可证保留在对应 official/ 子目录。OpenAI CLIP 为外部 MIT 依赖，请保留所安装包的许可证。项目适配不是官方发布版本，第三方原作者标识与许可不被统一覆盖。
