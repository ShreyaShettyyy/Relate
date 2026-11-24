/**
 * RELATE (LUXSTORE) - AI VOICE ASSISTANT
 * Features:
 * - Continuous "Hey Relate" Wake-Word Detection
 * - Real-Time Speech Recognition & Live Transcription
 * - Conversational AI Product Suggestions for Occasions & Events
 * - Voice Actions (Add to Cart, View Cart, Checkout, Category Filters)
 * - Custom Voice Options (Voice Selector, Pitch, Speed, Test Preview)
 * - Synthesized Audio Chimes (Web Audio API)
 * - Fallback & Error Handling (Never leaves user hanging)
 */

(function () {
    'use strict';

    // -------------------------------------------------------------------------
    // ASSISTANT STATE & CONFIGURATION
    // -------------------------------------------------------------------------
    const state = {
        isOpen: false,
        isListening: false,
        isWakeWordActive: false,
        isSpeaking: false,
        activeUtterance: null,
        lastRecommendedProduct: null,
        voices: [],
        settings: {
            voiceURI: '',
            voiceName: '',
            lang: 'en-US',
            rate: 1.0,
            pitch: 1.0,
            wakeWordEnabled: true
        },
        recognition: null,
        speechSupported: false,
        synthesisSupported: false,
        silenceTimer: null,
        speechFailsafeTimeout: null,
        interimQueryTimeout: null,
        lastSpokenText: '',
        restartRecognitionTimeout: null
    };

    // Load saved settings from localStorage
    try {
        const saved = localStorage.getItem('relate_voice_settings');
        if (saved) {
            state.settings = Object.assign(state.settings, JSON.parse(saved));
        }
    } catch (e) {
        console.warn('Could not load voice settings from localStorage:', e);
    }

    // -------------------------------------------------------------------------
    // WEB AUDIO API CHIME GENERATOR
    // -------------------------------------------------------------------------
    function playChime(type = 'wake') {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (!AudioContext) return;
            const ctx = new AudioContext();
            const now = ctx.currentTime;

            if (type === 'wake') {
                // Two-tone rising chime (D5 -> A5)
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, now); // D5
                osc.frequency.exponentialRampToValueAtTime(880.0, now + 0.14); // A5
                gain.gain.setValueAtTime(0.09, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.28);
            } else if (type === 'success') {
                // Bright confirmation bell (F#5 -> C#6)
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'triangle';
                osc.frequency.setValueAtTime(739.99, now);
                osc.frequency.exponentialRampToValueAtTime(1108.73, now + 0.12);
                gain.gain.setValueAtTime(0.08, now);
                gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.start(now);
                osc.stop(now + 0.3);
            }
        } catch (e) {
            // Audio context may require prior user interaction in strict browsers
        }
    }

    // -------------------------------------------------------------------------
    // SPEECH SYNTHESIS ENGINE (CUSTOMIZABLE VOICES)
    // -------------------------------------------------------------------------
    function initSpeechSynthesis() {
        if (!('speechSynthesis' in window)) {
            state.synthesisSupported = false;
            return;
        }
        state.synthesisSupported = true;

        function loadVoices() {
            state.voices = window.speechSynthesis.getVoices() || [];
            populateVoiceDropdown();
        }

        loadVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
    }

    function populateVoiceDropdown() {
        const select = document.getElementById('va-voice-select');
        if (!select || !state.voices.length) return;

        const currentVal = state.settings.voiceURI || select.value;
        select.innerHTML = '<option value="">Default System Voice</option>';

        // Filter / sort for clean English & native natural voices
        const sorted = [...state.voices].sort((a, b) => {
            const aEn = a.lang.toLowerCase().startsWith('en');
            const bEn = b.lang.toLowerCase().startsWith('en');
            if (aEn && !bEn) return -1;
            if (!aEn && bEn) return 1;
            return a.name.localeCompare(b.name);
        });

        sorted.forEach(voice => {
            const opt = document.createElement('option');
            opt.value = voice.voiceURI;
            const langLabel = voice.lang ? ` (${voice.lang})` : '';
            opt.textContent = `${voice.name}${langLabel}`;
            if (voice.voiceURI === currentVal || voice.name === state.settings.voiceName) {
                opt.selected = true;
            }
            select.appendChild(opt);
        });
    }

    function getSelectedVoice() {
        if (!state.voices.length) return null;
        if (state.settings.voiceURI) {
            const match = state.voices.find(v => v.voiceURI === state.settings.voiceURI);
            if (match) return match;
        }
        if (state.settings.voiceName) {
            const match = state.voices.find(v => v.name === state.settings.voiceName);
            if (match) return match;
        }
        // Preferred natural English voices fallback
        const preferred = state.voices.find(v => 
            v.lang.toLowerCase().startsWith('en') && 
            (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha') || v.name.includes('Zira') || v.name.includes('Jenny') || v.name.includes('Guy'))
        );
        if (preferred) return preferred;

        // Default to any English voice
        return state.voices.find(v => v.lang.toLowerCase().startsWith('en')) || state.voices[0];
    }

    function speak(text, onComplete) {
        if (!state.synthesisSupported || !text) {
            if (onComplete) onComplete();
            return;
        }

        // Cancel any ongoing speech
        stopSpeaking();

        const utterance = new SpeechSynthesisUtterance(text);
        const voice = getSelectedVoice();
        if (voice) {
            utterance.voice = voice;
            utterance.lang = voice.lang;
        } else {
            utterance.lang = 'en-US';
        }

        utterance.rate = state.settings.rate || 1.0;
        utterance.pitch = state.settings.pitch || 1.0;
        utterance.volume = 1.0;

        // Keep global reference to prevent Chrome garbage-collection bug
        window.__relateSpeechUtterance = utterance;

        utterance.onstart = () => {
            state.isSpeaking = true;
            state.activeUtterance = utterance;
            updateSpeakingVisuals(true);
            // Temporarily pause recognition so the assistant doesn't hear itself speak
            pauseRecognitionForSpeech();
        };

        const finalizeSpeech = () => {
            clearTimeout(state.speechFailsafeTimeout);
            state.isSpeaking = false;
            state.activeUtterance = null;
            window.__relateSpeechUtterance = null;
            updateSpeakingVisuals(false);
            resumeRecognitionAfterSpeech();
            if (onComplete) onComplete();
        };

        // Failsafe watchdog: Chrome on Windows frequently drops `onend` on speech synthesis!
        // This ensures recognition is ALWAYS safely unpaused after speech completes.
        const estimatedDurationMs = Math.max(2200, (text.length * 85) + 1200);
        clearTimeout(state.speechFailsafeTimeout);
        state.speechFailsafeTimeout = setTimeout(() => {
            if (state.isSpeaking) {
                finalizeSpeech();
            }
        }, estimatedDurationMs);

        utterance.onend = finalizeSpeech;
        utterance.onerror = (e) => {
            console.warn('Speech synthesis notice:', e);
            finalizeSpeech();
        };

        try {
            window.speechSynthesis.speak(utterance);
        } catch (err) {
            console.warn('Speech synthesis speak error:', err);
            finalizeSpeech();
        }
    }

    function stopSpeaking() {
        clearTimeout(state.speechFailsafeTimeout);
        if ('speechSynthesis' in window && window.speechSynthesis.speaking) {
            window.speechSynthesis.cancel();
        }
        state.isSpeaking = false;
        state.activeUtterance = null;
        window.__relateSpeechUtterance = null;
        updateSpeakingVisuals(false);
        resumeRecognitionAfterSpeech();
    }

    function updateSpeakingVisuals(isSpeaking) {
        const stopBtn = document.getElementById('va-stop-speech-btn');
        const fab = document.getElementById('voice-assistant-fab');
        const pulse = document.getElementById('va-header-pulse');

        if (stopBtn) stopBtn.classList.toggle('hidden', !isSpeaking);
        if (fab) fab.classList.toggle('is-speaking', isSpeaking);
        if (pulse) pulse.classList.toggle('speaking', isSpeaking);
    }

    // -------------------------------------------------------------------------
    // SPEECH RECOGNITION ENGINE (WAKE-WORD & COMMANDS)
    // -------------------------------------------------------------------------
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            state.speechSupported = false;
            updateStatus('Mic not supported in this browser • Type below');
            const micBtn = document.getElementById('va-mic-btn');
            if (micBtn) micBtn.title = 'Speech recognition not supported in this browser';
            return;
        }

        state.speechSupported = true;
        const recog = new SpeechRecognition();
        recog.continuous = true;
        recog.interimResults = true;
        recog.lang = 'en-US';
        recog.maxAlternatives = 1;

        recog.onstart = () => {
            state.isWakeWordActive = true;
            updateWakeWordStatus();
        };

        recog.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }

            const currentSpoken = (finalTranscript || interimTranscript).trim();
            if (!currentSpoken) return;

            // Show real-time streaming text in the UI
            showLiveTranscription(currentSpoken);

            // Check for Wake-Word: "Hey Relate" / "Hi Relate" / "Relate" (plus common STT variants like reality, relay, re late)
            const wakeMatch = currentSpoken.match(/\b(?:hey|hi|hello|ok|okay)?\s*(?:relate|re\s*late|reality|relay|relat|relet|elate)\b/i);
            
            if (wakeMatch) {
                // Wake word detected!
                playChime('wake');
                if (!state.isOpen) {
                    openAssistantPanel();
                }

                // Check if user continued their command in the same utterance
                // e.g., "Hey Relate, add iPhone 13 Pro to cart"
                const wakeIndex = wakeMatch.index + wakeMatch[0].length;
                const commandAfterWake = currentSpoken.slice(wakeIndex).trim().replace(/^[,.!\s]+/, '');

                if (commandAfterWake.length > 2) {
                    clearTimeout(state.silenceTimer);
                    clearTimeout(state.interimQueryTimeout);
                    handleQuery(commandAfterWake);
                    return;
                }

                // If user just said "Hey Relate", acknowledge with voice and keep listening!
                if (!commandAfterWake && (!state.isListening || !state.lastSpokenText)) {
                    state.isListening = true;
                    updateListeningVisuals(true);
                    updateStatus("Listening... speak your request");
                    speak("Hello! I'm listening. What would you like to explore or add to your cart?", () => {
                        resetSilenceTimer();
                    });
                    return;
                }
            }

            // If assistant is actively listening or panel is open
            if (state.isListening || state.isOpen) {
                let queryCandidate = (finalTranscript || interimTranscript).trim();
                const prefixMatch = queryCandidate.match(/^\b(?:hey|hi|hello|ok|okay)?\s*(?:relate|re\s*late|reality|relay|relat|relet|elate)\b[,.!\s]*/i);
                if (prefixMatch) {
                    queryCandidate = queryCandidate.slice(prefixMatch[0].length).trim();
                }

                if (queryCandidate.length > 1) {
                    if (finalTranscript) {
                        clearTimeout(state.silenceTimer);
                        clearTimeout(state.interimQueryTimeout);
                        handleQuery(queryCandidate);
                    } else {
                        // Interim text with natural speech pause detection (1000ms pause)
                        clearTimeout(state.interimQueryTimeout);
                        state.interimQueryTimeout = setTimeout(() => {
                            if (!state.isSpeaking && queryCandidate.length > 1) {
                                clearTimeout(state.silenceTimer);
                                handleQuery(queryCandidate);
                            }
                        }, 1000);
                    }
                }
            }
        };

        recog.onerror = (event) => {
            if (event.error === 'no-speech') {
                // Silence - natural timeout, keep running smoothly
                return;
            }
            if (event.error === 'not-allowed') {
                console.warn('Microphone permission requires user click or permission in browser settings.');
                state.isWakeWordActive = false;
                updateWakeWordStatus();
                updateStatus('Microphone click required • Tap mic to activate');
                return;
            }
            console.warn('Speech recognition notice:', event.error);
        };

        recog.onend = () => {
            state.isWakeWordActive = false;
            // Automatically restart if wake word is enabled and assistant is not speaking
            if (state.settings.wakeWordEnabled && !state.isSpeaking) {
                scheduleRestartRecognition(400);
            } else {
                updateWakeWordStatus();
            }
        };

        state.recognition = recog;

        // Auto-start wake-word listening if enabled in settings
        if (state.settings.wakeWordEnabled) {
            startRecognition();
        }
    }

    function startRecognition() {
        if (!state.recognition || state.isWakeWordActive) return;
        try {
            state.recognition.start();
        } catch (e) {
            // Already started or busy
        }
    }

    function stopRecognition() {
        clearTimeout(state.restartRecognitionTimeout);
        if (state.recognition && state.isWakeWordActive) {
            try {
                state.recognition.stop();
            } catch (e) {}
        }
        state.isWakeWordActive = false;
        state.isListening = false;
        updateListeningVisuals(false);
        updateWakeWordStatus();
    }

    function pauseRecognitionForSpeech() {
        if (state.recognition && state.isWakeWordActive) {
            try {
                state.recognition.stop();
            } catch (e) {}
        }
    }

    function resumeRecognitionAfterSpeech() {
        if (state.settings.wakeWordEnabled) {
            scheduleRestartRecognition(350);
        }
    }

    function scheduleRestartRecognition(delay = 400) {
        clearTimeout(state.restartRecognitionTimeout);
        state.restartRecognitionTimeout = setTimeout(() => {
            if (state.settings.wakeWordEnabled && !state.isSpeaking && !state.isWakeWordActive) {
                startRecognition();
            }
        }, delay);
    }

    function resetSilenceTimer() {
        clearTimeout(state.silenceTimer);
        state.silenceTimer = setTimeout(() => {
            if (state.isListening && !state.isSpeaking) {
                state.isListening = false;
                updateListeningVisuals(false);
                hideLiveTranscription();
                updateStatus('Ready • Say "Hey Relate"');
            }
        }, 8000);
    }

    // -------------------------------------------------------------------------
    // QUERY EXECUTION & RESPONSE HANDLER
    // -------------------------------------------------------------------------
    async function handleQuery(queryText) {
        if (!queryText || !queryText.trim()) return;

        state.isListening = false;
        updateListeningVisuals(false);
        hideLiveTranscription();
        clearTimeout(state.silenceTimer);

        // Add User Speech Bubble in Chat Body
        appendMessage('user', queryText.trim());
        updateStatus('Thinking...');

        // Gather context from window.RelateApp
        let currentProduct = null;
        if (window.RelateApp && typeof window.RelateApp.getCurrentProduct === 'function') {
            currentProduct = window.RelateApp.getCurrentProduct();
        }

        try {
            const response = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: queryText.trim(),
                    current_product: currentProduct,
                    last_recommended_product: state.lastRecommendedProduct
                })
            });

            if (!response.ok) {
                throw new Error(`Server returned HTTP ${response.status}`);
            }

            const data = await response.json();
            handleAssistantReply(data);
        } catch (error) {
            console.error('Error fetching voice assistant reply:', error);
            const fallbackText = "I'm having a little trouble connecting to the catalog right now. Please try again or tap the suggestions below.";
            appendMessage('assistant', fallbackText);
            speak(fallbackText);
            updateStatus('Ready • Say "Hey Relate"');
        }
    }

    function handleAssistantReply(data) {
        const replyText = data.reply || "I've checked the catalog for you.";
        const products = data.products || [];
        const action = data.action || { type: 'none' };

        // Save last recommended product for context follow-ups (e.g. "add to cart")
        if (products && products.length > 0) {
            state.lastRecommendedProduct = products[0];
        }

        // 1. Execute direct UI / Cart actions
        if (action.type === 'add_to_cart' && action.product_id) {
            if (window.RelateApp && typeof window.RelateApp.addToCart === 'function') {
                window.RelateApp.addToCart(action.product_id);
                playChime('success');
                if (typeof window.RelateApp.showToast === 'function') {
                    window.RelateApp.showToast(`Added ${action.product_name || 'product'} to cart!`, 'success');
                }
            }
            if (products && products.length > 0) {
                state.lastRecommendedProduct = products[0];
            }
        } else if (action.type === 'view_cart') {
            if (window.RelateApp && typeof window.RelateApp.openCartDrawer === 'function') {
                window.RelateApp.openCartDrawer();
            }
        } else if (action.type === 'checkout') {
            if (window.RelateApp && typeof window.RelateApp.navigateTo === 'function') {
                window.RelateApp.navigateTo('checkout-section');
            }
        } else if (action.type === 'view_wishlist') {
            if (window.RelateApp && typeof window.RelateApp.openWishlist === 'function') {
                window.RelateApp.openWishlist();
            }
        } else if (action.type === 'navigate_category' && action.category) {
            if (window.RelateApp && typeof window.RelateApp.setCategory === 'function') {
                window.RelateApp.setCategory(action.category);
            }
            if (window.RelateApp && typeof window.RelateApp.navigateTo === 'function') {
                window.RelateApp.navigateTo('catalog-section');
            }
        }

        // 2. Render Assistant Bubble & Interactive Product Cards
        appendMessage('assistant', replyText, products, action);

        // 3. Speak the reply
        speak(replyText);
        updateStatus('Ready • Say "Hey Relate"');
    }

    // -------------------------------------------------------------------------
    // UI RENDERING & DOM BUILDERS
    // -------------------------------------------------------------------------
    function appendMessage(role, text, products = [], action = null) {
        const container = document.getElementById('va-messages');
        if (!container) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = `va-msg va-msg-${role}`;

        let actionBadgeHtml = '';
        if (action && action.type === 'add_to_cart') {
            actionBadgeHtml = `
                <div class="va-action-pill success">
                    <span><i class="fa-solid fa-circle-check"></i> Added to Cart</span>
                    <button class="va-inline-cart-btn" data-action="open-cart">
                        <i class="fa-solid fa-bag-shopping"></i> View Cart
                    </button>
                </div>
            `;
        }

        let productsHtml = '';
        if (products && products.length > 0) {
            const cardsHtml = products.slice(0, 4).map(p => {
                const img = getProductThumbnail(p);
                const price = p.Price ? `₹${Number(p.Price).toLocaleString('en-IN')}` : '';
                return `
                    <div class="va-product-card" data-id="${p.ID}">
                        <div class="va-prod-img-box">
                            <img src="${img}" alt="${escapeHtml(p.Name)}" loading="lazy">
                        </div>
                        <div class="va-prod-info">
                            <h5 class="va-prod-title">${escapeHtml(p.Name)}</h5>
                            <div class="va-prod-meta">
                                <span class="va-prod-price">${price}</span>
                                <span class="va-prod-rating"><i class="fa-solid fa-star"></i> ${p.Rating || '4.5'}</span>
                            </div>
                            <div class="va-prod-actions">
                                <button class="va-btn-add-cart" data-id="${p.ID}">
                                    <i class="fa-solid fa-cart-plus"></i> Add
                                </button>
                                <button class="va-btn-view" data-id="${p.ID}">
                                    View
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');

            productsHtml = `<div class="va-products-carousel">${cardsHtml}</div>`;
        }

        msgDiv.innerHTML = `
            <div class="va-msg-bubble">
                ${actionBadgeHtml}
                <p>${escapeHtml(text)}</p>
                ${productsHtml}
            </div>
        `;

        container.appendChild(msgDiv);
        scrollChatToBottom();

        // Bind clicks on inline view-cart button
        msgDiv.querySelectorAll('.va-inline-cart-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (window.RelateApp && typeof window.RelateApp.openCartDrawer === 'function') {
                    window.RelateApp.openCartDrawer();
                }
            });
        });

        // Bind clicks on mini product card buttons
        msgDiv.querySelectorAll('.va-btn-add-cart').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const pId = parseInt(btn.getAttribute('data-id'), 10);
                if (window.RelateApp && typeof window.RelateApp.addToCart === 'function') {
                    window.RelateApp.addToCart(pId);
                    playChime('success');
                    btn.innerHTML = '<i class="fa-solid fa-check"></i> Added';
                    btn.classList.add('added');
                }
            });
        });

        msgDiv.querySelectorAll('.va-btn-view').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const pId = parseInt(btn.getAttribute('data-id'), 10);
                if (window.RelateApp && typeof window.RelateApp.renderProductDetail === 'function') {
                    window.RelateApp.renderProductDetail(pId);
                }
            });
        });
    }

    function showLiveTranscription(text) {
        const bar = document.getElementById('va-live-stream');
        const span = document.getElementById('va-live-transcript');
        if (bar && span) {
            span.textContent = text;
            bar.classList.remove('hidden');
            scrollChatToBottom();
        }
    }

    function hideLiveTranscription() {
        const bar = document.getElementById('va-live-stream');
        if (bar) bar.classList.add('hidden');
    }

    function updateStatus(statusText) {
        const el = document.getElementById('va-status-text');
        if (el) el.textContent = statusText;
    }

    function updateListeningVisuals(isListening) {
        const micBtn = document.getElementById('va-mic-btn');
        const fab = document.getElementById('voice-assistant-fab');
        const pulse = document.getElementById('va-header-pulse');

        if (micBtn) micBtn.classList.toggle('active', isListening);
        if (fab) fab.classList.toggle('is-listening', isListening);
        if (pulse) pulse.classList.toggle('active', isListening);
    }

    function updateWakeWordStatus() {
        const toggleBtn = document.getElementById('va-wake-toggle-btn');
        const dot = document.getElementById('fab-status-dot');
        const isEnabled = state.settings.wakeWordEnabled;

        if (toggleBtn) {
            toggleBtn.classList.toggle('active', isEnabled);
            toggleBtn.querySelector('span').textContent = isEnabled ? 'Wake Word ON' : 'Wake Word OFF';
        }

        if (dot) {
            dot.className = `fab-status-dot ${isEnabled ? 'online' : 'paused'}`;
            dot.title = isEnabled ? "Say 'Hey Relate' to activate" : "Wake word paused (click mic)";
        }
    }

    function scrollChatToBottom() {
        const body = document.getElementById('va-chat-body');
        if (body) {
            setTimeout(() => {
                body.scrollTop = body.scrollHeight;
            }, 60);
        }
    }

    function getProductThumbnail(prod) {
        const fallback = 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500&auto=format&fit=crop&q=60';
        if (!prod || !prod.Image) return fallback;
        const first = String(prod.Image).split(',')[0].trim();
        return (first.startsWith('http://') || first.startsWith('https://')) ? first : fallback;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // -------------------------------------------------------------------------
    // PANEL CONTROLS & EVENT BINDINGS
    // -------------------------------------------------------------------------
    function openAssistantPanel() {
        const panel = document.getElementById('voice-assistant-panel');
        if (!panel) return;
        panel.classList.remove('hidden');
        state.isOpen = true;

        if (typeof gsap !== 'undefined') {
            gsap.fromTo(panel, 
                { opacity: 0, scale: 0.92, y: 20 }, 
                { opacity: 1, scale: 1, y: 0, duration: 0.35, ease: 'power2.out' }
            );
        }
        scrollChatToBottom();
    }

    function closeAssistantPanel() {
        const panel = document.getElementById('voice-assistant-panel');
        if (!panel) return;

        if (typeof gsap !== 'undefined') {
            gsap.to(panel, {
                opacity: 0,
                scale: 0.92,
                y: 20,
                duration: 0.22,
                ease: 'power2.in',
                onComplete: () => {
                    panel.classList.add('hidden');
                    state.isOpen = false;
                }
            });
        } else {
            panel.classList.add('hidden');
            state.isOpen = false;
        }

        stopSpeaking();
    }

    function setupEventListeners() {
        // Floating FAB button click
        const fab = document.getElementById('voice-assistant-fab');
        if (fab) {
            fab.addEventListener('click', () => {
                if (state.isOpen) {
                    closeAssistantPanel();
                } else {
                    openAssistantPanel();
                    // If recognition is ready, trigger one-shot query listen
                    if (state.speechSupported) {
                        triggerActiveVoiceInput();
                    }
                }
            });
        }

        // Close button
        const closeBtn = document.getElementById('va-close-btn');
        if (closeBtn) closeBtn.addEventListener('click', closeAssistantPanel);

        // Mic Button in Assistant input bar
        const micBtn = document.getElementById('va-mic-btn');
        if (micBtn) {
            micBtn.addEventListener('click', () => {
                if (state.isListening) {
                    state.isListening = false;
                    updateListeningVisuals(false);
                    hideLiveTranscription();
                } else {
                    triggerActiveVoiceInput();
                }
            });
        }

        // Text input submission
        const inputField = document.getElementById('va-text-input');
        const sendBtn = document.getElementById('va-send-btn');

        function submitTextInput() {
            if (!inputField) return;
            const text = inputField.value.trim();
            if (text) {
                inputField.value = '';
                handleQuery(text);
            }
        }

        if (sendBtn) sendBtn.addEventListener('click', submitTextInput);
        if (inputField) {
            inputField.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    submitTextInput();
                }
            });
        }

        // Quick Suggestion Chips
        document.querySelectorAll('.va-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                const query = chip.getAttribute('data-query');
                if (query) handleQuery(query);
            });
        });

        // Wake word toggle button
        const wakeToggle = document.getElementById('va-wake-toggle-btn');
        if (wakeToggle) {
            wakeToggle.addEventListener('click', () => {
                state.settings.wakeWordEnabled = !state.settings.wakeWordEnabled;
                saveSettings();
                updateWakeWordStatus();
                if (state.settings.wakeWordEnabled) {
                    startRecognition();
                    if (window.RelateApp && typeof window.RelateApp.showToast === 'function') {
                        window.RelateApp.showToast("Wake word listening is now ON (Say 'Hey Relate')", "info");
                    }
                } else {
                    stopRecognition();
                    if (window.RelateApp && typeof window.RelateApp.showToast === 'function') {
                        window.RelateApp.showToast("Wake word listening paused", "info");
                    }
                }
            });
        }

        // Voice Settings popover toggle
        const settingsBtn = document.getElementById('va-settings-btn');
        const settingsPopover = document.getElementById('va-settings-popover');
        const closeSettingsBtn = document.getElementById('va-close-settings-btn');
        const saveSettingsBtn = document.getElementById('va-save-settings-btn');

        function toggleSettings(show) {
            if (!settingsPopover) return;
            settingsPopover.classList.toggle('hidden', !show);
        }

        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                const isHidden = settingsPopover.classList.contains('hidden');
                toggleSettings(isHidden);
            });
        }
        if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', () => toggleSettings(false));
        if (saveSettingsBtn) closeSettingsBtn.addEventListener('click', () => toggleSettings(false));

        // Voice selection change
        const voiceSelect = document.getElementById('va-voice-select');
        if (voiceSelect) {
            voiceSelect.addEventListener('change', () => {
                const selectedURI = voiceSelect.value;
                const match = state.voices.find(v => v.voiceURI === selectedURI);
                if (match) {
                    state.settings.voiceURI = match.voiceURI;
                    state.settings.voiceName = match.name;
                    state.settings.lang = match.lang;
                } else {
                    state.settings.voiceURI = '';
                    state.settings.voiceName = '';
                }
                saveSettings();
            });
        }

        // Sliders (Rate & Pitch)
        const rateSlider = document.getElementById('va-rate-slider');
        const rateVal = document.getElementById('va-rate-val');
        if (rateSlider && rateVal) {
            rateSlider.value = state.settings.rate || 1.0;
            rateVal.textContent = `${rateSlider.value}x`;
            rateSlider.addEventListener('input', () => {
                state.settings.rate = parseFloat(rateSlider.value);
                rateVal.textContent = `${state.settings.rate.toFixed(2)}x`;
                saveSettings();
            });
        }

        const pitchSlider = document.getElementById('va-pitch-slider');
        const pitchVal = document.getElementById('va-pitch-val');
        if (pitchSlider && pitchVal) {
            pitchSlider.value = state.settings.pitch || 1.0;
            pitchVal.textContent = `${pitchSlider.value}x`;
            pitchSlider.addEventListener('input', () => {
                state.settings.pitch = parseFloat(pitchSlider.value);
                pitchVal.textContent = `${state.settings.pitch.toFixed(2)}x`;
                saveSettings();
            });
        }

        // Test Voice button
        const testVoiceBtn = document.getElementById('va-test-voice-btn');
        if (testVoiceBtn) {
            testVoiceBtn.addEventListener('click', () => {
                speak("Hello! I am Relate AI. This is how I will sound when guiding your shopping on Relate.");
            });
        }

        // Stop speaking button
        const stopSpeechBtn = document.getElementById('va-stop-speech-btn');
        if (stopSpeechBtn) {
            stopSpeechBtn.addEventListener('click', stopSpeaking);
        }
    }

    function triggerActiveVoiceInput() {
        if (!state.speechSupported) {
            if (window.RelateApp && typeof window.RelateApp.showToast === 'function') {
                window.RelateApp.showToast('Speech recognition is not available in this browser. Please type your query.', 'error');
            }
            return;
        }

        playChime('wake');
        state.isListening = true;
        updateListeningVisuals(true);
        updateStatus("Listening... speak your request");
        showLiveTranscription("Listening...");

        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia && !state.hasMicPermission) {
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    state.hasMicPermission = true;
                    stream.getTracks().forEach(t => t.stop());
                    startRecognition();
                })
                .catch(() => {
                    startRecognition();
                });
        } else {
            startRecognition();
        }
        resetSilenceTimer();
    }

    function saveSettings() {
        try {
            localStorage.setItem('relate_voice_settings', JSON.stringify(state.settings));
        } catch (e) {}
    }

    // -------------------------------------------------------------------------
    // INITIALIZATION ON DOM READY
    // -------------------------------------------------------------------------
    function initVoiceAssistant() {
        initSpeechSynthesis();
        setupEventListeners();
        initSpeechRecognition();
        updateWakeWordStatus();

        // Enable microphone listening seamlessly upon first user gesture (Chrome autoplay policy compliance)
        const onFirstInteraction = () => {
            if (state.settings.wakeWordEnabled && !state.isWakeWordActive && state.speechSupported) {
                startRecognition();
            }
            document.removeEventListener('click', onFirstInteraction);
            document.removeEventListener('keydown', onFirstInteraction);
            document.removeEventListener('touchstart', onFirstInteraction);
        };
        document.addEventListener('click', onFirstInteraction);
        document.addEventListener('keydown', onFirstInteraction);
        document.addEventListener('touchstart', onFirstInteraction);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initVoiceAssistant);
    } else {
        initVoiceAssistant();
    }

})();
