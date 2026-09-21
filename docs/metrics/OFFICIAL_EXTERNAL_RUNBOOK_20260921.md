# Official external metric runbook

Date: 2026-09-21

This document records the commands that the **user of the evaluator** runs. The project does not download or commit the large checkpoints. Every command below must be run from the exact official repository named in the section. Do not replace the official model with a smaller model and still call the result official.

## Project wrapper for the external official evaluators

The repository now provides scripts/run_official_external.py for every evaluator that was previously labelled external_caller_run. It does not reimplement any metric. It checks the pinned source revision and caller-owned paths, then forwards the exact official command after -- to the selected official working directory.

Example preflight and execution:

~~~bash
PYTHON=/root/metrics_pr_validation_20260919/dev-env/bin/python
$PYTHON scripts/run_official_external.py \
  --metric action_binding \
  --source-dir /data/sources/T2V-CompBench \
  --manifest /data/manifests/action_binding.official.json \
  --check-only -- \
  python LLaVA/llava/eval/compbench_eval_action_binding.py \
    --video-path /data/videos/action_binding \
    --output-path /data/results/action_binding \
    --read-prompt-file /data/manifests/action_binding.official.json \
    --t2v-model MODEL_NAME
~~~

Remove --check-only to run the unchanged official command. The runner writes a log when --output is supplied and fails closed if the pinned source, checkpoint, manifest, generated frames, or reference collection is missing. Motion Binding uses the official two-stage process, so invoke the runner once for each official stage. FVD still requires the caller to provide the pinned Google Research command and matched real/generated collections.

## 1. VBench base dimensions

Official source: `https://github.com/Vchitect/VBench`, pinned in this project to `fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`.

The upstream README installs the CUDA 11.8 PyTorch wheels (or another CUDA-compatible PyTorch with CUDA <= 12.1) and `vbench`; it places pretrained files under `~/.cache/vbench`. The official utility names the following files and URLs:

```bash
# Run in a persistent shell such as tmux.
git clone https://github.com/Vchitect/VBench.git /root/official_video_metrics_20260918/sources/VBench
cd /root/official_video_metrics_20260918/sources/VBench
git checkout fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490
python -m venv /root/official_video_metrics_20260918/envs/vbench
source /root/official_video_metrics_20260918/envs/vbench/bin/activate
python -m pip install --upgrade pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
python -m pip install -e .
```

Download only the official files used by the selected dimension. The file names and URLs below come from the pinned VBench utility; keep the paths unchanged:

```bash
export VBENCH_CACHE=/root/official_video_metrics_20260918/cache/vbench
mkdir -p "$VBENCH_CACHE/pyiqa_model" "$VBENCH_CACHE/clip_model" "$VBENCH_CACHE/ViCLIP" "$VBENCH_CACHE/dino_model/facebookresearch_dino_main"

# Imaging Quality / MUSIQ
wget -O "$VBENCH_CACHE/pyiqa_model/musiq_spaq_ckpt-358bb6af.pth" \
  https://github.com/chaofengc/IQA-PyTorch/releases/download/v0.1-weights/musiq_spaq_ckpt-358bb6af.pth

# Background Consistency and CLIPScore / OpenAI CLIP ViT-B/32
wget -O "$VBENCH_CACHE/clip_model/ViT-B-32.pt" \
  https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt

# Overall Consistency / ViCLIP
wget -O "$VBENCH_CACHE/ViCLIP/ViClip-InternVid-10M-FLT.pth" \
  https://huggingface.co/OpenGVLab/VBench_Used_Models/resolve/main/ViClip-InternVid-10M-FLT.pth

# Aesthetic Quality / OpenAI CLIP ViT-L/14 and LAION predictor
wget -O "$VBENCH_CACHE/clip_model/ViT-L-14.pt" \
  https://openaipublic.azureedge.net/clip/models/b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt
mkdir -p "$VBENCH_CACHE/aesthetic_model/emb_reader"
wget -O "$VBENCH_CACHE/aesthetic_model/emb_reader/sa_0_4_vit_l_14_linear.pth" \
  https://raw.githubusercontent.com/LAION-AI/aesthetic-predictor/main/sa_0_4_vit_l_14_linear.pth

# Dynamic Degree / official RAFT archive
mkdir -p "$VBENCH_CACHE/raft_model"
wget -O "$VBENCH_CACHE/raft_model/models.zip" \
  https://dl.dropboxusercontent.com/s/4j4z58wuv8o0mfz/models.zip
unzip -d "$VBENCH_CACHE/raft_model" "$VBENCH_CACHE/raft_model/models.zip"
rm -f "$VBENCH_CACHE/raft_model/models.zip"
```

