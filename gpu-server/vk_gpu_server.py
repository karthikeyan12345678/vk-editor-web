"""VK Editor: your own free GPU server (Kaggle or Google Colab).

It starts a small Gradio app on the notebook's GPU and prints a public link. Paste that link into
VK Editor on the web: Settings -> "My own GPU server". The website then sends Text to video,
Picture to video, Continue a clip and Start/End picture jobs here instead of to Hugging Face, so the
Hugging Face daily GPU limit no longer applies.

The endpoints and input names are the same ones the website already uses, so nothing else changes.
Nothing is stored: pictures and videos only live in this notebook session.

Engines (set VK_ENGINE):
  ltx   LTX-Video 0.9.5. Text, picture, and start+end picture to video. Fits a 16 GB GPU. Default.
  wan   Wan 2.2 TI2V 5B. Higher quality text/picture to video, slower. (Start+end still uses ltx.)
  stub  No AI model: makes a test pattern video. Only for checking that the connection works.
"""
from __future__ import annotations

import gc
import inspect
import math
import os
import random
import re
import subprocess
import sys
import tempfile
import threading
import time

ENGINE = os.environ.get("VK_ENGINE", "ltx").strip().lower()
PORT = int(os.environ.get("VK_PORT", "7860"))
FPS = 24
OUT = tempfile.mkdtemp(prefix="vk_out_")
LOCK = threading.Lock()

NEG_DEFAULT = "worst quality, inconsistent motion, blurry, jittery, distorted, low quality, watermark, text"


def log(*a):
    print("[VK GPU]", *a, flush=True)


# ---------------------------------------------------------------------------------------------- helpers
def snap32(n: float, lo: int = 256, hi: int = 1280) -> int:
    return int(max(lo, min(hi, round(n / 32) * 32)))


def frames_for(seconds: float, step: int, max_frames: int) -> int:
    """Number of frames: step*k + 1 (what the models need), at least 9, at most max_frames."""
    want = max(9, round(float(seconds) * FPS))
    k = max(1, round((want - 1) / step))
    return int(min(max_frames, step * k + 1))


def fit(width: int, height: int, frames: int, budget: int) -> tuple[int, int]:
    """Shrinks the picture size (keeping its shape) until width*height*frames fits the GPU's memory budget."""
    w, h = snap32(width), snap32(height)
    while w * h * frames > budget and (w > 256 and h > 256):
        w2, h2 = snap32(w * 0.92), snap32(h * 0.92)
        if (w2, h2) == (w, h):
            w2, h2 = snap32(w - 32), snap32(h - 32)
        w, h = w2, h2
    return w, h


def vram_gb() -> float:
    try:
        import torch
        return torch.cuda.get_device_properties(0).total_memory / 1024 ** 3 if torch.cuda.is_available() else 0.0
    except Exception:
        return 0.0


def to_pil_cover(img, w: int, h: int):
    """Any picture (path or PIL) -> RGB picture of exactly w x h (centre crop, like the website does)."""
    from PIL import Image
    if isinstance(img, str):
        img = Image.open(img)
    img = img.convert("RGB")
    k = max(w / img.width, h / img.height)
    nw, nh = max(w, round(img.width * k)), max(h, round(img.height * k))
    img = img.resize((nw, nh), Image.LANCZOS)
    l, t = (nw - w) // 2, (nh - h) // 2
    return img.crop((l, t, l + w, t + h))


def encode_mp4(frames, path: str, fps: int = FPS) -> str:
    """Frames (PIL or arrays) -> an H.264 yuv420p mp4 that every browser can play."""
    from diffusers.utils import export_to_video
    raw = path + ".raw.mp4"
    export_to_video(frames, raw, fps=fps)
    try:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], check=True)
        os.remove(raw)
        return path
    except Exception as e:  # ffmpeg missing: the raw file is still a video
        log("ffmpeg step skipped:", e)
        os.replace(raw, path)
        return path


def step_callback(progress, steps: int, label: str):
    """A diffusers callback that moves the progress bar the website shows."""
    def cb(pipe, i, t, kw):
        try:
            progress((i + 1) / max(1, steps), desc=f"{label}: step {i + 1} of {steps}")
        except Exception:
            pass
        return kw
    return cb


def accepted(fn, **kw):
    """Only pass the arguments this version of diffusers knows about."""
    names = set(inspect.signature(fn).parameters)
    return {k: v for k, v in kw.items() if k in names}


def default_budget(big_gpu: int, small_gpu: int) -> int:
    """width*height*frames the GPU can hold. A free 15 GB T4 gets a small budget on purpose (attention memory grows very fast)."""
    env = os.environ.get("VK_BUDGET")
    if env:
        return int(env)
    return big_gpu if vram_gb() >= 40 else small_gpu


def run_with_retry(make_call, width, height, frames, budget, tries=4):
    """Runs make_call(w, h); when the GPU runs out of memory it shrinks the picture and tries again instead of failing."""
    import torch
    last = None
    for attempt in range(tries):
        w, h = fit(width, height, frames, budget)
        try:
            return make_call(w, h)
        except torch.OutOfMemoryError as e:
            last = e
            log(f"GPU out of memory at {w}x{h}, {frames} frames: trying a smaller size ...")
            free_gpu()
            budget = int(budget * 0.55)
            if w <= 256 and h <= 256:
                break
    raise RuntimeError("The GPU is too small for this video. Try a shorter length or a smaller size.") from last


