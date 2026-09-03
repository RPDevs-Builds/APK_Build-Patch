# GitHub Actions CI/CD Workflows Reference

## 1. Workflows Catalog

| Workflow | File | Triggers | Description |
| :--- | :--- | :--- | :--- |
| **CI / Lint & Tests** | `ci.yml` | `push`, `pull_request`, `workflow_dispatch` | Validates Python syntax, runs Ruff linter, and executes Pytest test suite. |
| **Patch Pipeline** | `patch-pipeline.yml` | `schedule` (weekly), `workflow_dispatch` | Fetches base APKs, merges splits, executes ReVanced/Morphe patchers, creates releases, and updates storage. |
| **Repo Builder** | `build-repos.yml` | `workflow_dispatch` | Clones and builds open-source Android projects defined in `config/repos.toml`. |
| **Upstream Tracker** | `update-check.yml` | `schedule` (daily), `workflow_dispatch` | Tracks new patch/APK versions and triggers builds when updates are detected. |
| **Deploy Portal** | `deploy-portal.yml` | `workflow_dispatch` | Regenerates F-Droid repository and deploys static Web Portal to GitHub Pages. |
| **Release Pruner** | `release-pruner.yml` | `schedule` (monthly), `workflow_dispatch` | Enforces release retention policy (keeps recent N builds per app). |

---

## 2. Secrets & Variables Reference

Configure these in **GitHub Settings** -> **Secrets and variables** -> **Actions**:

- `GITHUB_TOKEN`: Provided automatically by GitHub Actions (requires `contents: write`, `pages: write`, `id-token: write`).
- `KEYSTORE_BASE64`: (Optional) Base64-encoded production `.keystore` or `.jks` file.
- `KEYSTORE_PASSWORD`: Keystore password.
- `KEY_ALIAS`: Key entry alias.
- `KEY_PASSWORD`: Key password.
- `TELEGRAM_BOT_TOKEN`: (Optional) Telegram bot token for release broadcast messages.
- `TELEGRAM_CHAT_ID`: (Optional) Telegram chat ID or channel @username.
- `DISCORD_WEBHOOK_URL`: (Optional) Discord Webhook URL for release notifications.
- `GPLAY_EMAIL`: (Optional) Google Play Store account email.
- `GPLAY_TOKEN`: (Optional) Google Play Store app password or token.
