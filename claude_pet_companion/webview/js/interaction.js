/**
 * Interaction - Handles user interactions with the pet
 *
 * Manages clicks, pet interactions, and UI button actions.
 */

class PetInteraction {
    constructor(petState, renderer) {
        this.state = petState;
        this.renderer = renderer;
        this.interactionCooldown = false;
        this.cooldownTime = 500;

        this.init();
    }

    /**
     * Initialize interaction handlers
     */
    init() {
        // Setup button handlers
        this.setupButtons();

        // Setup pet click handler
        this.setupPetClick();

        // Setup keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    /**
     * Setup action buttons
     */
    setupButtons() {
        const feedBtn = document.getElementById('btn-feed');
        const playBtn = document.getElementById('btn-play');
        const sleepBtn = document.getElementById('btn-sleep');

        if (feedBtn) {
            feedBtn.addEventListener('click', () => this.handleFeed());
        }

        if (playBtn) {
            playBtn.addEventListener('click', () => this.handlePlay());
        }

        if (sleepBtn) {
            sleepBtn.addEventListener('click', () => this.handleSleep());
        }
    }

    /**
     * Setup pet click interactions
     */
    setupPetClick() {
        const canvas = document.getElementById('pet-canvas');
        if (!canvas) return;

        canvas.addEventListener('click', () => {
            this.handlePetClick();
        });
    }

    /**
     * Setup keyboard shortcuts
     */
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only trigger if not typing in an input
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                return;
            }