RAFT and DINO must be downloaded exactly as described by the pinned VBench `pretrained/*/model_path.txt` and utility code. Do not substitute a different RAFT or DINO checkpoint. DINO also needs the official source checkout, because VBench imports DINO code at runtime; a checkpoint file by itself is not enough. For example:

```bash
git clone https://github.com/facebookresearch/dino.git "$VBENCH_CACHE/dino_model/facebookresearch_dino_main"
# Record the exact DINO git commit used by the checkout.
wget -O "$VBENCH_CACHE/dino_model/dino_vitbase16_pretrain.pth" \
  https://dl.fbaipublicfiles.com/dino/dino_vitbase16_pretrain/dino_vitbase16_pretrain.pth
mkdir -p "$VBENCH_CACHE/torch/hub/checkpoints"
cp "$VBENCH_CACHE/dino_model/dino_vitbase16_pretrain.pth" \
  "$VBENCH_CACHE/torch/hub/checkpoints/dino_vitbase16_pretrain.pth"
```

The wrapper requires a manifest containing the hashes of the selected checkpoint files and every Python file in the DINO checkout. Generate it from the files you actually downloaded; do not copy a manifest from another machine:

```bash
python - <<'PY'
from pathlib import Path
import hashlib, json, os
cache = Path(os.environ["VBENCH_CACHE"])
relative = [
    "dino_model/dino_vitbase16_pretrain.pth",
    "clip_model/ViT-B-32.pt", "clip_model/ViT-L-14.pt",
    "ViCLIP/ViClip-InternVid-10M-FLT.pth",
    "pyiqa_model/musiq_spaq_ckpt-358bb6af.pth",
    "aesthetic_model/emb_reader/sa_0_4_vit_l_14_linear.pth",
]
relative += [str(p.relative_to(cache)).replace(os.sep, "/") for p in (cache / "dino_model/facebookresearch_dino_main").rglob("*.py")]
manifest = {}
for name in sorted(set(relative)):
    path = cache / name
    if path.is_file():
        h = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest[name] = h
(cache / "weights-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(cache / "weights-manifest.json")
PY
```

Record the final cache inventory and SHA-256 in the user-owned `weights-manifest.json`.

Run one selected dimension through the project wrapper:

```bash
python /mnt/yiyang-workspace/WM-PerceptHarness/scripts/score_vbench_official.py \
  --vbench-root /root/official_video_metrics_20260918/sources/VBench \
  --videos-path /data/videos/sample-0001.mp4 \
  --dimension imaging_quality \
  --cache-dir "$VBENCH_CACHE" \
  --weights-manifest /data/manifests/imaging_quality.weights.json \
  --gpu 0 \
  --output-dir /data/results/imaging_quality_sample-0001
```

VBench's README explicitly documents custom-video evaluation for `subject_consistency`, `background_consistency`, `motion_smoothness`, `dynamic_degree`, `aesthetic_quality`, and `imaging_quality`. The pinned `evaluate.py` also accepts `custom_input` for `temporal_flickering` and `overall_consistency`; the wrapper therefore supports those two with their official extra requirements (`--static-subset-ack` for Temporal Flickering and the original generation prompt for Overall Consistency). If the caller wants a benchmark-suite result rather than a custom-video result, use the official `VBench_full_info.json` and filename mapping; do not mix the two protocols. Before Temporal Flickering, run the upstream static-video filter and keep its output list:

```bash
cd /root/official_video_metrics_20260918/sources/VBench
export VBENCH_CACHE_DIR="$VBENCH_CACHE"
CUDA_VISIBLE_DEVICES=0 python static_filter.py \
  --videos_path /data/videos/vbench_temporal_candidates \
  --model "$VBENCH_CACHE/raft_model/models/raft-things.pth" \
  --result_path /data/results/temporal_filter \
  --store_name filtered_temporal_flickering.json \
  --filter_scope temporal_flickering
```

The command writes `/data/results/temporal_filter/filtered_temporal_flickering.json` and a `filtered_videos/` directory. Keep both the JSON and the count; pass the filtered video path(s) to the wrapper and include `--static-subset-ack`. The six custom dimensions still require their own dimension-specific prompt/metadata when the official evaluator asks for it.

## 2. VBench CLIPScore

The official competition file is `competitions/clip_score.py`, not the regular VBench overall-consistency implementation. It uses OpenAI CLIP ViT-B/32 and the OpenAI CLIP cache layout. Prepare that exact cache before using the wrapper:

```bash
mkdir -p /root/official_video_metrics_20260918/.cache/clip
wget -O /root/official_video_metrics_20260918/.cache/clip/ViT-B-32.pt \
  https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt
```

