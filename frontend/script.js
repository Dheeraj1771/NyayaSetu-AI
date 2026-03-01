// NyayaSetu AI - Frontend Logic

const API_BASE_URL = 'http://localhost:8000';

// DOM Elements
const queryForm = document.getElementById('queryForm');
const questionInput = document.getElementById('questionInput');
const submitBtn = document.getElementById('submitBtn');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const errorMessage = document.getElementById('errorMessage');
const answerCard = document.getElementById('answerCard');
const confidenceBadge = document.getElementById('confidenceBadge');
const confidenceValue = document.getElementById('confidenceValue');
const answerContent = document.getElementById('answerContent');
const sourcesToggle = document.getElementById('sourcesToggle');
const sourcesContent = document.getElementById('sourcesContent');
const sourcesList = document.getElementById('sourcesList');
const processingTime = document.getElementById('processingTime');

// Event Listeners
queryForm.addEventListener('submit', handleSubmit);
sourcesToggle.addEventListener('click', toggleSources);

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();

    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    // Show loading state
    showLoading();

    try {
        const response = await fetch(`${API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to get answer');
        }

        const data = await response.json();
        displayAnswer(data);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}

// Show loading state
function showLoading() {
    queryForm.parentElement.style.display = 'none';
    loadingState.style.display = 'block';
    errorState.style.display = 'none';
    answerCard.style.display = 'none';
}

// Show error state
function showError(message) {
    queryForm.parentElement.style.display = 'none';
    loadingState.style.display = 'none';
    errorState.style.display = 'block';
    answerCard.style.display = 'none';
    errorMessage.textContent = message;
}

// Display answer
function displayAnswer(data) {
    // Hide other states
    queryForm.parentElement.style.display = 'none';
    loadingState.style.display = 'none';
    errorState.style.display = 'none';

    // Show answer card
    answerCard.style.display = 'block';

    // Set confidence badge
    const confidence = data.confidence.toLowerCase();
    confidenceBadge.className = `confidence-badge ${confidence}`;
    confidenceValue.textContent = data.confidence;

    // Set answer content
    answerContent.textContent = data.answer;

    // Set processing time
    processingTime.textContent = `${data.processing_time_ms}ms`;

    // Render sources
    renderSources(data.sources);

    // Reset sources toggle
    sourcesContent.style.display = 'none';
    sourcesToggle.classList.remove('active');

    // Scroll to answer
    answerCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Render sources
function renderSources(sources) {
    sourcesList.innerHTML = '';

    sources.forEach((source, index) => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';

        sourceItem.innerHTML = `
            <div class="source-meta">
                <div>
                    <span class="source-label">Act:</span>
                    <span class="source-value">${escapeHtml(source.act)}</span>
                </div>
                <div>
                    <span class="source-label">Chapter:</span>
                    <span class="source-value">${escapeHtml(source.chapter)}</span>
                </div>
                <div>
                    <span class="source-label">Section:</span>
                    <span class="source-value">${escapeHtml(source.section)}</span>
                </div>
            </div>
            <span class="source-similarity">
                Relevance: ${(source.similarity * 100).toFixed(1)}%
            </span>
        `;

        sourcesList.appendChild(sourceItem);
    });
}

// Toggle sources visibility
function toggleSources() {
    const isVisible = sourcesContent.style.display === 'block';

    if (isVisible) {
        sourcesContent.style.display = 'none';
        sourcesToggle.classList.remove('active');
    } else {
        sourcesContent.style.display = 'block';
        sourcesToggle.classList.add('active');
    }
}

// Reset form
function resetForm() {
    queryForm.parentElement.style.display = 'block';
    loadingState.style.display = 'none';
    errorState.style.display = 'none';
    answerCard.style.display = 'none';
    questionInput.value = '';
    questionInput.focus();

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Check API health on load
async function checkApiHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        const data = await response.json();
        console.log('API Status:', data);

        if (!data.bedrock_available) {
            console.warn('Bedrock is not available. API running in retrieval-only mode.');
        }
    } catch (error) {
        console.error('API health check failed:', error);
        console.warn('Make sure the API server is running on http://localhost:8000');
    }
}

// Initialize
checkApiHealth();
questionInput.focus();
