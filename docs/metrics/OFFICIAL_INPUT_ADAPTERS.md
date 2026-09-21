> **2026-09-21 official runbook.** Use `OFFICIAL_EXTERNAL_RUNBOOK_20260921.md` for the exact upstream URLs, revisions, checkpoint locations, installation commands, and official input boundaries. The older examples below are explanatory only; do not treat `/path/to/...` placeholders as a verified command.

# Official input adapters

`scripts/official_input_adapters.py` is a format checker and field-preserving
adapter. It does not score videos, download checkpoints, generate prompts, or
replace an upstream evaluator. The caller remains responsible for supplying
the original task metadata and for running the official command in its
documented environment.

The emitted `official` files deliberately contain only the fields consumed by
the upstream repositories:

| adapter | upstream file shape |
| --- | --- |
| `worldmodelbench` | WorldModelBench `worldmodelbench.json`: `domain`, `subdomain`, `text_first_frame`, `text_instruction`, `first_frame` (domain/subdomain are optional in the upstream examples) |
| `action_binding` | T2V-CompBench V2 `meta_data/action_binding.json`: `prompt`, `phrase_0`, `phrase_1`; each phrase is exactly two strings |
| `motion_binding` | T2V-CompBench V2 `meta_data/motion_binding.json`: `prompt`, `object_1`, `d_1`, `object_2`, `d_2`; directions are `left/right/up/down` and the second pair is empty for a one-object task |
| `object_interactions` | T2V-CompBench V2 `meta_data/object_interactions.json`: `prompt` |
| `vbench2` | VBench-2.0 `prompts/meta_info/*.json` / `VBench2_full_info.json`: `prompt_en`, one retained `dimension`, and a non-empty string-list `auxiliary_info`; Motion Order has exactly two ordered actions |
| `phygen_*` | PhyGenBench `prompts.json` and the three question assets; records are validated and passed through without renaming fields |
| `videophy_pc` / `videophy_sa` | VideoPhy-2 AutoEval CSV: `videopath` for PC; `caption,videopath` for SA |

The official metadata files intentionally do not contain arbitrary local video
paths. For WorldModelBench, T2V-CompBench, and VBench-2.0 the script therefore
returns a separate `video_map` sidecar (`video_id` + `video`). The sidecar is a
local mapping aid and must not be mixed into an upstream metadata file.

Example local input for T2V-CompBench:

```json
[
  {
    "video_id": "sample-0001",
    "video": "/data/videos/sample-0001.mp4",
    "prompt": "A dog runs while a cat climbs a tree.",
    "phrase_0": ["a dog?", "a dog runs?"],
    "phrase_1": ["a cat?", "a cat climbs a tree?"]
  }
]
```

```bash
python scripts/official_input_adapters.py \
  --adapter action_binding \
  --input /data/manifests/action_binding.local.json \
  --output /data/manifests/action_binding.official.json \
  --video-map-output /data/manifests/action_binding.video_map.json
```

The command refuses to overwrite an existing output. It also refuses duplicate
video IDs/paths, unknown directions, missing prompts, malformed phrase lists,
and incomplete VBench-2.0 auxiliary questions. For PhyGenEval question files,
the adapter deliberately does not invent a schema: use the files shipped by
PhyGenBench or the exact schema accepted by the pinned upstream revision.
