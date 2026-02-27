/**
 * IPC Client for Pet Companion Webview
 *
 * WebSocket-based client for communicating with the pet daemon.
 */

class PetIPCClient {
    constructor(options = {}) {
        this.options = {
            host: options.host || '127.0.0.1',
            port: options.port || 15340,
            autoConnect: true,
            reconnectInterval: 5000,
            ...options
        };

        this.ws = null;
        this.connected = false;
        this.connecting = false;

        // Message handlers
        this.messageHandlers = new Map();
        this.pendingRequests = new Map();
        this.requestId = 0;

        // Auto-connect
        if (this.options.autoConnect) {
            this.connect();
        }
    }

    connect() {
        if (this.connected || this.connecting) {
            return Promise.resolve();
        }

        this.connecting = true;

        return new Promise((resolve, reject) => {
            try {
                const url = `ws://${this.options.host}:${this.options.port}`;
                console.log(`[IPC] Connecting to ${url}...`);

                this.ws = new WebSocket(url);

                this.ws.onopen = () => {
                    console.log('[IPC] Connected');
                    this.connected = true;
                    this.connecting = false;

                    // Send hello handshake
                    this._sendHello();

                    resolve();
                };

                this.ws.onmessage = (event) => {
                    this._handleMessage(event.data);
                };

                this.ws.onerror = (error) => {
                    console.error('[IPC] Error:', error);
                };

                this.ws.onclose = () => {
                    console.log('[IPC] Disconnected');
                    this.connected = false;
                    this.connecting = false;

                    // Auto-reconnect
                    if (this.options.autoConnect) {
                        setTimeout(() => {
                            if (!this.connected && !this.connecting) {
                                this.connect();
                            }
                        }, this.options.reconnectInterval);
                    }
                };

            } catch (error) {
                this.connecting = false;
                reject(error);
            }
        });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }

    _sendHello() {
        this.send({
            type: 'hello',
            payload: {
                client_name: 'webview',
                version: '1.0.0',
                capabilities: ['status', 'actions', 'conversations']
            }
        });
    }

    send(message) {
        if (!this.connected) {
            console.warn('[IPC] Not connected, message not sent');
            return false;
        }

        try {
            const data = JSON.stringify(message);
            this.ws.send(data);
            return true;
        } catch (error) {
            console.error('[IPC] Send error:', error);
            return false;
        }
    }

    sendRequest(type, payload = {}, timeout = 5000) {
        return new Promise((resolve, reject) => {
            if (!this.connected) {
                reject(new Error('Not connected'));
                return;
            }

            const requestId = ++this.requestId;
            const message = {
                type,
                id: `req-${requestId}`,
                payload
            };

            // Set up timeout
            const timer = setTimeout(() => {
                this.pendingRequests.delete(requestId);
                reject(new Error('Request timeout'));
            }, timeout);

            // Store pending request
            this.pendingRequests.set(requestId, {
                resolve,
                reject,
                timer,
                type
            });

            // Send message
            this.send(message);
        });
    }

    _handleMessage(data) {
        try {
            const message = JSON.parse(data);

            // Check if it's a response to a pending request
            if (message.type && message.type.endsWith('_response')) {
                // Try to match with pending request
                for (const [reqId, req] of this.pendingRequests) {
                    if (message.type === `${req.type}_response`) {
                        clearTimeout(req.timer);
                        this.pendingRequests.delete(reqId);
                        req.resolve(message.payload);
                        return;
                    }
                }
            }

            // Check for matching request ID
            if (message.id) {
                for (const [reqId, req] of this.pendingRequests) {
                    if (message.id.includes(reqId.toString()) ||
                        message.payload?.request_id === reqId) {
                        clearTimeout(req.timer);
                        this.pendingRequests.delete(reqId);

                        if (message.type === 'error') {
                            req.reject(new Error(message.payload?.error || 'Unknown error'));
                        } else {
                            req.resolve(message.payload);
                        }
                        return;
                    }
                }
            }

            // Call registered handlers
            const handlers = this.messageHandlers.get(message.type) || [];
            for (const handler of handlers) {
                try {
                    handler(message);
                } catch (error) {
                    console.error('[IPC] Handler error:', error);
                }
            }

        } catch (error) {
            console.error('[IPC] Message parse error:', error);
        }
    }

    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }

    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index !== -1) {
                handlers.splice(index, 1);
            }
        }
    }

    // Status methods
    async getStatus() {
        return this.sendRequest('status');
    }

    // Action methods
    async sendAction(action, data = {}) {
        return this.sendRequest('action', { action, ...data });
    }

    // Conversation methods
    async startConversation(title, tags = []) {
        return this.sendRequest('conversation_start', { title, tags });
    }

    async addConversationMessage(conversationId, role, content, data = {}) {
        return this.sendRequest('conversation_message', {
            conversation_id: conversationId,
            role,
            content,
            ...data
        });
    }

    async listConversations(limit = 50) {
        const response = await this.sendRequest('conversation_list', { limit });
        return response?.conversations || [];
    }

    async getConversation(conversationId) {
        return this.sendRequest('conversation_get', { conversation_id: conversationId });
    }

    async searchConversations(query, limit = 20) {
        return this.sendRequest('conversation_search', { query, limit });
    }

    // Context methods
    async restoreContext(conversationId, includeMessages = true) {
        const response = await this.sendRequest('restore_context', {
            conversation_id: conversationId,
            include_messages: includeMessages
        });
        return response?.context || '';
    }

    // Utility methods
    isConnected() {
        return this.connected;
    }

    // Feed, play, sleep shortcuts
    async feed() {
        return this.sendAction('feed');
    }

    async play() {
        return this.sendAction('play');
    }

    async sleep() {
        return this.sendAction('sleep');
    }
}

// Create global instance (will try to connect to IPC server)
let ipcClient = null;

function initIPC() {
    try {
        ipcClient = new PetIPCClient({
            autoConnect: true
        });
    } catch (error) {
        console.warn('[IPC] Failed to initialize:', error);
        // Fall back to vscode bridge
        ipcClient = null;
    }
}

// Initialize on load
if (typeof window !== 'undefined') {
    // Don't auto-initialize - let the app decide
    window.initPetIPC = initIPC;
    window.PetIPCClient = PetIPCClient;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PetIPCClient, initIPC };
}
