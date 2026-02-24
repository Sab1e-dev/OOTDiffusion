import argparse
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser(description="Test OOTDiffusion FastAPI /try-on endpoint")
    parser.add_argument("--server", type=str, default="http://127.0.0.1:7735", help="API server base URL")
    parser.add_argument("--person", type=str, required=True, help="Path to person image")
    parser.add_argument("--cloth", type=str, required=True, help="Path to cloth image")
    parser.add_argument("--output", type=str, default="result_try_on.png", help="Path to save output image")
    parser.add_argument("--model_type", type=str, default="hd", choices=["hd", "dc"], help="Model type: hd or dc")
    parser.add_argument("--category", type=int, default=0, help="Garment category: 0=upperbody, 1=lowerbody, 2=dress")
    parser.add_argument("--scale", type=float, default=2.0, help="Image scale parameter passed to backend")
    parser.add_argument("--sample", type=int, default=4, help="Number of samples passed to backend")
    parser.add_argument("--step", type=int, default=20, help="Number of steps passed to backend")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed passed to backend (-1 for random)")
    args = parser.parse_args()

    # 自动补全协议头，避免 "No connection adapters were found" 错误
    server = args.server
    if not server.startswith(("http://", "https://")):
        server = "http://" + server
    server = server.rstrip("/")
    url = f"{server}/try-on"

    person_path = Path(args.person)
    cloth_path = Path(args.cloth)

    if not person_path.is_file():
        raise SystemExit(f"Person image not found: {person_path}")
    if not cloth_path.is_file():
        raise SystemExit(f"Cloth image not found: {cloth_path}")

    files = {
        "model_image": (person_path.name, person_path.read_bytes(), "image/jpeg"),
        "cloth_image": (cloth_path.name, cloth_path.read_bytes(), "image/jpeg"),
    }

    data = {
        "model_type": args.model_type,
        "category": str(args.category),
        "scale": str(args.scale),
        "sample": str(args.sample),
        "step": str(args.step),
        "seed": str(args.seed),
    }

    print(f"Sending request to {url}...")
    resp = requests.post(url, files=files, data=data, timeout=600)

    if resp.status_code != 200:
        print("Request failed:")
        try:
            print(resp.json())
        except Exception:
            print(resp.text)
        raise SystemExit(f"HTTP {resp.status_code}")

    out_path = Path(args.output)
    out_path.write_bytes(resp.content)
    print(f"Saved result to {out_path.resolve()}")


if __name__ == "__main__":
    main()
