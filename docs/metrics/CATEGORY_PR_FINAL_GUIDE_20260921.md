
# 按类别提交最终版评测指标 PR

日期：2026-09-21

本文件只适用于当前已经补齐官方入口 wrapper 的最终版本。

当前最终状态：

- Motion Smoothness / AMT：已提交并完成真实 smoke test。
- 其余 25 项：已具备项目内官方入口、源码/输入预检和 contract tests，状态为 prepared_for_pr。
- 模型权重、官方环境、prompt、首帧、问题文件和参考集合不提交到 Git，由使用者按官方说明准备。

## 一、先同步并验证最终代码

所有类别 PR 都必须从最终的 origin/metrics 取文件，不能从旧工作区、旧 commit 或旧临时目录复制。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness

git fetch upstream main
git fetch origin metrics
git status --short --branch

git show origin/metrics:scripts/run_official_external.py >/dev/null
git show origin/metrics:tests/test_official_external_runner.py >/dev/null

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_official_external_runner.py \
  tests/test_vbench_official_wrapper.py \
  tests/test_vbench_clip_score_wrapper.py \
  tests/test_dover_official_wrapper.py \
  tests/test_official_input_adapters.py \
  tests/test_remaining_data_tools.py \
  tests/test_vbench_motion_script.py \
  tests/test_clipiqa_plus_script.py
~~~

最终验证结果应为：

~~~text
115 passed, 3 skipped
~~~

如果这一步失败，不要创建任何类别 PR。

## 二、类别划分

下面 8 个是便于审阅的业务类别。每个 PR 的 Summary 只能写对应类别，不要把 26 项总表复制进每个 PR。

| 分支 | 类别 | 指标 | PR 标题 |
|---|---|---|---|
| pr/metrics-quality | 图像与视频质量 | MUSIQ / Imaging Quality、DOVER | Add official image and video quality metrics |
| pr/metrics-motion | 运动质量与运动幅度 | Motion Smoothness、Temporal Flickering、Dynamic Degree | Add official VBench motion-quality metrics |
| pr/metrics-alignment | 文本-视频对齐与一致性 | CLIPScore、ViCLIP / Overall Consistency、Subject Consistency、Background Consistency | Add official text-video alignment and consistency metrics |
| pr/metrics-instruction | 指令遵循 | Instruction Following | Add WorldModelBench instruction-following wrapper |
| pr/metrics-action-relations | 动作与物体关系 | Action Binding、Motion Binding、Object Interactions | Add T2V-CompBench action and interaction wrappers |
| pr/metrics-temporal-physics | 时间推理与专门物理指标 | Motion Order、Motion Rationality、Mechanics、Thermotics、Material | Add VBench-2.0 temporal and physics wrappers |
| pr/metrics-physics-models | 独立物理模型 | PhyGenEval PCA、VideoPhy-2 PC、VideoPhy-2 SA | Add PhyGenEval and VideoPhy-2 wrappers |
| pr/metrics-reference-distribution | 参考质量与分布质量 | PSNR、SSIM、LPIPS、FID、FVD | Add reference and distribution metric wrappers |

VideoPhy-2 Joint 不是独立指标，随 pr/metrics-physics-models 提交 aggregate_videophy_joint.py。

CLIP-IQA+ 和 Aesthetic Quality 不属于最终 26 项，不放入任何类别 PR。

## 三、每个类别 PR 的共同操作规则

每个类别都从 upstream/main 新建分支，再从 origin/metrics 恢复最终文件。不要使用：

~~~bash
git add docs/metrics scripts/ tests/
~~~

每个类别都必须执行：

~~~bash
git switch -C CATEGORY_BRANCH upstream/main
git restore --source=origin/metrics -- SELECTED_FILES
git add SELECTED_FILES
git diff --name-status upstream/main...HEAD
git diff --check
git commit -m "COMMIT_MESSAGE"
git push -u origin CATEGORY_BRANCH
~~~