Use the project wrapper:

```bash
python /mnt/yiyang-workspace/WM-PerceptHarness/scripts/score_vbench_clip_score.py \
  --vbench-root /root/official_video_metrics_20260918/sources/VBench \
  --videos-path /data/videos/sample-0001.mp4 \
  --prompt "the original generation prompt" \
  --clip-home /root/official_video_metrics_20260918 \
  --output-dir /data/results/clip_score_sample-0001
```

The prompt must be the prompt that generated the video. Do not caption the finished video and use that caption as a replacement.

## 3. DOVER

Official source: `https://github.com/QualityAssessment/DOVER` (the upstream repository is also referenced as `VQAssessment/DOVER`), commit `f1ddc96215bc7fbcf8f315c65d47905f339c3419`.

```bash
git clone https://github.com/VQAssessment/DOVER.git /root/official_video_metrics_20260918/sources/DOVER
cd /root/official_video_metrics_20260918/sources/DOVER
git checkout f1ddc96215bc7fbcf8f315c65d47905f339c3419
# Create the environment supported by your platform, then follow the
# versions in the pinned repository's dover.yml/requirements.txt.
python3.10 -m venv /root/official_video_metrics_20260918/envs/dover
source /root/official_video_metrics_20260918/envs/dover/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt PyYAML
python -m pip install -e .
```

Download the two official files into the paths expected by the unchanged evaluator:

```bash
mkdir -p pretrained_weights
wget -O pretrained_weights/DOVER.pth \
  https://github.com/QualityAssessment/DOVER/releases/download/v0.1.0/DOVER.pth
export TORCH_HOME=/root/official_video_metrics_20260918/cache/dover-torch
mkdir -p "$TORCH_HOME/hub/checkpoints"
wget -O "$TORCH_HOME/hub/checkpoints/convnext_tiny_1k_224_ema.pth" \
  https://dl.fbaipublicfiles.com/convnext/convnext_tiny_1k_224_ema.pth
```

The unchanged upstream one-video command is:

```bash
TORCH_HOME="$TORCH_HOME" python evaluate_one_video.py \
  -v /data/videos/sample-0001.mp4 -f
```

The project wrapper below performs the same official `evaluate_one_video.py -f` call after its source/checkpoint/runtime preflight. Check the files before running:

```bash
python /mnt/yiyang-workspace/WM-PerceptHarness/scripts/score_dover_official.py \
  --dover-root /root/official_video_metrics_20260918/sources/DOVER \
  --video /data/videos/sample-0001.mp4 \
  --torch-home "$TORCH_HOME" \
  --device cpu \
  --output-dir /data/results/dover_sample-0001 \
  --check-only
```

Remove `--check-only` only when the user wants to run official inference. The wrapper calls the original `evaluate_one_video.py -f`; it does not recreate DOVER's fusion formula.

## 4. WorldModelBench / Instruction Following

Official source: `https://github.com/WorldModelBench-Team/WorldModelBench`, commit `00b7aa17a05f9fd1ab5c8f66bcf476d04c9c33bf`.

The official README says to install VILA, download the judge, keep the official `worldmodelbench.json` and `images/`, and name each generated video after the `first_frame` stem. The official command is:

```bash
git clone https://github.com/WorldModelBench-Team/WorldModelBench.git /root/official_video_metrics_20260918/sources/WorldModelBench
cd /root/official_video_metrics_20260918/sources/WorldModelBench
git checkout 00b7aa17a05f9fd1ab5c8f66bcf476d04c9c33bf
# Install VILA exactly as instructed by the VILA repository.
# Official judge: https://huggingface.co/Efficient-Large-Model/vila-ewm-qwen2-1.5b
# Download that judge to /data/models/worldmodelbench_judge.
python evaluate.py \
  --model_name MODEL_NAME \
  --video_dir /data/worldmodelbench/generated_videos \
  --judge /data/models/worldmodelbench_judge \
  --save_name /data/results/worldmodelbench_results
```

The project adapter only checks and preserves `domain`, `subdomain`, `text_first_frame`, `text_instruction`, and `first_frame`. It never invents these fields.

## 5. T2V-CompBench / Action Binding, Object Interactions, Motion Binding

Official source: `https://github.com/KaiyueSun98/T2V-CompBench`, official `V2` branch frozen at commit `dd5eff7b93af0550b9efa2bdabbb21b3b017ceda`. Use this exact commit before evaluation:

