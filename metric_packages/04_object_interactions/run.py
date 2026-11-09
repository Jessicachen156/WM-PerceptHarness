"""Portable invocation of the unchanged T2V-CompBench Object Interactions evaluator.

No model import, download or GPU work occurs with --help or --check-only.
The scoring, grid sampling, questions and answer parsing remain upstream.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

REVISION = "dd5eff7b93af0550b9efa2bdabbb21b3b017ceda"
SOURCE_HASHES = {
    "llava/eval/compbench_eval_interaction.py": "1b41b8d37d211844cab8c4eef9bce024d0d3ccce22db82b606e58a2e40a48a0c",
    "llava/model/builder.py": "901a83fe993168b60e5632872ce230aa23e7c404e5e1b3f1ea04cd13d6dc9b81",
}
FIXED_ARGUMENTS = {
    "model_base": None, "conv_mode": None, "sep": ",", "temperature": 0.1,
    "top_p": None, "num_beams": 1, "max_new_tokens": 512, "seed": 0,
    "image_grid_path": None,
}
PATH_ARGUMENTS = ("model_path", "video_path", "read_prompt_file", "output_path")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(source_root: Path) -> dict:
    """source_root is the upstream checkout's LLaVA directory."""
    source_root = source_root.expanduser().resolve(strict=True)
    revision = subprocess.check_output(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise ValueError(f"Expected upstream HEAD {REVISION}, got {revision}")
    actual = {name: sha256(source_root / name) for name in SOURCE_HASHES}
    if actual != SOURCE_HASHES:
        raise ValueError("Official evaluator or loader differs from the audited runtime")
    # A local openai/CLIP symlink may be untracked; tracked changes are rejected.
    dirty = subprocess.check_output(
        ["git", "-C", str(source_root), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty.strip():
        raise ValueError("Tracked upstream files are modified; use an unchanged checkout")
    return {"revision": revision, "sha256": actual}


def load_arguments(path: Path) -> dict:
    arguments = json.loads(path.read_text(encoding="utf-8-sig"))
    required = set(FIXED_ARGUMENTS) | set(PATH_ARGUMENTS) | {"t2v_model"}
    if not isinstance(arguments, dict) or set(arguments) != required:
        raise ValueError(f"Argument JSON must have exactly these fields: {sorted(required)}")
    for key, value in FIXED_ARGUMENTS.items():
        if type(arguments[key]) is not type(value) or arguments[key] != value:
            raise ValueError(f"Protocol argument {key} must be {value!r}")
    if not isinstance(arguments["t2v_model"], str) or not arguments["t2v_model"] or any(
            c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in arguments["t2v_model"]):
        raise ValueError("t2v_model must be a simple nonempty filename label")
    for key in PATH_ARGUMENTS:
        value = arguments[key]
        if not isinstance(value, str) or not value:
            raise ValueError(f"{key} must be a nonempty path")
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = path.parent / candidate
        arguments[key] = str(candidate.resolve())
    if Path(arguments["model_path"]).name != "llava-v1.6-34b":
        raise ValueError("Keep checkpoint basename llava-v1.6-34b for upstream model-family detection")
    if not Path(arguments["model_path"]).is_dir():
        raise ValueError("Provide the predownloaded llava-v1.6-34b checkpoint directory")
    videos = Path(arguments["video_path"])
    if not videos.is_dir():
        raise ValueError("video_path must be a dedicated directory of numbered MP4 files")
    files = sorted(p.name for p in videos.iterdir())
    if not files or files != [f"{i:04d}.mp4" for i in range(1, len(files) + 1)] or len(files) > 9999:
        raise ValueError("Input directory must contain only 0001.mp4, 0002.mp4, ...")
    if any(not (videos / name).is_file() for name in files):
        raise ValueError("All numbered video entries must be files")
    metadata = json.loads(Path(arguments["read_prompt_file"]).read_text(encoding="utf-8-sig"))
    if not isinstance(metadata, list) or len(metadata) != len(files) or any(
            not isinstance(row, dict) or set(row) != {"prompt"} or not isinstance(row["prompt"], str) or not row["prompt"].strip()
            for row in metadata):
        raise ValueError("Metadata must be one original nonempty prompt per numbered video")
    if Path(arguments["output_path"]).exists():
        raise FileExistsError("Use a fresh output directory; upstream CSV line-count resume is not content-aware")
    # Official preprocessing writes sibling frames/image_grid directories.
    grid_dir = videos.parent / "image_grid" / videos.name
    if grid_dir.exists():
        raise FileExistsError("Use fresh staged video directory; a previous sibling image_grid exists")
    return arguments


def read_official_scores(csv_path: Path, expected_names: list[str]) -> dict:
    """Validate and expose official arithmetic; do not repair bad replies."""
    with csv_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    by_name = {}
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Malformed official CSV row width")
        name = row.get("name")
        if name not in expected_names or name in by_name:
            raise ValueError("Unexpected or duplicate official CSV video name")
        by_name[name] = row
    if set(by_name) != set(expected_names):
        raise ValueError("Official CSV does not cover every input video")
    result = []
    for name in expected_names:
        row = by_name[name]
        item = {"name": name, "status": "invalid", "score": None}
        try:
            seeds = [float(row[f"seed{i}_score"]) for i in range(3)]
            raw = float(row["Score"])
            if not all(math.isfinite(s) and s.is_integer() and 1 <= s <= 10 for s in seeds):
                raise ValueError("Invalid official seed score")
            if not math.isfinite(raw) or not math.isclose(sum(seeds) / 3, raw, rel_tol=0, abs_tol=1e-8):
                raise ValueError("Seed mean differs from official Score")
            item.update(status="complete", raw_seed_scores=seeds, raw_seed_mean=raw, score=(raw - 1) / 9)
        except (KeyError, ValueError, TypeError) as error:
            item["error"] = str(error)
        result.append(item)
    invalid = sum(row["status"] != "complete" for row in result)
    valid_scores = [row["score"] for row in result if row["status"] == "complete"]
    official_aggregate = sum(valid_scores) / len(valid_scores) if valid_scores else None
    return {"metric": "object_interactions", "rule": "(official three-seed raw mean - 1) / 9",
            "rows": result, "valid_count": len(result) - invalid, "invalid_count": invalid,
            "aggregate": official_aggregate,
            "aggregate_policy": "official valid-row mean; invalid rows skipped; null if none valid",
            "complete_coverage_aggregate": None if invalid else official_aggregate}


def invoke(source_root: Path, arguments: dict) -> dict:
    if not os.environ.get("TMUX"):
        raise RuntimeError("Create, enter and verify tmux before model inference")
    output = Path(arguments["output_path"])
    output.mkdir(parents=True, exist_ok=False)
    os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false",
                      OMP_NUM_THREADS="2", TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="1",
                      PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True")
    sys.path.insert(0, str(source_root))
    os.chdir(source_root)
    from llava.eval import compbench_eval_interaction as module
    original = module.load_pretrained_model

    def observed(*args, **kwargs):
        result = original(*args, **kwargs)
        model = result[1]
        receipt = {"loaded_unix": time.time(), "dtype": str(model.dtype),
                   "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
                   "hf_device_map": {k: str(v) for k, v in getattr(model, "hf_device_map", {}).items()},
                   "adapter": "record returned placement only; loader arguments and scoring unchanged"}
        (output / "model_placement.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        if str(model.dtype) != "torch.float16":
            raise ValueError("Historical protocol requires unquantized float16")
        return result

    module.load_pretrained_model = observed
    try:
        csv_path = Path(module.eval_model(SimpleNamespace(**arguments)))
    finally:
        module.load_pretrained_model = original
    count = len(json.loads(Path(arguments["read_prompt_file"]).read_text(encoding="utf-8-sig")))
    result = read_official_scores(csv_path, [f"{i:04d}.png" for i in range(1, count + 1)])
    (output / "project_scores.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="Pinned checkout's LLaVA directory")
    parser.add_argument("--arguments", type=Path, required=True, help="Official arguments JSON; relative paths resolve beside it")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    root = args.source_root.expanduser().resolve(strict=True)
    source = verify_source(root)
    arguments = load_arguments(args.arguments.expanduser().resolve(strict=True))
    if args.check_only:
        print(json.dumps({"status": "preflight_passed_not_scored", "source": source, "arguments": arguments}, indent=2))
        return 0
    result = invoke(root, arguments)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if result["invalid_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
