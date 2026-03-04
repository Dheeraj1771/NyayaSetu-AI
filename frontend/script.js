// NyayaSetu AI - Frontend Logic with Multilingual Support

const API_BASE_URL = 'http://localhost:8000';

// Internationalization
let currentLanguage = 'en';
let translations = {};

// Voice Recognition
let recognition = null;
let isListening = false;

// Voice Synthesis
let synthesis = window.speechSynthesis;
let isSpeaking = false;
let currentUtterance = null;

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
const voiceInputBtn = document.getElementById('voiceInputBtn');
const voiceOutputBtn = document.getElementById('voiceOutputBtn');

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

    // Update voice recognition language if initialized
    if (recognition) {
        const languageMap = {
            'en': 'en-IN',
            'hi': 'hi-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'mr': 'mr-IN'
        };
        recognition.lang = languageMap[newLanguage] || 'en-IN';
    }

    // Stop any ongoing speech
    if (isSpeaking) {
        stopSpeaking();
    }
});

// Event Listeners
queryForm.addEventListener('submit', handleSubmit);
sourcesToggle.addEventListener('click', toggleSources);
voiceInputBtn.addEventListener('click', toggleVoiceInput);
voiceOutputBtn.addEventListener('click', toggleVoiceOutput);

// Voice Input: Initialize Speech Recognition
function initVoiceInput() {
    // Check browser support
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn('Speech Recognition not supported in this browser');
        voiceInputBtn.style.display = 'none';
        return;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    // Language mapping for Indian languages
    const languageMap = {
        'en': 'en-IN',
        'hi': 'hi-IN',
        'ta': 'ta-IN',
        'te': 'te-IN',
        'mr': 'mr-IN'
    };

    recognition.lang = languageMap[currentLanguage] || 'en-IN';

    recognition.onstart = () => {
        isListening = true;
        voiceInputBtn.classList.add('listening');
        voiceInputBtn.title = 'Listening...';
    };

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        questionInput.value = transcript;
        questionInput.focus();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;
        voiceInputBtn.classList.remove('listening');
        voiceInputBtn.title = 'Voice Input';

        if (event.error === 'not-allowed') {
            alert('Microphone access denied. Please allow microphone access in your browser settings.');
        } else if (event.error === 'no-speech') {
            alert('No speech detected. Please try again.');
        }
    };

    recognition.onend = () => {
        isListening = false;
        voiceInputBtn.classList.remove('listening');
        voiceInputBtn.title = 'Voice Input';
    };
}

// Toggle Voice Input
function toggleVoiceInput() {
    if (!recognition) {
        alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    if (isListening) {
        recognition.stop();
    } else {
        // Update language before starting
        const languageMap = {
            'en': 'en-IN',
            'hi': 'hi-IN',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'mr': 'mr-IN'
        };
        recognition.lang = languageMap[currentLanguage] || 'en-IN';
        recognition.start();
    }
}

// Voice Output: Initialize Speech Synthesis
function initVoiceOutput() {
    if (!synthesis) {
        console.warn('Speech Synthesis not supported in this browser');
        return;
    }

    // Check if voices are loaded
    if (synthesis.getVoices().length === 0) {
        synthesis.addEventListener('voiceschanged', () => {
            console.log('Voices loaded:', synthesis.getVoices().length);
        });
    }
}

// Toggle Voice Output
function toggleVoiceOutput() {
    if (!synthesis) {
        alert('Text-to-speech is not supported in your browser.');
        return;
    }

    if (isSpeaking) {
        stopSpeaking();
    } else {
        speakAnswer();
    }
}

// Speak Answer
function speakAnswer() {
    const text = answerContent.textContent;

    if (!text) {
        return;
    }

    // Stop any ongoing speech
    synthesis.cancel();

    // Create utterance
    currentUtterance = new SpeechSynthesisUtterance(text);

    // Language mapping for speech synthesis
    const languageMap = {
        'en': 'en-IN',
        'hi': 'hi-IN',
        'ta': 'ta-IN',
        'te': 'te-IN',
        'mr': 'mr-IN'
    };

    currentUtterance.lang = languageMap[currentLanguage] || 'en-IN';
    currentUtterance.rate = 0.9;
    currentUtterance.pitch = 1.0;

    // Try to find appropriate voice
    const voices = synthesis.getVoices();
    const preferredVoice = voices.find(voice =>
        voice.lang.startsWith(currentLanguage) ||
        voice.lang.startsWith(languageMap[currentLanguage])
    );

    if (preferredVoice) {
        currentUtterance.voice = preferredVoice;
    }

    currentUtterance.onstart = () => {
        isSpeaking = true;
        voiceOutputBtn.classList.add('speaking');
        voiceOutputBtn.title = 'Stop Speaking';
    };

    currentUtterance.onend = () => {
        isSpeaking = false;
        voiceOutputBtn.classList.remove('speaking');
        voiceOutputBtn.title = 'Listen to Answer';
    };

    currentUtterance.onerror = (event) => {
        console.error('Speech synthesis error:', event.error);
        isSpeaking = false;
        voiceOutputBtn.classList.remove('speaking');
        voiceOutputBtn.title = 'Listen to Answer';
    };

    synthesis.speak(currentUtterance);
}

// Stop Speaking
function stopSpeaking() {
    if (synthesis && isSpeaking) {
        synthesis.cancel();
        isSpeaking = false;
        voiceOutputBtn.classList.remove('speaking');
        voiceOutputBtn.title = 'Listen to Answer';
    }
}

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

    // Stop any ongoing speech
    if (isSpeaking) {
        stopSpeaking();
    }

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
    initVoiceInput();
    initVoiceOutput();
    checkApiHealth();
    questionInput.focus();
})();
