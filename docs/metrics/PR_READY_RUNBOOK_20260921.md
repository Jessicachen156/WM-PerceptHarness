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

```markdown
## Summary

- Add thin, fail-closed wrappers around the pinned official VBench and DOVER entry points.
- Add the official CLIPScore one-video adapter and strict source/checkpoint checks.
- Add field-preserving input adapters for WorldModelBench, T2V-CompBench, VBench-2.0, PhyGenBench, and VideoPhy-2.
- Add reference-frame pairing and VideoPhy-2 PC/SA joining without inventing ground truth, prompts, questions, or scores.
- Freeze the final 21 main metrics and 5 appendix metrics.
- Document the official environments, checkpoint locations, input files, and caller-run commands.

## Official fidelity

The wrappers do not reimplement sampling, preprocessing, model inference, judge prompts, or score formulas. They verify the pinned upstream source and required files, invoke the upstream entry point, retain its original output, and fail when an input or checkpoint is missing.

External evaluators remain caller-run in their official repositories. This repository supplies format validation and commands; it does not replace a judge model with a smaller model.

## Validation

- Python compilation passed for all new scripts.
- Wrapper and schema contract tests passed without downloading model weights (`108 passed, 3 skipped`).
- `git diff --check` is clean.

## Scope and limitations

This PR is an official integration/preflight contribution. It does not claim that every checkpoint or virtual environment is bundled, and it does not claim that all metrics have been run on the project's future dataset. Users must provide the official checkpoints, the environment described by each upstream project, and task-owned prompts, first frames, auxiliary questions, or reference collections when the metric requires them.
```

## What the PR must not say

Do not write “all metrics are fully verified” or “all metrics run from one video with no metadata”. The accurate claim is “official integration/preflight is provided; runtime assets and task inputs are caller-owned.”
