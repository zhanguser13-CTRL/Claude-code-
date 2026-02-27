/**
 * Main entry point for Pet Companion Webview
 *
 * Initializes all components and starts the application.
 */

// Tab Management
function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;

            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show corresponding content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${tabName}-tab`) {
                    content.classList.add('active');
                }
            });

            // Initialize history view when switching to history tab
            if (tabName === 'history' && !window.historyViewInitialized) {
                initHistoryView();
                window.historyViewInitialized = true;
            }
        });
    });
}

// History View
let historyView = null;

function initHistoryView() {
    if (typeof HistoryView !== 'undefined') {
        historyView = new HistoryView('history-view', {
            onSelect: (conv) => {
                console.log('Selected conversation:', conv.id);
            },
            onRestore: (convId) => {
                handleRestoreConversation(convId);
            },
            onContinue: (convId) => {
                handleContinueConversation(convId);
            },
            onExport: (convId) => {
                console.log('Export conversation:', convId);
            }
        });
    }
}

async function handleRestoreConversation(convId) {
    try {
        let context = '';

        if (typeof ipcClient !== 'undefined' && ipcClient?.isConnected()) {
            context = await ipcClient.restoreContext(convId);
        } else if (typeof vscodeBridge !== 'undefined') {
            const result = await vscodeBridge.sendPetAction('restore_context', {
                conversation_id: convId
            });
            context = result?.context || '';
        }

        if (context) {
            await navigator.clipboard.writeText(context);
            showNotification('Context copied to clipboard! Switch to Pet tab and paste to continue.');
        } else {
            showNotification('Failed to load conversation context');
        }
    } catch (error) {
        console.error('Failed to restore:', error);
        showNotification('Failed to restore conversation');
    }
}

async function handleContinueConversation(convId) {
    // Switch to pet tab
    document.querySelector('.tab[data-tab="pet"]')?.click();

    // Load and copy context
    await handleRestoreConversation(convId);
}

function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        background: rgba(74, 222, 128, 0.9);
        color: white;
        border-radius: 8px;
        font-size: 12px;
        z-index: 1000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.remove();
    }, 4000);
}

class PetCompanionApp {
    constructor() {
        this.state = null;
        this.renderer = null;
        this.spriteManager = null;
        this.animationLoop = null;
        this.dragHandler = null;
        this.interaction = null;
        this.isInitialized = false;
    }

    /**
     * Initialize the application
     */
    async init() {
        if (this.isInitialized) return;

        console.log('Initializing Pet Companion...');

        // Initialize tabs
        initTabs();

        // Try to initialize IPC client
        if (typeof initPetIPC === 'function') {
            try {
                initPetIPC();
                if (typeof ipcClient !== 'undefined' && ipcClient?.isConnected()) {
                    console.log('IPC client connected');
                }
            } catch (e) {
                console.log('IPC not available, using vscode bridge');
            }
        }

        // Load initial state
        await this.loadState();

        // Initialize sprite manager
        this.spriteManager = new SpriteManager();

        // Initialize renderer
        const canvas = document.getElementById('pet-canvas');
        this.renderer = new PetRenderer(canvas);

        // Load sprite data
        const spriteData = await this.spriteManager.getSpriteForStage(this.state.evolution_stage || 0);
        this.renderer.setSpriteData(spriteData);

        // Initialize animation loop
        this.animationLoop = new AnimationLoop();
        this.animationLoop.registerRenderer(this.renderer);
        this.animationLoop.start();

        // Initialize drag handler
        const container = document.getElementById('pet-container');
        this.dragHandler = new DragHandler(container, {
            savePosition: true,
            onDragEnd: () => this.savePosition()
        });

        // Initialize interactions
        this.interaction = new PetInteraction(this.state, this.renderer);

        // Setup state update listener
        this.setupStateListener();

        // Update UI with initial state
        this.updateUI();

        // Start periodic state refresh
        this.startStateRefresh();

        this.isInitialized = true;
        console.log('Pet Companion initialized!');
    }

    /**
     * Load pet state
     */
    async loadState() {
        if (typeof vscodeBridge !== 'undefined') {
            this.state = await vscodeBridge.requestState();
        } else {
            this.state = this.getDefaultState();
        }
    }

    /**
     * Get default state
     */
    getDefaultState() {
        return {
            name: 'Pixel',
            species: 'code-companion',
            level: 1,
            xp: 0,
            xp_to_next_level: 100,
            hunger: 100,
            happiness: 100,
            energy: 100,
            mood: 'content',
            is_sleeping: false,
            evolution_stage: 0,
            evolution_name: 'Egg',
            achievements: []
        };
    }

    /**
     * Setup state change listener
     */
    setupStateListener() {
        if (typeof vscodeBridge !== 'undefined') {
            vscodeBridge.on('stateUpdate', (message) => {
                if (message.state) {
                    this.state = { ...this.state, ...message.state };
                    this.updateUI();
                    this.updateSprite();
                }
            });
        }
    }

    /**
     * Update sprite based on evolution stage
     */
    async updateSprite() {
        if (!this.spriteManager || !this.renderer) return;

        const spriteData = await this.spriteManager.getSpriteForStage(this.state.evolution_stage || 0);
        this.renderer.setSpriteData(spriteData);

        // Update animation based on mood
        const moodAnimations = {
            'happy': 'bounce',
            'excited': 'bounce',
            'ecstatic': 'wobble',
            'sleepy': 'sleep',
            'sad': 'idle',
            'worried': 'idle',
            'hungry': 'wobble',
            'content': 'idle'
        };

        const animation = moodAnimations[this.state.mood] || 'idle';
        this.renderer.setAnimation(animation);
    }

    /**
     * Update UI elements
     */
    updateUI() {
        this.updateStatBars();
        this.updateLevelInfo();
        this.updateMoodDisplay();
        this.updateButtons();
    }

    /**
     * Update stat bars
     */
    updateStatBars() {
        const setBar = (id, value) => {
            const bar = document.getElementById(id);
            const valueEl = document.getElementById(id + '-value');
            if (bar) bar.style.width = Math.max(0, Math.min(100, value)) + '%';
            if (valueEl) valueEl.textContent = value;
        };

        setBar('hunger-bar', this.state.hunger);
        setBar('happiness-bar', this.state.happiness);
        setBar('energy-bar', this.state.energy);

        // Color code based on values
        const updateBarColor = (id, value) => {
            const bar = document.getElementById(id);
            if (!bar) return;

            bar.classList.remove('critical', 'warning', 'healthy');
            if (value <= 20) {
                bar.classList.add('critical');
            } else if (value <= 50) {
                bar.classList.add('warning');
            } else {
                bar.classList.add('healthy');
            }
        };

        updateBarColor('hunger-bar', this.state.hunger);
        updateBarColor('happiness-bar', this.state.happiness);
        updateBarColor('energy-bar', this.state.energy);
    }

    /**
     * Update level info
     */
    updateLevelInfo() {
        const levelBadge = document.getElementById('level-badge');
        const speciesName = document.getElementById('species-name');
        const xpBar = document.getElementById('xp-bar');
        const xpText = document.getElementById('xp-text');

        if (levelBadge) levelBadge.textContent = 'Lv.' + (this.state.level || 1);
        if (speciesName) speciesName.textContent = this.state.evolution_name || 'Baby';

        const xpPercent = ((this.state.xp || 0) / (this.state.xp_to_next_level || 100)) * 100;
        if (xpBar) xpBar.style.width = xpPercent + '%';
        if (xpText) {
            xpText.textContent = `${this.state.xp || 0}/${this.state.xp_to_next_level || 100} XP`;
        }
    }

    /**
     * Update mood display
     */
    updateMoodDisplay() {
        const moodEmoji = document.getElementById('mood-emoji');
        const moodText = document.getElementById('mood-text');

        const moodEmojis = {
            'content': '😊',
            'happy': '😄',
            'excited': '🤩',
            'ecstatic': '🥳',
            'worried': '😟',
            'sad': '😢',
            'sleepy': '😴',
            'hungry': '😋',
            'confused': '😕',
            'proud': '😎',
            'lonely': '😔'
        };

        if (moodEmoji) {
            moodEmoji.textContent = moodEmojis[this.state.mood] || '😊';
        }
        if (moodText) {
            moodText.textContent = (this.state.mood || 'Content').charAt(0).toUpperCase() +
                                   (this.state.mood || 'content').slice(1);
        }
    }

    /**
     * Update button states
     */
    updateButtons() {
        const sleepBtn = document.getElementById('btn-sleep');

        if (sleepBtn && this.state.is_sleeping) {
            sleepBtn.querySelector('.btn-text').textContent = 'Wake';
        } else if (sleepBtn) {
            sleepBtn.querySelector('.btn-text').textContent = 'Sleep';
        }

        // Disable buttons if sleeping
        const buttons = document.querySelectorAll('.pixel-btn:not(#btn-sleep)');
        buttons.forEach(btn => {
            btn.disabled = this.state.is_sleeping;
        });
    }

    /**
     * Start periodic state refresh
     */
    startStateRefresh() {
        // Refresh state every 5 seconds
        setInterval(async () => {
            if (typeof vscodeBridge !== 'undefined') {
                const newState = await vscodeBridge.requestState();
                if (newState) {
                    this.state = { ...this.state, ...newState };
                    this.updateUI();
                }
            }
        }, 5000);
    }

    /**
     * Save position
     */
    savePosition() {
        if (this.dragHandler) {
            const pos = this.dragHandler.getPosition();
            if (typeof vscodeBridge !== 'undefined') {
                vscodeBridge.setWebviewState({ petPosition: pos });
            }
        }
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        const container = document.getElementById('pet-container');

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: absolute;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
        `;

        container.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    /**
     * Clean up
     */
    destroy() {
        if (this.animationLoop) {
            this.animationLoop.stop();
        }
        if (this.dragHandler) {
            this.dragHandler.destroy();
        }
        if (this.interaction) {
            this.interaction.destroy();
        }
    }
}

// Initialize app when DOM is ready
let app;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        app = new PetCompanionApp();
        await app.init();
    });
} else {
    app = new PetCompanionApp();
    app.init();
}

// Export for debugging
if (typeof window !== 'undefined') {
    window.petCompanionApp = app;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = PetCompanionApp;
}