```bash
git clone --branch V2 https://github.com/KaiyueSun98/T2V-CompBench.git /data/sources/T2V-CompBench
cd /data/sources/T2V-CompBench
git checkout dd5eff7b93af0550b9efa2bdabbb21b3b017ceda
git rev-parse HEAD
``` The official README supplies the environments, checkpoint URLs, metadata locations, and scripts.

MLLM environment:

```bash
conda create -n llava python==3.10.15 -y
conda activate llava
cd /data/sources/T2V-CompBench/LLaVA
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[train]"
python -m pip install flash-attn --no-build-isolation --no-cache-dir
```

Action Binding:

```bash
python LLaVA/llava/eval/compbench_eval_action_binding.py \
  --video-path /data/videos/action_binding \
  --output-path /data/results/action_binding \
  --read-prompt-file /data/manifests/action_binding.official.json \
  --t2v-model MODEL_NAME
```

Object Interactions:

```bash
python LLaVA/llava/eval/compbench_eval_interaction.py \
  --video-path /data/videos/object_interactions \
  --output-path /data/results/object_interactions \
  --read-prompt-file /data/manifests/object_interactions.official.json \
  --t2v-model MODEL_NAME
```

Motion Binding uses the official two-step Grounded-Segment-Anything and DOT commands. Install the separate official tracking environment and checkpoints exactly as in the V2 README:

```bash
export AM_I_DOCKER=False
export BUILD_WITH_CUDA=True
export CUDA_HOME=/path/to/cuda/
conda create -n compbench python==3.12.3 -y
conda activate compbench
cd Grounded-Segment-Anything
python -m pip install -e segment_anything
python -m pip install -r requirements.txt
cd ..
mkdir -p Grounded-Segment-Anything/GroundingDINO/weights
cd Grounded-Segment-Anything/GroundingDINO/weights
wget -q https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth
cd ../../..
cd dot
wget -P checkpoints https://huggingface.co/16lemoing/dot/resolve/main/cvo_raft_patch_8.pth
wget -P checkpoints https://huggingface.co/16lemoing/dot/resolve/main/movi_f_raft_patch_4_alpha.pth
wget -P checkpoints https://huggingface.co/16lemoing/dot/resolve/main/movi_f_cotracker_patch_4_wind_8.pth
wget -P checkpoints https://huggingface.co/16lemoing/dot/resolve/main/movi_f_cotracker2_patch_4_wind_8.pth
wget -O checkpoints/movi_f_cotracker3_wind_60.pth https://huggingface.co/facebook/cotracker3/resolve/main/scaled_offline.pth
wget -P checkpoints https://huggingface.co/16lemoing/dot/resolve/main/panning_movi_e_tapir.pth
wget -P checkpoints https://huggingface.co/16lemoing/dot/resolve/main/panning_movi_e_plus_bootstapir.pth
cd ..
```

Then run both official stages (the second command is run from `dot`):

```bash
python Grounded-Segment-Anything/compbench_motion_binding_seg.py \
  --video-path video/motion_binding \
  --read-prompt-file meta_data/motion_binding.json \
  --t2v-model mymodel --total_frame 16 --fps 8 \
  --output_dir output_motion_binding_seg
cd dot
python compbench_eval_motion_binding.py \
  --video-path ../video/video_standard/motion_binding \
  --mask_folder ../output_motion_binding_seg \
  --read-prompt-file ../meta_data/motion_binding.json \
  --t2v_model mymodel --output_path ../csv_motion_binding \
  --output_dir ../output_motion_binding
```

The project adapter creates only the official metadata; it does not replace these two official programs.

## 6. VBench-2.0 / Motion Order, Motion Rationality, Mechanics, Thermotics, Material

Official source: `https://github.com/Vchitect/VBench`, `VBench-2.0` at the same pinned VBench revision. The official README specifies Python 3.10, Torch 2.5.1 with CUDA 11.8, Flash-Attention 2.7.2.post1, `requirement.txt`, RetinaFace, the official Instance detector, and MMCV 2.2.0. Follow the upstream commands:

```bash
conda create -n vbench2 python=3.10 -y
conda activate vbench2
conda install psutil -y
python -m pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
python -m pip install ninja
python -m pip install git+https://github.com/Dao-AILab/flash-attention.git@v2.7.2.post1
python -m pip install -r VBench-2.0/requirement.txt
python -m pip install retinaface_pytorch==0.0.8 --no-deps
cd VBench-2.0/vbench2/third_party/Instance_detector
python -m pip install -e .
cd ../../..
python -m pip install mmcv==2.2.0 -f https://download.openmmlab.com/mmcv/dist/cu118/torch2.4/index.html --no-cache-dir
```

