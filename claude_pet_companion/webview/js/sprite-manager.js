/**
 * SpriteManager - Handles loading and caching of sprite data
 *
 * Manages sprite data from JSON files and provides caching.
 */

class SpriteManager {
    constructor() {
        this.cache = new Map();
        this.basePath = 'assets/sprites/';
        this.currentSpecies = 'base_pet';
        this.currentEvolutionStage = 0;
    }

    /**
     * Load sprite data from JSON file
     */
    async loadSprite(filename) {
        // Check cache first
        if (this.cache.has(filename)) {
            return this.cache.get(filename);
        }

        try {
            const response = await fetch(this.basePath + filename);
            if (!response.ok) {
                throw new Error(`Failed to load sprite: ${filename}`);
            }

            const data = await response.json();
            this.cache.set(filename, data);
            return data;
        } catch (error) {
            console.error('Error loading sprite:', error);
            return this.getDefaultSprite();
        }
    }

    /**
     * Get sprite for current evolution stage
     */
    async getSpriteForStage(stage) {
        const stageFilenames = [
            'base_pet.json',      // 0: Egg
            'baby_pet.json',       // 1: Baby
            'child_pet.json',      // 2: Child
            'teen_pet.json',       // 3: Teen
            'adult_pet.json',      // 4: Adult
            'elder_pet.json',      // 5: Elder
            'ancient_pet.json'     // 6: Ancient
        ];

        const filename = stageFilenames[Math.min(stage, stageFilenames.length - 1)];
        return await this.loadSprite(filename);
    }

    /**
     * Get expression sprite overlay
     */
    async loadExpression(expressionName) {
        return await this.loadSprite(`expressions.json`);
    }

    /**
     * Get default sprite (placeholder)
     */
    getDefaultSprite() {
        return {
            name: 'Default Pet',
            width: 64,
            height: 64,
            animations: {
                idle: {
                    frames: [
                        {
                            pixels: this.generateDefaultPixels()
                        }
                    ]
                },
                happy: {
                    frames: [
                        {
                            pixels: this.generateHappyPixels()
                        }
                    ]
                },
                sad: {
                    frames: [
                        {
                            pixels: this.generateSadPixels()
                        }
                    ]
                },
                sleep: {
                    frames: [
                        {
                            pixels: this.generateSleepPixels()
                        }
                    ]
                }
            }
        };
    }

    /**
     * Generate default idle pixels
     */
    generateDefaultPixels() {
        const pixels = [];
        const color = '#f0e6d3';

        // Simple egg shape
        for (let y = 20; y < 44; y++) {
            const width = this.getEggWidth(y);
            const startX = 32 - Math.floor(width / 2);

            for (let x = startX; x < startX + width; x++) {
                pixels.push({ x, y, color });
            }
        }

        // Eyes
        pixels.push({ x: 26, y: 28, color: '#333' });
        pixels.push({ x: 27, y: 28, color: '#333' });
        pixels.push({ x: 26, y: 29, color: '#333' });
        pixels.push({ x: 27, y: 29, color: '#333' });

        pixels.push({ x: 35, y: 28, color: '#333' });
        pixels.push({ x: 36, y: 28, color: '#333' });
        pixels.push({ x: 35, y: 29, color: '#333' });
        pixels.push({ x: 36, y: 29, color: '#333' });

        // Smile
        pixels.push({ x: 28, y: 34, color: '#c9a' });
        pixels.push({ x: 29, y: 34, color: '#c9a' });
        pixels.push({ x: 30, y: 34, color: '#c9a' });
        pixels.push({ x: 31, y: 34, color: '#c9a' });
        pixels.push({ x: 32, y: 34, color: '#c9a' });
        pixels.push({ x: 33, y: 34, color: '#c9a' });
        pixels.push({ x: 34, y: 34, color: '#c9a' });
        pixels.push({ x: 35, y: 34, color: '#c9a' });

        return pixels;
    }

