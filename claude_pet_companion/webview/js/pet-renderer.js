/**
 * PetRenderer - Canvas rendering engine for pixel art pet
 *
 * Handles rendering the pet sprite to canvas with pixel-perfect scaling.
 */

class PetRenderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');

        // Disable image smoothing for pixel-perfect rendering
        this.ctx.imageSmoothingEnabled = false;
        this.ctx.mozImageSmoothingEnabled = false;
        this.ctx.webkitImageSmoothingEnabled = false;
        this.ctx.msImageSmoothingEnabled = false;

        // Canvas size (internal resolution)
        this.width = canvas.width;
        this.height = canvas.height;

        // Current animation state
        this.currentAnimation = 'idle';
        this.currentFrame = 0;
        this.frameCount = 0;
        this.fps = 8; // Pixel art runs at 8 FPS
        this.lastFrameTime = 0;

        // Sprite data
        this.spriteData = null;
        this.currentPalette = 'default';

        // Render callbacks
        this.onFrameUpdate = null;
    }

    /**
     * Set the sprite data for rendering
     */
    setSpriteData(spriteData) {
        this.spriteData = spriteData;
    }

    /**
     * Set the current animation
     */
    setAnimation(animationName) {
        if (this.spriteData && this.spriteData.animations && this.spriteData.animations[animationName]) {
            this.currentAnimation = animationName;
            this.currentFrame = 0;
        }
    }

    /**
     * Set the color palette
     */
    setPalette(palette) {
        this.currentPalette = palette;
    }

    /**
     * Get the current animation frame data
     */
    getCurrentFrame() {
        if (!this.spriteData || !this.spriteData.animations) {
            return null;
        }

        const animation = this.spriteData.animations[this.currentAnimation];
        if (!animation || !animation.frames) {
            return null;
        }

        return animation.frames[this.currentFrame % animation.frames.length];
    }

    /**
     * Clear the canvas
     */
    clear() {
        this.ctx.clearRect(0, 0, this.width, this.height);
    }

    /**
     * Draw a single pixel
     */
    drawPixel(x, y, color) {
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, 1, 1);
    }

    /**
     * Draw a rectangle of pixels (optimized)
     */
    drawRect(x, y, width, height, color) {
        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, width, height);
    }

    /**
     * Draw the current frame
     */
    renderFrame() {
        this.clear();

        const frame = this.getCurrentFrame();
        if (!frame) {
            // Draw placeholder if no sprite data
            this.drawPlaceholder();
            return;
        }

        // Draw pixels from frame data
        if (frame.pixels) {
            for (const pixel of frame.pixels) {
                this.drawPixel(pixel.x, pixel.y, pixel.color);
            }
        }

        // Draw layers if present
        if (frame.layers) {
            for (const layer of frame.layers) {
                this.drawLayer(layer);
            }
        }
    }

    /**
     * Draw a sprite layer
     */
    drawLayer(layer) {
        if (layer.pixels) {
            for (const pixel of layer.pixels) {
                this.drawPixel(
                    layer.x + pixel.x,
                    layer.y + pixel.y,
                    pixel.color
                );
            }
        }
    }

    /**
     * Draw a placeholder when no sprite is loaded
     */
    drawPlaceholder() {
        // Draw a simple egg shape
        const ctx = this.ctx;

        // Egg body
        ctx.fillStyle = '#f0e6d3';
        ctx.fillRect(24, 20, 16, 24);
        ctx.fillRect(22, 22, 20, 20);
        ctx.fillRect(20, 24, 24, 16);

        // Eyes
        ctx.fillStyle = '#333';
        ctx.fillRect(26, 28, 3, 3);
        ctx.fillRect(35, 28, 3, 3);

        // Highlights
        ctx.fillStyle = '#fff';
        ctx.fillRect(26, 28, 1, 1);
        ctx.fillRect(35, 28, 1, 1);

        // Smile
        ctx.fillStyle = '#c9a';
        ctx.fillRect(28, 34, 8, 1);
    }

    /**
     * Main render loop
     */
    render(timestamp) {
        // Check if it's time for next frame
        if (timestamp - this.lastFrameTime >= (1000 / this.fps)) {
            this.lastFrameTime = timestamp;
            this.currentFrame++;
            this.frameCount++;

            this.renderFrame();

            if (this.onFrameUpdate) {
                this.onFrameUpdate(this.currentFrame, this.frameCount);
            }
        }
    }

    /**
     * Start animation loop
     */
    start() {
        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);
    }

    /**
     * Stop animation loop
     */
    stop() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
    }

    /**
     * Animation frame handler
     */
    animate(timestamp) {
        this.render(timestamp);
        this.animationFrame = requestAnimationFrame(this.animate);
    }

    /**
     * Reset to initial state
     */
    reset() {
        this.currentAnimation = 'idle';
        this.currentFrame = 0;
        this.frameCount = 0;
    }

    /**
     * Set FPS for animation
     */
    setFPS(fps) {
        this.fps = fps;
    }

    /**
     * Get canvas as data URL
     */
    toDataURL() {
        return this.canvas.toDataURL('image/png');
    }

    /**
     * Export canvas as image
     */
    exportImage() {
        const link = document.createElement('a');
        link.download = 'pet-sprite.png';
        link.href = this.toDataURL();
        link.click();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PetRenderer;
}
