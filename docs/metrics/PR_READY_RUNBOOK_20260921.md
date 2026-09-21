# Category-based official metric integration PR runbook

Date: 2026-09-21

This guide supersedes the old single-PR workflow. The final list is still 21 main metrics + 5 appendix metrics, but they must be proposed in separate category PRs.

## Non-negotiable PR rule

One PR contains one metric category. Do not open one PR whose summary lists all 26 metrics.

The existing metrics branch is a staging branch that contains the complete integration catalog. It is not a category PR branch. Every category PR must start from upstream/main and contain only the files, functions, tests, and documentation needed for that category.

The repository does not commit model weights, virtual environments, generated videos, prompt answers, judge answers, or ground-truth frames.

## Status definitions in plain language

### prepared_for_pr

This means the repository contains a wrapper or preflight check for the metric. The code checks the pinned official source and required files, passes the official arguments to the unchanged upstream evaluator, and has contract tests.

It means the code is ready for a reviewer to inspect and for a PR to be opened. It does not mean that the official checkpoint is stored in this repository, that a fresh official environment has been installed here, or that the metric has scored the future dataset.

All 25 metrics other than the already submitted Motion Smoothness are now prepared_for_pr. Their direct wrappers are score_vbench_official.py, score_vbench_clip_score.py, and score_dover_official.py; the former 17 external metrics use scripts/run_official_external.py.

### Former external_caller_run label

The former external_caller_run label meant that the repository only had an input adapter or runbook. Those 17 retained metrics now have a project wrapper in scripts/run_official_external.py, so they are promoted to prepared_for_pr.

The wrapper still does not bundle weights or environments. It checks the pinned source and caller-owned paths, then forwards the unchanged official command. Runtime evidence remains separate and is currently not_run_in_project_environment.

## Recommended category PRs

| PR category | Metrics covered by this PR | Files and tests | PR title |
|---|---|---|---|
| Image and video quality | MUSIQ / Imaging Quality; DOVER | scripts/score_vbench_official.py (imaging_quality only), scripts/score_dover_official.py, docs/metrics/DOVER.md, tests/test_vbench_official_wrapper.py, tests/test_dover_official_wrapper.py | Add official image and video quality metrics |
| Motion quality and amount | Motion Smoothness / AMT; Temporal Flickering; Dynamic Degree | scripts/score_vbench_motion_smoothness.py, scripts/score_vbench_official.py (temporal_flickering and dynamic_degree only), tests/test_vbench_motion_script.py, tests/test_vbench_official_wrapper.py | Add official VBench motion-quality metrics |
| Text-video alignment and consistency | CLIPScore; ViCLIP / Overall Consistency; Subject Consistency; Background Consistency | scripts/score_vbench_clip_score.py, scripts/score_vbench_official.py (overall_consistency, subject_consistency, background_consistency), tests/test_vbench_clip_score_wrapper.py, tests/test_vbench_official_wrapper.py | Add official text-video alignment and consistency metrics |
| Instruction following | Instruction Following | scripts/run_official_external.py --metric instruction_following, scripts/official_input_adapters.py: adapt_worldmodelbench, scripts/validate_metric_manifest.py, tests/test_official_input_adapters.py, WorldModelBench section of docs/metrics/OFFICIAL_EXTERNAL_RUNBOOK_20260921.md | Add WorldModelBench instruction-following input adapter |
| Action and object relations | Action Binding; Motion Binding; Object Interactions | scripts/run_official_external.py --metric action_binding|motion_binding|object_interactions, scripts/official_input_adapters.py, scripts/validate_metric_manifest.py, tests/test_official_input_adapters.py, T2V-CompBench V2 section of the official runbook | Add T2V-CompBench action and interaction adapters |
| Temporal reasoning | Motion Order Understanding; Motion Rationality | scripts/run_official_external.py --metric motion_order_understanding|motion_rationality, scripts/official_input_adapters.py: adapt_vbench2, scripts/validate_metric_manifest.py, tests/test_official_input_adapters.py, VBench-2.0 temporal sections of the official runbook | Add VBench-2.0 temporal reasoning adapters |
| Physical metrics | PhyGenEval PCA; VideoPhy-2 PC; VideoPhy-2 SA; Mechanics; Thermotics; Material | scripts/run_official_external.py --metric phygen_eval_pca|videophy_pc|videophy_sa|mechanics|thermotics|material, scripts/official_input_adapters.py, scripts/aggregate_videophy_joint.py, tests/test_official_input_adapters.py, tests/test_remaining_data_tools.py, PhyGenBench/VideoPhy-2/VBench-2.0 sections of the official runbook | Add official physics-metric input adapters |
| Reference and distribution quality | PSNR; SSIM; LPIPS; FVD; FID | scripts/run_official_external.py --metric psnr|ssim|lpips|fid|fvd, scripts/build_reference_manifest.py, scripts/validate_metric_manifest.py, tests/test_remaining_data_tools.py, official IQA-PyTorch/Google FVD sections of the official runbook | Add reference and distribution metric input manifests |

Motion Smoothness was already submitted and smoke-tested in the earlier PR. If that PR is already merged, the motion-quality PR must not copy the same implementation again; it should contain only the new motion metrics and a link to the earlier PR.

VideoPhy-2 Joint is a derived PC/SA join, not a separate metric. Include aggregate_videophy_joint.py only in the physical-metrics PR and describe it as a post-processing helper.

## Strict split by FINAL_METRICS.json category

If one PR must correspond exactly to one category value in FINAL_METRICS.json, use these 15 PRs instead of the eight business-level groups above:

