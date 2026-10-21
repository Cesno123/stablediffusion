"""Kaggle GPU kernel: FLUX.1-schnell stills + LTX-Video image-to-video clips.

kaggle_job.py replaces the __JOB__ placeholder with the job JSON before
pushing. Everything written to /kaggle/working comes back as kernel output.
Falls back to SDXL if FLUX cannot run on the assigned GPU.
"""

import gc
import json
import os
import subprocess
import time
import traceback

JOB = json.loads(r"""__JOB__""")
OUT = "/kaggle/working"


def sh(cmd):
    print("+", cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


sh("nvidia-smi --query-gpu=name,memory.total --format=csv")
sh("pip install -q -U diffusers transformers accelerate bitsandbytes sentencepiece "
   "protobuf imageio imageio-ffmpeg")

import numpy as np  # noqa: E402
import torch  # noqa: E402

CAP = torch.cuda.get_device_capability()
DT = torch.bfloat16 if CAP[0] >= 8 else torch.float16  # T4/P100 have no fast bf16
log(f"GPU capability {CAP}, dtype {DT}")
W, H = 768, 1344  # 9:16-ish, multiple of 16


def free(*objs):
    for o in objs:
        del o
    gc.collect()
    torch.cuda.empty_cache()


def is_blank(img):
    a = np.asarray(img)
    return a.max() < 8 or a.std() < 2


def flux_pipe():
    from diffusers import BitsAndBytesConfig as DiffusersBnb
    from diffusers import FluxPipeline, FluxTransformer2DModel
    from transformers import BitsAndBytesConfig as TransformersBnb
    from transformers import T5EncoderModel

    mid = "black-forest-labs/FLUX.1-schnell"
    nf4 = dict(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=DT)
    transformer = FluxTransformer2DModel.from_pretrained(
        mid, subfolder="transformer", quantization_config=DiffusersBnb(**nf4), torch_dtype=DT)
    text_encoder_2 = T5EncoderModel.from_pretrained(
        mid, subfolder="text_encoder_2", quantization_config=TransformersBnb(**nf4), torch_dtype=DT)
    pipe = FluxPipeline.from_pretrained(
        mid, transformer=transformer, text_encoder_2=text_encoder_2, torch_dtype=DT)
    pipe.enable_model_cpu_offload()
    pipe.set_progress_bar_config(disable=True)
    return lambda prompt, seed: pipe(
        prompt, width=W, height=H, num_inference_steps=4, guidance_scale=0.0,
        max_sequence_length=256, generator=torch.Generator("cpu").manual_seed(seed),
    ).images[0]


def sdxl_pipe():
    from diffusers import AutoencoderKL, StableDiffusionXLPipeline

    vae = AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", vae=vae, torch_dtype=torch.float16,
        variant="fp16", use_safetensors=True).to("cuda")
    pipe.set_progress_bar_config(disable=True)
    neg = "text, title, watermark, signature, blurry, deformed, duplicate, asymmetrical, lowres"
    return lambda prompt, seed: pipe(
        prompt, negative_prompt=neg, width=W, height=H, num_inference_steps=30,
        guidance_scale=6.0, generator=torch.Generator("cpu").manual_seed(seed),
    ).images[0]


def make_images(items):
    report = {}
    try:
        gen, model = flux_pipe(), "flux-schnell"
        test = gen(items[0]["prompt"], items[0]["seed"])
        if is_blank(test):
            raise RuntimeError("FLUX produced a blank image")
    except Exception:
        traceback.print_exc()
        log("FLUX failed, falling back to SDXL")
        gc.collect()
        torch.cuda.empty_cache()
        gen, model, test = sdxl_pipe(), "sdxl", None
    report["image_model"] = model
    for i, item in enumerate(items):
        t = time.time()
        img = test if (i == 0 and test is not None) else gen(item["prompt"], item["seed"])
        path = f"{OUT}/image_{i + 1}.png"
        img.save(path)
        item["image"] = os.path.basename(path)
        log(f"image {i + 1}/{len(items)} done in {time.time() - t:.0f}s ({model})")
    free(gen)
    return report


def make_videos(items, negative):
    from diffusers import LTXImageToVideoPipeline
    from diffusers.utils import export_to_video
    from PIL import Image

    pipe = LTXImageToVideoPipeline.from_pretrained("Lightricks/LTX-Video", torch_dtype=DT)
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_tiling()
    pipe.set_progress_bar_config(disable=True)
    vw, vh = 480, 832  # divisible by 32; upscaled to 1080x1920 later
    for i, item in enumerate(items):
        if not item["video"]:
            continue
        t = time.time()
        image = Image.open(f"{OUT}/{item['image']}").convert("RGB").resize((vw, vh), Image.LANCZOS)
        frames = pipe(
            image=image, prompt=item["motion"], negative_prompt=negative,
            width=vw, height=vh, num_frames=97, num_inference_steps=40,
            generator=torch.Generator("cpu").manual_seed(item["seed"]),
        ).frames[0]
        path = f"{OUT}/clip_{i + 1}.mp4"
        export_to_video(frames, path, fps=24)
        item["clip"] = os.path.basename(path)
        log(f"clip {i + 1} done in {time.time() - t:.0f}s")
    free(pipe)


def main():
    items = JOB["items"]
    report = {"gpu": torch.cuda.get_device_name(0)}
    t0 = time.time()
    report.update(make_images(items))
    try:
        make_videos(items, JOB["negative_video"])
    except Exception:
        traceback.print_exc()
        report["video_error"] = traceback.format_exc()[-2000:]
    report["minutes"] = round((time.time() - t0) / 60, 1)
    with open(f"{OUT}/result.json", "w") as f:
        json.dump({**JOB, "report": report}, f, indent=2)
    log(f"finished: {report}")


main()
