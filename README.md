# 🚀 RPDevs APK Vault & CI/CD Engine

<div align="center">

[![CI / Lint & Unit Tests](https://github.com/RPDevs-Builds/APK_Build-Patch/actions/workflows/ci.yml/badge.svg)](https://github.com/RPDevs-Builds/APK_Build-Patch/actions/workflows/ci.yml)
[![ReVanced & Morphe Patch Pipeline](https://github.com/RPDevs-Builds/APK_Build-Patch/actions/workflows/patch-pipeline.yml/badge.svg)](https://github.com/RPDevs-Builds/APK_Build-Patch/actions/workflows/patch-pipeline.yml)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)

**Universal Android CI/CD Pipeline, ReVanced & Morphe Patcher Engine, Open-Source Repo Builder, and Ultimate APK Storage Hub**

[Features](#-key-features) •
[Architecture](#-system-architecture) •
[Quick Start](#-quick-start) •
[Distribution Channels](#-distribution-channels) •
[Documentation](#-documentation)

</div>

---

## 🌟 Key Features

- **⚡ Dual-Engine CI/CD**:
  - **ReVanced & Morphe Patch Engine**: Automated downloading, split APK merging (`.apkm`/`.xapk`), patch compatibility resolution, architecture stripping (`arm64-v8a`, `arm-v7a`, `universal`), custom keystore signing, and Magisk/KernelSU/APatch root module creation.
  - **Open-Source Repo Builder**: Clones open-source Android projects (NewPipe, Seal, Mihon, RPDev-Launcher, etc.), compiles release APKs via Gradle/Flutter/React Native, signs, and packages artifacts.
- **🌐 Multi-Source Base APK Fetcher**:
  - **APKMirror Engine**: Scrapes and downloads APKs with architecture and DPI matching.
  - **Google Play Store Integration**: Direct APK retrieval via `gplaycli` / `apkeep`.
  - **Uptodown & Archive.org**: Fallback mirrors for older builds or rate limit resilience.
  - **Direct Downloads**: Pulls companion APKs (MicroG-RE, ReVanced GmsCore, Zygisk-Detach).
- **📦 The Ultimate APK Storage & Multi-Channel Distribution**:
  - **F-Droid Repository Index (`index-v1.jar` & `index-v2.json`)**: Direct subscription in F-Droid, Neo Store, or Droid-ify for background auto-updates.
  - **Obtainium App Feed (`obtainium-feed.json`)**: 1-click import into Obtainium.
  - **Magisk / KernelSU OTA Updates (`*-update.json`)**: In-root-manager automated updates.
  - **Modern Static Web Portal (`index.html`)**: Fast, searchable responsive web UI with architecture filters, direct downloads, SHA-256 hashes, and mobile QR codes.
  - **GitHub Releases & Webhook Alerts**: Automatic tagged releases + Discord/Telegram alerts.

---

## 🏗️ System Architecture

```
APK_Build-Patch/
├── .github/workflows/       # Automated GitHub Actions pipelines
├── .github/actions/         # Composite actions (setup-android-env, setup-patcher-tools)
├── config/                  # Declarative TOML configurations
│   ├── patches.toml         # Patched apps configuration (YouTube, YT Music, Reddit, TikTok, etc.)
│   ├── repos.toml           # Open-source repositories to compile
│   ├── sources.toml         # Downloader priorities & backend settings
│   └── storage.toml         # F-Droid, Web Portal, Obtainium, and retention settings
├── src/                     # Core Python orchestration framework
│   ├── cli.py               # Unified CLI tool (`python -m src.cli`)
│   ├── core/                # Config loader, logger, process runner, semver helpers
│   ├── fetchers/            # APKMirror, Google Play, Uptodown, Archive, Direct
│   ├── patchers/            # ReVanced & Morphe CLI patcher, split merger, signer, Magisk packager
│   ├── builders/            # Android Gradle, Flutter, React Native builders
│   └── storage/             # F-Droid generator, Web Portal, Obtainium feed, Magisk OTA
├── bin/                     # Precompiled JAR tools (apksigner, apkeditor, paccer, dexlib2)
├── modules/template/        # Flashable Magisk/KernelSU root module template
├── web/                     # Static Web Portal source & assets
├── docs/                    # Full technical documentation manuals
└── tests/                   # Pytest test suite
```

---

## 🚀 Quick Start

### 1. Local Environment Setup
```bash
# Clone the repository
git clone https://github.com/RPDevs-Builds/APK_Build-Patch.git
cd APK_Build-Patch

# Run automated setup
./scripts/setup_environment.sh
```

### 2. Run Patcher Locally
```bash
# Patch all enabled applications
python -m src.cli patch

# Patch a specific application
python -m src.cli patch --app YouTube
```

### 3. Build an Open-Source Repository Locally
```bash
# Build all configured repositories
python -m src.cli build

# Build a specific repository
python -m src.cli build --repo NewPipe
```

### 4. Generate Storage Hub (F-Droid Repo, Web Portal & Feeds)
```bash
python -m src.cli storage --tag latest
```

---

## 📱 Distribution Channels

### 1. F-Droid Repository
Add the repository URL to F-Droid, Neo Store, or Droid-ify:
```
https://rpdevs-builds.github.io/APK_Build-Patch/fdroid/repo
```

### 2. Obtainium App Feed
Import the feed URL in Obtainium:
```
https://rpdevs-builds.github.io/APK_Build-Patch/obtainium-feed.json
```

---

## 📚 Documentation

- [Architecture & System Design](docs/ARCHITECTURE.md)
- [Configuration Guide](docs/CONFIG_GUIDE.md)
- [Google Play Store Integration](docs/PLAYSTORE_SETUP.md)
- [ReVanced & Morphe Patching Details](docs/PATCHING_GUIDE.md)
- [Storage & Distribution Hub](docs/STORAGE_DISTRIBUTION.md)
- [CI/CD Workflows Reference](docs/CICD_WORKFLOWS.md)

---

## 📄 License
Licensed under the [GNU General Public License v3.0](LICENSE).
