# 🔧 CRITICAL FIX: Environment Variables Setup

## 🚨 Current Error: 502 Bad Gateway

**Root Cause:** `GOOGLE_API_KEY` environment variable is NOT set in Render.

The app is live but cannot function without the API key.

---

## ✅ IMMEDIATE FIX (5 Minutes)

### Step 1: Go to Render Dashboard

1. Open: https://dashboard.render.com
2. Find your service: **KB-RAG**
3. Click on it

### Step 2: Add Environment Variable

1. Click on **"Environment"** tab (left sidebar)
2. Click **"Add Environment Variable"**
3. Add this:

```
Key:   GOOGLE_API_KEY
Value: AIzaSyCeRGwIg6V0_oYcaTeafSdbeBs3wwkk5f4
```

4. Click **"Save Changes"**

### Step 3: Redeploy

Render will automatically redeploy with the new environment variable.

**Wait 2-3 minutes** for deployment to complete.

---

## 🧪 After Setting the API Key

### Test 1: Health Check
```
https://kb-rag-fbv7.onrender.com/health
```
Should return: `{"status":"healthy"}`

### Test 2: Upload Document
1. Go to: https://kb-rag-fbv7.onrender.com/app
2. Upload a PDF
3. Should work in 20-40 seconds

### Test 3: Query
1. After upload, ask a question
2. Should get AI-generated answer

---

## 🔍 Why This Happened

**Locally:** Your `.env` file contains `GOOGLE_API_KEY`, so it works.

**On Render:** Environment variables in `.env` are NOT automatically deployed.

You must manually add them in Render's dashboard.

---

## 📋 Complete Environment Variables Checklist

Make sure these are set in Render:

✅ **Required:**
- `GOOGLE_API_KEY` = `AIzaSyCeRGwIg6V0_oYcaTeafSdbeBs3wwkk5f4`

⚠️ **Optional (already set by Render):**
- `PORT` = (auto-set by Render)
- `PYTHON_VERSION` = `3.12.6` (from runtime.txt)

---

## 🎯 What's Fixed in Latest Code

1. ✅ Better error messages when API key missing
2. ✅ Prevents crashes - shows helpful instructions
3. ✅ Upload still works even without API key
4. ✅ Query shows clear error if API key missing

---

## 💡 Expected Behavior After Fix

**Before (current):**
- ❌ 502 Bad Gateway
- ❌ App crashes on startup or query

**After (with API key):**
- ✅ Health check works
- ✅ Upload works (20-40s first time)
- ✅ Query works with AI answers
- ✅ No more crashes

---

## 🚀 Quick Visual Guide

### In Render Dashboard:

```
KB-RAG service
  └─ Environment tab
      └─ Environment Variables section
          └─ [Add Environment Variable] button
              ├─ Key: GOOGLE_API_KEY
              └─ Value: AIzaSyCeRGwIg6V0_oYcaTeafSdbeBs3wwkk5f4
```

---

## ⏱️ Timeline

1. **Now**: 502 error because API key missing
2. **Add API key** (2 minutes)
3. **Render redeploys** (2-3 minutes)
4. **Test again** - should work!

**Total time: ~5 minutes**

---

## 📞 Still Having Issues?

After adding the API key, if you still get errors:

1. Check Render logs for new error messages
2. The logs will now show EXACTLY what's wrong
3. Share the logs with me

---

## 🎉 Once Working

Your app will:
- ✅ Load in 2-3 seconds
- ✅ Accept document uploads
- ✅ Generate AI answers from documents
- ✅ Run 24/7 on Render free tier

**Just need to add that one environment variable!**
