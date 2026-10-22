"""Prepare a Kaggle kernel job and turn its output into postable reels.

  build     write render.py (with the job embedded) + kernel-metadata.json
  assemble  upscale clips to 1080x1920, add the synthesized soundtrack,
            collect stills, captions and release notes
"""

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from covers import make_job  # noqa: E402

KERNEL_SLUG = "spaceage-render"


def build(args):
    user = os.environ.get("KAGGLE_USER") or os.environ.get("KAGGLE_USERNAME")
    if not user:
        sys.exit("KAGGLE_USER is not set")
    if args.seed is not None:
        seed = args.seed
    else:  # date + run number, so reruns on the same day pick new scenes
        seed = int(dt.date.today().strftime("%Y%m%d")) * 100 + int(os.environ.get("GITHUB_RUN_NUMBER", "0")) % 100
    job = make_job(seed, args.count, args.videos)
    os.makedirs(args.dir, exist_ok=True)
    with open(os.path.join(HERE, "kaggle", "render.py")) as f:
        script = f.read().replace("__JOB__", json.dumps(job))
    token = os.environ.get("HF_TOKEN", "").strip()
    if token:
        if not token.isalnum() and not token.replace("_", "").isalnum():
            sys.exit("HF_TOKEN has unexpected characters")
        script = script.replace("__HF_TOKEN__", token)
    with open(os.path.join(args.dir, "render.py"), "w") as f:
        f.write(script)
    meta = {
        "id": f"{user}/{KERNEL_SLUG}",
        "title": KERNEL_SLUG,
        "code_file": "render.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "machine_shape": "NvidiaTeslaT4",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [],
    }
    with open(os.path.join(args.dir, "kernel-metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"{user}/{KERNEL_SLUG}")


def assemble(args):
    from make_reel import synth_audio

    with open(os.path.join(args.src, "result.json")) as f:
        result = json.load(f)
    os.makedirs(args.out, exist_ok=True)
    notes = [f"GPU: {result['report'].get('gpu')} · Bildmodell: {result['report'].get('image_model')} "
             f"· Dauer: {result['report'].get('minutes')} min"]
    if result["report"].get("flux_error"):
        notes.append("\n⚠️ FLUX-Fehler (Ersatz SDXL benutzt):\n```\n" + result["report"]["flux_error"][-800:] + "\n```")
    if result["report"].get("refine_error"):
        notes.append("\n⚠️ Schärfe-Pass fehlgeschlagen (Rohbilder):\n```\n" + result["report"]["refine_error"][-800:] + "\n```")
    if result["report"].get("video_error"):
        notes.append("\n⚠️ Video-Fehler:\n```\n" + result["report"]["video_error"][-800:] + "\n```")
    for i, item in enumerate(result["items"], 1):
        if item.get("image"):
            shutil.copy(os.path.join(args.src, item["image"]), os.path.join(args.out, f"bild_{i}.png"))
        if item.get("clip"):
            wav = os.path.join(args.out, f"audio_{i}.wav")
            synth_audio(wav, 4.1, 55.0 + 7 * i, [], item["seed"])
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-i", os.path.join(args.src, item["clip"]), "-i", wav,
                "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
                "-profile:v", "high", "-level", "4.1", "-r", "24",
                "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-shortest", "-movflags", "+faststart",
                os.path.join(args.out, f"reel_{i}.mp4"),
            ], check=True)
            os.remove(wav)
        with open(os.path.join(args.out, f"caption_{i}.txt"), "w") as f:
            f.write(item["caption"])
        kind = "Bild + Video" if item.get("clip") else "Bild"
        notes.append(f"\n**{i}. ({kind})** {item['prompt'].split('. ')[0]}\n\n{item['caption']}")
    with open(os.path.join(args.out, "notes.md"), "w") as f:
        f.write("\n".join(notes))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--dir", default="kernel")
    b.add_argument("--seed", type=int)
    b.add_argument("--count", type=int, default=8)
    b.add_argument("--videos", type=int, default=2)
    a = sub.add_parser("assemble")
    a.add_argument("--src", default="kaggle_out")
    a.add_argument("--out", default="out")
    args = ap.parse_args()
    build(args) if args.cmd == "build" else assemble(args)


if __name__ == "__main__":
    main()
