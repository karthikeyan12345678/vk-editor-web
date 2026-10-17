<div align="center">

# 🎬 VK Editor — the website

### AI video, motion control, a video editor and an AI assistant, all in your browser. Free.

**Live site:** `https://karthikeyan12345678.github.io/vk-editor-web/`
**Run it on your own computer instead:** [offline-Local-AI-Video-Editor](https://github.com/karthikeyan12345678/offline-Local-AI-Video-Editor) (download page)

Made by [Karthikeyan V](https://karthikeyanv.netlify.app) · [LinkedIn](https://www.linkedin.com/in/karthikeyan-v-8a203a195) · [GitHub](https://github.com/karthikeyan12345678)

</div>

---

## What you can do on the website

Sign in with Google (or use guest mode), then:

| Page | What it does |
| --- | --- |
| **Home** | Your old projects, a **New project** button, and a history of everything you made |
| **Make video** | Text to video, picture to video, continue a clip (free Hugging Face GPU) |
| **Motion control** | A character picture copies the moves of a video (Pose Retarget or Character Swap) |
| **Editor** | Timeline, 51 looks, 34 effects, 59 transitions, 38 sounds, layers, green screen, keyframes, chat editing, MP4 / WebM / GIF export |
| **AI Assistant** | Chat, PDF / PowerPoint / Word / Excel / CSV files, resume check and tailoring, compare, analyse data, pictures |
| **Guide** | The full user guide, inside the site at `#/guide` |

## Is it really free?

Yes. The honest limits:

| Part | Free allowance |
| --- | --- |
| Editor and export | No limit (your computer does the work; export is slow, roughly 10 to 15 times the video length) |
| AI video and motion control | Hugging Face free GPU time (ZeroGPU): about 5 minutes a day with a free account token, about 2 without. Shared queues. A Space can be paused by its owner |
| Chat and Assistant writing | Your own free key (Groq, Gemini and others), each renews daily |
| Pictures | AI Horde (free, may queue) or a free Hugging Face token |

For no limits and no queue use the [desktop edition](https://github.com/karthikeyan12345678/offline-Local-AI-Video-Editor).

## 🔐 Keys and privacy (read this)

- Google sign-in uses only a **public client ID**. No client secret exists in this project.
- Chat keys and Hugging Face tokens are typed by each visitor and stay in **that visitor's browser**. They are not in this repository, the build, the README or any screenshot.
- Videos, pictures and sounds never leave the browser, except what you send on purpose to your chosen AI service or the Hugging Face Space.
- The Google Drive copy (project list and history) lives in a hidden app folder of the visitor's own Drive. Media files are never copied.
- Never commit `.env` files, keys or tokens. `.gitignore` already blocks the usual names.

## 🚀 Put your own copy online (about 15 minutes)

1. **Google sign-in:** follow [docs/GOOGLE-SIGNIN.md](docs/GOOGLE-SIGNIN.md) and paste your client ID into `frontend/public/config.js`.
2. **GitHub Pages:** repository **Settings, Pages, Source: GitHub Actions**. The workflow *Deploy website to GitHub Pages* runs on every push to `main`.
3. **Or Netlify:** import the repository; `netlify.toml` has all settings.
4. Add the final address to the Google client's **Authorised JavaScript origins**.

Details and fixes: [docs/HOSTING.md](docs/HOSTING.md).

## 🧪 Try it on your computer

```bash
cd frontend
npm install
npm run build:web
npm run preview:web      # open http://localhost:4173
```

Node 22 or newer. The first build copies the Python engine and fetches the editor wheels; it needs internet.

## 🛠 For developers

```
frontend/src/site/        landing page, Google sign-in gate, workspace, guide
frontend/src/web/         the in-browser "server" (Pyodide + ffmpeg.wasm, Hugging Face client)
assistant-ui/             the AI Assistant (own app, loaded in an iframe at /assistant/)
shared/web/               settings, Google account + Drive sync, history, chat streaming
backend/ltxps/            Python engine and assistant toolbox (run in the browser through Pyodide)
frontend/e2e/             browser tests with mocked Google / Hugging Face / AI services
```

| Task | Command |
| --- | --- |
| Build | `cd frontend && npm install && npm run build:web` |
| Browser tests | `cd frontend && npm run build:web && node e2e/site.e2e.mjs` (needs Playwright's Chromium) |
| Type-check | `cd frontend && npx tsc --noEmit` and `cd assistant-ui && npx tsc --noEmit` |
| Regenerate catalog / sounds / fonts | `cd backend && python tools/build_web_data.py` |

Third-party: fonts keep their own licences (`frontend/public/fonts`); Pyodide, ffmpeg.wasm (GPL-2.0-or-later core) and FFmpeg are open source under their own licences.

## ⚠️ Good to know

Personal project, free for everyone, no guarantee. Free AI services change their limits. AI can make mistakes, so check results before sharing.
