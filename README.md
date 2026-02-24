# OOTDiffusion
This repository is the official implementation of OOTDiffusion

🤗 [Try out OOTDiffusion](https://huggingface.co/spaces/levihsu/OOTDiffusion)

(Thanks to [ZeroGPU](https://huggingface.co/zero-gpu-explorers) for providing A100 GPUs)

<!-- Or [try our own demo](https://ootd.ibot.cn/) on RTX 4090 GPUs -->

> **OOTDiffusion: Outfitting Fusion based Latent Diffusion for Controllable Virtual Try-on** [[arXiv paper](https://arxiv.org/abs/2403.01779)]<br>
> [Yuhao Xu](http://levihsu.github.io/), [Tao Gu](https://github.com/T-Gu), [Weifeng Chen](https://github.com/ShineChen1024), [Chengcai Chen](https://www.researchgate.net/profile/Chengcai-Chen)<br>
> Xiao-i Research


Our model checkpoints trained on [VITON-HD](https://github.com/shadow2496/VITON-HD) (half-body) and [Dress Code](https://github.com/aimagelab/dress-code) (full-body) have been released

* 🤗 [Hugging Face link](https://huggingface.co/levihsu/OOTDiffusion) for ***checkpoints*** (ootd, humanparsing, and openpose)
* 📢📢 We support ONNX for [humanparsing](https://github.com/GoGoDuck912/Self-Correction-Human-Parsing) now. Most environmental issues should have been addressed : )
* Please also download [clip-vit-large-patch14](https://huggingface.co/openai/clip-vit-large-patch14) into ***checkpoints*** folder
* We've only tested our code and models on Linux (Ubuntu 22.04)

![demo](images/demo.png)&nbsp;
![workflow](images/workflow.png)&nbsp;

## Installation
1. Clone the repository

```sh
git clone https://github.com/levihsu/OOTDiffusion
```

2. Create a conda environment and install the required packages

```sh
conda create -n ootd python==3.10
conda activate ootd
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
pip install -r requirements.txt
```

## Inference
1. Half-body model

```sh
cd OOTDiffusion/run
python run_ootd.py --model_path <model-image-path> --cloth_path <cloth-image-path> --scale 2.0 --sample 4
```

2. Full-body model 

> Garment category must be paired: 0 = upperbody; 1 = lowerbody; 2 = dress

```sh
cd OOTDiffusion/run
python run_ootd.py --model_path <model-image-path> --cloth_path <cloth-image-path> --model_type dc --category 2 --scale 2.0 --sample 4
```

## FastAPI service (local)

We provide a simple FastAPI-based HTTP service in this repo to call `run_ootd.py` from other programs.

### Environment (GPU)

Make sure you are using a GPU build of PyTorch and a CUDA-enabled environment. One working combination:

```sh
conda create -n ootd python==3.10
conda activate ootd

pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 torchaudio==2.0.2+cu118 \
  --index-url https://download.pytorch.org/whl/cu118

pip install -r requirements.txt
pip install fastapi uvicorn[standard] python-multipart
pip install huggingface-hub==0.24.0
```

Check CUDA:

```python
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.version.cuda)"
```

### Start API server

From the project root:

```sh
cd OOTDiffusion
python run/api_ootd.py
```

The default address is:

- `http://127.0.0.1:7735`
- Health check: `GET /health` → `{ "status": "ok" }`

### General try-on API: `POST /try-on`

`multipart/form-data` request:

- `model_image` (file, required): person image
- `cloth_image` (file, required): garment image
- `model_type` (str, optional, default `"hd"`): `"hd"` (VITON-HD) or `"dc"` (Dress Code)
- `category` (int, optional, default `0`): only used when `model_type="dc"`; `0=upperbody`, `1=lowerbody`, `2=dress`
- `scale` (float, optional, default `2.0`)
- `sample` (int, optional, default `4`)
- `step` (int, optional, default `20`)
- `seed` (int, optional, default `-1`)

Response:

- `200 OK`: PNG image body (try-on result)
- Error: JSON with `detail` field and backend logs

Example with `curl`:

```sh
curl -X POST "http://127.0.0.1:7735/try-on" \
  -F "model_image=@/path/to/person.png" \
  -F "cloth_image=@/path/to/cloth.png" \
  -F "model_type=dc" \
  -F "category=2" \
  --output result_try_on.png
```

### Qipao-only API: `POST /try-on-qipao`

This endpoint is specialized for cheongsam/qipao clothes and internally fixes:

- `model_type = "dc"`
- `category = 2` (dress)

Request (`multipart/form-data`):

- `model_image` (file, required): person image
- `cloth_image` (file, required): qipao garment image
- `scale`, `sample`, `step`, `seed`: same as `/try-on`

Response:

- `200 OK`: PNG image body (qipao try-on result)

Example:

```sh
curl -X POST "http://127.0.0.1:7735/try-on-qipao" \
  -F "model_image=@/path/to/person.png" \
  -F "cloth_image=@/path/to/qipao.png" \
  --output qipao_result.png
```

## Citation
```
@article{xu2024ootdiffusion,
  title={OOTDiffusion: Outfitting Fusion based Latent Diffusion for Controllable Virtual Try-on},
  author={Xu, Yuhao and Gu, Tao and Chen, Weifeng and Chen, Chengcai},
  journal={arXiv preprint arXiv:2403.01779},
  year={2024}
}
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=levihsu/OOTDiffusion&type=Date)](https://star-history.com/#levihsu/OOTDiffusion&Date)

## TODO List
- [x] Paper
- [x] Gradio demo
- [x] Inference code
- [x] Model weights
- [ ] Training code
