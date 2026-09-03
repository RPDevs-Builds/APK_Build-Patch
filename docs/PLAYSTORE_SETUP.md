# Google Play Store Integration Setup

The RPDevs APK Engine supports fetching official, untouched base APKs directly from the Google Play Store via `gplaycli` or `apkeep`.

## Option 1: Anonymous / Aurora Token Dispenser (Default & Zero Setup)
The fetcher subsystem automatically uses anonymous device credentials and Aurora Token Dispenser APIs when available. No user configuration is required for downloading free target applications (e.g. YouTube, YouTube Music, Reddit, Twitter).

## Option 2: Configured Google Account Credentials
If downloading from regions requiring authenticated tokens or specific device profiles:

1. Create an App Password for your Google account at [Google Account Security](https://myaccount.google.com/apppasswords).
2. Set the following environment variables (locally or in GitHub Repository Secrets):
   - `GPLAY_EMAIL`: Your Google account email.
   - `GPLAY_TOKEN`: Your 16-character Google App Password or auth token.
3. Configure `device_codename` in `config/sources.toml`:
   ```toml
   [playstore]
   backend = "auto"
   device_codename = "bramble" # Pixel 4a (5G)
   ```

## CLI Verification
Verify local Google Play CLI capability:
```bash
gplaycli -d -p com.google.android.youtube
```
or via apkeep:
```bash
apkeep -a com.google.android.youtube temp/
```
