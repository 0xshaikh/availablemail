# PUBLISH.md — deploy availablemail as a live web app

The repo ships two ways to serve a live demo:

1. **GitHub Pages (static, no server)** — the default, already published.
   Push to `main` and it's live at
   <https://0xshaikh.github.io/availablemail/demo/>. The demo is a pure
   client-side JavaScript port of the Python generator. Zero dependencies,
   zero API keys, works offline once loaded.

2. **Flask backend (server-side)** — for users who want to call the actual
   Python package over HTTP. Deploy anywhere that runs Python 3.10+.

---

## Deploy to Render.com (recommended, free)

[Render.com free tier](https://render.com/pricing): 750 hours/month, 512MB
RAM, 0.5GB disk, no credit card.

1. Push this repo to GitHub (already there).
2. Go to <https://dashboard.render.com> and sign in with GitHub.
3. Click **New** → **Blueprint**.
4. Pick the `0xshaikh/availablemail` repo. Render reads `deploy/render.yaml`
   automatically.
5. Click **Create**. The first deploy takes ~2 minutes.

When done, your app is live at `https://<name>.onrender.com`. Health check:
`https://<name>.onrender.com/health`.

## Deploy to Fly.io (free, shared VM)

[Fly.io free tier](https://fly.io/docs/about/pricing/): shared-cpu-1x256mb,
512MB RAM, 25GB I/O.

```bash
# Install flyctl: https://fly.io/docs/hands-on/installing-flyctl/
fly auth login
cd /path/to/availablemail
fly launch --config deploy/fly.toml --no-deploy
fly deploy
fly open
```

## Deploy to PythonAnywhere (free)

1. <https://www.pythonanywhere.com> — free tier has 1 web app.
2. Create a new **Files** tab, upload the repo, or use the built-in Git
   integration.
3. Open a **Bash** console and:
   ```bash
   pip install --user availablemail gunicorn
   ```
4. Open the **Web** tab → **Add a new web app** → **Flask** → pick the
   directory that contains `webapp/app.py`.
5. Add a URL route `* -> webapp.app:app`.
6. Click **Reload**.

## Deploy to your own VPS (any Linux box with a public IP)

```bash
cd /path/to/availablemail
python3 -m venv .venv
. .venv/bin/activate
pip install -e . -r webapp/requirements.txt
gunicorn webapp.app:app -b 0.0.0.0:5000 -w 2 --timeout 60
```

Put a reverse proxy (nginx, Caddy, Traefik) in front of it for HTTPS.

## Local (one-shot, no deploy)

```bash
bash deploy/local.sh
```

Creates a venv, installs deps, starts Flask on port 5000, and (if
`cloudflared` is installed) prints a public temporary URL you can share.

## API

`POST /api/search` — accepts JSON:

```json
{
  "first_name": "Anas",
  "last_name": "Shaikh",
  "provider": "gmail.com",
  "limit": 20,
  "suffixes": ["dev", "hello", "founder"],
  "max_digits": 3,
  "check": "heuristic"
}
```

Returns ranked candidates with score, pattern, and heuristic availability
tag. `check: "microsoft"` does real availability lookups against
Microsoft's signup API for Outlook/Hotmail/Live.

## Static demo (already live)

The static demo at <https://0xshaikh.github.io/availablemail/demo/> is the
**same code** as the Python generator, translated to client-side JS. It runs
entirely in the visitor's browser — no server cost, no rate limits. Edit
`docs/demo/index.html` and push to `main` to update it.
