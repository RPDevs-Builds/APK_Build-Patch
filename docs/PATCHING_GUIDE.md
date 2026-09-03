# ReVanced & Morphe Patching Guide

## 1. Supported Patch Engines
The engine supports interchangeable patcher implementations:
- **Official ReVanced**: `ReVanced/revanced-patches` with `ReVanced/revanced-cli`.
- **Morphe Ecosystem**: `MorpheApp/morphe-patches` with `MorpheApp/morphe-cli`.
- **ReVanced Extended (anddea / inotia00)**: `anddea/revanced-patches` with `MorpheApp/morphe-cli` or `revanced-cli`.
- **Custom Patches**: Any custom patch bundle conforming to ReVanced/Morphe CLI formats (e.g. `tiktok-patches-for-morphe`).

## 2. MicroG / GmsCore Non-Root Requirements
Non-root YouTube and YouTube Music builds require microG support:
- [ReVanced GmsCore](https://github.com/ReVanced/GmsCore/releases/latest)
- [Morphe MicroG-RE](https://github.com/MorpheApp/MicroG-RE/releases/latest)

The engine automatically handles microG patch injection for non-root APKs and excludes it when building Magisk root modules.

## 3. Split APK Bundle Merging
Many upstream APK sources (such as APKMirror and Google Play) distribute apps as split APK bundles (`.apkm`, `.apks`, `.xapk`). The engine automatically uses `APKEditor.jar` to decompress, merge splits, clean metadata, and align them into a single installable APK signed with the configured signing key before passing it to the patcher.
