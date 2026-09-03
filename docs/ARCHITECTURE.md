# Architecture & System Design - RPDevs APK Vault & CI/CD Engine

## 1. System Overview
The **RPDevs APK Vault & CI/CD Engine** is an automated, enterprise-grade continuous integration and distribution framework for Android applications. It unifies:
1. **Automated ReVanced & Morphe Patching**: Downloads stock applications from multiple mirrors (APKMirror, Google Play Store, Uptodown, Archive.org), strips unneeded architectures, executes patchers, signs APKs with dedicated keystores, and packages root modules (Magisk, KernelSU, APatch).
2. **Open-Source Repository Builder**: Clones arbitrary Android source repositories (e.g. NewPipe, Seal, Mihon, RPDev-Launcher, RPDev-Feed), manages JDK/SDK environments, compiles release artifacts via Gradle, signs, and indexes them.
3. **Ultimate APK Storage & Multi-Channel Distribution Hub**:
   - **GitHub Releases**: Tagged nightly/weekly releases with rich changelogs.
   - **F-Droid Repository Index (`index-v1.jar` & `index-v2.json`)**: Allows seamless client subscription via F-Droid, Neo Store, or Droid-ify for background auto-updates.
   - **Obtainium App Feed (`obtainium-feed.json`)**: 1-click import into Obtainium.
   - **Magisk / KernelSU OTA Updates (`*-update.json`)**: In-root-manager automated updates.
   - **Modern Static Web Portal (`index.html`)**: Searchable, responsive web UI with architecture filters, direct downloads, SHA-256 hashes, and QR codes for instant mobile installation.

---

## 2. Subsystem Architecture

```
APK_Build-Patch/
├── config/             # Declarative configurations (patches, repos, sources, storage)
├── src/
│   ├── core/           # Configuration parsing, logging, subcommands, process execution
│   ├── fetchers/       # Multi-source APK downloaders (APKMirror, PlayStore, Uptodown, etc.)
│   ├── patchers/       # ReVanced/Morphe patcher, split merger, signer, Magisk packager
│   ├── builders/       # Android Gradle, Flutter, and React Native source builders
│   └── storage/        # F-Droid indexer, Web Portal, Obtainium feed, Magisk OTA, publisher
├── bin/                # Precompiled JAR utilities (apksigner, apkeditor, paccer, dexlib2)
├── modules/            # Magisk & KernelSU root module template
├── web/                # Static web portal assets & UI templates
├── docs/               # Technical manuals and configuration references
├── tests/              # Test suite
└── .github/workflows/  # Automated GitHub Actions pipelines
```

---

## 3. Data Flow & Execution Lifecycle

1. **Trigger Phase**:
   - Scheduled cron (`0 2 * * 0` weekly) or manual GitHub Actions dispatch (`workflow_dispatch`).
2. **Configuration & Fetch Phase**:
   - Load `patches.toml` and `repos.toml`.
   - Query patcher CLI (`list-patches` & `list-versions`) to determine the highest compatible version for target packages.
   - Fetch base APKs via prioritized downloaders (APKMirror -> Google Play -> Uptodown -> Archive).
3. **Patcher & Build Phase**:
   - Merge split APK bundles (`.apkm`/`.xapk`) into standalone APKs via `APKEditor.jar`.
   - Strip unneeded architectures to keep outputs lean.
   - Execute patch routine using ReVanced/Morphe CLI with custom keystore signing.
   - Compile open-source repositories via `./gradlew assembleRelease`.
   - Package Magisk/KernelSU root module zips.
4. **Metadata & Distribution Phase**:
   - Extract `aapt2` badging metadata (version code, minSdk, targetSdk, permissions, architectures, icon).
   - Generate F-Droid `index-v1.jar` and modern `index-v2.json`.
   - Generate `obtainium-feed.json`.
   - Generate static web catalog (`index.html` + QR codes).
   - Publish tagged GitHub Release and broadcast notifications.
