# Configuration Guide - Adding Apps & Repositories

## 1. Patched Applications (`config/patches.toml`)

To add a new target app to be patched by ReVanced or Morphe, append a new section to `config/patches.toml`:

```toml
[AppName]
enabled = true
app_name = "Twitter"
pkg_name = "com.twitter.android"
version = "auto"                         # "auto", "latest", or explicit "10.34.0"
arch = "all"                             # "arm64-v8a", "arm-v7a", "both", or "all"
build_mode = "apk"                       # "apk", "module", or "both"
patches_source = "ReVanced/revanced-patches"
cli_source = "ReVanced/revanced-cli"
rv_brand = "ReVanced"

# Downloader URLs
apkmirror_dlurl = "https://www.apkmirror.com/apk/x-corp/twitter"
uptodown_dlurl = "https://twitter.en.uptodown.com/android"
playstore_pkg = "com.twitter.android"

# Optional Patch Filters
included_patches = ["Hide ads", "Enable video download"]
excluded_patches = ["Custom branding"]
patcher_args = "-e 'Theme' -OdarkThemeBackgroundColor=@android:color/black"
```

---

## 2. Open-Source Repositories (`config/repos.toml`)

To add an open-source Android repository to build automatically from source:

```toml
[NewPipe]
enabled = true
repo_url = "https://github.com/TeamNewPipe/NewPipe"
branch = "dev"
build_system = "gradle"                  # "gradle", "flutter", or "react-native"
java_version = "21"                      # "17", "21", or "25"
gradle_task = "assembleRelease"
artifact_glob = "app/build/outputs/apk/release/*.apk"
category = "Media & Streaming"
description = "A libre lightweight streaming frontend for Android."
```

---

## 3. Storage & Distribution (`config/storage.toml`)

Configure repository distribution metadata:

```toml
[fdroid]
enabled = true
repo_name = "RPDevs APK Vault & Patcher"
repo_description = "Automated nightly builds for ReVanced and open-source Android tools."
repo_url = "https://rpdevs-builds.github.io/APK_Build-Patch/fdroid/repo"

[releases]
github_repository = "RPDevs-Builds/APK_Build-Patch"
keep_recent_releases_count = 10
```