    /**
     * Generate happy pixels
     */
    generateHappyPixels() {
        const pixels = this.generateDefaultPixels();

        // Bigger smile and closed eyes for happy
        // Remove regular eyes
        const eyePixels = pixels.filter(p =>
            (p.x >= 26 && p.x <= 27 && p.y >= 28 && p.y <= 29) ||
            (p.x >= 35 && p.x <= 36 && p.y >= 28 && p.y <= 29)
        );
        eyePixels.forEach(ep => {
            const idx = pixels.indexOf(ep);
            if (idx > -1) pixels.splice(idx, 1);
        });

        // Happy eyes (arches)
        for (let i = 0; i < 3; i++) {
            pixels.push({ x: 25 + i, y: 28, color: '#333' });
            pixels.push({ x: 36 + i, y: 28, color: '#333' });
        }

        // Bigger smile
        pixels.push({ x: 27, y: 34, color: '#c9a' });
        pixels.push({ x: 36, y: 34, color: '#c9a' });
        pixels.push({ x: 27, y: 35, color: '#c9a' });
        pixels.push({ x: 36, y: 35, color: '#c9a' });

        return pixels;
    }

    /**
     * Generate sad pixels
     */
    generateSadPixels() {
        const pixels = this.generateDefaultPixels();

        // Sad eyes
        // Remove regular eyes and add sad ones
        const eyePixels = pixels.filter(p =>
            (p.x >= 26 && p.x <= 27 && p.y >= 28 && p.y <= 29) ||
            (p.x >= 35 && p.x <= 36 && p.y >= 28 && p.y <= 29)
        );
        eyePixels.forEach(ep => {
            const idx = pixels.indexOf(ep);
            if (idx > -1) pixels.splice(idx, 1);
        });

        // Sad eyes (upward arch)
        pixels.push({ x: 26, y: 29, color: '#333' });
        pixels.push({ x: 27, y: 28, color: '#333' });
        pixels.push({ x: 35, y: 29, color: '#333' });
        pixels.push({ x: 36, y: 28, color: '#333' });

        // Frown
        const smilePixels = pixels.filter(p => p.y === 34 && p.color === '#c9a');
        smilePixels.forEach(sp => {
            const idx = pixels.indexOf(sp);
            if (idx > -1) pixels.splice(idx, 1);
        });

        pixels.push({ x: 29, y: 35, color: '#999' });
        pixels.push({ x: 30, y: 35, color: '#999' });
        pixels.push({ x: 31, y: 35, color: '#999' });
        pixels.push({ x: 32, y: 35, color: '#999' });
        pixels.push({ x: 33, y: 35, color: '#999' });
        pixels.push({ x: 34, y: 35, color: '#999' });

        return pixels;
    }

    /**
     * Generate sleep pixels
     */
    generateSleepPixels() {
        const pixels = this.generateDefaultPixels();

        // Closed eyes
        const eyePixels = pixels.filter(p =>
            (p.x >= 26 && p.x <= 27 && p.y >= 28 && p.y <= 29) ||
            (p.x >= 35 && p.x <= 36 && p.y >= 28 && p.y <= 29)
        );
        eyePixels.forEach(ep => {
            const idx = pixels.indexOf(ep);
            if (idx > -1) pixels.splice(idx, 1);
        });

        // Sleep lines
        for (let i = 0; i < 3; i++) {
            pixels.push({ x: 25 + i, y: 29, color: '#666' });
            pixels.push({ x: 36 + i, y: 29, color: '#666' });
        }

        // Slight smile (contented sleep)
        const smilePixels = pixels.filter(p => p.y === 34 && p.color === '#c9a');
        smilePixels.forEach(sp => {
            const idx = pixels.indexOf(sp);
            if (idx > -1) pixels.splice(idx, 1);
        });

        for (let x = 29; x <= 34; x++) {
            pixels.push({ x, y: 34, color: '#aaa' });
        }

        // Z's for sleeping
        pixels.push({ x: 40, y: 16, color: '#666', alpha: 0.5 });
        pixels.push({ x: 44, y: 12, color: '#666', alpha: 0.3 });

        return pixels;
    }

    /**
     * Get egg width at given Y coordinate
     */
    getEggWidth(y) {
        if (y < 20 || y > 44) return 0;

        // Egg shape calculation
        const centerY = 32;
        const distFromCenter = Math.abs(y - centerY);

        if (distFromCenter < 8) {
            return 24 - distFromCenter;
        } else {
            return 16 - (distFromCenter - 8);
        }
    }

    /**
     * Clear the sprite cache
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Preload all sprites
     */
    async preloadAll() {
        const sprites = [
            'base_pet.json',
            'expressions.json'
        ];

        const promises = sprites.map(s => this.loadSprite(s));
        await Promise.all(promises);
    }

    /**
     * Set base path for sprite files
     */
    setBasePath(path) {
        this.basePath = path;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SpriteManager;
}
