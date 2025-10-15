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
            <div class="history-item" onclick="loadHistoryItem(${item.id})" data-question="${escapeHtml(item.question).toLowerCase()}" data-answer="${escapeHtml(item.answer).toLowerCase()}">
                <div class="history-item-question">❓ ${escapeHtml(item.question)}</div>
                <div class="history-item-answer">${escapeHtml(item.answer)}</div>
                <div class="history-item-time">${timeAgo}</div>
            </div>
        `;
    }).join('');
}

function filterHistory() {
    const searchTerm = document.getElementById('historySearch').value.toLowerCase();
    const historyItems = document.querySelectorAll('.history-item');
    
    historyItems.forEach(item => {
        const question = item.getAttribute('data-question') || '';
        const answer = item.getAttribute('data-answer') || '';
        
        if (question.includes(searchTerm) || answer.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
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
let uploadedDocuments = []; // Track uploaded documents

// Load uploaded documents from localStorage
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('kb-rag-documents');
    if (saved) {
        uploadedDocuments = JSON.parse(saved);
        renderUploadedDocs();
    }
});

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
    uploadDocuments();
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        const count = fileInput.files.length;
        uploadArea.querySelector('h3').textContent = `${count} file${count > 1 ? 's' : ''} selected`;
    }
});

function renderUploadedDocs() {
    const docsSection = document.getElementById('uploadedDocs');
    const docsList = document.getElementById('docsList');
    
    if (uploadedDocuments.length === 0) {
        docsSection.style.display = 'none';
        return;
    }
    
    docsSection.style.display = 'block';
    docsList.innerHTML = uploadedDocuments.map(doc => `
        <div class="doc-item">
            <div class="doc-item-info">
                <div class="doc-item-name">📄 ${doc.filename}</div>
                <div class="doc-item-meta">${doc.chunks} chunks • Uploaded ${new Date(doc.timestamp).toLocaleString()}</div>
            </div>
            <button class="doc-item-delete" onclick="removeDocument('${doc.filename}')" title="Remove document">🗑️</button>
        </div>
    `).join('');
}

function removeDocument(filename) {
    if (confirm(`Remove "${filename}" from the knowledge base?`)) {
        uploadedDocuments = uploadedDocuments.filter(doc => doc.filename !== filename);
        localStorage.setItem('kb-rag-documents', JSON.stringify(uploadedDocuments));
        renderUploadedDocs();
    }
}

async function clearAllDocuments() {
    if (!confirm('⚠️ This will DELETE ALL documents and reset your entire knowledge base. This cannot be undone. Continue?')) {
        return;
    }
    
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = '<div class="loader"></div><p style="color: #b3b3b3; margin-top: 10px;">🗑️ Clearing knowledge base...</p>';
    
    try {
        const response = await fetch('/clear', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Clear localStorage
            uploadedDocuments = [];
            localStorage.removeItem('kb-rag-documents');
            renderUploadedDocs();
            
            statusDiv.innerHTML = '<div class="status-message status-success">✅ Knowledge base cleared! Upload new documents to start fresh.</div>';
        } else {
            throw new Error(result.error || 'Failed to clear knowledge base');
        }
    } catch (error) {
        console.error('Error clearing documents:', error);
        statusDiv.innerHTML = `<div class="status-message status-error">❌ Error: ${error.message}</div>`;
    }
}

async function uploadDocuments() {
    const files = fileInput.files;
    const source = document.getElementById('sourceInput').value;
    const statusDiv = document.getElementById('uploadStatus');
    
    if (files.length === 0) {
        statusDiv.innerHTML = '<div class="status-message status-error">Please select at least one file</div>';
        return;
    }
    
    statusDiv.innerHTML = `<div class="loader"></div><p style="color: #b3b3b3; margin-top: 10px;">⏳ Uploading ${files.length} document${files.length > 1 ? 's' : ''}... This may take a while for multiple files.</p>`;
    
    let successCount = 0;
    let failCount = 0;
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const formData = new FormData();
        formData.append('file', file);
        if (source) formData.append('source', source);
        
        try {
            statusDiv.innerHTML = `<div class="loader"></div><p style="color: #b3b3b3; margin-top: 10px;">⏳ Uploading ${i + 1}/${files.length}: ${file.name}...</p>`;
            
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 180000);
            
            const response = await fetch('/ingest', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            const responseText = await response.text();
            
            if (!responseText) {
                throw new Error('Server returned empty response');
            }
            
            let result;
            try {
                result = JSON.parse(responseText);
            } catch (parseError) {
                throw new Error(`Failed to parse response: ${responseText.substring(0, 100)}`);
            }
            
            if (response.ok && result.ingested) {
                successCount++;
                
                // Add to uploaded documents list
                uploadedDocuments.push({
                    filename: file.name,
                    chunks: result.ingested,
                    timestamp: new Date().toISOString()
                });
            } else {
                failCount++;
                console.error(`Failed to upload ${file.name}:`, result);
            }
        } catch (error) {
            failCount++;
            console.error(`Error uploading ${file.name}:`, error);
        }
    }
    
    // Save to localStorage
    localStorage.setItem('kb-rag-documents', JSON.stringify(uploadedDocuments));
    renderUploadedDocs();
    
    // Show final status
    if (successCount > 0 && failCount === 0) {
        statusDiv.innerHTML = `<div class="status-message status-success">✅ Successfully uploaded ${successCount} document${successCount > 1 ? 's' : ''}!</div>`;
    } else if (successCount > 0 && failCount > 0) {
        statusDiv.innerHTML = `<div class="status-message status-success">⚠️ Uploaded ${successCount} document${successCount > 1 ? 's' : ''}, ${failCount} failed</div>`;
    } else {
        statusDiv.innerHTML = `<div class="status-message status-error">❌ Failed to upload documents</div>`;
    }
    
    // Reset form
    fileInput.value = '';
    uploadArea.querySelector('h3').textContent = 'Drag & Drop or Click to Upload';
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