Download the models using the official `VBench-2.0/pretrained/download.sh` into `~/.cache/vbench2`. The official `LLaVA-Video-7B-Qwen2` and `Qwen2.5-7B-Instruct` directories must be the exact models named by that script.

Important: the five selected dimensions are **standard-suite dimensions**. The upstream `VBench-2.0` code asserts that `custom_input` is unsupported for Motion Order, Motion Rationality, Mechanics, Thermotics, and Material. Therefore the user must use the official `VBench2_full_info.json`, official prompt/video naming, and official `auxiliary_info`; an arbitrary local video cannot be relabeled as an official result.

Run the official standard evaluator:

```bash
cd /data/sources/VBench/VBench-2.0
bash evaluate.sh --max_parallel_tasks 1
```

The project adapter validates the official field shape, but it cannot turn a non-official custom task into a VBench-2.0 standard-suite sample.

## 7. PhyGenEval PCA

Official source: `https://github.com/OpenGVLab/PhyGenBench`, commit `f8642cb796f3bcb01f0b7c1b2ec53b75d357c739`.

```bash
git clone https://github.com/OpenGVLab/PhyGenBench.git /data/sources/PhyGenBench
cd /data/sources/PhyGenBench
git checkout f8642cb796f3bcb01f0b7c1b2ec53b75d357c739
# Follow the official VQAScore / LLaVA-Interleave / InternVideo2 instructions.
python PhyGenEval/single/vqascore.py
python PhyGenEval/multi/multiimage_clip.py
python PhyGenEval/video/MTScore/InternVideo_physical.py
python PhyGenEval/overall.py
```

The official repository ships `prompts.json`, `single_question.json`, `multi_question.json`, and `video_question.json`. The project adapter preserves these official files; it does not write new physics questions after looking at the generated video.

## 8. VideoPhy-2 PC, SA, and Joint

Official source: `https://github.com/Hritikbansal/videophy`, directory `VIDEOPHY2`. The official checkpoint is `https://huggingface.co/videophysics/videophy_2_auto`.

```bash
git clone https://github.com/Hritikbansal/videophy.git /data/sources/videophy
cd /data/sources/videophy/VIDEOPHY2
conda create -n videophy python=3.10 -y
conda activate videophy
python -m pip install -r ../requirements.txt
git lfs install
git clone https://huggingface.co/videophysics/videophy_2_auto /data/models/videophy_2_auto

# SA CSV: videopath and caption
CUDA_VISIBLE_DEVICES=0 python inference.py \
  --input_csv /data/manifests/videophy_sa.csv \
  --checkpoint /data/models/videophy_2_auto \
  --output_csv /data/results/videophy_sa.csv \
  --task sa

# PC CSV: videopath
CUDA_VISIBLE_DEVICES=0 python inference.py \
  --input_csv /data/manifests/videophy_pc.csv \
  --checkpoint /data/models/videophy_2_auto \
  --output_csv /data/results/videophy_pc.csv \
  --task pc
```

Then use the project joiner. Joint means the same video has `SA >= 4` and `PC >= 4`; it is not a third official model.

## 9. Reference and distribution metrics

### PSNR, SSIM, LPIPS

The frozen source for these appendix metrics is IQA-PyTorch commit `18dd7a19694e94aac21019170e3f5e63d6b4e19e`. The official directory CLI is:

```bash
git clone https://github.com/chaofengc/IQA-PyTorch.git /data/sources/IQA-PyTorch
cd /data/sources/IQA-PyTorch
git checkout 18dd7a19694e94aac21019170e3f5e63d6b4e19e
python inference_iqa.py -m PSNR -t /data/generated_frames -r /data/reference_frames
python inference_iqa.py -m SSIM -t /data/generated_frames -r /data/reference_frames
python inference_iqa.py -m LPIPS -t /data/generated_frames -r /data/reference_frames
```

The generated and reference directories must contain real, time-aligned frames with the same relative names. The project `build_reference_manifest.py` only checks the pairing; it does not create or align frames. If the caller does not have real future reference frames, report `N/A`.

### FID

Use the pinned IQA-PyTorch/official FID path and its CLI shape, with a real reference image/frame directory or an official precomputed statistic. Do not substitute statistics from another dataset:

```bash
pyiqa fid -t /data/generated_frames -r /data/reference_frames
```

### FVD

FVD is the Google Research TensorFlow metric. It compares two collections, not one video. The official implementation expects tensors shaped `[N, T, H, W, 3]` with RGB values in the 0--255 range and computes I3D embeddings before the Fréchet distance. The caller must create the real and generated collections using the official preprocessing, then run the pinned Google Research code in its TensorFlow/tensorflow-hub environment. If a matching real collection is unavailable, report `N/A`.
