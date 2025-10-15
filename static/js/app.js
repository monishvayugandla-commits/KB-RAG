// Chat History Management
let chatHistory = [];

// Load history from localStorage on page load
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    
    // Start with sidebar closed
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.add('collapsed');
    }
});

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('collapsed');
}

function loadHistory() {
    const savedHistory = localStorage.getItem('kb-rag-history');
    if (savedHistory) {
        chatHistory = JSON.parse(savedHistory);
        renderHistory();
    }
}

function saveHistory() {
    localStorage.setItem('kb-rag-history', JSON.stringify(chatHistory));
}

function addToHistory(question, answer, sources) {
    const historyItem = {
        id: Date.now(),
        question: question,
        answer: answer,
        sources: sources || [],
        timestamp: new Date().toISOString()
    };
    
    chatHistory.unshift(historyItem); // Add to beginning
    
    // Keep only last 50 items
    if (chatHistory.length > 50) {
        chatHistory = chatHistory.slice(0, 50);
    }
    
    saveHistory();
    renderHistory();
}

function renderHistory() {
    const historyList = document.getElementById('historyList');
    
    if (chatHistory.length === 0) {
        historyList.innerHTML = `
            <div class="empty-history">
                <p>No chat history yet</p>
                <small>Your questions and answers will appear here</small>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = chatHistory.map(item => {
        const date = new Date(item.timestamp);
        const timeAgo = getTimeAgo(date);
        
        return `
            <div class="history-item" onclick="loadHistoryItem(${item.id})">
                <div class="history-item-question">❓ ${escapeHtml(item.question)}</div>
                <div class="history-item-answer">${escapeHtml(item.answer)}</div>
                <div class="history-item-time">${timeAgo}</div>
            </div>
        `;
    }).join('');
}

function loadHistoryItem(id) {
    const item = chatHistory.find(h => h.id === id);
    if (!item) return;
    
    // Populate query input
    document.getElementById('queryInput').value = item.question;
    
    // Show results
    const resultsSection = document.getElementById('resultsSection');
    const answerBox = document.getElementById('answerBox');
    const sourcesBox = document.getElementById('sourcesBox');
    
    answerBox.textContent = item.answer;
    
    if (item.sources && item.sources.length > 0) {
        sourcesBox.innerHTML = item.sources.map(source => 
            `<div class="source-item">
                <strong>${source.source || 'Unknown'}</strong>
                <p>${source.chunk || ''}</p>
            </div>`
        ).join('');
    } else {
        sourcesBox.innerHTML = '<p>No sources available</p>';
    }
    
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function clearHistory() {
    if (confirm('Are you sure you want to clear all chat history?')) {
        chatHistory = [];
        localStorage.removeItem('kb-rag-history');
        renderHistory();
    }
}

function getTimeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' min ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hrs ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
    
    statusDiv.innerHTML = '<div class="loader"></div><p style="color: #b3b3b3; margin-top: 10px;">⏳ Uploading... First upload may take 60-120 seconds (model download + processing)</p>';
    
    const formData = new FormData();
    formData.append('file', file);
    if (source) formData.append('source', source);
    
    try {
        // Create abort controller with 180 second timeout (for Render cold starts)
        // Cold start: model download (40-60s) + processing (20-40s) + overhead = 100-120s
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 180000); // 180 seconds (3 minutes)
        
        const response = await fetch('/ingest', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Read response as text first (defensive)
        const responseText = await response.text();
        console.log('Upload response status:', response.status);
        console.log('Upload response text (first 500 chars):', responseText.substring(0, 500));
        console.log('Full response text:', responseText); // Log full response for debugging
        
        // Check if we got a response
        if (!responseText) {
            throw new Error('Server returned empty response');
        }
        
        // Check content type
        const contentType = response.headers.get('content-type');
        console.log('Content-Type:', contentType);
        
        // Try to parse as JSON regardless of content-type (more defensive)
        let result;
        try {
            result = JSON.parse(responseText);
        } catch (parseError) {
            console.error('Failed to parse JSON:', parseError);
            console.error('Response text was:', responseText);
            
            // If it's HTML, show a more helpful error
            if (responseText.includes('<!DOCTYPE') || responseText.includes('<html')) {
                statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: Server returned HTML instead of JSON. The service may be restarting or crashed. Check Render logs.</div>`;
            } else {
                statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${responseText.substring(0, 200)}</div>`;
            }
            return;
        }
        
        // Check response status
        if (response.ok) {
            const timeInfo = result.time_seconds ? ` (${result.time_seconds}s)` : '';
            statusDiv.innerHTML = `<div class="status-message status-success">✅ Successfully ingested ${result.ingested} chunks!${timeInfo}</div>`;
            fileInput.value = '';
            uploadArea.querySelector('h3').textContent = 'Drag & Drop or Click to Upload';
        } else {
            const errorMsg = result.error || result.details || 'Upload failed';
            console.error('Server error:', result);
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${errorMsg}</div>`;
        }
    } catch (error) {
        console.error('Upload error:', error);
        if (error.name === 'AbortError') {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Upload timeout (>180s). Server may be experiencing issues. Please try again or check Render logs.</div>`;
        } else {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${error.message}</div>`;
        }
    }
}

async function queryDocuments() {
    const query = document.getElementById('queryInput').value;
    const statusDiv = document.getElementById('queryStatus');
    const resultsSection = document.getElementById('resultsSection');
    const answerBox = document.getElementById('answerBox');
    const sourcesBox = document.getElementById('sourcesBox');
    
    if (!query.trim()) {
        statusDiv.innerHTML = '<div class="status-message status-error">Please enter a question</div>';
        return;
    }
    
    statusDiv.innerHTML = '<div class="loader"></div><p style="color: #b3b3b3; margin-top: 10px;">⏳ Querying... (using all available context for best accuracy)</p>';
    resultsSection.style.display = 'none';
    
    const formData = new FormData();
    formData.append('question', query);
    // k parameter removed - system now automatically uses all chunks
    
    try {
        // 120 second timeout for queries (Gemini can be slow)
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000);
        
        const response = await fetch('/query', {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Server returned non-JSON response. The service may be restarting.');
        }
        
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
            
            // Add to history
            addToHistory(query, result.answer, result.sources);
        } else {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${result.error || 'Unknown error'}</div>`;
        }
    } catch (error) {
        console.error('Query error:', error);
        if (error.name === 'AbortError') {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Query timeout (>120s). Server may be busy or restarting.</div>`;
        } else {
            statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${error.message}</div>`;
        }
    }
}

// Allow Enter key for query
document.getElementById('queryInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        queryDocuments();
    }
});
