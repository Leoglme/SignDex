<p align="center">
  <a href="#">
    <img src="web/public/signdex_logo.svg" alt="SignDex" width="160" />
  </a>
</p>

## SignDex

**SignDex** is a “home-made” app to manage **clients** (details + colors + images), apply that data to **email signature templates**, preview the result, and generate a **ComeUp deliverable** (ZIP) containing:

- a `HTML/` folder (HTML signatures ready for Gmail/Probador),
- a `PNG/` and `JPG/` folder (image exports),
- a `LISEZMOI-signatures.txt` at the root of the ZIP.

## Table of contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Run locally](#run-locally)
  - [API + DB](#api--db)
  - [Run the API (outside Docker)](#run-the-api-outside-docker)
  - [Web (Nuxt)](#web-nuxt)
  - [Desktop (Tauri)](#desktop-tauri)
- [Environment variables](#environment-variables)
- [CI/CD](#cicd)

## Architecture

| Dossier | Rôle |
|---|---|
| `web/` | Nuxt 4 + Nuxt UI + Tailwind + Tauri shell (desktop) |
| `api/` | FastAPI (Python) + MariaDB/MySQL, SQL migrations, seeders, Supabase uploads, ZIP generation |
| `.github/workflows/` | CI/CD (déploiement web, déploiement API, release desktop) |

## Prerequisites

- **Docker Desktop** (for MariaDB + API via compose)
- **Node.js** 22+ / **npm** 10+
- **Python** 3.12 (if you run the API outside Docker)
- For desktop: **Rust toolchain** (Tauri)

## Run locally

### API + DB

From `api/`:

```powershell
docker compose up -d --build
```

Endpoints:
- API: `http://localhost:8010`
- Health: `GET /health`

### Run the API (outside Docker)

From `api/`:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run_dev.py
```

### Web (Nuxt)

From `web/`:

```powershell
npm install
npm run dev
```

### Desktop (Tauri)

From `web/`:

```powershell
npm run tauri:dev
```

## Environment variables

### API (`api/.env`)

Copy `api/.env.example` to `api/.env`, then adjust:

- `DATABASE_URL`
- `SUPABASE_URL`, `SUPABASE_API_KEY`, `SUPABASE_STORAGE_BUCKET` (required to upload images)
- `CORS_ORIGINS`
- `SIGNDEX_SEED_IF_EMPTY` (`1` = si la table `clients` est vide, insère les clients initiaux ; `0` = ne jamais seed automatiquement)

### Web (`web/.env` optionnel)

### Web (`web/.env` optional)

- `NUXT_PUBLIC_API_BASE` (defaults to `http://localhost:8010` in dev)
- `NUXT_PUBLIC_SITE_URL` (production canonical URL)

## CI/CD

- **API**: `.github/workflows/deploy-api.yml`
  - deploys `api/` to a VPS (venv + systemd + nginx reload)
  - required secrets: `SSH_HOST`, `SSH_PORT`, `SSH_USERNAME`, `SSH_PRIVATE_KEY`, `DEPLOY_API_DIR`, `API_SYSTEMD_SERVICE`, `API_APP_PORT`, `DATABASE_URL`, `SUPABASE_*`, `CORS_ORIGINS` (optionnel : `SIGNDEX_SEED_IF_EMPTY`, défaut `1` si absent)
- **Web**: `.github/workflows/deploy-web.yml`
  - builds Nuxt (Nitro) then deploys `.output` to a VPS (PM2 + nginx)
  - required secrets: `SSH_*`, `DEPLOY_WEB_DIR`, `WEB_PM2_APP_NAME`, `WEB_APP_PORT`, `NUXT_PUBLIC_API_BASE`, `NUXT_PUBLIC_SITE_URL`
- **Desktop (Windows)**: `.github/workflows/desktop-release.yml`
  - builds the Windows Tauri app and publishes a GitHub Release `v0.1.<run_number>`