检查 git diff --name-status 的结果，只允许出现本类别所需文件和已经说明的共享官方 runner。PR 目标统一为：

~~~text
head: Jessicachen156/WM-PerceptHarness:CATEGORY_BRANCH
base: lindaxhy/WM-PerceptHarness:main
~~~

## 四、类别一：图像与视频质量

指标：MUSIQ / Imaging Quality、DOVER。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-quality upstream/main
git restore --source=origin/metrics -- \
  scripts/score_vbench_official.py \
  scripts/score_dover_official.py \
  tests/test_vbench_official_wrapper.py \
  tests/test_dover_official_wrapper.py \
  docs/metrics/DOVER.md

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_vbench_official_wrapper.py \
  tests/test_dover_official_wrapper.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/score_vbench_official.py \
  scripts/score_dover_official.py \
  tests/test_vbench_official_wrapper.py \
  tests/test_dover_official_wrapper.py \
  docs/metrics/DOVER.md
git commit -m "Add official image and video quality metrics"
git push -u origin pr/metrics-quality
~~~

## 五、类别二：运动质量与运动幅度

指标：Motion Smoothness / AMT、Temporal Flickering、Dynamic Degree。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-motion upstream/main
git restore --source=origin/metrics -- \
  scripts/score_vbench_motion_smoothness.py \
  scripts/score_vbench_official.py \
  tests/test_vbench_motion_script.py \
  tests/test_vbench_official_wrapper.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_vbench_motion_script.py \
  tests/test_vbench_official_wrapper.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/score_vbench_motion_smoothness.py \
  scripts/score_vbench_official.py \
  tests/test_vbench_motion_script.py \
  tests/test_vbench_official_wrapper.py
git commit -m "Add official VBench motion-quality metrics"
git push -u origin pr/metrics-motion
~~~

如果 Motion Smoothness 已在之前 PR 合并，恢复文件后不会产生新的 diff，不要重复提交同一实现。

## 六、类别三：文本-视频对齐与一致性

指标：CLIPScore、ViCLIP / Overall Consistency、Subject Consistency、Background Consistency。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-alignment upstream/main
git restore --source=origin/metrics -- \
  scripts/score_vbench_clip_score.py \
  scripts/score_vbench_official.py \
  tests/test_vbench_clip_score_wrapper.py \
  tests/test_vbench_official_wrapper.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_vbench_clip_score_wrapper.py \
  tests/test_vbench_official_wrapper.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/score_vbench_clip_score.py \
  scripts/score_vbench_official.py \
  tests/test_vbench_clip_score_wrapper.py \
  tests/test_vbench_official_wrapper.py
git commit -m "Add official text-video alignment and consistency metrics"
git push -u origin pr/metrics-alignment
~~~

## 七、类别四：指令遵循

指标：Instruction Following。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-instruction upstream/main
git restore --source=origin/metrics -- \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py
git commit -m "Add WorldModelBench instruction-following wrapper"
git push -u origin pr/metrics-instruction
~~~

## 八、类别五：动作与物体关系

指标：Action Binding、Motion Binding、Object Interactions。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-action-relations upstream/main
git restore --source=origin/metrics -- \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py
git commit -m "Add T2V-CompBench action and interaction wrappers"
git push -u origin pr/metrics-action-relations
~~~

Motion Binding 必须在 PR 说明中写清楚官方 Grounded-SAM 和 DOT 是两个阶段。

## 九、类别六：时间推理与专门物理指标

指标：Motion Order、Motion Rationality、Mechanics、Thermotics、Material。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-temporal-physics upstream/main
git restore --source=origin/metrics -- \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py
git commit -m "Add VBench-2.0 temporal and physics wrappers"
git push -u origin pr/metrics-temporal-physics
~~~

这五项使用 VBench-2.0 官方标准套件，不能把任意 custom video 伪装成标准套件结果。

## 十、类别七：独立物理模型

