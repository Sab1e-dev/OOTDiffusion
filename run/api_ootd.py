from pathlib import Path
import shutil
import subprocess
import sys
import uuid
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, JSONResponse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = PROJECT_ROOT / "run"
UPLOAD_DIR = RUN_DIR / "uploads"
OUTPUT_DIR = RUN_DIR / "images_output"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="OOTDiffusion API", description="Virtual try-on API wrapping run_ootd.py", version="1.0.0")


def _save_upload(file: UploadFile, suffix_default: str = ".png") -> Path:
    if not file.filename:
        suffix = suffix_default
    else:
        suffix = Path(file.filename).suffix or suffix_default
    tmp_name = f"{uuid.uuid4().hex}{suffix}"
    dst = UPLOAD_DIR / tmp_name
    with dst.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return dst


def _run_ootd(
    model_path: Path,
    cloth_path: Path,
    model_type: str = "hd",
    category: int = 0,
    scale: float = 2.0,
    sample: int = 4,
    step: int = 20,
    seed: int = -1,
) -> Path:
    if model_type not in {"hd", "dc"}:
        raise HTTPException(status_code=400, detail="model_type must be 'hd' or 'dc'")
    if model_type == "hd" and category != 0:
        raise HTTPException(status_code=400, detail="When model_type is 'hd', category must be 0 (upperbody)")
    if category not in {0, 1, 2}:
        raise HTTPException(status_code=400, detail="category must be 0, 1 or 2")

    # 清理旧输出，避免混淆
    for p in OUTPUT_DIR.glob("out_*_*.png"):
        try:
            p.unlink()
        except OSError:
            pass

    cmd = [
        sys.executable,
        "run_ootd.py",
        "--model_path",
        str(model_path),
        "--cloth_path",
        str(cloth_path),
        "--model_type",
        model_type,
        "--category",
        str(category),
        "--scale",
        str(scale),
        "--sample",
        str(sample),
        "--step",
        str(step),
        "--seed",
        str(seed),
    ]

    try:
        completed = subprocess.run(
            cmd,
            cwd=RUN_DIR,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start run_ootd.py: {e}")

    if completed.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "run_ootd.py failed",
                "stdout": completed.stdout.decode(errors="ignore"),
                "stderr": completed.stderr.decode(errors="ignore"),
            },
        )

    # 寻找输出图片（out_<model_type>_*.png）
    candidates = sorted(OUTPUT_DIR.glob(f"out_{model_type}_*.png"))
    if not candidates:
        raise HTTPException(status_code=500, detail="No output image found in images_output")

    return candidates[-1]


@app.post("/try-on")
async def try_on(
    model_image: UploadFile = File(..., description="Person image"),
    cloth_image: UploadFile = File(..., description="Garment image"),
    model_type: str = Form("hd"),
    category: int = Form(0),
    scale: float = Form(2.0),
    sample: int = Form(4),
    step: int = Form(20),
    seed: int = Form(-1),
):
    """虚拟试穿接口：上传人物图和衣服图，返回合成后人物图。"""
    if model_image.content_type is None or not model_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="model_image must be an image file")
    if cloth_image.content_type is None or not cloth_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="cloth_image must be an image file")

    try:
        model_path = _save_upload(model_image)
        cloth_path = _save_upload(cloth_image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded files: {e}")

    try:
        output_path = _run_ootd(
            model_path=model_path,
            cloth_path=cloth_path,
            model_type=model_type,
            category=category,
            scale=scale,
            sample=sample,
            step=step,
            seed=seed,
        )
    finally:
        # 简单清理上传文件
        for p in (locals().get("model_path"), locals().get("cloth_path")):
            if isinstance(p, Path) and p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    return FileResponse(
        path=str(output_path),
        media_type="image/png",
        filename=output_path.name,
    )


@app.post("/try-on-qipao")
async def try_on_qipao(
    model_image: UploadFile = File(..., description="Person image"),
    cloth_image: UploadFile = File(..., description="Cheongsam garment image"),
    scale: float = Form(2.0),
    sample: int = Form(4),
    step: int = Form(20),
    seed: int = Form(-1),
):
    """旗袍专用接口：内部固定使用 Dress Code 全身模型 (model_type='dc', category=2)。"""
    if model_image.content_type is None or not model_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="model_image must be an image file")
    if cloth_image.content_type is None or not cloth_image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="cloth_image must be an image file")

    try:
        model_path = _save_upload(model_image)
        cloth_path = _save_upload(cloth_image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded files: {e}")

    try:
        output_path = _run_ootd(
            model_path=model_path,
            cloth_path=cloth_path,
            model_type="dc",
            category=2,
            scale=scale,
            sample=sample,
            step=step,
            seed=seed,
        )
    finally:
        for p in (locals().get("model_path"), locals().get("cloth_path")):
            if isinstance(p, Path) and p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass

    return FileResponse(
        path=str(output_path),
        media_type="image/png",
        filename=output_path.name,
    )


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_ootd:app",
        host="0.0.0.0",
        port=7735,
        reload=False,
    )
