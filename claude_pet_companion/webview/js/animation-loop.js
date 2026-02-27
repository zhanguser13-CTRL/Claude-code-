/**
 * AnimationLoop - Manages the animation frame loop
 *
 * Coordinates all animated elements in the pet webview.
 */

class AnimationLoop {
    constructor() {
        this.isRunning = false;
        this.animationFrame = null;
        this.lastTime = 0;
        this.deltaTime = 0;

        // Registered renderers
        this.renderers = [];

        // Animation callbacks
        this.onUpdate = null;
        this.onFixedUpdate = null;

        // FPS tracking
        this.fps = 0;
        this.frameCount = 0;
        this.fpsUpdateTime = 0;
    }

    /**
     * Start the animation loop
     */
    start() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.lastTime = performance.now();
        this.animate(this.lastTime);
    }

    /**
     * Stop the animation loop
     */
    stop() {
        this.isRunning = false;
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
    }

    /**
     * Main animation loop
     */
    animate(currentTime) {
        if (!this.isRunning) return;

        // Calculate delta time
        this.deltaTime = currentTime - this.lastTime;
        this.lastTime = currentTime;

        // Update FPS counter
        this.frameCount++;
        if (currentTime - this.fpsUpdateTime >= 1000) {
            this.fps = this.frameCount;
            this.frameCount = 0;
            this.fpsUpdateTime = currentTime;
        }

        // Call update callbacks
        if (this.onUpdate) {
            this.onUpdate(this.deltaTime, currentTime);
        }

        // Render all registered renderers
        for (const renderer of this.renderers) {
            if (renderer && typeof renderer.render === 'function') {
                renderer.render(currentTime);
            }
        }

        // Schedule next frame
        this.animationFrame = requestAnimationFrame(this.animate.bind(this));
    }

    /**
     * Register a renderer to be called each frame
     */
    registerRenderer(renderer) {
        if (!this.renderers.includes(renderer)) {
            this.renderers.push(renderer);
        }
    }

    /**
     * Unregister a renderer
     */
    unregisterRenderer(renderer) {
        const index = this.renderers.indexOf(renderer);
        if (index > -1) {
            this.renderers.splice(index, 1);
        }
    }

    /**
     * Set the update callback
     */
    setOnUpdate(callback) {
        this.onUpdate = callback;
    }

    /**
     * Set the fixed update callback (called at fixed intervals)
     */
    setOnFixedUpdate(callback, interval = 1000) {
        this.onFixedUpdate = {
            callback,
            interval,
            lastUpdate: 0
        };
    }

    /**
     * Get current FPS
     */
    getFPS() {
        return this.fps;
    }

    /**
     * Get delta time in seconds
     */
    getDeltaTime() {
        return this.deltaTime / 1000;
    }

    /**
     * Check if loop is running
     */
    isActive() {
        return this.isRunning;
    }
}

/**
 * TimedAnimation - Handles timed animation sequences
 */
class TimedAnimation {
    constructor(duration, onComplete = null) {
        this.duration = duration;
        this.elapsed = 0;
        this.isRunning = false;
        this.onComplete = onComplete;
        this.onUpdate = null;
    }

    /**
     * Start the animation
     */
    start() {
        this.isRunning = true;
        this.elapsed = 0;
        this.startTime = performance.now();
    }

    /**
     * Update the animation
     */
    update(deltaTime) {
        if (!this.isRunning) return false;

        this.elapsed += deltaTime;
        const progress = Math.min(this.elapsed / this.duration, 1);

        if (this.onUpdate) {
            this.onUpdate(progress, this.elapsed);
        }

        if (progress >= 1) {
            this.isRunning = false;
            if (this.onComplete) {
                this.onComplete();
            }
            return false;
        }

        return true;
    }

    /**
     * Stop the animation
     */
    stop() {
        this.isRunning = false;
    }

    /**
     * Reset the animation
     */
    reset() {
        this.elapsed = 0;
        this.isRunning = false;
    }

    /**
     * Get animation progress (0-1)
     */
    getProgress() {
        return Math.min(this.elapsed / this.duration, 1);
    }

    /**
     * Check if animation is complete
     */
    isComplete() {
        return this.elapsed >= this.duration;
    }
}

/**
 * Easing functions for animations
 */
const Easing = {
    linear: t => t,
    easeInQuad: t => t * t,
    easeOutQuad: t => t * (2 - t),
    easeInOutQuad: t => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
    easeInCubic: t => t * t * t,
    easeOutCubic: t => (--t) * t * t + 1,
    easeInOutCubic: t => t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1,
    easeOutBounce: t => {
        const n1 = 7.5625;
        const d1 = 2.75;
        if (t < 1 / d1) {
            return n1 * t * t;
        } else if (t < 2 / d1) {
            return n1 * (t -= 1.5 / d1) * t + 0.75;
        } else if (t < 2.5 / d1) {
            return n1 * (t -= 2.25 / d1) * t + 0.9375;
        } else {
            return n1 * (t -= 2.625 / d1) * t + 0.984375;
        }
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AnimationLoop, TimedAnimation, Easing };
}
