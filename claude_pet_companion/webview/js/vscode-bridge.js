/**
 * VSCodeBridge - Bridge for communication between webview and VS Code extension
 *
 * Handles message passing and state management with the VS Code extension API.
 */

class VSCodeBridge {
    constructor() {
        this.vscode = null;
        this.messageHandlers = new Map();
        this.state = {};
        this.isConnected = false;

        this.init();
    }

    /**
     * Initialize the bridge
     */
    init() {
        // Check if running in VS Code webview
        if (typeof acquireVsCodeApi !== 'undefined') {
            this.vscode = acquireVsCodeApi();
            this.isConnected = true;

            // Load initial state
            this.loadState();

            // Setup message listener
            window.addEventListener('message', this.handleMessage.bind(this));

            // Notify extension that webview is ready
            this.postMessage({ type: 'ready' });
        } else {
            // Running in browser (development mode)
            console.log('Running in development mode (no VS Code API)');
            this.isConnected = false;

            // Use mock state for development
            this.state = this.getMockState();
        }
    }

    /**
     * Handle incoming messages from extension
     */
    handleMessage(event) {
        const message = event.data;

        // Call registered handler for this message type
        if (message.type && this.messageHandlers.has(message.type)) {
            const handlers = this.messageHandlers.get(message.type);
            handlers.forEach(handler => handler(message));
        }

        // Handle state updates
        if (message.type === 'stateUpdate') {
            this.state = { ...this.state, ...message.state };
        }
    }

    /**
     * Post a message to the extension
     */
    postMessage(message) {
        if (this.vscode) {
            this.vscode.postMessage(message);
        } else {
            // Development mode: simulate response
            console.log('[Dev Mode] Posting message:', message);
            this.simulateResponse(message);
        }
    }

    /**
     * Register a message handler
     */
    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }

    /**
     * Unregister a message handler
     */
    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }

    /**
     * Get current state
     */
    getState() {
        return { ...this.state };
    }

    /**
     * Update state (syncs with extension)
     */
    setState(newState) {
        this.state = { ...this.state, ...newState };

        if (this.vscode) {
            // Persist to VS Code state (survives webview hide/show)
            const currentVsCodeState = this.vscode.getState() || {};
            this.vscode.setState({ ...currentVsCodeState, petState: this.state });
        }
    }

    /**
     * Load state from VS Code
     */
    loadState() {
        if (this.vscode) {
            const vscodeState = this.vscode.getState();
            if (vscodeState && vscodeState.petState) {
                this.state = vscodeState.petState;
            }
        }
    }

    /**
     * Get webview state (position, etc.)
     */
    getWebviewState() {
        if (this.vscode) {
            return this.vscode.getState() || {};
        }
        return {};
    }

    /**
     * Set webview state
     */
    setWebviewState(state) {
        if (this.vscode) {
            const current = this.vscode.getState() || {};
            this.vscode.setState({ ...current, ...state });
        }
    }

    /**
     * Send pet action command
     */
    async sendPetAction(action, data = {}) {
        return new Promise((resolve) => {
            const messageType = action + 'Response';

            const handler = (message) => {
                this.off(messageType, handler);
                resolve(message.data);
            };

            this.on(messageType, handler);
            this.postMessage({
                type: action,
                data: data
            });
        });
    }

    /**
     * Request pet state from extension
     */
    async requestState() {
        if (!this.isConnected) {
            return this.getMockState();
        }

        return new Promise((resolve) => {
            const handler = (message) => {
                this.off('stateResponse', handler);
                resolve(message.data);
            };

            this.on('stateResponse', handler);
            this.postMessage({ type: 'getState' });
        });
    }

    /**
     * Get mock state for development
     */
    getMockState() {
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
     * Simulate response for development
     */
    simulateResponse(message) {
        setTimeout(() => {
            const mockResponse = {
                type: message.type + 'Response',
                data: this.getMockResponseFor(message)
            };

            if (this.messageHandlers.has(mockResponse.type)) {
                const handlers = this.messageHandlers.get(mockResponse.type);
                handlers.forEach(handler => handler(mockResponse));
            }
        }, 100);
    }

    /**
     * Get mock response for a message
     */
    getMockResponseFor(message) {
        const mockState = this.getMockState();

        switch (message.type) {
            case 'feed':
                return {
                    state: {
                        ...mockState,
                        hunger: Math.min(100, mockState.hunger + 30)
                    },
                    message: 'Yummy!'
                };
            case 'play':
                return {
                    state: {
                        ...mockState,
                        happiness: Math.min(100, mockState.happiness + 25)
                    },
                    message: 'Wheee!'
                };
            case 'sleep':
                return {
                    state: {
                        ...mockState,
                        is_sleeping: !mockState.is_sleeping
                    },
                    message: mockState.is_sleeping ? 'Wake up!' : 'Zzz...'
                };
            default:
                return mockState;
        }
    }

    /**
     * Check if connected to VS Code
     */
    connected() {
        return this.isConnected;
    }
}

// Create global instance
const vscodeBridge = new VSCodeBridge();

// Also expose as global for inline scripts
if (typeof window !== 'undefined') {
    window.vscode = vscodeBridge;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { VSCodeBridge, vscodeBridge };
}
