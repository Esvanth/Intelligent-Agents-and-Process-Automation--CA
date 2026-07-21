# Deployment: GitHub + Streamlit Cloud

## 1. Push to GitHub

Verify `.env` is in `.gitignore` (already done). Then:

```powershell
git init
git branch -M main
git add .
git status                        # confirm .env is NOT staged
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/recruitment-automation.git
git push -u origin main
```

## 2. Deploy on Streamlit Cloud

1. https://share.streamlit.io -> New app
2. Repo: your fork; Branch: `main`; Main file path: `dashboard/app.py`
3. Deploy
4. Settings -> Secrets, paste:
```toml
GROQ_API_KEY = "gsk_your_real_key"
GROQ_MODEL = "llama-3.3-70b-versatile"
SCORER_MODE = "llm"
MAILBOX_MODE = "mock"
EMAIL_MODE = "mock"
```

## 3. Test

Open your `*.streamlit.app` URL. Click "Run screening pipeline" in the
sidebar. Six candidates should score in about 10 seconds.
