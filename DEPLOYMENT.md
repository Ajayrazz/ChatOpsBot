# 🚀 ChatOps Security Mentor — Deployment Guide

## Overview

This guide covers deploying the ChatOps bot as:
1. **GitHub App** (registered on GitHub)
2. **Fly.io** (production hosting)

---

## Part 1: GitHub App Setup

### Step 1 — Register a New GitHub App

1. Go to **[GitHub Settings → Developer Settings → GitHub Apps → New GitHub App](https://github.com/settings/apps/new)**
2. Fill in the required fields:

| Field | Value |
|---|---|
| **GitHub App name** | `CodeReviewerAndDebugger` (or any unique name) |
| **Homepage URL** | `https://chatops-security-mentor.fly.dev` (your Fly.io URL after deploy) |
| **Webhook URL** | `https://chatops-security-mentor.fly.dev/webhook` |
| **Webhook secret** | Generate one: run `python -c "import secrets; print(secrets.token_hex(32))"` |

### Step 2 — Set Permissions

Under **Repository permissions**:
| Permission | Access |
|---|---|
| **Issues** | Read & Write |
| **Pull requests** | Read & Write |
| **Metadata** | Read-only |

### Step 3 — Subscribe to Events

Check these boxes under **Subscribe to events**:
- ✅ **Issue comment**

### Step 4 — Generate Private Key

1. After creating the app, click **"Generate a private key"**
2. A `.pem` file will download — **keep this safe!**
3. Note your **App ID** (shown at the top of the app settings page)

### Step 5 — Install the App

1. Go to your App's page → **"Install App"** (left sidebar)
2. Choose the repositories where you want the bot active
3. Note the **Installation ID** from the URL (e.g., `https://github.com/settings/installations/12345678` → ID is `12345678`)

---

## Part 2: Deploy to Fly.io

### Step 1 — Login & Launch

```bash
cd ChatOpsBot

# Login to Fly.io (if not already)
fly auth login

# Launch the app (first time only)
fly launch --no-deploy
```

> **Note:** When prompted, accept the auto-detected `fly.toml` config. If it asks to rename the app (because `chatops-security-mentor` is taken), pick a unique name and update the webhook URL in your GitHub App settings accordingly.

### Step 2 — Set Secrets

Convert your `.pem` private key to a single-line string:

```bash
# On Linux/Mac:
cat private-key.pem | awk 'NF {sub(/\r/, ""); printf "%s\\n",$0;}'

# On Windows PowerShell:
(Get-Content private-key.pem -Raw) -replace "`r`n", "\n" -replace "`n", "\n"
```

Then set all secrets on Fly.io:

```bash
fly secrets set GITHUB_APP_ID="your_app_id_here"
fly secrets set GITHUB_WEBHOOK_SECRET="your_webhook_secret_here"
fly secrets set GEMINI_API_KEY="your_gemini_api_key_here"
fly secrets set GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIE...your_key_here...\n-----END RSA PRIVATE KEY-----"
```

> ⚠️ **Important:** The `GITHUB_PRIVATE_KEY` must be the entire PEM content on a **single line** with `\n` separating the lines.

### Step 3 — Deploy!

```bash
fly deploy
```

### Step 4 — Verify

```bash
# Check that the app is running
fly status

# View live logs
fly logs

# Test the health endpoint
curl https://chatops-security-mentor.fly.dev/
```

You should see: `{"status": "ok", "app": "ChatOps Security Mentor"}`

---

## Part 3: Update GitHub App Webhook URL

Go back to your GitHub App settings and update:
- **Webhook URL** → `https://<your-app-name>.fly.dev/webhook`

---

## Part 4: Test the Bot! 🎉

1. Open any PR in a repo where the app is installed
2. Post a comment:
   ```
   @CodeReviewerAndDebugger How do I prevent SQL injection in this code?
   ```
3. The bot should reply within a few seconds with a detailed, formatted response!

---

## Useful Fly.io Commands

| Command | Purpose |
|---|---|
| `fly deploy` | Deploy latest code |
| `fly logs` | View live logs |
| `fly status` | Check app status |
| `fly secrets list` | List configured secrets |
| `fly ssh console` | SSH into the running machine |
| `fly scale count 1` | Ensure 1 machine is always running |
| `fly apps destroy chatops-security-mentor` | Delete the app |

---

## Troubleshooting

### Bot isn't responding?
1. Check `fly logs` for errors
2. Verify the Webhook URL is correct in GitHub App settings
3. Go to GitHub App settings → **Advanced** → Check **Recent Deliveries** to see webhook payloads and responses

### 401 Invalid Signature?
- Ensure `GITHUB_WEBHOOK_SECRET` matches between Fly.io secrets and GitHub App settings

### Private key errors?
- Make sure the `GITHUB_PRIVATE_KEY` env var has proper `\n` line separators
- The key must start with `-----BEGIN RSA PRIVATE KEY-----` and end with `-----END RSA PRIVATE KEY-----`