            switch(e.key.toLowerCase()) {
                case 'f':
                    this.handleFeed();
                    break;
                case 'p':
                    this.handlePlay();
                    break;
                case 's':
                    this.handleSleep();
                    break;
            }
        });
    }

    /**
     * Handle feed action
     */
    async handleFeed() {
        if (this.interactionCooldown || this.state.is_sleeping) return;

        this.setCooldown();

        // Send feed command to extension
        if (typeof vscode !== 'undefined') {
            const result = await this.sendMessage({ type: 'feed' });
            this.handleActionResult(result);
        }

        // Play eating animation
        this.playAnimation('eat');

        // Show speech bubble
        this.showSpeech('Yummy! 🍖');
    }

    /**
     * Handle play action
     */
    async handlePlay() {
        if (this.interactionCooldown || this.state.is_sleeping) return;

        this.setCooldown();

        // Send play command to extension
        if (typeof vscode !== 'undefined') {
            const result = await this.sendMessage({ type: 'play' });
            this.handleActionResult(result);
        }

        // Play bounce animation
        this.playAnimation('bounce');

        // Show speech bubble
        this.showSpeech('Wheee! 🎉');
    }

    /**
     * Handle sleep action
     */
    async handleSleep() {
        if (this.interactionCooldown) return;

        this.setCooldown();

        // Send sleep command to extension
        if (typeof vscode !== 'undefined') {
            const result = await this.sendMessage({ type: 'sleep' });
            this.handleActionResult(result);

            if (result && result.is_sleeping) {
                this.playAnimation('sleep');
                this.showSpeech('Zzz... 😴');
            } else {
                this.stopAnimation('sleep');
                this.showSpeech('Good morning! ☀️');
            }
        }
    }

    /**
     * Handle pet click (pet the pet)
     */
    handlePetClick() {
        if (this.interactionCooldown) return;

        this.setCooldown();

        // Play happy animation
        this.playAnimation('bounce');

        // Random happy responses
        const responses = [
            '❤️',
            'Hehe!',
            '*happy wiggles*',
            'Yay!',
            'Thanks!',
            '*purrs*'
        ];

        const response = responses[Math.floor(Math.random() * responses.length)];
        this.showSpeech(response);

        // Small happiness boost
        if (typeof vscode !== 'undefined') {
            this.sendMessage({ type: 'pet' });
        }
    }

    /**
     * Handle action result from extension
     */
    handleActionResult(result) {
        if (!result) return;

        // Update state
        if (result.state) {
            Object.assign(this.state, result.state);
        }

        // Check for level up
        if (result.leveled_up) {
            this.showLevelUp(result.new_level);
        }

        // Check for achievements
        if (result.achievements) {
            result.achievements.forEach(a => this.showAchievement(a));
        }

        // Update UI
        this.updateUI();
    }

    /**
     * Update UI elements
     */
    updateUI() {
        // Update stat bars
        this.updateStatBars();

        // Update level info
        this.updateLevelInfo();

        // Update mood display
        this.updateMoodDisplay();

        // Update animation based on mood
        this.updateAnimation();
    }

    /**
     * Update stat bars
     */
    updateStatBars() {
        const hungerBar = document.getElementById('hunger-bar');
        const hungerValue = document.getElementById('hunger-value');
        const happinessBar = document.getElementById('happiness-bar');
        const happinessValue = document.getElementById('happiness-value');
        const energyBar = document.getElementById('energy-bar');
        const energyValue = document.getElementById('energy-value');

        if (hungerBar) hungerBar.style.width = this.state.hunger + '%';
        if (hungerValue) hungerValue.textContent = this.state.hunger;

        if (happinessBar) happinessBar.style.width = this.state.happiness + '%';
        if (happinessValue) happinessValue.textContent = this.state.happiness;

        if (energyBar) energyBar.style.width = this.state.energy + '%';
        if (energyValue) energyValue.textContent = this.state.energy;
    }

    /**
     * Update level info
     */
    updateLevelInfo() {
        const levelBadge = document.getElementById('level-badge');
        const speciesName = document.getElementById('species-name');
        const xpBar = document.getElementById('xp-bar');
        const xpText = document.getElementById('xp-text');

        if (levelBadge) levelBadge.textContent = 'Lv.' + this.state.level;
        if (speciesName) speciesName.textContent = this.state.evolution_name || 'Baby';

        const xpPercent = (this.state.xp / this.state.xp_to_next_level) * 100;
        if (xpBar) xpBar.style.width = xpPercent + '%';
        if (xpText) xpText.textContent = `${this.state.xp}/${this.state.xp_to_next_level} XP`;
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
            'hungry': '😋'
        };

        if (moodEmoji) moodEmoji.textContent = moodEmojis[this.state.mood] || '😊';
        if (moodText) moodText.textContent = this.state.mood || 'Content';
    }

    /**
     * Update animation based on mood
     */
    updateAnimation() {
        const moodAnimations = {
            'happy': 'bounce',
            'excited': 'bounce',
            'ecstatic': 'wobble',
            'sleepy': 'sleep',
            'sad': 'idle',
            'worried': 'idle',
            'hungry': 'wobble'
        };

        const animation = moodAnimations[this.state.mood] || 'idle';
        this.renderer.setAnimation(animation);
    }

    /**
     * Play a temporary animation
     */
    playAnimation(animationName) {
        const canvas = document.getElementById('pet-canvas');
        if (!canvas) return;

        canvas.classList.add('animating', animationName);

        setTimeout(() => {
            canvas.classList.remove('animating', animationName);
        }, 1000);
    }

    /**
     * Stop an animation
     */
    stopAnimation(animationName) {
        const canvas = document.getElementById('pet-canvas');
        if (!canvas) return;

        canvas.classList.remove('animating', animationName);
    }

    /**
     * Show speech bubble
     */
    showSpeech(text, duration = 2000) {
        const bubble = document.getElementById('speech-bubble');
        const speechText = document.getElementById('speech-text');

        if (!bubble || !speechText) return;

        speechText.textContent = text;
        bubble.classList.remove('hidden');

        setTimeout(() => {
            bubble.classList.add('hidden');
        }, duration);
    }

    /**
     * Show level up notification
     */
    showLevelUp(level) {
        const notification = document.getElementById('levelup-notification');
        const levelText = document.getElementById('levelup-text');

        if (!notification) return;

        if (levelText) levelText.textContent = `Level ${level}!`;
        notification.classList.remove('hidden');

        setTimeout(() => {
            notification.classList.add('hidden');
        }, 3000);
    }

    /**
     * Show achievement notification
     */
    showAchievement(achievement) {
        const notification = document.getElementById('achievement-notification');
        const nameEl = document.getElementById('achievement-name');

        if (!notification) return;

        if (nameEl) nameEl.textContent = achievement.name || 'Achievement!';
        notification.classList.remove('hidden');

        setTimeout(() => {
            notification.classList.add('hidden');
        }, 3000);
    }

    /**
     * Send message to extension
     */
    async sendMessage(message) {
        if (typeof vscode !== 'undefined' && vscode.postMessage) {
            return new Promise((resolve) => {
                const listener = (event) => {
                    if (event.data.type === message.type + '_response') {
                        vscode.removeEventListener('message', listener);
                        resolve(event.data);
                    }
                };
                vscode.addEventListener('message', listener);
                vscode.postMessage(message);
            });
        }
        return null;
    }

    /**
     * Set interaction cooldown
     */
    setCooldown() {
        this.interactionCooldown = true;
        setTimeout(() => {
            this.interactionCooldown = false;
        }, this.cooldownTime);
    }

    /**
     * Clean up
     */
    destroy() {
        // Remove event listeners
        const feedBtn = document.getElementById('btn-feed');
        const playBtn = document.getElementById('btn-play');
        const sleepBtn = document.getElementById('btn-sleep');
        const canvas = document.getElementById('pet-canvas');

        [feedBtn, playBtn, sleepBtn, canvas].forEach(el => {
            if (el) el.replaceWith(el.cloneNode(true));
        });
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PetInteraction;
}
