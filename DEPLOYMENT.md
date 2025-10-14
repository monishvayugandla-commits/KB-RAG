# 🚀 KB-RAG Deployment Guide

## 📋 Prerequisites

- Python 3.12.6
- Git installed
- GitHub account
- Render.com account (free tier available)

## 🎯 Quick Deployment to Render

### Step 1: Initialize Git Repository

```bash
# Initialize Git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit for KB-RAG deployment"

# Create main branch
git branch -M main
```

### Step 2: Push to GitHub

```bash
# Add your GitHub repository
git remote add origin https://github.com/yourusername/kb-rag.git

# Push to GitHub
git push -u origin main
```

### Step 3: Deploy to Render

1. Go to [Render.com](https://render.com) and sign in
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `kb-rag-app`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free

5. Add Environment Variables:
   - Key: `GOOGLE_API_KEY`
   - Value: Your Google API key

6. Click **"Create Web Service"**

### Step 4: Wait for Deployment

- Render will automatically build and deploy
- Takes 5-10 minutes for first deployment
- You'll get a URL like: `https://kb-rag-app.onrender.com`

## 🌐 Alternative: Deploy to Railway

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy to Railway

1. Go to [Railway.app](https://railway.app)
2. Click **"Start a New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway auto-detects Python
5. Add environment variable:
   - `GOOGLE_API_KEY`

6. Click **"Deploy"**

## 🔧 Environment Variables Required

Make sure to set these in your hosting platform:

```env
GOOGLE_API_KEY=your_google_api_key_here
```

## 📦 Files for Deployment

✅ **Procfile** - Tells Render/Railway how to start the app
✅ **requirements.txt** - Python dependencies with versions
✅ **runtime.txt** - Python version specification
✅ **.gitignore** - Files to exclude from Git

## 🧪 Test Locally Before Deploying

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000

# Test at http://localhost:8000
```

## 🐛 Troubleshooting

### Build Fails

- Check `requirements.txt` versions match your local
- Ensure Python version in `runtime.txt` matches

### App Crashes on Start

- Verify `GOOGLE_API_KEY` environment variable is set
- Check logs in Render/Railway dashboard

### Static Files Not Loading

- Ensure `static/` and `templates/` folders are committed to Git
- Check `.gitignore` isn't excluding them

## 📊 Post-Deployment

After deployment:
1. Visit your app URL
2. Upload a document
3. Ask questions
4. Share with others! 🎉

## 🔄 Update Deployment

When you make changes:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render/Railway will automatically redeploy!

## 💰 Cost

- **Render Free Tier:** Free, spins down after 15 minutes of inactivity
- **Railway Free Tier:** $5 credit/month, then pay as you go
- **Render Paid:** Starts at $7/month for always-on service

## 🎓 Additional Resources

- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
