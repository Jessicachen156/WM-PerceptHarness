# Official metric integration PR runbook

Date: 2026-09-21

This file describes the **code-and-documentation PR**. It does not claim that this repository has downloaded every checkpoint or run every external judge.

## What this PR contains

The PR contains only small adapters around unchanged official evaluators:

- VBench direct dimensions: Imaging Quality, Temporal Flickering, Dynamic Degree, Subject Consistency, Background Consistency, and Overall Consistency;
- the official VBench competition CLIPScore entry point;
- the official DOVER command entry point;
- strict input adapters for WorldModelBench, T2V-CompBench, VBench-2.0, PhyGenBench, and VideoPhy-2;
- reference-frame pairing for PSNR/SSIM/LPIPS;
- VideoPhy-2 PC/SA result joining (Joint is a derived field, not a third evaluator);
- the frozen final metric list and external-run instructions.

The repository does not commit model weights, virtual environments, generated videos, prompt answers, or ground-truth frames.

## Exact local checks before pushing

Run on the Ali02 checkout:

```bash
cd /mnt/yiyang-workspace/WM-PerceptHarness

git switch metrics
git status --short --branch
git fetch origin metrics
git log --oneline --decorate -8

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
"$PYTHON" -m py_compile \
  scripts/score_vbench_official.py \
  scripts/score_vbench_clip_score.py \
  scripts/score_dover_official.py \
  scripts/official_input_adapters.py \
  scripts/validate_metric_manifest.py \
  scripts/build_reference_manifest.py \
  scripts/aggregate_videophy_joint.py

"$PYTHON" -m pytest -q \
  tests/test_vbench_official_wrapper.py \
  tests/test_vbench_clip_score_wrapper.py \
  tests/test_dover_official_wrapper.py \
  tests/test_official_input_adapters.py \
  tests/test_remaining_data_tools.py \
  tests/test_vbench_motion_script.py \
  tests/test_clipiqa_plus_script.py

git diff --check
git status --short
```

On the current `metrics` checkout this command produced `108 passed, 3 skipped` in 1.88 seconds. The system `/usr/local/bin/python` does not contain pytest; use the project validation environment shown above. The tests above are contract tests. They confirm that the wrapper calls the expected official entry point, rejects missing or changed files, preserves official output, and validates metadata. They do not download checkpoints or pretend that an external judge has run.

## Commit and push

Do not create a PR from the fork to itself. Push the branch to the fork first:

```bash
cd /mnt/yiyang-workspace/WM-PerceptHarness
git add docs/metrics scripts/ requirements/ tests/
git commit -m "Add official remaining metric integration runbook"
git push origin metrics
```

If the branch already contains the same changes, do not make an empty commit.

## Pull request target

The target is:

```text
head: Jessicachen156/WM-PerceptHarness:metrics
base: lindaxhy/WM-PerceptHarness:main
```

Create the PR only after reviewing `git diff upstream/main...metrics`. The fork branch may contain later commits than the already merged PR #10; this is a new proposed change set, not a new PR created by this runbook.

## PR title

```text
Add official integration preflight for remaining video metrics
```

## PR body

~~~markdown
## Summary

This PR freezes the final 26 retained metrics (21 main + 5 appendix) and records exactly which repository file owns each integration. It adds official wrappers, field-preserving adapters, reference manifests, tests, and caller-run instructions. It does not commit model weights or virtual environments.

### Main benchmark (21)

