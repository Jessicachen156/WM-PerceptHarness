# Remaining metrics preparation package

This increment prepares the metrics that were absent from the earlier
CLIP-IQA+ / Motion Smoothness PR.  It keeps the official evaluators as the
source of scores and adds only orchestration, input validation, and an
analysis-only VideoPhy-2 Joint aggregation.

## What is included

`scripts/score_vbench_official.py` runs the pinned VBench `evaluate.py` for
`imaging_quality`, `aesthetic_quality`, `temporal_flickering`,
`dynamic_degree`, `subject_consistency`, `background_consistency`, and
`overall_consistency`.  Motion Smoothness remains in its already-submitted
wrapper and is deliberately rejected here.  The wrapper records the exact
command, environment choices, source root, cache, and log.  It does not alter
VBench sampling, preprocessing, models, or formulas.  `overall_consistency`
requires a frozen prompt or video-to-prompt JSON. `temporal_flickering`
requires an explicit static/near-static-subset acknowledgement.

`scripts/score_vbench_clip_score.py` calls the official competition
`competitions/clip_score.py` implementation.  It creates only the official
one-video metadata JSON and checks the official OpenAI CLIP ViT-B/32 cache;
frame sampling and similarity calculation remain in the upstream file.

`scripts/validate_metric_manifest.py` checks a frozen JSON manifest before
semantic, VBench-2.0, or reference metrics are run.  It requires prompts for
semantic dimensions, `auxiliary_info` for Motion Order/Rationality/Mechanics/
Thermotics/Material, and reference-frame directories for PSNR/SSIM/LPIPS.
It never generates missing metadata.

`scripts/build_reference_manifest.py` pairs generated and real future frames
by identical relative filenames.  It reports unmatched files and refuses to
make copies or synthetic references.  This is preparation for PSNR/SSIM/LPIPS,
not a claim that the 75 videos already have valid future ground truth.

`scripts/aggregate_videophy_joint.py` joins the two official VideoPhy-2 CSV
outputs and computes the documented analysis field `SA >= 4 and PC >= 4`.
Joint is not a new model or an independent metric.

`scripts/official_input_adapters.py` validates and emits the official input
shapes for WorldModelBench, T2V-CompBench V2, VBench-2.0, PhyGenBench, and
VideoPhy-2. It only preserves caller-supplied fields and writes a separate
local `video_map` when an upstream metadata file intentionally has no video
path. See `docs/metrics/OFFICIAL_INPUT_ADAPTERS.md`; this helper does not
replace any upstream evaluator or make missing checkpoints available.

## Current state by family

The direct VBench wrapper is ready for environment-level smoke tests once the
corresponding cache and prompt manifest are available.  The wrapper does not
make these dimensions complete: MUSIQ/RAFT/CLIP/ViCLIP/DINO paths still need
cache mapping and a real single-video run; Temporal Flickering needs a frozen
static subset; and long-video VBench uses a separate official entry point.

For model-backed dimensions, `--weights-manifest` is required.  It is a JSON
object mapping every cache-relative required file to its SHA-256.  Create it
from files already provisioned on Ali02 and review the digests; the wrapper
never downloads a missing checkpoint.  `--check-only` validates this inventory
without starting inference.  Only after a trusted, hash-verified checkpoint
has been provisioned should a caller opt into `--allow-trusted-pickle` for an
official legacy loader.

The following remain external, conditional, or blocked and are intentionally
not faked by this package:

- DOVER needs its own Torch 1.13-compatible environment and `DOVER.pth`.
- Instruction Following needs WorldModelBench's VILA judge, data layout,
  and original question fields. Physical Adherence is not part of the
  frozen final benchmark list; it is retained only as an optional
  WorldModelBench diagnostic/compatibility reference.
- Action Binding / Motion Binding / Object Interactions need the official
  T2V-CompBench repositories, numeric IDs, metadata, and large judge/vision
  environments.
- Motion Order, Motion Rationality, Mechanics, Thermotics, and Material need
  VBench-2.0's full metadata and `auxiliary_info`; `custom_input` is rejected
  by the official code.
- PhyGenEval and VideoPhy-2 need their own checkpoints and environments.
- PSNR/SSIM/LPIPS need aligned future reference frames; FVD/FID need matched
  real collections.  The generated videos themselves are not valid GT.

