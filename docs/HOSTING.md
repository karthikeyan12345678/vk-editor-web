# Hosting VK Editor for free

> **Before the first deploy:** switch on Google sign-in with [GOOGLE-SIGNIN.md](GOOGLE-SIGNIN.md) (add your site address as an authorised origin). Without it the site offers guest mode only.

VK Editor (website version) is only static files: HTML, JavaScript, fonts, sounds and the in-browser video engine (about 50 MB the first time, then cached by the browser). Any static host works. The two easiest free ones are **GitHub Pages** and **Netlify**.

> You do not need any server, database, credit card or API key to host it. **Never** put an AI key into the repository or into a build setting: each visitor pastes their own key in the page, and it stays in their browser.

## 1. GitHub Pages

1. Push the project to GitHub (see below if you have not yet).
2. Repository → **Settings** → **Pages** → **Build and deployment** → **Source: GitHub Actions**.
3. Repository → **Actions** → **Deploy website to GitHub Pages** → it runs on every push to `main` (or press **Run workflow**).
4. When it is green, open `https://<your-name>.github.io/<repo>/`.

Push from your computer:

```bash
cd F:\VKEditor-source          # your project folder
git add -A
git commit -m "Web version"
git push origin main
```

Troubleshooting

| Problem | Fix |
| --- | --- |
| The workflow does not exist / Pages says "no site" | Do step 2 first (Source must be **GitHub Actions**, not "Deploy from a branch") |
| Workflow fails at "Build the website" | Open the log. Most often `npm install` could not reach the internet; press **Re-run jobs** |
| The page is blank | Open it with the full path ending in `/` (for example `.../offline-Local-AI-Video-Editor/`). A hard refresh (Ctrl + F5) clears an old cache |
| "Could not load part of the editor engine" | The `engine` folder is missing from the deploy. Run the workflow again and check that the step "Build the website" prints `engine ready` |
| Private repository | GitHub Pages on private repositories needs a paid plan. Make the repository public (the project contains no secrets) or use Netlify |

## 2. Netlify

### From GitHub (recommended)

1. [app.netlify.com](https://app.netlify.com) → **Add new site** → **Import an existing project** → **GitHub** → choose the repository.
2. The settings come from `netlify.toml` (nothing to type): base directory `frontend`, build command `npm install && npm run build:web`, publish directory `dist-web`.
3. **Deploy**. Later pushes redeploy automatically.
4. Optional: **Site configuration → Domain management** to rename the site or add your own domain.

### Drag and drop (no GitHub)

```bash
cd frontend
npm install
npm run build:web
```

Then drag the `frontend/dist-web` folder onto [app.netlify.com/drop](https://app.netlify.com/drop).

| Problem | Fix |
| --- | --- |
| Build fails with "node: command not found" or an old Node | The file `netlify.toml` asks for Node 22; do not override it in the Netlify UI |
| Blank page after drag and drop | You dropped the wrong folder. Drop `dist-web` itself (the folder that contains `index.html`) |
| `Failed to fetch` in the chat | The AI service blocked browser use or the key is wrong. Test the key on the **AI & free credits** page |

## 3. Other free hosts

Cloudflare Pages, Vercel, GitLab Pages and Codeberg Pages all work the same way: build command `cd frontend && npm install && npm run build:web`, output folder `frontend/dist-web`. The site uses only relative paths, so it also works in a sub-folder.

## 4. Try it on your own computer

```bash
cd frontend
npm install
npm run build:web
npm run preview:web      # http://localhost:4173
```

(`npm run dev` starts the older desktop interface, which needs the Python server.)

## 5. Updating the site

Change the code, `git push`. If you changed the Python engine (anything in `backend/ltxps/editor`), also run:

```bash
cd backend
python tools/build_web_data.py
```

and commit the changed files in `frontend/public/data` and `frontend/public/fonts`. The automatic tests fail if you forget.

## 6. What the site needs from the visitor

- A current Chrome, Edge or Firefox (WebAssembly is built in).
- About 50 MB of one-time download and a few hundred MB of free memory while exporting.
- Optional: a free AI key for the chat (see the main README).

## 7. Security notes

- The site makes no requests to your own servers. The only outside requests are the AI service the visitor chose and the files hosted with the site.
- Keys live in the visitor's browser local storage. Do not add API keys to GitHub secrets, `netlify.toml`, environment variables or the source.
- Turn on GitHub's **secret scanning** (Settings → Code security) as an extra safety net.
