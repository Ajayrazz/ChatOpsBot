import os
import hmac
import hashlib
import time
import jwt
import httpx
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI()

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH", "private-key.pem")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Support private key as env var (for Fly.io / cloud) or file (for local dev)
GITHUB_PRIVATE_KEY = os.getenv("GITHUB_PRIVATE_KEY")


def _get_private_key() -> str:
    """Load the GitHub App private key from env var or file."""
    if GITHUB_PRIVATE_KEY:
        # In production (Fly.io), the key is passed as an env var
        # Replace literal \n with actual newlines (common when pasting PEM into env vars)
        return GITHUB_PRIVATE_KEY.replace("\\n", "\n")
    # Fallback: read from file (local dev)
    with open(PRIVATE_KEY_PATH, "r") as f:
        return f.read()


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    if not GITHUB_WEBHOOK_SECRET:
        return True
    
    hash_object = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    return hmac.compare_digest(expected_signature, signature_header)

def get_jwt():
    private_key = _get_private_key()
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + (10 * 60),
        "iss": GITHUB_APP_ID
    }
    return jwt.encode(payload, private_key, algorithm="RS256")

async def get_installation_token(installation_id: int):
    jwt_token = get_jwt()
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github.v3+json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers)
        resp.raise_for_status()
        return resp.json()["token"]

async def post_github_comment(repo_full_name, pr_number, text, installation_id):
    token = await get_installation_token(installation_id)
    url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json={"body": text})
        resp.raise_for_status()

async def process_chatops(comment_body, repo_full_name, pr_number, installation_id):
    if not GEMINI_API_KEY:
        await post_github_comment(repo_full_name, pr_number, "❌ Error: GEMINI_API_KEY is missing in the .env file!", installation_id)
        return
        
    try:
        # 1. Ask Gemini to generate an answer
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
A developer asked this question in a GitHub Pull Request: 
'{comment_body}'

Reply as a highly detailed, expert AI security mentor and code reviewer.
Your response MUST be extremely organized. Use Markdown formatting, including:
- 📝 Clear headers
- 💡 Bullet points for readability
- 💻 Code blocks/snippets with syntax highlighting if relevant
- 🛡️ Security best practices if applicable

Provide a comprehensive, deep-dive explanation.
"""
        
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # 2. Reply back to GitHub
        reply = f"🤖 **AI Security Mentor:**\n\n{response.text}"
        await post_github_comment(repo_full_name, pr_number, reply, installation_id)
        print(f"✅ Successfully replied to PR #{pr_number}")
        
    except Exception as e:
        print(f"❌ Error processing ChatOps: {e}")

@app.post("/webhook")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_body = await request.body()
    signature_header = request.headers.get("X-Hub-Signature-256", "")
    
    if not verify_signature(payload_body, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_type = request.headers.get("X-GitHub-Event")

    if event_type == "issue_comment":
        action = payload.get("action")
        if action == "created":
            comment_body = payload["comment"]["body"]
            sender_login = payload["sender"]["login"]
            pr_number = payload["issue"]["number"]
            repo_full_name = payload["repository"]["full_name"]
            installation_id = payload["installation"]["id"]
            
            # Check if someone mentioned our bot (case-insensitive and handles accidental spaces)
            body_lower = comment_body.lower()
            if ("@coderevieweranddebugger" in body_lower or "@ coderevieweranddebugger" in body_lower) and "[bot]" not in sender_login.lower():
                print(f"🚨 Bot mentioned by {sender_login}! Triggering ChatOps logic...")
                
                # Run the LLM processing in the background so we can instantly return 200 OK to GitHub
                background_tasks.add_task(
                    process_chatops, 
                    comment_body, 
                    repo_full_name, 
                    pr_number, 
                    installation_id
                )
                
            return {"status": "comment_processed"}

    return {"status": "ignored"}


@app.get("/")
async def health():
    """Health check endpoint — Fly.io uses this to verify the app is alive."""
    return {"status": "ok", "app": "ChatOps Security Mentor"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