| Category | Metrics |
|---|---|
| technical_quality | MUSIQ / Imaging Quality |
| video_quality | DOVER |
| motion_quality | Motion Smoothness / AMT; Temporal Flickering |
| motion_quantity | Dynamic Degree |
| text_video_alignment | CLIPScore; ViCLIP / Overall Consistency |
| instruction_completion | Instruction Following |
| action_binding | Action Binding |
| motion_binding | Motion Binding |
| temporal_semantics | Motion Order Understanding |
| action_consequence | Motion Rationality; Object Interactions |
| physics | PhyGenEval PCA; VideoPhy-2 PC; VideoPhy-2 SA |
| physics_specialized | Mechanics; Thermotics; Material |
| consistency | Subject Consistency; Background Consistency |
| reference_quality | PSNR; SSIM; LPIPS |
| distribution_quality | FVD; FID |

The eight groups above are only a reviewer-friendly business grouping. They must not be used when the review requirement is literally one FINAL_METRICS.json category per PR. In that case, use the 15-category table and create a separate branch for each row.

CLIP-IQA+ and Aesthetic Quality are outside the frozen 26 and must not be added to the technical_quality PR.

## Important shared-file rule

Some current files contain more than one category:

- score_vbench_official.py contains several VBench dimensions.
- official_input_adapters.py contains adapters for several external projects.
- validate_metric_manifest.py is shared validation infrastructure.

Do not blindly copy one of these whole files into every category branch and call the result category-only. Before opening the category PR, either split the relevant functions into category modules or create a category-specific patch that adds only the required functions and tests. The PR body must name the exact functions included.

The complete file-to-metric catalog remains in docs/metrics/METRIC_FILE_MAP_20260921.md. That catalog is not a reason to include all files in every PR.

## Exact branch and push procedure

Run these commands on Ali02 for each category. Replace CATEGORY with one of image-video-quality, motion-quality, alignment-consistency, instruction-following, action-relations, temporal-reasoning, physical-metrics, or reference-distribution.

~~~bash
cd /mnt/yiyang-workspace/WM-PerceptHarness

git fetch upstream main
git fetch origin metrics
git switch -c pr/CATEGORY upstream/main

# Bring in only the selected category's files or category-specific patch.
# Do not merge the complete metrics branch.
git status --short
git diff --stat upstream/main...HEAD

PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
# Run only the tests listed for this category in the table above.
"$PYTHON" -m pytest -q SELECTED_TEST_FILES
git diff --check
git diff --stat upstream/main...HEAD

git add SELECTED_FILES
git commit -m "Add CATEGORY official metric integration"
git push -u origin pr/CATEGORY
~~~

For an already-created local branch, use git switch pr/CATEGORY and continue with the same validation. Do not force-push a shared branch.

The GitHub target for every PR is:

~~~
head: Jessicachen156/WM-PerceptHarness:pr/CATEGORY
base: lindaxhy/WM-PerceptHarness:main
~~~

Before creating the PR, inspect the complete category-only diff:

~~~bash
git diff --name-status upstream/main...HEAD
git diff upstream/main...HEAD
~~~

If the diff contains another category's evaluator, remove it before opening the PR.

## Category-specific test commands

Image and video quality:

~~~bash
"$PYTHON" -m pytest -q tests/test_vbench_official_wrapper.py tests/test_dover_official_wrapper.py
~~~

Motion quality and amount:

~~~bash
"$PYTHON" -m pytest -q tests/test_vbench_motion_script.py tests/test_vbench_official_wrapper.py
~~~

Text-video alignment and consistency:

~~~bash
"$PYTHON" -m pytest -q tests/test_vbench_clip_score_wrapper.py tests/test_vbench_official_wrapper.py
~~~

Instruction following, action relations, temporal reasoning, and physical metrics:

~~~bash
"$PYTHON" -m pytest -q tests/test_official_input_adapters.py
~~~

Reference and distribution quality:

~~~bash
"$PYTHON" -m pytest -q tests/test_remaining_data_tools.py
~~~

These are contract tests. They verify official paths, hashes, arguments, and input schemas. They do not download official weights or run external judge models.

## PR body template

Use only the rows for the selected category. Do not paste the 26-metric table into every PR.

~~~markdown
## Summary

- Add the official integration or input adapter for CATEGORY.
- List the exact metrics covered by this PR.
- List the exact scripts, tests, and official runbook section changed.
- Preserve the pinned upstream source, input format, and evaluator behavior.

## Status

State prepared_for_pr for every retained metric in this catalog. Keep runtime evidence separate from PR readiness.

For prepared_for_pr, say that this repository calls the unchanged official evaluator after checking the configured source and assets. Do not say that weights or environments are bundled.

For the former external category, say that scripts/run_official_external.py validates the official input contract and forwards the upstream command; the evaluator, weights, environment, and task-owned metadata remain caller-run.

## Validation

- List the category-specific contract-test command and result.
- State that no model weights or future-dataset scores are included.

## Scope

State that this PR covers only CATEGORY. Do not claim that the other metric categories are included or completed.
~~~

## What a reviewer should understand

prepared_for_pr means: the project code has a reviewable official wrapper and preflight contract.

All retained metrics are now prepared_for_pr: the project has a reviewable official wrapper or direct official entry point. Scoring still happens in the metric author's official environment when that is what the upstream project requires.

Neither status means that all 26 metrics can accept one arbitrary MP4 with no prompt, first frame, auxiliary metadata, or reference data. The final status registry and the complete mapping are in docs/metrics/FINAL_METRICS.json, docs/metrics/STATUS_REMAINING.json, and docs/metrics/METRIC_FILE_MAP_20260921.md.
