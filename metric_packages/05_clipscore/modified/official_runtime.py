"""Independent source validation and loading for CLIPScore."""
from pathlib import Path
import ast
import hashlib
import json
import os
import re

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
CLIP_SHA256 = '40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af'


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def verify_official():
    manifest = json.loads((PACKAGE_ROOT / 'OFFICIAL_MANIFEST.json').read_text(encoding='utf-8'))
    for entry in manifest['files']:
        path = PACKAGE_ROOT / entry['path']
        if file_sha256(path) != entry['sha256']:
            raise ValueError('Bundled official source changed: ' + entry['path'])
    return manifest


def load_functions(path, names, namespace):
    """Select definitions only; imports and unrelated module side effects stay out."""
    tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    selected = [node for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    if {node.name for node in selected} != set(names):
        raise ValueError('Official definitions missing: ' + str(names))
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


def load_clip_functions():
    verify_official()
    import numpy as np
    import torch
    import torch.nn.functional as F
    import clip
    from tqdm import tqdm
    from decord import VideoReader
    from torchvision import transforms
    from torchvision.transforms import Compose, Resize, CenterCrop, Normalize, InterpolationMode
    namespace = dict(np=np, torch=torch, F=F, clip=clip, tqdm=tqdm, VideoReader=VideoReader,
                     transforms=transforms, Compose=Compose, Resize=Resize, CenterCrop=CenterCrop,
                     Normalize=Normalize, BICUBIC=InterpolationMode.BICUBIC)
    load_functions(PACKAGE_ROOT/'official/vbench/vbench/utils.py',
                   ['clip_transform', 'get_frame_indices', 'read_frames_decord_by_fps'], namespace)
    load_functions(PACKAGE_ROOT/'official/vbench/competitions/clip_score.py', ['clip_alignment'], namespace)
    return namespace


def verify_checkpoint(path):
    path = Path(path).expanduser().resolve(strict=True)
    digest = file_sha256(path)
    if digest != CLIP_SHA256:
        raise ValueError('Expected the official OpenAI CLIP ViT-B/32 checkpoint; SHA256 mismatch')
    return path, digest


def exact_prompt(segment, model):
    if model == 'lingbot-dense':
        # Exact saved prompt argument: only caption, no outer duration and no
        # removal of empty JSON fields. This is the project's historical mapping.
        return json.dumps(segment['structured_caption']['caption'], ensure_ascii=False, separators=(',', ':'))
    if model == 'wan':
        return segment['prompt']
    raise ValueError('This frozen project protocol supports wan and lingbot-dense only')


def read_manifest(path, kind):
    path = Path(path).resolve(strict=True)
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        raise ValueError('Empty manifest')
    seen = set()
    for row in rows:
        model, sample_id = row['model'], row['sample_id']
        if model not in ('wan', 'lingbot-dense'):
            raise ValueError('Unsupported model geometry/prompt mapping: ' + str(model))
        if not isinstance(sample_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', sample_id):
            raise ValueError('sample_id must be an ASCII filename-safe identifier')
        if (model, sample_id) in seen:
            raise ValueError('Duplicate model/sample_id')
        seen.add((model, sample_id))
        keys = ['video_path'] + (['source_video_path'] if kind == 'psnr' else [])
        for key in keys:
            p = Path(row[key]).expanduser()
            row[key] = str((path.parent/p if not p.is_absolute() else p).resolve(strict=True))
        hash_keys = ['recorded_final_sha256'] + (['source_sha256', 'first_frame_sha256'] if kind == 'psnr' else [])
        for key in hash_keys:
            if not isinstance(row.get(key), str) or not re.fullmatch('[0-9a-f]{64}', row[key]):
                raise ValueError(key + ' must be the frozen lowercase SHA-256')
        if not isinstance(row.get('recorded_evaluation_frames'), int) or row['recorded_evaluation_frames'] < 1:
            raise ValueError('recorded_evaluation_frames must be a positive integer')
        if kind == 'clip':
            segments = row.get('actual_segment_prompts')
            if not segments:
                if model == 'lingbot-dense':
                    raise ValueError('LingBot requires actual_segment_prompts with structured_caption.caption')
                segments = [{'prompt': row['prompt']}]
            for segment in segments:
                prompt = exact_prompt(segment, model)
                if not isinstance(prompt, str) or not prompt.strip():
                    raise ValueError('Missing exact runtime prompt')
                interval = segment.get('final_frame_range_inclusive')
                if interval is not None and (not isinstance(interval, list) or len(interval) != 2
                        or any(type(x) is not int for x in interval)
                        or not 0 <= interval[0] <= interval[1] < row['recorded_evaluation_frames']):
                    raise ValueError('Invalid inclusive final-frame interval')
    return sorted(rows, key=lambda x: (x['sample_id'], x['model']))


def require_persistent_remote_session():
    # Honor the project's remote-session rule, without requiring tmux on a local
    # Windows workstation. Documentation requires tmux for every remote long run.
    if (os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_TTY')) and not os.environ.get('TMUX'):
        raise RuntimeError('Create and enter tmux before starting a remote scoring run')
