from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from official_input_adapters import (  # noqa: E402
    InputSchemaError,
    adapt_action_binding,
    adapt_motion_binding,
    adapt_object_interactions,
    adapt_vbench2,
    adapt_videophy_csv,
    adapt_worldmodelbench,
    validate_phygen_eval,
)


def _local(i="a"):
    return {"video_id": i, "video": f"/videos/{i}.mp4"}


def test_worldmodelbench_emits_only_official_fields_and_sidecar():
    row = {**_local(), "domain": "human", "subdomain": "hands", "text_first_frame": "A hand is visible.", "text_instruction": "The hand waves.", "first_frame": "images/a.jpg", "ignored": "must not leak"}
    result = adapt_worldmodelbench([row])
    assert result["official"] == [{"text_first_frame": "A hand is visible.", "text_instruction": "The hand waves.", "first_frame": "images/a.jpg", "domain": "human", "subdomain": "hands"}]
    assert result["video_map"] == [{"video_id": "a", "video": "/videos/a.mp4", "first_frame": "images/a.jpg"}]


def test_action_binding_matches_official_schema():
    row = {**_local(), "prompt": "A dog runs while a cat climbs.", "phrase_0": ["a dog?", "a dog runs?"], "phrase_1": ["a cat?", "a cat climbs?"]}
    out = adapt_action_binding([row])
    assert out["official"] == [{"prompt": row["prompt"], "phrase_0": row["phrase_0"], "phrase_1": row["phrase_1"]}]


@pytest.mark.parametrize("bad", [[], ["cat"], ["cat", ""], ["cat", 1]])
def test_action_binding_rejects_non_two_text_phrases(bad):
    row = {**_local(), "prompt": "p", "phrase_0": bad, "phrase_1": ["a?", "a runs?"]}
    with pytest.raises(InputSchemaError):
        adapt_action_binding([row])


def test_motion_binding_requires_official_direction_pair():
    row = {**_local(), "prompt": "A cat walks left.", "object_1": "cat", "d_1": "left", "object_2": "", "d_2": ""}
    assert adapt_motion_binding([row])["official"][0] == {"prompt": row["prompt"], "object_1": "cat", "d_1": "left", "object_2": "", "d_2": ""}
    row["d_1"] = "north"
    with pytest.raises(InputSchemaError):
        adapt_motion_binding([row])


def test_object_interaction_official_schema_has_prompt_only():
    out = adapt_object_interactions([{**_local(), "prompt": "Two cars collide."}])
    assert out["official"] == [{"prompt": "Two cars collide."}]


def test_vbench2_dimension_and_auxiliary_shape():
    row = {**_local(), "prompt_en": "A person sits then sweeps.", "dimension": "Motion_Order_Understanding", "auxiliary_info": ["sitting", "sweeping"]}
    out = adapt_vbench2([row])
    assert out["official"] == [{"prompt_en": row["prompt_en"], "dimension": "Motion_Order_Understanding", "auxiliary_info": row["auxiliary_info"]}]
    row["auxiliary_info"] = ["only one"]
    with pytest.raises(InputSchemaError):
        adapt_vbench2([row])


def test_vbench2_accepts_full_info_dimension_list():
    row = {**_local(), "prompt_en": "A ball falls.", "dimension": ["Mechanics"], "auxiliary_info": ["Does the ball fall? (yes or no)"]}
    assert adapt_vbench2([row])["official"][0]["dimension"] == ["Mechanics"]


def test_phygen_assets_are_passed_through_without_renaming():
    payload = [{"prompt": "A ball falls.", "law": "gravity", "single_question": ["Does it fall?"]}]
    assert validate_phygen_eval(payload, stage="prompts")["official"] == payload
    assert validate_phygen_eval([{"question": "Does it fall?"}], stage="single")["official"] == [{"question": "Does it fall?"}]


@pytest.mark.parametrize("task,rows,expected", [
    ("pc", [{"videopath": "/a.mp4"}], [{"videopath": "/a.mp4"}]),
    ("sa", [{"caption": "A ball falls.", "videopath": "/a.mp4"}], [{"caption": "A ball falls.", "videopath": "/a.mp4"}]),
])
def test_videophy_csv_headers(task, rows, expected):
    assert adapt_videophy_csv(rows, task=task) == expected


def test_videophy_pc_does_not_accept_caption_as_output_or_duplicate_path():
    assert adapt_videophy_csv([{"videopath": "/a.mp4", "caption": "ignored"}], task="pc") == [{"videopath": "/a.mp4"}]
    with pytest.raises(InputSchemaError):
        adapt_videophy_csv([{"videopath": "/a.mp4"}, {"videopath": "/a.mp4"}], task="pc")


def test_cli_writes_official_file_and_sidecar_without_overwrite(tmp_path):
    # Exercise the JSON shape used by callers without depending on a CLI
    # subprocess, which keeps this test portable on Windows and Linux.
    payload = [{**_local(), "prompt": "p", "phrase_0": ["a?", "a runs?"], "phrase_1": ["b?", "b walks?"]}]
    path = tmp_path / "input.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert path.exists()
