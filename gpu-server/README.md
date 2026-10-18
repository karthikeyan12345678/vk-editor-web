# VK Editor: your own free GPU server

Removes the Hugging Face daily GPU limit for the website. A free **Kaggle** or **Google Colab** GPU runs the video
model; the website sends Text to video, Picture to video, Continue a clip and Start/End pictures to it.

- `vk_gpu_server.py`: the server (Gradio). Same endpoints and input names the website already uses
  (`/text_to_video`, `/image_to_video`, `/generate_video`).
- `make_notebook.py`: builds `frontend/public/gpu-server/VK_Editor_GPU_Server.ipynb` (the server is embedded in it).
  Run it again after you change `vk_gpu_server.py`.

## Use it
1. Download `VK_Editor_GPU_Server.ipynb` from the website (Guide → Your own free GPU).
2. Kaggle: *Create → Notebook → File → Import notebook*. Settings: Accelerator **GPU T4 x2**, Internet **On**
   (Kaggle asks you to verify your phone once). About 30 free GPU hours a week.
   Colab: upload the notebook, *Runtime → Change runtime type → T4 GPU*.
3. *Run all*. The first start downloads the model (about 5 to 15 minutes).
4. Copy the printed `https://…` link into the website: Settings → My own GPU server → Save.

## Engines (first cell of the notebook)
| Engine | Good for | Notes |
|---|---|---|
| `ltx` (default) | all four modes | LTX-Video 0.9.5, 24 fps, fits a 16 GB GPU |
| `wan` | text and picture to video | Wan 2.2 5B, sharper and more natural motion, several times slower; start+end pictures still use ltx |

The size and length are reduced automatically if the GPU would run out of memory. "Better" in the website maps to more
denoising steps (50 instead of 30 for ltx).

## Honest limits
- Free sessions end after some hours or when idle. Run the notebook again and paste the new link.
- A free T4 is slower than the Hugging Face GPUs: expect minutes per clip (more with `wan`).
- The notebook code was checked against the website's calls with a test mode (`VK_ENGINE=stub`), but the AI models
  themselves need a real GPU, so test one short clip first. If a library version changes, the error appears in the
  notebook output.
- Keep the link private. Your Hugging Face token is never sent to it.

## Check the connection without a GPU
```
pip install gradio
VK_ENGINE=stub VK_SHARE=0 python vk_gpu_server.py
```
It then returns a test-pattern video from the same endpoints.
