# Validation record (2026-09-20)

## What was validated

- `python -m py_compile` passed for the new wrappers, adapters and tests.
- The VBench wrapper was run in `--check-only` mode against the pinned official source tree at `fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`. The source fingerprint matched the pinned tree; no model inference was started.
- The wrapper, DOVER wrapper, CLIPScore wrapper, input adapters and reference/aggregation tools passed the targeted Ali02 test run:

  ```text
  99 passed, 42 subtests passed
  ```

  The targeted run used `/root/reuse75_runtime/venvs/eval/bin/python` and did not download checkpoints.

## What was not claimed

- No new model weight was committed or downloaded by this package.
- No full 75-video run was required or performed for the newly added metrics.
- The new CLIPScore wrapper has not been claimed as a GPU inference result; its official source call, checkpoint layout and result parser are covered by offline contract tests.
- The external WorldModelBench, T2V-CompBench, PhyGenBench and VideoPhy-2 model environments are not silently substituted with another judge.

## Existing repository test limitation

The full repository suite was also started on Ali02. In the current server image, pre-existing CV/SAM3.1 tests fail because their artifact directory and local SAM3.1 runtime are unavailable; the failures are outside these metric files. The full run therefore must not be reported as green. The new metric test set above is the relevant validation for this commit.
