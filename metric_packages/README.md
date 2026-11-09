# Standalone metric source packages

These seven directories contain the reviewed source packages and experiment
adaptations for metrics that already have entries in the harness. Each directory
is independently usable with its documented runtime and external assets. They
are source directories, not ZIP files or a shared Python environment, and are
not installed by `pip install -e .`.

Keep the existing `percept` commands for their documented workflows. Use these
packages when you need the additional runners or explicitly selected modified
protocols below. Their scores must retain the protocol name and configuration.

| Package | Official code and existing harness support | Additional code in this directory | Main limits |
| --- | --- | --- | --- |
| [01_semantic_adherence](01_semantic_adherence/README.md) | Pinned VideoPhy-2 source; main has CSV preparation and an external launcher | Independent SA inference; official 32-frame mode or `min(max(ceil(N/2),32),256)` sampling; raw responses and sampling records | Requires a frozen target caption; added frames have no established accuracy benefit; official answer parser can return 0 |
| [02_physical_commonsense](02_physical_commonsense/README.md) | Same VideoPhy-2 source and fixed physical-commonsense question | Independent PC inference with the same selectable sampling protocols | Physical plausibility does not establish task completion; judge reliability and added-frame benefit remain unvalidated |
| [04_object_interactions](04_object_interactions/README.md) | Unchanged T2V-CompBench evaluator/loader subset; main has metadata preparation and an external launcher | Invocation of a complete pinned upstream checkout, device/dtype records, official aggregate and a separate complete-coverage aggregate | Six-frame grid can miss interactions; judge/seed disagreement; full upstream checkout and large local model required |
| [05_clipscore](05_clipscore/README.md) | Main already calls the official function for one video; this package includes pinned import dependencies | Recommended official JSON batch call, plus the optional existing Wan/Dense window protocol | CLIP text truncation and frame-level similarity limits; window scores use different inputs/aggregation from whole-video scores |
| [06_psnr](06_psnr/README.md) | Unchanged IQA-PyTorch RGB PSNR kernel; main only prepares reference pairs and launches external scoring | Source-PTS matching, real conditioning-image identity checks, native Wan/Dense geometry and exclusion of generated frame 0 | Requires matched source videos; protocol is limited to documented Wan/Dense geometry and 24 fps; valid timing/trajectory changes can lower scores |
| [07_dynamic_degree](07_dynamic_degree/README.md) | Unchanged VBench 0.1.5 wheel baseline; main already provides official scoring | Explicit `official` or `cpu-staging` modes; modified mode keeps decoded inputs on CPU and transfers the current frame pair | Camera motion affects the Boolean motion threshold; input staging is not streaming decoding and does not reduce model memory |
| [08_motion_smoothness](08_motion_smoothness/README.md) | Unchanged VBench 0.1.5 / AMT-S baseline; main already provides official scoring | Explicit `official` or `cpu-staging` modes; modified mode keeps input tensors on CPU | Smoothness is not action correctness; CPU resize can differ numerically; long videos still need CPU memory |

Package numbers retain the delivered layout. The missing `03` is intentional:
Motion Rationality is excluded from this addition. The SA/PC sampler's unused MR
branch and context-budget helper have also been removed; VideoPhy sampling and
scoring are unchanged by that cleanup. Action Binding, historical candidates,
old comparison directories and already adequate MUSIQ/Subject Consistency
packages are outside this addition.

## Run a package

Read its README, prepare a separate compatible environment and the exact local
weights/checkouts, then run from that package directory. Input files under
`examples/` are synthetic placeholders. No videos, checkpoints or private
evaluation outputs are included. Several `official/` directories are selected
source subsets, not complete installable upstream repositories.

For example, the recommended CLIPScore path accepts any video source and does
not require Wan/Dense labels:

```bash
cd metric_packages/05_clipscore
python examples/call_official.py --input /data/official_inputs.json \
  --output /data/results/clipscore.json --device cuda
```

Prepare the dependencies and OpenAI CLIP cache described in
[OFFICIAL_USAGE.md](05_clipscore/OFFICIAL_USAGE.md) first. The official function
can download its checkpoint when missing. Before remote installation, downloads
or inference, enter and verify a persistent session:

```bash
tmux new-session -s metric-run
test -n "$TMUX"
tmux display-message -p '#S'
```

Detach with `Ctrl-b`, then `d`; reattach with `tmux attach -t metric-run`.
Preserve existing caches, partial files, destination paths, authentication
environment and download backend when resuming.

## Provenance and validation

Each package has a `MANIFEST.json` covering its files, plus upstream provenance
and retained licenses. `.gitattributes` preserves exact bytes because some
runners validate source hashes. Official files are kept separate from project
adaptations. SA and PC, and the two VBench wheel-based packages, deliberately
repeat necessary files so each directory can be copied independently.

Repository tests check file hashes, complete manifest coverage, command help
without model imports, and SA/PC sampling boundaries. These checks do not install
the metric environments, load models or demonstrate score accuracy. This source
submission has not repeated real CPU/GPU scoring, fresh metric-environment
installation or full-dataset validation. Recorded earlier experiments in the
individual READMEs are not validation of a new installation.

Third-party source and model licenses remain separate from this repository's
MIT license. In particular, the PSNR package retains IQA-PyTorch's PolyForm
Noncommercial and S-Lab terms. See [third-party notices](../docs/third-party-notices.md#vendored-standalone-metric-packages).
