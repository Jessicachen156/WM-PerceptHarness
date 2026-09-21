# 26项指标与代码/文件对应关系

更新时间：2026-09-21

这份清单解决一个容易混淆的问题：仓库不是“每个指标一个文件夹”。多个指标共享同一个官方 wrapper，通过 `--dimension` 或适配器名称选择具体指标。文件只负责校验输入、固定官方源码、调用官方入口或合并官方输出，不重新实现评分公式。

## 状态含义

- **已提交并 smoke tested**：已有真实单视频验证记录。
- **可提交 PR / prepared_for_pr**：项目代码、源码校验、输入检查和官方运行说明齐全；使用者仍需下载官方权重、创建官方环境并运行。
- **外部官方运行 / external_caller_run**：项目提供官方输入格式适配或结果合并；真正评分必须在指标作者的官方仓库和环境中完成。

## 21项主榜

| 指标 | 当前状态 | 项目代码文件 | 代码包实际做什么 | 官方运行入口 |
|---|---|---|---|---|
| MUSIQ / Imaging Quality | prepared_for_pr | `scripts/score_vbench_official.py`；`tests/test_vbench_official_wrapper.py` | 选择 `--dimension imaging_quality`，校验 VBench 源码、MUSIQ 权重哈希和单视频结果 | VBench `evaluate.py`；运行说明第1节 |
| DOVER | prepared_for_pr | `scripts/score_dover_official.py`；`tests/test_dover_official_wrapper.py`；`docs/metrics/DOVER.md` | 校验 DOVER 固定源码、DOVER.pth、ConvNeXt 缓存和运行环境，然后调用官方 `evaluate_one_video.py -f` | DOVER 官方 `evaluate_one_video.py -f`；运行说明第3节 |
| Motion Smoothness / AMT | submitted_and_smoke_tested | `scripts/score_vbench_motion_smoothness.py`；`tests/test_vbench_motion_script.py`；`docs/metrics/README.md` | 调用已提交的 VBench 0.1.5 AMT-S CLI，并保存官方结果 | VBench Motion Smoothness CLI |
| Temporal Flickering | prepared_for_pr | `scripts/score_vbench_official.py`；`tests/test_vbench_official_wrapper.py` | 选择 `--dimension temporal_flickering`；要求先完成官方静态过滤并显式确认过滤结果 | VBench `static_filter.py` + `evaluate.py`；运行说明第1节 |
| Dynamic Degree | prepared_for_pr | `scripts/score_vbench_official.py`；`tests/test_vbench_official_wrapper.py` | 选择 `--dimension dynamic_degree`，校验官方 RAFT 权重和结果类型 | VBench `evaluate.py`；运行说明第1节 |
| CLIPScore | prepared_for_pr | `scripts/score_vbench_clip_score.py`；`tests/test_vbench_clip_score_wrapper.py` | 构造官方 `clip_score.py` 所需的单视频 metadata，校验 OpenAI CLIP B/32 缓存 | VBench `competitions/clip_score.py`；运行说明第2节 |
| ViCLIP / Overall Consistency | prepared_for_pr | `scripts/score_vbench_official.py`；`tests/test_vbench_official_wrapper.py` | 选择 `--dimension overall_consistency`，要求原始生成 prompt 和 ViCLIP 权重 | VBench `evaluate.py`；运行说明第1节 |
| Instruction Following | external_caller_run | `scripts/official_input_adapters.py: adapt_worldmodelbench`；`tests/test_official_input_adapters.py` | 保留 `domain`、`subdomain`、`text_first_frame`、`text_instruction`、`first_frame`，另存本地视频映射 | WorldModelBench `evaluate.py` + 官方 VILA judge；运行说明第4节 |
| Action Binding | external_caller_run | `scripts/official_input_adapters.py: adapt_action_binding`；`tests/test_official_input_adapters.py` | 输出官方 `action_binding.json` 字段，不生成 prompt 或分数 | T2V-CompBench V2 LLaVA evaluator；运行说明第5节 |
| Motion Binding | external_caller_run | `scripts/official_input_adapters.py: adapt_motion_binding`；`tests/test_official_input_adapters.py` | 校验对象、方向和视频映射；不替代 Grounded-SAM/DOT 两阶段程序 | T2V-CompBench V2 Grounded-SAM + DOT；运行说明第5节 |
| Motion Order Understanding | external_caller_run | `scripts/official_input_adapters.py: adapt_vbench2`；`scripts/validate_metric_manifest.py`；测试同上 | 保留官方 `prompt_en`、`dimension`、两个有序 `auxiliary_info` 动作 | VBench-2.0 标准套件；运行说明第6节 |
| Motion Rationality | external_caller_run | `scripts/official_input_adapters.py: adapt_vbench2`；`scripts/validate_metric_manifest.py` | 保留官方 prompt、维度和 auxiliary_info；不允许伪造 custom 评分 | VBench-2.0 标准套件；运行说明第6节 |
| Object Interactions | external_caller_run | `scripts/official_input_adapters.py: adapt_object_interactions`；`tests/test_official_input_adapters.py` | 输出官方 interaction metadata 和视频映射 | T2V-CompBench V2 LLaVA evaluator；运行说明第5节 |
| PhyGenEval PCA | external_caller_run | `scripts/official_input_adapters.py: validate_phygen_eval`；`tests/test_official_input_adapters.py` | 原样校验官方 prompts/questions，不改写物理问题 | PhyGenBench `PhyGenEval`；运行说明第7节 |
| VideoPhy-2 PC | external_caller_run | `scripts/official_input_adapters.py: adapt_videophy_csv(task="pc")`；测试同上 | 写出官方只有 `videopath` 列的 PC CSV | VideoPhy-2 `inference.py --task pc`；运行说明第8节 |
| VideoPhy-2 SA | external_caller_run | `scripts/official_input_adapters.py: adapt_videophy_csv(task="sa")`；测试同上 | 写出官方 `videopath,caption` 两列的 SA CSV | VideoPhy-2 `inference.py --task sa`；运行说明第8节 |
| Mechanics | external_caller_run | `scripts/official_input_adapters.py: adapt_vbench2`；`scripts/validate_metric_manifest.py` | 保留官方 auxiliary_info；项目不替代 VBench-2.0 物理模型 | VBench-2.0 标准套件；运行说明第6节 |
| Thermotics | external_caller_run | `scripts/official_input_adapters.py: adapt_vbench2`；`scripts/validate_metric_manifest.py` | 保留官方 auxiliary_info；项目不替代 VBench-2.0 物理模型 | VBench-2.0 标准套件；运行说明第6节 |
| Material | external_caller_run | `scripts/official_input_adapters.py: adapt_vbench2`；`scripts/validate_metric_manifest.py` | 保留官方 auxiliary_info；项目不替代 VBench-2.0 物理模型 | VBench-2.0 标准套件；运行说明第6节 |
| Subject Consistency | prepared_for_pr | `scripts/score_vbench_official.py`；`tests/test_vbench_official_wrapper.py` | 选择 `--dimension subject_consistency`，校验 DINO 源码 checkout、DINO 权重和 Torch cache | VBench `evaluate.py`；运行说明第1节 |
| Background Consistency | prepared_for_pr | `scripts/score_vbench_official.py`；`tests/test_vbench_official_wrapper.py` | 选择 `--dimension background_consistency`，校验 OpenAI CLIP B/32 权重 | VBench `evaluate.py`；运行说明第1节 |

