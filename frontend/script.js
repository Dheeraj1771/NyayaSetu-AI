// NyayaSetu AI - Frontend Logic with Multilingual Support

const API_BASE_URL = 'http://localhost:8000';

// Internationalization
let currentLanguage = 'en';
let translations = {};

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
const languageSelect = document.getElementById('languageSelect');

// Initialize i18n
async function initI18n() {
    // Load saved language from localStorage
    const savedLanguage = localStorage.getItem('nyayasetu_language') || 'en';
    currentLanguage = savedLanguage;
    languageSelect.value = savedLanguage;

    // Load translations
    await loadTranslations(savedLanguage);

    // Apply translations
    applyTranslations();
}

// Load translation file
async function loadTranslations(lang) {
    try {
        const response = await fetch(`locales/${lang}.json`);
        translations = await response.json();
    } catch (error) {
        console.error(`Failed to load translations for ${lang}:`, error);
        // Fallback to English
        if (lang !== 'en') {
            const response = await fetch('locales/en.json');
            translations = await response.json();
        }
    }
}

// Apply translations to DOM
function applyTranslations() {
    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(element => {
        const key = element.getAttribute('data-i18n');
        const translation = getNestedTranslation(key);
        if (translation) {
            element.textContent = translation;
        }
    });

    // Update placeholders
    document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
        const key = element.getAttribute('data-i18n-placeholder');
        const translation = getNestedTranslation(key);
        if (translation) {
            element.placeholder = translation;
        }
    });
}

// Get nested translation value
function getNestedTranslation(key) {
    return key.split('.').reduce((obj, k) => obj?.[k], translations);
}

// Language change handler
languageSelect.addEventListener('change', async (e) => {
    const newLanguage = e.target.value;
    currentLanguage = newLanguage;

    // Save to localStorage
    localStorage.setItem('nyayasetu_language', newLanguage);

    // Load and apply new translations
    await loadTranslations(newLanguage);
    applyTranslations();
});

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
            body: JSON.stringify({
                question,
                language: currentLanguage
            })
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

    // Update sources toggle text
    const sourcesToggleText = sourcesToggle.querySelector('span:first-child');
    sourcesToggleText.textContent = getNestedTranslation('answer.viewSources');

    // Scroll to answer
    answerCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Render sources
function renderSources(sources) {
    sourcesList.innerHTML = '';

    sources.forEach((source, index) => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';

        const actLabel = getNestedTranslation('sources.actLabel') || 'Act:';
        const chapterLabel = getNestedTranslation('sources.chapterLabel') || 'Chapter:';
        const sectionLabel = getNestedTranslation('sources.sectionLabel') || 'Section:';
        const relevanceLabel = getNestedTranslation('sources.relevanceLabel') || 'Relevance:';

        sourceItem.innerHTML = `
            <div class="source-meta">
                <div>
                    <span class="source-label">${actLabel}</span>
                    <span class="source-value">${escapeHtml(source.act)}</span>
                </div>
                <div>
                    <span class="source-label">${chapterLabel}</span>
                    <span class="source-value">${escapeHtml(source.chapter)}</span>
                </div>
                <div>
                    <span class="source-label">${sectionLabel}</span>
                    <span class="source-value">${escapeHtml(source.section)}</span>
                </div>
            </div>
            <span class="source-similarity">
                ${relevanceLabel} ${(source.similarity * 100).toFixed(1)}%
            </span>
        `;

        sourcesList.appendChild(sourceItem);
    });
}

// Toggle sources visibility
function toggleSources() {
    const isVisible = sourcesContent.style.display === 'block';
    const sourcesToggleText = sourcesToggle.querySelector('span:first-child');

    if (isVisible) {
        sourcesContent.style.display = 'none';
        sourcesToggle.classList.remove('active');
        sourcesToggleText.textContent = getNestedTranslation('answer.viewSources');
    } else {
        sourcesContent.style.display = 'block';
        sourcesToggle.classList.add('active');
        sourcesToggleText.textContent = getNestedTranslation('answer.hideSources');
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
(async function () {
    await initI18n();
    checkApiHealth();
    questionInput.focus();
})();