def free_gpu():
    gc.collect()
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass


# ---------------------------------------------------------------------------------------------- engines
class Stub:
    name = "stub"

    def run(self, *, prompt, negative, width, height, seconds, start=None, end=None, seed=0, quality="fast", progress=None, **_):
        path = os.path.join(OUT, f"stub-{int(time.time() * 1000)}.mp4")
        w, h = snap32(width, 64, 1280), snap32(height, 64, 1280)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate={FPS}:duration={max(1, seconds)}",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", path], check=True)
        if progress:
            progress(1.0, desc="stub")
        return path


class LTX:
    """LTX-Video 0.9.5 with the condition pipeline: text, first picture, or first + last picture."""
    name = "ltx"
    REPO = os.environ.get("VK_LTX_REPO", "Lightricks/LTX-Video-0.9.5")

    def __init__(self):
        self.pipe = None

    def load(self):
        if self.pipe is not None:
            return
        import torch
        from diffusers import LTXConditionPipeline
        log("Loading LTX-Video (first time: a few minutes) ...")
        pipe = LTXConditionPipeline.from_pretrained(self.REPO, torch_dtype=torch.bfloat16)
        if vram_gb() >= 40:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        pipe.vae.enable_tiling()
        self.pipe = pipe
        log("LTX-Video ready.")

    def unload(self):
        self.pipe = None
        free_gpu()

    def run(self, *, prompt, negative, width, height, seconds, start=None, end=None, seed=0, quality="fast", progress=None, **_):
        import torch
        from diffusers.pipelines.ltx.pipeline_ltx_condition import LTXVideoCondition
        self.load()
        big = vram_gb() >= 40
        budget = default_budget(130_000_000, 24_000_000)
        nf = frames_for(seconds, 8, 257 if big else 161)
        steps = 50 if quality == "good" else 30

        def call(w, h):
            conds = []
            if start is not None:
                conds.append(LTXVideoCondition(video=[to_pil_cover(start, w, h)], frame_index=0))
            if end is not None:
                conds.append(LTXVideoCondition(video=[to_pil_cover(end, w, h)], frame_index=nf - 1))
            gen = torch.Generator(device="cpu").manual_seed(int(seed))
            kw = accepted(self.pipe.__call__, conditions=conds or None, prompt=prompt, negative_prompt=negative or NEG_DEFAULT, width=w, height=h,
                          num_frames=nf, num_inference_steps=steps, generator=gen, decode_timestep=0.05, decode_noise_scale=0.025,
                          callback_on_step_end=step_callback(progress, steps, "Making it") if progress else None, output_type="pil")
            log(f"LTX {w}x{h}, {nf} frames, {steps} steps, start={start is not None}, end={end is not None}")
            return self.pipe(**kw).frames[0]

        frames = run_with_retry(call, width, height, nf, budget)
        free_gpu()
        return encode_mp4(frames, os.path.join(OUT, f"ltx-{int(time.time() * 1000)}.mp4"))


class Wan:
    """Wan 2.2 TI2V 5B: text to video and picture to video at higher quality (slower)."""
    name = "wan"
    REPO = os.environ.get("VK_WAN_REPO", "Wan-AI/Wan2.2-TI2V-5B-Diffusers")

    def __init__(self):
        self.t2v = None
        self.i2v = None

    def load(self):
        if self.t2v is not None:
            return
        import torch
        from diffusers import AutoencoderKLWan, WanPipeline
        log("Loading Wan 2.2 5B (first time: several minutes) ...")
        vae = AutoencoderKLWan.from_pretrained(self.REPO, subfolder="vae", torch_dtype=torch.float32)
        pipe = WanPipeline.from_pretrained(self.REPO, vae=vae, torch_dtype=torch.bfloat16)
        if vram_gb() >= 40:
            pipe.to("cuda")
        else:
            pipe.enable_model_cpu_offload()
        try:
            pipe.vae.enable_tiling()
        except Exception:
            pass
        self.t2v = pipe
        log("Wan ready.")

    def unload(self):
        self.t2v = self.i2v = None
        free_gpu()

    def run(self, *, prompt, negative, width, height, seconds, start=None, end=None, seed=0, quality="fast", progress=None, **_):
        import torch
        self.load()
        budget = default_budget(130_000_000, 20_000_000)
        nf = frames_for(seconds, 4, 121)
        steps = 40 if quality == "good" else 24
        pipe = self.t2v
        if start is not None:
            if self.i2v is None:
                from diffusers import WanImageToVideoPipeline
                self.i2v = WanImageToVideoPipeline.from_pipe(self.t2v)
            pipe = self.i2v

        def call(w, h):
            gen = torch.Generator(device="cpu").manual_seed(int(seed))
            extra = {"image": to_pil_cover(start, w, h)} if start is not None else {}
            kw = accepted(pipe.__call__, prompt=prompt, negative_prompt=negative or NEG_DEFAULT, height=h, width=w, num_frames=nf,
                          num_inference_steps=steps, guidance_scale=5.0, generator=gen, output_type="pil",
                          callback_on_step_end=step_callback(progress, steps, "Making it") if progress else None, **extra)
            log(f"Wan {w}x{h}, {nf} frames, {steps} steps, image={start is not None}")
            return pipe(**kw).frames[0]

        frames = run_with_retry(call, width, height, nf, budget)
        free_gpu()
        return encode_mp4(frames, os.path.join(OUT, f"wan-{int(time.time() * 1000)}.mp4"))
