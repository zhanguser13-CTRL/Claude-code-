/**
 * DragHandler - Handles mouse drag interactions for the pet container
 *
 * Allows the pet to be dragged around the screen.
 */

class DragHandler {
    constructor(element, options = {}) {
        this.element = element;
        this.options = {
            savePosition: true,
            constrainToWindow: true,
            onDragStart: null,
            onDrag: null,
            onDragEnd: null,
            ...options
        };

        this.isDragging = false;
        this.dragStarted = false;
        this.startX = 0;
        this.startY = 0;
        this.offsetX = 0;
        this.offsetY = 0;

        // Current position
        this.position = { left: 100, top: 100 };

        this.init();
    }

    /**
     * Initialize drag handlers
     */
    init() {
        // Mouse events
        this.element.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mousemove', this.handleMouseMove.bind(this));
        document.addEventListener('mouseup', this.handleMouseUp.bind(this));

        // Touch events
        this.element.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this));

        // Load saved position
        this.loadPosition();
    }

    /**
     * Handle mouse down event
     */
    handleMouseDown(e) {
        // Only drag if clicking on the pet canvas, not buttons
        if (e.target.closest('button')) return;

        this.isDragging = true;
        this.dragStarted = false;

        const rect = this.element.getBoundingClientRect();
        this.offsetX = e.clientX - rect.left;
        this.offsetY = e.clientY - rect.top;

        this.startX = e.clientX;
        this.startY = e.clientY;

        e.preventDefault();
    }

    /**
     * Handle mouse move event
     */
    handleMouseMove(e) {
        if (!this.isDragging) return;

        // Check if actually dragging (moved more than threshold)
        if (!this.dragStarted) {
            const dx = e.clientX - this.startX;
            const dy = e.clientY - this.startY;
            if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
                this.dragStarted = true;
                this.element.style.cursor = 'grabbing';

                if (this.options.onDragStart) {
                    this.options.onDragStart(this.position);
                }
            }
        }

        if (!this.dragStarted) return;

        // Calculate new position
        let newX = e.clientX - this.offsetX;
        let newY = e.clientY - this.offsetY;

        // Constrain to window if option is set
        if (this.options.constrainToWindow) {
            const rect = this.element.getBoundingClientRect();
            newX = Math.max(0, Math.min(newX, window.innerWidth - rect.width));
            newY = Math.max(0, Math.min(newY, window.innerHeight - rect.height));
        }

        // Update position
        this.updatePosition(newX, newY);

        if (this.options.onDrag) {
            this.options.onDrag(this.position);
        }
    }

    /**
     * Handle mouse up event
     */
    handleMouseUp(e) {
        if (!this.isDragging) return;

        if (this.dragStarted) {
            if (this.options.onDragEnd) {
                this.options.onDragEnd(this.position);
            }

            // Save position
            if (this.options.savePosition) {
                this.savePosition();
            }
        }

        this.isDragging = false;
        this.dragStarted = false;
        this.element.style.cursor = '';
    }

    /**
     * Handle touch start event
     */
    handleTouchStart(e) {
        if (e.target.closest('button')) return;

        const touch = e.touches[0];
        this.isDragging = true;
        this.dragStarted = false;

        const rect = this.element.getBoundingClientRect();
        this.offsetX = touch.clientX - rect.left;
        this.offsetY = touch.clientY - rect.top;

        this.startX = touch.clientX;
        this.startY = touch.clientY;
    }

    /**
     * Handle touch move event
     */
    handleTouchMove(e) {
        if (!this.isDragging) return;
        e.preventDefault();

        const touch = e.touches[0];

        if (!this.dragStarted) {
            const dx = touch.clientX - this.startX;
            const dy = touch.clientY - this.startY;
            if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
                this.dragStarted = true;
                if (this.options.onDragStart) {
                    this.options.onDragStart(this.position);
                }
            }
        }

        if (!this.dragStarted) return;

        let newX = touch.clientX - this.offsetX;
        let newY = touch.clientY - this.offsetY;

        if (this.options.constrainToWindow) {
            const rect = this.element.getBoundingClientRect();
            newX = Math.max(0, Math.min(newX, window.innerWidth - rect.width));
            newY = Math.max(0, Math.min(newY, window.innerHeight - rect.height));
        }

        this.updatePosition(newX, newY);
    }

    /**
     * Handle touch end event
     */
    handleTouchEnd(e) {
        if (!this.isDragging) return;

        if (this.dragStarted) {
            if (this.options.onDragEnd) {
                this.options.onDragEnd(this.position);
            }

            if (this.options.savePosition) {
                this.savePosition();
            }
        }

        this.isDragging = false;
        this.dragStarted = false;
    }

    /**
     * Update the element position
     */
    updatePosition(x, y) {
        this.position.left = x;
        this.position.top = y;
        this.element.style.position = 'fixed';
        this.element.style.left = x + 'px';
        this.element.style.top = y + 'px';
    }

    /**
     * Set position programmatically
     */
    setPosition(x, y) {
        this.updatePosition(x, y);
    }

    /**
     * Get current position
     */
    getPosition() {
        return { ...this.position };
    }

    /**
     * Save position to VS Code state
     */
    savePosition() {
        if (typeof vscode !== 'undefined' && vscode.setState) {
            vscode.setState({
                petPosition: this.position
            });
        }
    }

    /**
     * Load position from VS Code state
     */
    loadPosition() {
        if (typeof vscode !== 'undefined' && vscode.getState) {
            const state = vscode.getState();
            if (state && state.petPosition) {
                this.updatePosition(
                    state.petPosition.left || 100,
                    state.petPosition.top || 100
                );
            }
        }
    }

    /**
     * Reset to default position
     */
    reset() {
        this.updatePosition(100, 100);
        this.savePosition();
    }

    /**
     * Clean up event listeners
     */
    destroy() {
        this.element.removeEventListener('mousedown', this.handleMouseDown);
        document.removeEventListener('mousemove', this.handleMouseMove);
        document.removeEventListener('mouseup', this.handleMouseUp);
        this.element.removeEventListener('touchstart', this.handleTouchStart);
        document.removeEventListener('touchmove', this.handleTouchMove);
        document.removeEventListener('touchend', this.handleTouchEnd);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DragHandler;
}
