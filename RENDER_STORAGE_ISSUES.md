# Render Deployment Issues and Solutions

## Critical Issue: Ephemeral Filesystem ⚠️

### The Problem

**Render's free tier uses an EPHEMERAL filesystem**, meaning:

1. ✗ **Uploaded files are lost** when the service restarts
2. ✗ **Vector store is deleted** when the service spins down (after 15 min inactivity)
3. ✗ **All data resets** on every deployment
4. ✗ **Cold starts** take 10-30 seconds to download the embedding model

This is why your application works locally but fails on Render:
- **Local**: Files persist on your hard drive
- **Render**: Files exist only in temporary container storage

### What Happens

```
User uploads document → Saved to /uploads → Vector store created
       ↓
Service sleeps (15 min inactivity)
       ↓
Service wakes up → ALL FILES GONE → Queries fail!
```

### Current Workarounds

The code now includes:

1. **Storage Info Endpoint**: Visit `/storage-info` to see what files exist
2. **Better Error Messages**: Tells you when vector store is missing
3. **Lazy Loading**: Models load only when needed (faster startup)
4. **Timeouts**: Extended timeouts for long operations

### Symptoms You're Seeing

- ✗ Upload works, but queries fail after service restart
- ✗ "Vector store not found" errors
- ✗ Slow first upload (downloading 90MB model)
- ✗ 502 Gateway errors on cold starts
- ✗ Data disappears randomly

## Solutions

### Option 1: Accept Data Loss (Current - FREE)

**Pros**: Free, no setup needed
**Cons**: Users must re-upload documents after every sleep

Users need to:
1. Upload document
2. Use immediately (within 15 minutes)
3. Re-upload if service sleeps

### Option 2: Use Render Persistent Disks ($7/month)

Add persistent storage to your Render service:

```yaml
# render.yaml
services:
  - type: web
    name: kb-rag
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    disk:
      name: kb-rag-data
      mountPath: /opt/render/project/.data
      sizeGB: 1
```

Update environment variables:
- `PERSISTENT_DIR=/opt/render/project/.data`

**Cost**: $7/month for 1GB SSD

### Option 3: Use External Storage (RECOMMENDED for production)

Store files in cloud storage:

#### AWS S3
```python
# Install: pip install boto3
import boto3

s3 = boto3.client('s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

# Upload
s3.upload_file(local_path, 'your-bucket', key)

# Download
s3.download_file('your-bucket', key, local_path)
```

#### Google Cloud Storage
```python
# Install: pip install google-cloud-storage
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('your-bucket')
blob = bucket.blob(filename)
blob.upload_from_filename(local_path)
```

**Pros**: Truly persistent, scalable, reliable
**Cons**: Requires cloud account setup, costs for storage/requests

### Option 4: Upgrade to Render Paid Plan

Standard plan ($25/month) includes:
- Faster cold starts
- More memory
- Better performance

Still ephemeral filesystem unless you add persistent disk.

## Implementation Status

### ✅ Completed
- Lazy imports (fast startup)
- Storage info endpoint
- Better error messages
- Timeout handling
- Comprehensive logging

### ⏳ Requires Your Decision
- Choose storage solution (Options 1-4 above)
- Configure persistent storage (if Option 2/3)
- Set up cloud storage (if Option 3)

## Testing Your Deployment

### 1. Check Health
```bash
curl https://kb-rag-fbv7.onrender.com/health
```

Expected: `{"status":"healthy","message":"KB-RAG is running"}`

### 2. Check Storage Info
```bash
curl https://kb-rag-fbv7.onrender.com/storage-info
```

Shows:
- Vector store status
- Uploaded files
- Storage mode

### 3. Upload Document
```bash
curl -X POST https://kb-rag-fbv7.onrender.com/ingest \
  -F "file=@document.pdf"
```

Expected: `{"ingested": N, "source": "...", "time_seconds": X}`

### 4. Query (Must be within same session as upload)
```bash
curl -X POST https://kb-rag-fbv7.onrender.com/query \
  -F "question=Your question here"
```

Expected: `{"answer": "...", "sources": [...]}`

## Performance Expectations

### Current Performance
- **Cold start**: 10-30 seconds (downloading model)
- **First upload**: 15-25 seconds (initializing embeddings)
- **Subsequent uploads**: 8-15 seconds (cached embeddings)
- **Query**: 2-5 seconds

### With Persistent Disk
- **Cold start**: 2-3 seconds (model cached)
- **First upload**: 8-12 seconds (embeddings cached)
- **Subsequent uploads**: 5-10 seconds
- **Query**: 2-5 seconds

### With Pre-warmed Service
- Add a cron job to ping your service every 10 minutes
- Prevents cold starts
- Free with services like cron-job.org

## Logs to Check in Render

Look for these in your Render logs:

✓ **Success**:
```
✓ Storage initialized: {...}
✓ Embeddings model ready in 12.34s
✓ SUCCESS: Ingested 45 chunks in 18.23s
```

✗ **Problems**:
```
⚠ Storage initialization warning: ...
✗ ERROR in ingest_file: ...
Vector store not found
```

## Recommended Next Steps

1. **Immediate** (FREE):
   - Deploy current changes
   - Test upload + query in same session
   - Accept that data is temporary

2. **Short-term** ($7/month):
   - Add Render Persistent Disk
   - Configure `PERSISTENT_DIR` environment variable
   - Test persistence across restarts

3. **Production** (Variable cost):
   - Set up S3 or GCS bucket
   - Implement storage.py S3/GCS handlers
   - Deploy with cloud storage

## Cost Comparison

| Solution | Monthly Cost | Data Persistence | Setup Complexity |
|----------|-------------|------------------|------------------|
| Current (Ephemeral) | $0 | ✗ Lost on sleep | ✓ None |
| Render Disk | $7 | ✓ Persistent | ✓ Low |
| S3/GCS | ~$1-5 | ✓ Persistent | ⚠ Medium |
| Render Standard + Disk | $32 | ✓ Persistent | ✓ Low |

## Questions?

- **Why is my upload slow?**: First upload downloads 90MB model
- **Why do queries fail?**: Service slept and lost data
- **How to keep data?**: Add persistent disk or cloud storage
- **Why 502 errors?**: Cold start timeout (now fixed with lazy imports)

---

**Bottom Line**: Render's free tier is great for testing but **not suitable for production** without persistent storage. Choose a storage solution based on your needs and budget.
