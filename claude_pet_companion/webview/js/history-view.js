/**
 * History View for Pet Companion
 *
 * Displays conversation history and allows searching/filtering.
 */

class HistoryView {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            onSelect: options.onSelect,
            onRestore: options.onRestore,
            onContinue: options.onContinue,
            onExport: options.onExport,
            ...options
        };

        this.conversations = [];
        this.selectedConversation = null;
        this.filter = '';
        this.filterType = 'all'; // all, successful, failed, recent
        this.loading = false;
        this.splitView = false;

        this.init();
    }

    init() {
        // Create the view structure
        this.container.innerHTML = this._getTemplate();

        // Cache elements
        this.searchInput = this.container.querySelector('#search-input');
        this.filterSelect = this.container.querySelector('#filter-select');
        this.conversationList = this.container.querySelector('#conversation-list');
        this.conversationDetail = this.container.querySelector('#conversation-detail');
        this.messagesList = this.container.querySelector('#messages-list');

        // Bind events
        this._bindEvents();

        // Load conversations
        this.loadConversations();
    }

    _getTemplate() {
        return `
            <div id="history-search">
                <input type="text" id="search-input" placeholder="Search conversations...">
                <select id="filter-select">
                    <option value="all">All</option>
                    <option value="successful">Successful</option>
                    <option value="recent">Recent (24h)</option>
                </select>
            </div>
            <div id="history-split">
                <div id="history-split-left" class="left-panel">
                    <div id="conversation-list">
                        <div class="loading-state">
                            <span class="loading-spinner"></span>
                            <span>Loading conversations...</span>
                        </div>
                    </div>
                </div>
                <div id="history-split-right" class="right-panel">
                    <div id="conversation-detail">
                        <div class="empty-state">
                            <div class="empty-state-icon">💬</div>
                            <div class="empty-state-text">Select a conversation to view details</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    _bindEvents() {
        // Search input
        this.searchInput.addEventListener('input', (e) => {
            this.filter = e.target.value;
            this._filterConversations();
        });

        // Filter select
        this.filterSelect.addEventListener('change', (e) => {
            this.filterType = e.target.value;
            this._filterConversations();
        });
    }

    async loadConversations() {
        this.loading = true;

        try {
            // Try to load from IPC client first
            if (typeof ipcClient !== 'undefined' && ipcClient.isConnected()) {
                this.conversations = await ipcClient.listConversations(100);
            } else if (typeof vscodeBridge !== 'undefined') {
                // Fall back to vscode bridge
                const result = await vscodeBridge.sendPetAction('list_conversations', { limit: 100 });
                this.conversations = result?.conversations || [];
            } else {
                // Dev mode - use mock data
                this.conversations = this._getMockConversations();
            }

            this._renderConversationList();
        } catch (error) {
            console.error('Failed to load conversations:', error);
            this._showError('Failed to load conversations');
        }

        this.loading = false;
    }

    _filterConversations() {
        let filtered = [...this.conversations];

        // Apply text filter
        if (this.filter) {
            const filterLower = this.filter.toLowerCase();
            filtered = filtered.filter(conv =>
                conv.title?.toLowerCase().includes(filterLower) ||
                conv.summary?.toLowerCase().includes(filterLower) ||
                conv.tags?.some(tag => tag.toLowerCase().includes(filterLower))
            );
        }

        // Apply type filter
        if (this.filterType === 'successful') {
            filtered = filtered.filter(conv => conv.success !== false);
        } else if (this.filterType === 'recent') {
            const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
            filtered = filtered.filter(conv => {
                const started = new Date(conv.started_at).getTime();
                return started > dayAgo;
            });
        }

        this._renderConversationList(filtered);
    }

    _renderConversationList(conversations = this.conversations) {
        if (!conversations || conversations.length === 0) {
            this.conversationList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <div class="empty-state-text">No conversations found</div>
                </div>
            `;
            return;
        }

        this.conversationList.innerHTML = conversations.map(conv => this._renderConversationItem(conv)).join('');

        // Bind click events
        this.conversationList.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', () => {
                const convId = item.dataset.id;
                this.selectConversation(convId);
            });
        });
    }

    _renderConversationItem(conv) {
        const date = new Date(conv.started_at);
        const dateStr = this._formatDate(date);
        const preview = conv.summary || 'No summary available';
        const tags = (conv.tags || []).slice(0, 3).map(tag =>
            `<span class="conversation-tag">${this._escapeHtml(tag)}</span>`
        ).join('');

        return `
            <div class="conversation-item" data-id="${conv.id}">
                <div class="conversation-title">
                    <span>${this._escapeHtml(conv.title || 'Untitled')}</span>
                </div>
                <div class="conversation-date">${dateStr}</div>
                <div class="conversation-preview">${this._escapeHtml(preview)}</div>
                ${tags ? `<div class="conversation-tags">${tags}</div>` : ''}
            </div>
        `;
    }

    async selectConversation(convId) {
        // Update selection UI
        this.conversationList.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.toggle('selected', item.dataset.id === convId);
        });

        // Find conversation
        const conv = this.conversations.find(c => c.id === convId);
        if (!conv) return;

        this.selectedConversation = conv;

        // Load full conversation details
        this._renderConversationDetail(conv);

        // Trigger callback
        if (this.options.onSelect) {
            this.options.onSelect(conv);
        }
    }

    async _renderConversationDetail(conv) {
        // Get full conversation if needed
        let fullConv = conv;

        if (typeof ipcClient !== 'undefined' && ipcClient.isConnected()) {
            fullConv = await ipcClient.getConversation(conv.id);
        } else if (typeof vscodeBridge !== 'undefined') {
            const result = await vscodeBridge.sendPetAction('get_conversation', { conversation_id: conv.id });
            fullConv = result;
        }

        // Build detail HTML
        const startedAt = new Date(fullConv.started_at || conv.started_at);
        const endedAt = fullConv.ended_at ? new Date(fullConv.ended_at) : null;
        const duration = endedAt ? Math.round((endedAt - startedAt) / 60000) : null;

        this.conversationDetail.innerHTML = `
            <div class="detail-header">
                <div class="detail-title">${this._escapeHtml(fullConv.title || conv.title)}</div>
                <div class="detail-meta">
                    <span>📅 ${this._formatDate(startedAt)}</span>
                    ${duration ? `<span>⏱️ ${duration} min</span>` : ''}
                    ${fullConv.messages ? `<span>💬 ${fullConv.messages.length} messages</span>` : ''}
                </div>
                <div class="detail-actions">
                    <button class="detail-btn primary" id="btn-restore" title="Restore context to new conversation">
                        ↺ Restore Context
                    </button>
                    <button class="detail-btn" id="btn-continue" title="Continue this conversation">
                        ▶ Continue
                    </button>
                    <button class="detail-btn" id="btn-export" title="Export conversation">
                        ⬇ Export
                    </button>
                </div>
            </div>
            <div id="messages-list">
                ${this._renderMessages(fullConv.messages || [])}
            </div>
        `;

        // Bind action buttons
        const restoreBtn = this.conversationDetail.querySelector('#btn-restore');
        const continueBtn = this.conversationDetail.querySelector('#btn-continue');
        const exportBtn = this.conversationDetail.querySelector('#btn-export');

        if (restoreBtn) {
            restoreBtn.addEventListener('click', () => this._handleRestore(conv.id));
        }
        if (continueBtn) {
            continueBtn.addEventListener('click', () => this._handleContinue(conv.id));
        }
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this._handleExport(conv.id));
        }
    }

    _renderMessages(messages) {
        if (!messages || messages.length === 0) {
            return `
                <div class="empty-state">
                    <div class="empty-state-text">No messages in this conversation</div>
                </div>
            `;
        }

        return messages.map(msg => {
            const time = new Date(msg.timestamp).toLocaleTimeString();
            return `
                <div class="message-item ${msg.role}">
                    <div class="message-header">
                        <span class="message-role ${msg.role}">${this._formatRole(msg.role)}</span>
                        <span class="message-time">${time}</span>
                    </div>
                    <div class="message-content">${this._escapeHtml(msg.content)}</div>
                </div>
            `;
        }).join('');
    }

    async _handleRestore(convId) {
        if (this.options.onRestore) {
            this.options.onRestore(convId);
            return;
        }

        // Default behavior: get context and display
        try {
            let context = '';

            if (typeof ipcClient !== 'undefined' && ipcClient.isConnected()) {
                context = await ipcClient.restoreContext(convId);
            } else if (typeof vscodeBridge !== 'undefined') {
                const result = await vscodeBridge.sendPetAction('restore_context', {
                    conversation_id: convId
                });
                context = result?.context || '';
            }

            if (context) {
                // Copy to clipboard
                navigator.clipboard.writeText(context);
                this._showNotification('Context copied to clipboard!');
            }
        } catch (error) {
            console.error('Failed to restore context:', error);
            this._showNotification('Failed to restore context');
        }
    }

    async _handleContinue(convId) {
        if (this.options.onContinue) {
            this.options.onContinue(convId);
            return;
        }

        // Default: switch to pet tab with context
        try {
            let context = '';

            if (typeof ipcClient !== 'undefined' && ipcClient.isConnected()) {
                const result = await ipcClient.restoreContext(convId, false);
                context = result?.context || '';
            }

            // Switch to pet tab
            document.querySelector('.tab[data-tab="pet"]')?.click();

            this._showNotification('Conversation context loaded!');
        } catch (error) {
            console.error('Failed to continue:', error);
            this._showNotification('Failed to continue conversation');
        }
    }

    async _handleExport(convId) {
        if (this.options.onExport) {
            this.options.onExport(convId);
            return;
        }

        // Default: export as JSON
        try {
            const conv = this.conversations.find(c => c.id === convId);
            if (!conv) return;

            const json = JSON.stringify(conv, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `conversation-${convId}.json`;
            a.click();

            URL.revokeObjectURL(url);
            this._showNotification('Conversation exported!');
        } catch (error) {
            console.error('Failed to export:', error);
            this._showNotification('Failed to export conversation');
        }
    }

    _showError(message) {
        this.conversationList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">⚠️</div>
                <div class="empty-state-text">${this._escapeHtml(message)}</div>
            </div>
        `;
    }

    _showNotification(message) {
        // Create a temporary notification
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
        }, 3000);
    }

    _formatDate(date) {
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
        if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;

        return date.toLocaleDateString();
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

    _getMockConversations() {
        // Mock data for development
        return [
            {
                id: 'mock-1',
                title: 'Fixed authentication bug',
                started_at: new Date(Date.now() - 3600000).toISOString(),
                ended_at: new Date(Date.now() - 3000000).toISOString(),
                summary: 'Resolved JWT token validation issue in login flow',
                tags: ['bugfix', 'auth'],
                success: true,
                messages: [
                    { role: 'user', content: 'The login is failing with token error', timestamp: new Date().toISOString() },
                    { role: 'assistant', content: 'Let me check the auth module...', timestamp: new Date().toISOString() }
                ]
            },
            {
                id: 'mock-2',
                title: 'Added user profile feature',
                started_at: new Date(Date.now() - 86400000).toISOString(),
                summary: 'Implemented profile editing with image upload',
                tags: ['feature', 'ui'],
                success: true,
                messages: []
            }
        ];
    }

    refresh() {
        this.loadConversations();
    }

    destroy() {
        // Cleanup
        this.conversationList.innerHTML = '';
        this.conversationDetail.innerHTML = '';
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.HistoryView = HistoryView;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = HistoryView;
}
