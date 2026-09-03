# Changelog

All notable changes to **APK_Build-Patch** (RPDevs APK Vault & CI/CD Engine) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-09-03 (Initial Production Release)

### Added
- **⚡ Dual-Engine CI/CD Framework**:
  - **ReVanced & Morphe Patch Engine**: Automated downloading, split APK merging (`.apkm`, `.xapk`, `.apks`), patch bundle compatibility (`.mpp`, `.jar`), architecture filtering (`arm64-v8a`, `arm-v7a`, `universal`), custom keystore signing, and Magisk/KernelSU root module packaging.
  - **Open-Source Repository Builder**: Clones open-source repositories (e.g. NewPipe, Seal, Mihon, RPDev-Launcher), executes Gradle/Flutter/React Native builds, and packages release APKs.
- **🌐 Cloudflare-Resilient Multi-Source Fetcher**:
  - Integrated Electronic Frontier Foundation's `apkeep` engine to pull clean APKs directly from Google Play Store, bypassing Cloudflare bot-blocks on mirror sites.
  - Multi-tier fallback architecture: Play Store ➔ APKMirror ➔ Uptodown ➔ Archive.org ➔ Direct HTTP Downloads.
- **🎯 First Target Release: TikTok Morphe**:
  - Configured `[TikTok-Morphe]` target for `com.zhiliaoapp.musically` v46.2.3 (arm64-v8a).
  - Integrated `icysymmetra/tiktok-patches-for-morphe` bundle with full patch suite (ad removal, region unlock, media downloader, pure mode, playback speed controls).
- **📦 The Ultimate APK Storage & Multi-Channel Distribution Hub**:
  - **F-Droid Repository**: Automated generation of `index-v1.jar` and `index-v2.json` for F-Droid, Neo Store, and Droid-ify clients.
  - **Obtainium Feed**: Unified `obtainium-feed.json` for 1-tap app subscription and automatic background updates.
  - **Magisk / KernelSU OTA**: Generates module update metadata (`*-update.json`) for root managers.
  - **Modern Static Web Portal**: Responsive UI with dark-theme neon styling, live architecture filters, search bar, direct downloads, SHA-256 integrity badges, and mobile QR codes.
- **🤖 GitHub Actions Automation Pipelines**:
  - `.github/workflows/patch-pipeline.yml`: Continuous automated patch and build pipeline for ReVanced and Morphe applications.
  - `.github/workflows/repo-builder.yml`: Automated compilation and release pipeline for open-source Git repositories.
  - `.github/workflows/ci.yml`: Automated Python linting (ruff) and pytest test suite.
  - `.github/actions/setup-patcher-tools/`: Composite action pre-provisioning `apkeep`, `APKEditor.jar`, and Android SDK build-tools.
