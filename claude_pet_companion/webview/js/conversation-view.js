/**
 * Conversation Detail View for Pet Companion
 *
 * Detailed view of a single conversation with restore actions.
 */

class ConversationDetailView {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            onRestore: options.onRestore,
            onContinue: options.onContinue,
            onExport: options.onExport,
            onClose: options.onClose,
            ...options
        };

        this.conversation = null;
        this.context = null;

        this.init();
    }

    init() {
        // Create the view structure
        this.container.innerHTML = this._getTemplate();

        // Cache elements
        this.detailContainer = this.container.querySelector('.detail-content');
        this.actionsContainer = this.container.querySelector('.detail-actions');
        this.messagesContainer = this.container.querySelector('.detail-messages');
        this.contextContainer = this.container.querySelector('.detail-context');

        // Bind events
        this._bindEvents();
    }

    _getTemplate() {
        return `
            <div class="conversation-detail-wrapper">
                <div class="detail-header">
                    <button class="detail-close-btn" id="btn-close">← Back</button>
                    <h2 class="detail-title" id="detail-title">Conversation</h2>
                    <div class="detail-meta" id="detail-meta"></div>
                </div>

                <div class="detail-actions" id="detail-actions">
                    <button class="detail-btn primary" id="btn-restore" title="Restore context">
                        ↺ Restore Context
                    </button>
                    <button class="detail-btn" id="btn-continue" title="Continue conversation">
                        ▶ Continue
                    </button>
                    <button class="detail-btn" id="btn-export" title="Export">
                        ⬇ Export
                    </button>
                    <button class="detail-btn" id="btn-copy" title="Copy to clipboard">
                        📋 Copy
                    </button>
                </div>

                <div class="detail-content">
                    <div class="detail-section">
                        <h3>Context Preview</h3>
                        <div class="detail-context" id="detail-context">
                            <div class="context-placeholder">Loading context...</div>
                        </div>
                    </div>

                    <div class="detail-section">
                        <h3>Messages</h3>
                        <div class="detail-messages" id="detail-messages">
                            <div class="loading-state">
                                <span class="loading-spinner"></span>
                                <span>Loading messages...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    _bindEvents() {
        // Close button
        this.container.querySelector('#btn-close')?.addEventListener('click', () => {
            if (this.options.onClose) {
                this.options.onClose();
            }
        });

        // Action buttons
        this.container.querySelector('#btn-restore')?.addEventListener('click', () => {
            this._handleRestore();
        });

        this.container.querySelector('#btn-continue')?.addEventListener('click', () => {
            this._handleContinue();
        });

        this.container.querySelector('#btn-export')?.addEventListener('click', () => {
            this._handleExport();
        });

        this.container.querySelector('#btn-copy')?.addEventListener('click', () => {
            this._handleCopy();
        });
    }

    async loadConversation(convId) {
        try {
            // Try to get full conversation
            let conv = null;

            if (typeof ipcClient !== 'undefined' && ipcClient.isConnected()) {
                conv = await ipcClient.getConversation(convId);
            } else if (typeof vscodeBridge !== 'undefined') {
                const result = await vscodeBridge.sendPetAction('get_conversation', {
                    conversation_id: convId
                });
                conv = result;
            }

            if (conv) {
                this.conversation = conv;
                this._render();
                await this._loadContext();
            } else {
                this._showError('Conversation not found');
            }
        } catch (error) {
            console.error('Failed to load conversation:', error);
            this._showError('Failed to load conversation');
        }
    }

    async _loadContext() {
        if (!this.conversation) return;

        try {
            let context = '';

            if (typeof ipcClient !== 'undefined' && ipcClient.isConnected()) {
                context = await ipcClient.restoreContext(this.conversation.id);
            } else if (typeof vscodeBridge !== 'undefined') {
                const result = await vscodeBridge.sendPetAction('restore_context', {
                    conversation_id: this.conversation.id
                });
                context = result?.context || '';
            }

            this.context = context;

            // Render context preview
            this.contextContainer.innerHTML = `
                <pre class="context-preview">${this._escapeHtml(context.slice(0, 1000))}${context.length > 1000 ? '...' : ''}</pre>
            `;

        } catch (error) {
            console.error('Failed to load context:', error);
            this.contextContainer.innerHTML = '<div class="error">Failed to load context</div>';
        }
    }

    _render() {
        const conv = this.conversation;
        if (!conv) return;

        // Update header
        this.container.querySelector('#detail-title').textContent = conv.title || 'Untitled';

        const startedAt = new Date(conv.started_at);
        const endedAt = conv.ended_at ? new Date(conv.ended_at) : null;
        const duration = endedAt ? Math.round((endedAt - startedAt) / 60000) : null;

        this.container.querySelector('#detail-meta').innerHTML = `
            <span>📅 ${startedAt.toLocaleString()}</span>
            ${duration ? `<span>⏱️ ${duration} minutes</span>` : ''}
            ${conv.tags?.length ? `<span>🏷️ ${conv.tags.join(', ')}</span>` : ''}
        `;

        // Render messages
        this._renderMessages();
    }

    _renderMessages() {
        const messages = this.conversation?.messages || [];

        if (!messages.length) {
            this.messagesContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-text">No messages in this conversation</div>
                </div>
            `;
            return;
        }

        this.messagesContainer.innerHTML = messages.map(msg => {
            const time = new Date(msg.timestamp).toLocaleString();
            return `
                <div class="message-item ${msg.role}">
                    <div class="message-header">
                        <span class="message-role ${msg.role}">${this._formatRole(msg.role)}</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-content">${this._escapeHtml(msg.content)}</div>
                    ${msg.tool_used ? `<div class="message-tool">🔧 Used: ${this._escapeHtml(msg.tool_used)}</div>` : ''}
                </div>
            `;
        }).join('');
    }

    _handleRestore() {
        if (!this.context) {
            this._showNotification('No context available');
            return;
        }

        // Copy context to clipboard
        navigator.clipboard.writeText(this.context);
        this._showNotification('Context copied to clipboard! Paste it into your new conversation.');

        if (this.options.onRestore) {
            this.options.onRestore(this.conversation, this.context);
        }
    }

    _handleContinue() {
        // Switch to pet tab
        document.querySelector('.tab[data-tab="pet"]')?.click();

        // Copy context
        if (this.context) {
            navigator.clipboard.writeText(this.context);
            this._showNotification('Context loaded! Paste it to continue.');
        }

        if (this.options.onContinue) {
            this.options.onContinue(this.conversation);
        }
    }

    _handleExport() {
        if (!this.conversation) return;

        const json = JSON.stringify(this.conversation, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${this.conversation.id}.json`;
        a.click();

        URL.revokeObjectURL(url);
        this._showNotification('Conversation exported!');

        if (this.options.onExport) {
            this.options.onExport(this.conversation);
        }
    }

    _handleCopy() {
        if (!this.conversation) return;

        const text = this.context || JSON.stringify(this.conversation, null, 2);
        navigator.clipboard.writeText(text);
        this._showNotification('Copied to clipboard!');
    }

    _showError(message) {
        this.messagesContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <div class="empty-state-text">${this._escapeHtml(message)}</div>
            </div>
        `;
    }

    _showNotification(message) {
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
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    _formatRole(role) {
        const roles = {
            'user': '👤 User',
            'assistant': '🤖 Assistant',
            'system': '⚙️ System',
            'pet': '🐾 Pet'
        };
        return roles[role] || role;
    }

    _escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    destroy() {
        // Cleanup
        this.container.innerHTML = '';
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ConversationDetailView = ConversationDetailView;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = ConversationDetailView;
}