## 5项固定附表

| 指标 | 当前状态 | 项目代码文件 | 代码包实际做什么 | 官方运行入口 |
|---|---|---|---|---|
| PSNR | external_caller_run | `scripts/build_reference_manifest.py`；`scripts/validate_metric_manifest.py`；`tests/test_remaining_data_tools.py` | 只配对同名生成帧和真实参考帧，拒绝自引用；不生成 GT、不计算 PSNR | IQA-PyTorch `inference_iqa.py -m PSNR`；运行说明第9节 |
| SSIM | external_caller_run | `scripts/build_reference_manifest.py`；`scripts/validate_metric_manifest.py`；`tests/test_remaining_data_tools.py` | 同上，官方运行时选择 `-m SSIM` | IQA-PyTorch `inference_iqa.py -m SSIM`；运行说明第9节 |
| LPIPS | external_caller_run | `scripts/build_reference_manifest.py`；`scripts/validate_metric_manifest.py`；`tests/test_remaining_data_tools.py` | 同上，官方运行时选择 `-m LPIPS` | IQA-PyTorch `inference_iqa.py -m LPIPS`；运行说明第9节 |
| FVD | external_caller_run | `scripts/validate_metric_manifest.py`；`tests/test_remaining_data_tools.py` | 只登记真实/生成集合的输入边界；仓库没有重新实现 FVD 模型 | Google Research TensorFlow FVD；运行说明第9节 |
| FID | external_caller_run | `scripts/validate_metric_manifest.py`；`tests/test_remaining_data_tools.py` | 只登记真实图像帧集合或官方统计文件；仓库不替换 Inception/FID 实现 | IQA-PyTorch `pyiqa fid`；运行说明第9节 |

## 共享文件

- `docs/metrics/FINAL_METRICS.json`：冻结 21 项主榜 + 5 项附表及状态。
- `docs/metrics/STATUS_REMAINING.json`：逐项状态、调用者需要准备的输入和边界。
- `docs/metrics/OFFICIAL_EXTERNAL_RUNBOOK_20260921.md`：官方仓库、版本、权重、环境和命令。
- `scripts/official_input_adapters.py`：WorldModelBench、T2V-CompBench、VBench-2.0、PhyGenBench、VideoPhy-2 的输入适配。
- `scripts/validate_metric_manifest.py`：通用视频、prompt、auxiliary_info、参考帧和集合输入检查。
- `tests/test_official_input_adapters.py`、`tests/test_remaining_data_tools.py`：离线契约测试。

## 不能从这张表推断的内容

这张表不表示仓库已经下载了所有权重、创建了所有官方环境或在未来的完整数据集上完成了 26 项推理。它表示每项指标的项目接口和官方运行边界已经明确；真正外部评分仍需使用官方资源和官方程序。
