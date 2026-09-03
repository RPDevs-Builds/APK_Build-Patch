# Ultimate APK Storage & Multi-Channel Distribution

## 1. Multi-Channel Overview
The RPDevs storage engine distributes applications across 4 complementary channels:

| Channel | Format / Endpoint | Client Compatibility | Target Devices |
| :--- | :--- | :--- | :--- |
| **F-Droid Repo** | `index-v1.jar` / `index-v2.json` | F-Droid, Neo Store, Droid-ify | All Android devices |
| **Obtainium Feed** | `obtainium-feed.json` | Obtainium | All Android devices |
| **Magisk OTA** | `<module-id>-update.json` | Magisk App, KernelSU, APatch | Rooted Android devices |
| **Web Portal** | `index.html` + QR Codes | Modern Web Browsers | Desktop & Mobile devices |
| **GitHub Releases** | Tagged release assets | `gh`, direct browser download | Automated CI & Users |

---

## 2. Adding F-Droid Repository
1. Open your preferred F-Droid client (F-Droid, Droid-ify, Neo Store).
2. Navigate to **Repositories** -> **Add New Repository**.
3. Enter your repository URL:
   ```
   https://rpdevs-builds.github.io/APK_Build-Patch/fdroid/repo
   ```
4. Refresh repository list. All built and patched applications will now appear with auto-update support!

---

## 3. Importing into Obtainium
1. Open Obtainium on Android.
2. Tap **Add App** -> **Import from URL / File**.
3. Select the exported `obtainium-feed.json` URL:
   ```
   https://rpdevs-builds.github.io/APK_Build-Patch/obtainium-feed.json
   ```
4. All apps are instantly added and tracked for new GitHub releases.

---

## 4. Root Modules (Magisk / KernelSU / APatch)
Root modules are automatically packaged into flashable `.zip` files containing the patched APK as `base.apk`, mount scripts (`service.sh`, `post-fs-data.sh`), and `module.prop` containing the OTA update URL pointing to `*-update.json`.
