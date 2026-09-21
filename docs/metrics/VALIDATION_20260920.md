# Validation record (2026-09-21)

## Repository fixes

The remote branch `metrics` keeps all metric code under the repository layout used by the submitted CLIP-IQA+ and Motion Smoothness work:

- `scripts/` contains wrappers and adapters.
- `docs/metrics/` contains the frozen list, input contracts and validation records.
- `tests/` contains offline contracts and regression tests.

This run fixed four environment or integrity defects that were exposed by the full suite:

1. SAM3.1 child-process tests now inherit the repository `src` path.
2. CV artifact validation accepts only root-owned sticky temporary ancestors such as a correctly configured `/tmp`; writable non-sticky ancestors and unsafe final directories remain rejected.
3. CV artifact lookup performs a second SHA-256 confirmation read, catching same-size in-place mutations when filesystem timestamps are coarse.
4. Timeline extraction uses `-vsync 0`, the FFmpeg 4.4 spelling of the frame-preserving option used by this host.

The VBench source fingerprint now canonicalizes CRLF/LF only for declared text source files. Opaque binary bytes remain hashed exactly.

## Test evidence

The final full repository run is the gate for this commit. Its result is recorded below after the last code change:

```text
pytest -q: 1381 passed, 1 skipped, 54 subtests passed in 76.06s
```

Additional focused evidence:

```text
tests/test_sam31_adapter.py tests/test_sam31_smoke.py: 181 passed
tests/test_cv_artifacts.py: 72 passed
tests/test_vbench_official_wrapper.py: 12 passed, 31 subtests passed
focused metric/CV suite: 283 passed, 34 subtests passed
```

No model weights, source archives, virtual environments or inference results are committed.

## Real VBench smoke evidence

Pinned source:

- revision: `fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`
- canonical source fingerprint: `b2afd4fcb9bb0775ec872b34c88274f8f0753601871e03aabefe61582f710e13`

Input video:

- `/mnt/yiyang-workspace/75_outputs/reuse75_en_v1/wan/full_0582/final.mp4`
- SHA-256: `30a7cd1c16caa7681e855c86e855877e50b67670a51795ba8f2e929c5f5017e2`

Hash-verified cache files were kept outside Git in `/mnt/models/vbench-cache`. The raw official outputs and logs are outside Git:

- visual run: `/root/official_video_metrics_20260918/results/vbench_visual_smoke_0582_final2/`
- semantic/diagnostic run: `/root/official_video_metrics_20260918/results/vbench_semantic_smoke_0582/`

The visual run returned valid official output for:

- Imaging Quality: `0.6924868767893213`
- Dynamic Degree: `1.0` (the official Boolean result was `true`)
- Background Consistency: `0.8555138059951717`
- Subject Consistency: `0.762410238321247`

The semantic run also produced Aesthetic Quality `0.380208820104599` and Overall Consistency `0.12761658430099487`, but those values are **diagnostic only** for this record. The video is a concatenation of two generation segments, while the smoke prompt was only the exact `seg_000.txt` prompt; the project annotation does not contain a frozen task-level prompt. Therefore Overall Consistency and CLIPScore are not marked score-ready from this run.

The visual scores were produced in the existing GPU image (`torch 2.10.0+cu128`, `numpy 2.2.6`, `timm 1.0.28`, `transformers 5.8.1`). Those versions do not satisfy the pinned VBench requirements (`numpy<2`, `timm<=1.0.12`, `transformers==4.33.2`, CUDA 11.6/11.7/11.8/12.1). They are recorded as `scored_unverified_runtime`, not as strict official-environment B evidence. An isolated dependency environment is being prepared; until its CUDA and package gate passes, the status must remain qualified.

## What remains blocked or conditional

- Temporal Flickering needs an explicitly frozen static/near-static subset and excluded-count rule. The smoke video contains motion, so no static-subset acknowledgement was fabricated.
- CLIPScore and Overall Consistency need an exact task-level video-to-prompt manifest.
- DOVER needs the official `DOVER.pth`, ConvNeXt initialization and a separate Torch 1.13-compatible environment.
- WorldModelBench, T2V-CompBench, PhyGenBench and VideoPhy-2 require their official external repositories, checkpoints, judges and metadata; the repository adapters do not substitute them.
- VBench-2.0 Motion Order, Motion Rationality, Mechanics, Thermotics and Material require the official standard metadata and `auxiliary_info`; `custom_input` is not accepted for these dimensions.
- PSNR/SSIM/LPIPS require real aligned future reference frames. FVD/FID require a matching real collection or fixed statistics.

The frozen final selection remains exactly 21 main metrics plus 5 appendix metrics in `FINAL_METRICS.{md,json}`. Aesthetic Quality remains a diagnostic item and is not added to that selection.
