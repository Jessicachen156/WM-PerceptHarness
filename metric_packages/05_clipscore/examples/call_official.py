"""Minimal call example. Scoring is performed by VBench's unmodified function."""
import argparse
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Official VBench JSON metadata; use absolute video paths')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--device', choices=('cuda', 'cpu'), default='cuda')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; choose a new file')
    if (os.environ.get('SSH_CONNECTION') or os.environ.get('SSH_TTY')) and not os.environ.get('TMUX'):
        parser.error('Enter and verify tmux before remote model download or inference')

    # Import official packages normally, without extracting or editing functions.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'official' / 'vbench'))
    import torch
    from competitions.clip_score import compute_clip_score

    score, details = compute_clip_score(str(args.input.resolve(strict=True)), torch.device(args.device), [])
    result = {'mean': float(score), 'videos': [
        {'video_path': row['video_path'], 'video_results': float(row['video_results'])}
        for row in details
    ]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