指标：PhyGenEval PCA、VideoPhy-2 PC、VideoPhy-2 SA。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-physics-models upstream/main
git restore --source=origin/metrics -- \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  scripts/aggregate_videophy_joint.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py \
  tests/test_remaining_data_tools.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py \
  tests/test_remaining_data_tools.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  scripts/aggregate_videophy_joint.py \
  tests/test_official_input_adapters.py \
  tests/test_official_external_runner.py \
  tests/test_remaining_data_tools.py
git commit -m "Add PhyGenEval and VideoPhy-2 wrappers"
git push -u origin pr/metrics-physics-models
~~~

VideoPhy-2 Joint 只是 PC/SA 结果的确定性合并，不是新的评分模型。

## 十一、类别八：参考质量与分布质量

指标：PSNR、SSIM、LPIPS、FID、FVD。

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git switch -C pr/metrics-reference-distribution upstream/main
git restore --source=origin/metrics -- \
  scripts/build_reference_manifest.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_remaining_data_tools.py \
  tests/test_official_external_runner.py

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m pytest -q \
  tests/test_remaining_data_tools.py \
  tests/test_official_external_runner.py
git diff --check
git diff --name-status upstream/main...HEAD

git add \
  scripts/build_reference_manifest.py \
  scripts/validate_metric_manifest.py \
  scripts/run_official_external.py \
  tests/test_remaining_data_tools.py \
  tests/test_official_external_runner.py
git commit -m "Add reference and distribution metric wrappers"
git push -u origin pr/metrics-reference-distribution
~~~

PSNR、SSIM、LPIPS 需要真实时间对齐参考帧；FID 需要真实参考图像或官方统计量；FVD 需要真实视频集合。缺少这些输入时只能报告 N/A。

## 十二、创建 GitHub PR

每个分支推送成功后，打开：

~~~text
https://github.com/Jessicachen156/WM-PerceptHarness/compare
~~~

设置：

~~~text
base repository: lindaxhy/WM-PerceptHarness
base branch: main
head repository: Jessicachen156/WM-PerceptHarness
compare branch: 当前 pr/metrics-* 分支
~~~

PR Summary 只写当前类别：

~~~markdown
## Summary

- Add the final official wrapper for CATEGORY.
- Cover only: METRIC_NAMES.
- Use the pinned official source, input format, and command.
- Keep model weights, virtual environments, and task-owned data caller-provided.

## Validation

- CATEGORY_TEST_COMMAND
- RESULT passed
- No model weights or future-dataset scores are committed.

## Official fidelity

The wrapper performs source/input preflight and forwards the unchanged official command. It does not reimplement the metric formula or replace the official model.

## Scope

This PR covers CATEGORY only. Other metric categories are intentionally submitted separately.
~~~

不要写：

~~~text
All 26 metrics are implemented in this PR.
All metrics accept one arbitrary video without metadata.
All external evaluators have already been smoke-tested.
~~~

## Submission order and shared files

Do not create all eight branches at the same time from the old upstream/main. Several categories share the final wrapper files:

- score_vbench_official.py is used by the quality, motion, and alignment categories.
- official_input_adapters.py, validate_metric_manifest.py, and run_official_external.py are used by several external categories.
- tests/test_official_input_adapters.py and tests/test_official_external_runner.py are shared contract tests.

Submit and merge categories one at a time:

1. Create one category branch and run its tests.
2. Push it and create the PR.
3. After that PR is merged, run git fetch upstream main.
4. Create the next category branch from the new upstream/main.
5. If a shared file is already in the base branch, git restore will not create a duplicate diff.

Recommended order: quality, motion, alignment, instruction, action-relations, temporal-physics, physics-models, reference-distribution.

Do not create a dependent category branch from an old upstream/main while the previous shared-file PR is still open.


## 十三、最终检查

创建每个 PR 前必须确认：

~~~bash
git status --short --branch
git diff --check
git diff --name-only upstream/main...HEAD
git log -1 --oneline
~~~

如果工作树有未提交文件、diff 出现其他类别脚本，或者测试不是最终版文件上的结果，停止创建 PR，先清理分支并重新从 upstream/main 建立。
