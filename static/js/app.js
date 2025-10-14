// Upload area drag and drop
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    fileInput.files = e.dataTransfer.files;
    uploadDocument();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        uploadArea.querySelector('h3').textContent = fileInput.files[0].name;
    }
});

async function uploadDocument() {
    const file = fileInput.files[0];
    const source = document.getElementById('sourceInput').value;
    const statusDiv = document.getElementById('uploadStatus');
    
    if (!file) {
        statusDiv.innerHTML = '<div class="status-message status-error">Please select a file</div>';
        return;
    }
    
    statusDiv.innerHTML = '<div class="loader"></div>';
    
    const formData = new FormData();
    formData.append('file', file);
    if (source) formData.append('source', source);
    
    try {
        const response = await fetch('/ingest', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusDiv.innerHTML = `<div class="status-message status-success">✅ Successfully ingested ${result.ingested} chunks!</div>`;
            fileInput.value = '';
            uploadArea.querySelector('h3').textContent = 'Drag & Drop or Click to Upload';
        } else {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${result.error}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${error.message}</div>`;
    }
}

async function queryDocuments() {
    const query = document.getElementById('queryInput').value;
    const k = document.getElementById('kInput').value;
    const statusDiv = document.getElementById('queryStatus');
    const resultsSection = document.getElementById('resultsSection');
    const answerBox = document.getElementById('answerBox');
    const sourcesBox = document.getElementById('sourcesBox');
    
    if (!query.trim()) {
        statusDiv.innerHTML = '<div class="status-message status-error">Please enter a question</div>';
        return;
    }
    
    statusDiv.innerHTML = '<div class="loader"></div>';
    resultsSection.style.display = 'none';
    
    const formData = new FormData();
    formData.append('question', query);
    formData.append('k', k);
    
    try {
        const response = await fetch('/query', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        console.log('Response status:', response.status);
        console.log('Response data:', result);
        
        if (response.ok) {
            // Check if result has the expected properties
            if (!result.answer) {
                console.error('Missing answer in response:', result);
                statusDiv.innerHTML = '<div class="status-message status-error">❌ Error: Invalid response format</div>';
                return;
            }
            
            statusDiv.innerHTML = '<div class="status-message status-success">✅ Answer generated!</div>';
            answerBox.innerHTML = `<h3>Answer:</h3><p style="line-height: 1.8; color: #e5e5e5;">${result.answer}</p>`;
            
            if (result.sources && result.sources.length > 0) {
                sourcesBox.innerHTML = result.sources.map(source => `
                    <div class="source-card">
                        <strong>Source:</strong> ${source.source}<br>
                        <strong>Chunk:</strong> ${source.chunk}
                    </div>
                `).join('');
            } else {
                sourcesBox.innerHTML = '<p>No sources found</p>';
            }
            
            resultsSection.style.display = 'block';
        } else {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${result.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        console.error('Query error:', error);
        statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${error.message}</div>`;
    }
}

// Allow Enter key for query
document.getElementById('queryInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        queryDocuments();
    }
});