## Suggested directory layout on Ali02

```text
/mnt/yiyang-workspace/WM-PerceptHarness/
  scripts/
  docs/metrics/
  requirements/
/root/official_video_metrics_20260918/
  sources/                  # pinned official source trees
  weights/                  # external checkpoints, never committed
  manifests/                # frozen video/prompt/auxiliary metadata
  results/                  # one fresh directory per run
```

Keep source, dependencies, model caches, and results outside Git.  Large
downloads and inference must start inside the persistent `official-metrics`
tmux session described in the user guide.

## Direct VBench command

From the pinned VBench source root, after verifying the cache and a fresh
output directory:

```bash
python scripts/score_vbench_official.py \
  --vbench-root /root/official_video_metrics_20260918/sources/VBench \
  --videos-path /mnt/yiyang-workspace/75_outputs/reuse75_en_v1/wan/full_0582/final.mp4 \
  --dimension imaging_quality \
  --cache-dir /mnt/models/vbench-cache \
  --weights-manifest /root/official_video_metrics_20260918/manifests/imaging_quality.weights.json \
  --gpu 0 \
  --output-dir /root/official_video_metrics_20260918/results/imaging_quality_full_0582
```

For `overall_consistency`, add `--prompt` for a single video or
`--prompt-file /root/official_video_metrics_20260918/manifests/video_to_prompt.json`.
For `temporal_flickering`, add `--static-subset-ack` only after the subset
rule and excluded count have been recorded.

For CLIP Score, the official competition code hard-codes OpenAI CLIP
`ViT-B/32`.  Provision its official file at
`<clip-home>/.cache/clip/ViT-B-32.pt`, then run:

```bash
python scripts/score_vbench_clip_score.py \
  --vbench-root /root/official_video_metrics_20260918/sources/VBench \
  --videos-path /path/to/video.mp4 \
  --prompt 'the original frozen generation instruction' \
  --clip-home /root/official_video_metrics_20260918 \
  --output-dir /root/official_video_metrics_20260918/results/clip_score_one
```

The wrapper does not copy or download the checkpoint.  It calls the
unchanged `competitions/clip_score.py` function and validates its one-video
result.

The first run should be one short, decodable video.  Inspect the official
`*_eval_results.json`, the wrapper metadata, and the log before scaling out.

## Manifest example

```json
[
  {
    "video_id": "wan-full_0582",
    "video": "/mnt/yiyang-workspace/75_outputs/reuse75_en_v1/wan/full_0582/final.mp4",
    "prompt": "the original frozen generation instruction",
    "dimensions": ["overall_consistency", "clip_score"],
    "auxiliary_info": "/root/official_video_metrics_20260918/manifests/wan-full_0582.json"
  }
]
```

Validate it before running:

```bash
python scripts/validate_metric_manifest.py \
  --manifest /root/official_video_metrics_20260918/manifests/videos.json \
  --dimension overall_consistency --check-files
```

Do not fill a prompt, action order, physical question, or reference path from
an automatic caption of the generated result.  Those fields are task inputs
and must be frozen from the original task design.

## 2026-09-21 validation update

- The unchanged pinned VBench source has now emitted and passed wrapper validation for Imaging Quality, Dynamic Degree, Subject Consistency and Background Consistency on one real MP4. Evidence and raw logs remain outside Git under /root/official_video_metrics_20260918/results/vbench_visual_smoke_0582_committed/.
- These four runs are recorded as scored_unverified_runtime, not strict score-ready B: the host image is Torch 2.10/CUDA 12.8 with NumPy 2.2.6, timm 1.0.28 and transformers 5.8.1, while the official base requirements declare NumPy <2, timm <=1.0.12, transformers 4.33.2 and CUDA 11.6/11.7/11.8/12.1.
- Aesthetic Quality was run only as a diagnostic. Overall Consistency was not accepted as B evidence because the selected MP4 concatenates two segments and the available prompt file covers only the first segment. CLIPScore has the same exact-prompt requirement and has not been promoted.
- The full repository test gate and the isolated VBench dependency gate must pass before changing any of these statuses to scored.
