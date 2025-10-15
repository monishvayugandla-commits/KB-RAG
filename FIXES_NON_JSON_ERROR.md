# 🔍 Non-JSON Response Error - Fixed & Diagnosis Guide

## ✅ What Was Fixed

### Issue
You were seeing: **"Error: Server returned non-JSON response. Check console for details."**

### Root Cause Analysis
The frontend was **too strict** in validating the content-type header. If the server didn't send `Content-Type: application/json`, it would reject the response without even trying to parse it.

### Solution Applied
✅ **More Defensive Error Handling:**
1. Frontend now **attempts JSON parsing regardless** of content-type header
2. Backend **explicitly sets** `media_type="application/json"` on all error responses
3. Better error messages that distinguish between HTML errors and other types
4. Full response logging in console for debugging

---

## 🧪 After Deployment

### Wait for Render to Deploy (2-3 minutes)
Watch: https://dashboard.render.com/web/srv-d3n7tchr0fns73fdf40g/deploys

### Force Refresh Your Browser
- **Windows:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

This ensures you get the new JavaScript code (v3.1).

### Try Uploading Again

The error should now either:
1. ✅ **Work correctly** (upload succeeds)
2. 🔍 **Show the actual error** (not just "non-JSON response")

---

## 🔍 Diagnosing the Real Issue

### Check Browser Console (F12)

After uploading, look for these log messages:

```javascript
Upload response status: <number>
Upload response text (first 500 chars): <text>
Full response text: <full text>
Content-Type: <header>
```

### Common Scenarios:

#### Scenario 1: Server Returns HTML Error Page
**Console shows:**
```
Content-Type: text/html
Full response text: <!DOCTYPE html>...
```

**This means:** The server crashed before FastAPI handled the request

**Fix:** Check Render logs for Python errors

#### Scenario 2: Server Returns JSON Error
**Console shows:**
```
Content-Type: application/json
Full response text: {"error": "...", "details": "..."}
```

**This means:** FastAPI is working, but there's an application error

**Fix:** Look at the error message in the JSON

#### Scenario 3: Empty Response
**Console shows:**
```
Content-Type: (empty)
Full response text: (empty)
```

**This means:** Request timeout or server crashed

**Fix:** Check if service is running, check for memory issues

#### Scenario 4: 502 Bad Gateway
**Console shows:**
```
Upload response status: 502
Full response text: <html>Bad Gateway</html>
```

**This means:** Render's proxy can't reach your service

**Fix:** Service may be starting or crashed - check Render logs

---

## 🎯 What Should Happen Now

### If Everything Works:
```
Upload response status: 200
Content-Type: application/json
Full response text: {"ingested": 123, "time_seconds": 15.2, ...}
✅ Successfully ingested X chunks!
```

### If There's an Error (but now visible):
```
Upload response status: 500
Content-Type: application/json
Full response text: {"error": "ModuleNotFoundError: No module named 'xyz'", ...}
❌ Error: ModuleNotFoundError: No module named 'xyz'
```

At least now you'll see **what the actual error is** instead of a generic "non-JSON" message!

---

## 📝 Changes Made

### Frontend (static/js/app.js)
**Before:**
```javascript
// Check content type
if (!contentType || !contentType.includes('application/json')) {
    console.error('Server returned non-JSON response:', responseText);
    statusDiv.innerHTML = '❌ Error: Server returned non-JSON response.';
    return;
}

// Try to parse JSON
let result = JSON.parse(responseText);
```

**After:**
```javascript
// Check content type (for logging only)
const contentType = response.headers.get('content-type');
console.log('Content-Type:', contentType);

// Try to parse as JSON regardless of content-type
try {
    result = JSON.parse(responseText);
} catch (parseError) {
    // Show helpful error based on response type
    if (responseText.includes('<!DOCTYPE') || responseText.includes('<html')) {
        statusDiv.innerHTML = '❌ Server returned HTML. Service may be crashed.';
    } else {
        statusDiv.innerHTML = `❌ Error: ${responseText.substring(0, 200)}`;
    }
}
```

### Backend (app/main.py)
**Before:**
```python
return JSONResponse(
    status_code=500,
    content={"error": error_msg}
)
```

**After:**
```python
return JSONResponse(
    status_code=500,
    content={"error": error_msg},
    media_type="application/json"  # Explicitly set
)
```

---

## 🚀 Next Steps

### 1. Wait for Deployment (2-3 min)

### 2. Force Refresh Browser
`Ctrl + Shift + R` or `Cmd + Shift + R`

### 3. Open Browser Console (F12)

### 4. Try Uploading Again

### 5. Check Console Logs
- Look for "Upload response status"
- Look for "Full response text"
- Share these if still having issues

---

## 💡 Why This Fix Helps

### Before:
- ❌ Generic error message
- ❌ No visibility into actual problem
- ❌ Hard to debug

### After:
- ✅ Tries to parse JSON anyway (more flexible)
- ✅ Shows actual error text if JSON fails
- ✅ Distinguishes between HTML errors and other types
- ✅ Full logging for debugging

---

## 📞 If Still Not Working

### Share These from Browser Console:
1. `Upload response status: <number>`
2. `Full response text: <text>`
3. `Content-Type: <header>`

### Also Share from Render Logs:
1. Last 20 lines after "Your service is live"
2. Any error messages or stack traces

With this information, we can diagnose the actual problem!

---

**Deployment Status:** 🔄 Deploying now  
**Expected Time:** 2-3 minutes  
**Action Required:** Force-refresh browser after deployment completes  

**Result:** You'll either see upload succeed, OR see the actual error message (which we can then fix)! 🎯
