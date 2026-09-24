# 🤖 ChatOps: Interactive Security Mentor

![GitHub App Status](https://img.shields.io/badge/GitHub_App-Active-success)
![Gemini AI](https://img.shields.io/badge/AI-Google_Gemini_2.5_Flash-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)

## 📖 Overview
The **ChatOps Security Mentor** is an intelligent, AI-driven GitHub application built to assist developers during the code review process. It acts as a real-time, interactive security expert living directly inside GitHub Pull Request threads. 

Instead of switching context to ask security or code-related questions, developers can simply tag the bot (`@CodeReviewerAndDebugger`) in a PR comment. The bot instantly intercepts the comment, analyzes the context using the **Google Gemini 2.5 Flash** LLM, and replies directly in the GitHub thread with a highly detailed, markdown-formatted explanation.

---

## ✨ Key Features
- **Real-Time Webhook Interception:** Uses FastAPI to instantly process incoming GitHub `issue_comment` webhooks.
- **Smart Mention Detection:** Silently ignores normal team chatter; only activates when explicitly summoned via `@CodeReviewerAndDebugger`.
- **Advanced AI Brain:** Powered by Google's Gemini LLM, tailored with a strict prompt to act as an expert security mentor (providing headers, bullet points, and code snippets).
- **Secure GitHub Authentication:** Generates dynamic, short-lived JWTs (JSON Web Tokens) using an encrypted `.pem` private key to authenticate securely with the GitHub REST API.
- **Asynchronous Processing:** Uses FastAPI `BackgroundTasks` to instantly acknowledge GitHub's webhook (preventing timeouts) while processing the AI generation and API response in the background.
- **Fail-Safe Security:** Configured with a strict `.gitignore` to prevent accidental exposure of API keys and private `.pem` files.

---

## 🛠️ Tech Stack
- **Backend:** Python 3, FastAPI, Uvicorn
- **AI / LLM:** Google Gemini API (`google-genai`)
- **Authentication:** PyJWT, Cryptography (for GitHub App tokens)
- **Networking:** HTTPX (Async HTTP Client), Ngrok (Local Webhook Tunneling)

---

## ⚙️ How it Works

> [!IMPORTANT]
> **Important Note:** In order to ask the LLM for anything, you MUST explicitly mention the bot by including the annotation `@CodeReviewerAndDebugger` in your comment. If you do not tag the bot, it will intentionally ignore the comment!

1. **Trigger:** A developer comments `@CodeReviewerAndDebugger how do I fix this SQL Injection vulnerability?` on a Pull Request.
2. **Listen:** GitHub fires a webhook to the FastAPI server.
3. **Verify & Process:** The server verifies the webhook signature and checks if the bot was mentioned.
4. **Think:** The prompt is sent to Google Gemini to formulate a highly structured, expert response.
5. **Reply:** The bot securely requests an Installation Access Token from GitHub and posts the AI's response directly back as a reply in the PR thread.

---

## 🚀 Local Installation & Setup (For Teammates)

If you are a developer looking to run this bot locally, follow these steps carefully:

### 1. Clone the Repository
```bash
git clone https://github.com/Ajayrazz/ChatOpsBot.git
cd ChatOpsBot
```

### 2. Set Up Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r ChatOpsBot/requirements.txt
```

### 3. Add Environment Variables
You will need the secret keys (which are NOT tracked in Git for security).
Create a `.env` file inside the `ChatOpsBot` folder:
```env
GITHUB_APP_ID=5058194
GITHUB_PRIVATE_KEY_PATH=private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Ask the project maintainer for the exact keys and the `private-key.pem` file, and place the `.pem` file inside the `ChatOpsBot` folder).*

### 4. Run the Server
```bash
cd ChatOpsBot
uvicorn main:app --reload
```
The server will start running at `http://localhost:8000`. 
*(Note: You will need to expose this port to the internet using a tool like `ngrok` so GitHub can send webhooks to it).*
