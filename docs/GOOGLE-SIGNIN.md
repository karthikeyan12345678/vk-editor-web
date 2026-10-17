# Switch on "Sign in with Google" (10 minutes, free)

The website needs one public number from Google, the **OAuth client ID**. It is not a secret and is safe to publish. There is **no client secret** anywhere in this site.

Until you do this, the site shows guest mode only and a short hint on the start page.

## 1. Create the project

1. Open [console.cloud.google.com](https://console.cloud.google.com) and sign in with your Google account.
2. Top bar, project picker, **New project**. Name: `VK Editor`. Press **Create**.
3. Open **APIs and Services**, **Library**, search **Google Drive API**, press **Enable**. (It stores each person's project list and history in their private hidden app folder.)

## 2. Set up the consent screen

1. **APIs and Services**, **OAuth consent screen** (also called **Google Auth Platform**).
2. User type **External**. App name `VK Editor`, your email as support and developer contact.
3. **Data access** (scopes): add `openid`, `email`, `profile`, and `https://www.googleapis.com/auth/drive.appdata`. These are all non-sensitive, so no Google review is needed.
4. **Audience**: press **Publish app** so anyone with a Google account can sign in. While it says *Testing*, only the test users you list (up to 100) can.

## 3. Create the client ID

1. **Clients** (or **Credentials**), **Create client**, type **Web application**, name `VK Editor web`.
2. **Authorised JavaScript origins**: add every address the site is served from, with no path and no trailing slash:
   - `https://karthikeyan12345678.github.io` (GitHub Pages)
   - `https://your-site-name.netlify.app` (Netlify, if you use it)
   - `http://localhost:4173` (to try it on your own computer)
3. Leave **Authorised redirect URIs** empty. This site uses the popup token flow.
4. **Create**. Copy the **Client ID** (it ends with `.apps.googleusercontent.com`). Ignore any secret Google shows; the site never uses it.

## 4. Put the ID into the site

Edit `frontend/public/config.js`:

```js
window.VK_CONFIG = {
  googleClientId: "1234567890-abcdefg.apps.googleusercontent.com",
};
```

Commit and push. The site redeploys. Alternative for GitHub Actions or Netlify: set a build variable named `VITE_GOOGLE_CLIENT_ID` to the same value.

## Checks

| Problem | Fix |
| --- | --- |
| "Error 400: origin_mismatch" | The address in the browser bar is not in **Authorised JavaScript origins**. Add it exactly (https, no slash). Changes take a few minutes. |
| "Access blocked: app has not completed verification" | The app is still in *Testing*. Publish it, or add the person as a test user. |
| The pop-up is blocked | Allow pop-ups for the site. |
| Signed in but "not synced" | Drive API not enabled, or the `drive.appdata` scope was not added in step 2. |

Never put an API key, a Hugging Face token or a client **secret** into `config.js` or the repository.
