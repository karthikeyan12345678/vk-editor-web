"""Builds VK_Editor_GPU_Server.ipynb (the server script is embedded, so the notebook works on its own)."""
import json, pathlib
here = pathlib.Path(__file__).parent
server = (here / "vk_gpu_server.py").read_text()

def md(t): return {"cell_type": "markdown", "metadata": {}, "source": t.strip("\n").splitlines(True)}
def code(t): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": t.strip("\n").splitlines(True)}

cells = [
 md("""
# VK Editor: your own free GPU server

This notebook turns a **free Kaggle or Google Colab GPU** into your own video server for the VK Editor website.
There is **no Hugging Face daily limit** here. Text to video, Picture to video, Continue a clip and Start/End pictures run on this GPU.

**Steps**
1. **Turn on a GPU.** Kaggle: right side *Settings → Accelerator → GPU T4 x2* (and *Internet → On*). Colab: *Runtime → Change runtime type → T4 GPU*.
2. Press **Run all** (Kaggle: *Run → Run All*; Colab: *Runtime → Run all*).
3. Wait until the last cell prints **YOUR FREE GPU SERVER IS READY** and a link.
4. Copy that link into the website: *Settings → My own GPU server → Save*.

Keep this notebook open while you make videos. Free sessions stop after some hours: run it again and paste the new link.
Do not share the link: anyone who has it can use your GPU.
"""),
 md("## 1. Choose the engine"),
 code("""
# "ltx"  = LTX-Video 0.9.5 (default): good quality, faster, fits a free 16 GB GPU. Text, picture, and start+end picture to video.
# "wan"  = Wan 2.2 5B: sharper and more natural motion for text/picture to video, but much slower (start+end pictures still use ltx).
ENGINE = "ltx"
"""),
 md("## 2. Install (2 to 4 minutes the first time)"),
 code("""
!pip -q install -U "diffusers>=0.35" "transformers>=4.50" accelerate sentencepiece imageio imageio-ffmpeg gradio
!ffmpeg -version | head -1
import torch
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE - turn on a GPU in the notebook settings, then run again")
"""),
 md("## 3. The server file"),
 code("%%writefile vk_gpu_server.py\n" + server),
 md("## 4. Start it (the first start downloads the model: about 5 to 15 minutes)"),
 code("""
import os
os.environ["VK_ENGINE"] = ENGINE
!python vk_gpu_server.py
"""),
]
nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "accelerator": "GPU", "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
out = here.parent / "frontend" / "public" / "gpu-server"
out.mkdir(parents=True, exist_ok=True)
(out / "VK_Editor_GPU_Server.ipynb").write_text(json.dumps(nb, indent=1))
(out / "vk_gpu_server.py").write_text(server)
print("wrote", out)