| Metric | Repository code package | What this package does |
|---|---|---|
| MUSIQ / Imaging Quality | scripts/score_vbench_official.py --dimension imaging_quality | Checks the pinned VBench source and MUSIQ cache, then calls the unchanged official VBench evaluator. |
| DOVER | scripts/score_dover_official.py | Checks the pinned DOVER source, DOVER.pth, and ConvNeXt cache, then calls the official evaluator. |
| Motion Smoothness / AMT | scripts/score_vbench_motion_smoothness.py | Existing official VBench AMT integration; already submitted and smoke-tested in the earlier PR. |
| Temporal Flickering | scripts/score_vbench_official.py --dimension temporal_flickering | Runs the official static/near-static subset preparation and calls the official dimension. |
| Dynamic Degree | scripts/score_vbench_official.py --dimension dynamic_degree | Checks the official RAFT cache and calls unchanged VBench code. |
| CLIPScore | scripts/score_vbench_clip_score.py | Builds one-video official metadata and calls competitions/clip_score.py with the original prompt. |
| ViCLIP / Overall Consistency | scripts/score_vbench_official.py --dimension overall_consistency | Checks the official ViCLIP/BPE assets and original prompt, then calls VBench. |
| Instruction Following | scripts/official_input_adapters.py: adapt_worldmodelbench | Validates WorldModelBench fields; the official VILA-EWM judge remains caller-run. |
| Action Binding | scripts/official_input_adapters.py: adapt_action_binding | Preserves T2V-CompBench V2 metadata; the official Grid-LLaVA command remains caller-run. |
| Motion Binding | scripts/official_input_adapters.py: adapt_motion_binding | Preserves the official Grounded-SAM + DOT two-stage inputs; upstream inference remains caller-run. |
| Motion Order Understanding | scripts/official_input_adapters.py: adapt_vbench2 | Validates official ordered-action and auxiliary fields; caller runs the VBench-2.0 standard suite. |
| Motion Rationality | scripts/official_input_adapters.py: adapt_vbench2 | Validates official consequence-question fields; caller runs the standard suite. |
| Object Interactions | scripts/official_input_adapters.py: adapt_object_interactions | Preserves T2V-CompBench interaction metadata; caller runs the official evaluator. |
| PhyGenEval PCA | scripts/official_input_adapters.py: validate_phygen_eval | Validates official PhyGenBench question/video layout; caller runs PhyGenEval. |
| VideoPhy-2 PC | scripts/official_input_adapters.py: adapt_videophy_csv(task=pc) | Validates official PC CSV; caller runs VideoPhy-2 PC. |
| VideoPhy-2 SA | scripts/official_input_adapters.py: adapt_videophy_csv(task=sa) | Validates official SA CSV (videopath, caption); caller runs VideoPhy-2 SA. |
| Mechanics | scripts/official_input_adapters.py: adapt_vbench2 | Validates official VBench-2.0 auxiliary fields; caller runs the standard suite. |
| Thermotics | scripts/official_input_adapters.py: adapt_vbench2 | Validates official VBench-2.0 auxiliary fields; caller runs the standard suite. |
| Material | scripts/official_input_adapters.py: adapt_vbench2 | Validates official VBench-2.0 auxiliary fields; caller runs the standard suite. |
| Subject Consistency | scripts/score_vbench_official.py --dimension subject_consistency | Checks the official DINO source/checkpoint and calls unchanged VBench code. |
| Background Consistency | scripts/score_vbench_official.py --dimension background_consistency | Checks the official CLIP cache and calls unchanged VBench code. |

### Appendix (5)

| Metric | Repository code package | What this package does |
|---|---|---|
| PSNR | scripts/build_reference_manifest.py + official runbook | Pairs caller-provided generated/reference frames; official IQA-PyTorch computes the score. |
| SSIM | scripts/build_reference_manifest.py + official runbook | Uses the same strict frame pairing; no reference frames are invented. |
| LPIPS | scripts/build_reference_manifest.py + official runbook | Uses the same paired frames; caller runs the official LPIPS implementation. |
| FVD | docs/metrics/OFFICIAL_EXTERNAL_RUNBOOK_20260921.md + validate_metric_manifest.py | Documents official tensor/statistics inputs and command; this repository has no FVD inference wrapper. |
| FID | docs/metrics/OFFICIAL_EXTERNAL_RUNBOOK_20260921.md + validate_metric_manifest.py | Documents official feature/statistics inputs and command; this repository has no FID inference wrapper. |

### Shared files and non-counted helpers

- scripts/validate_metric_manifest.py is the common schema guard for video paths, prompts, reference frames, and auxiliary_info; it never invents metadata or scores a video.
- scripts/aggregate_videophy_joint.py joins official PC and SA outputs and computes SA >= 4 AND PC >= 4; VideoPhy-2 Joint is a derived field, not a 27th evaluator.
- scripts/score_clipiqa_plus.py remains the previously submitted backup metric and is outside the frozen 26.
- score_vbench_official.py also retains an Aesthetic Quality diagnostic entry point; Aesthetic Quality is outside the frozen 26.
- docs/metrics/METRIC_FILE_MAP_20260921.md repeats this mapping in repository form so reviewers can trace every metric to its file.

### Status

The 26 metrics are frozen and each has an official integration path documented. Only Motion Smoothness is already submitted and smoke-tested. The eight additional direct wrappers are prepared_for_pr and still require the caller's official assets/environment. The remaining metrics are external_caller_run: the caller must run the exact upstream environment with official weights and task-owned prompts, questions, first frames, auxiliary metadata, or reference collections. This PR does not claim that all 26 scores have already been produced.

## Official fidelity

The wrappers do not reimplement sampling, preprocessing, model inference, judge prompts, or score formulas. They verify the pinned upstream source and required files, invoke the upstream entry point, retain its original output, and fail when an input or checkpoint is missing.

External evaluators remain caller-run in their official repositories. This repository supplies format validation and commands; it does not replace a judge model with a smaller model.

## Validation

- Python compilation passed for all new scripts.
- Wrapper and schema contract tests passed without downloading model weights (108 passed, 3 skipped).
- git diff --check is clean.

## Scope and limitations

This PR is an official integration/preflight contribution. It does not claim that every checkpoint or virtual environment is bundled, and it does not claim that all metrics have been run on the project's future dataset. Users must provide the official checkpoints, the environment described by each upstream project, and task-owned prompts, first frames, auxiliary questions, or reference collections when the metric requires them.
~~~
## What the PR must not say

Do not write “all metrics are fully verified” or “all metrics run from one video with no metadata”. The accurate claim is “official integration/preflight is provided; runtime assets and task inputs are caller-owned.”
