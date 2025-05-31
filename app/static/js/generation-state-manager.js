/**
 * Generation State Manager
 * ======================
 * 
 * Manages persistent state for ongoing generation requests across page navigations.
 * Provides a centralized system for tracking generation progress, handling multiple
 * concurrent requests, and restoring UI state when users return to the generator.
 * 
 * Key Features:
 * - Persistent state storage using localStorage
 * - Multi-request tracking with unique request IDs
 * - Automatic state cleanup for completed/failed requests
 * - Cross-page progress synchronization
 * - Conflict prevention for overlapping requests
 * 
 * State Schema:
 * {
 *   activeGenerations: {
 *     [requestId]: {
 *       id: string,
 *       modelId: string,
 *       prompt: string,
 *       startTime: number,
 *       status: 'pending'|'completed'|'failed'|'timeout',
 *       formData: object,
 *       numOutputs: number,
 *       lastUpdate: number
 *     }
 *   },
 *   completedGenerations: {
 *     [requestId]: {
 *       id: string,
 *       results: array,
 *       completionTime: number
 *     }
 *   }
 * }
 */

class GenerationStateManager {
    constructor() {
        this.storageKey = 'ai_generator_state';
        this.maxRetentionTime = 24 * 60 * 60 * 1000; // 24 hours
        this.maxActiveGenerations = 3; // Prevent too many concurrent requests
        
        // Initialize state structure
        this.initializeState();
        
        // Cleanup old entries on initialization
        this.cleanupOldEntries();
        
        // Set up periodic cleanup
        this.setupPeriodicCleanup();
    }

    /**
     * Initialize the state structure in localStorage if it doesn't exist
     */
    initializeState() {
        const existingState = this.getState();
        if (!existingState || !existingState.activeGenerations) {
            const defaultState = {
                activeGenerations: {},
                completedGenerations: {},
                lastCleanup: Date.now()
            };
            this.setState(defaultState);
        }
    }

    /**
     * Get the complete state from localStorage
     * @returns {object} The current state object
     */
    getState() {
        try {
            const stateStr = localStorage.getItem(this.storageKey);
            return stateStr ? JSON.parse(stateStr) : null;
        } catch (error) {
            console.error('[GenerationStateManager] Failed to parse state from localStorage:', error);
            return null;
        }
    }

    /**
     * Save the complete state to localStorage
     * @param {object} state - The state object to save
     */
    setState(state) {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(state));
        } catch (error) {
            console.error('[GenerationStateManager] Failed to save state to localStorage:', error);
        }
    }

    /**
     * Generate a unique request ID for tracking
     * @returns {string} Unique request identifier
     */
    generateRequestId() {
        return `gen_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Start tracking a new generation request
     * @param {object} config - Generation configuration
     * @param {string} config.modelId - The model being used
     * @param {string} config.prompt - The user's prompt
     * @param {FormData} config.formData - The form data for the request
     * @param {number} config.numOutputs - Number of expected outputs
     * @returns {string} The request ID for tracking
     */
    startGeneration(config) {
        const state = this.getState();
        const requestId = this.generateRequestId();
        
        // Check if we're at the concurrent request limit
        const activeCount = Object.keys(state.activeGenerations).length;
        if (activeCount >= this.maxActiveGenerations) {
            throw new Error(`Maximum ${this.maxActiveGenerations} concurrent generations allowed`);
        }

        // Create generation record
        const generationRecord = {
            id: requestId,
            modelId: config.modelId,
            prompt: config.prompt,
            startTime: Date.now(),
            status: 'pending',
            formData: this.serializeFormData(config.formData),
            numOutputs: config.numOutputs,
            lastUpdate: Date.now()
        };

        // Add to active generations
        state.activeGenerations[requestId] = generationRecord;
        this.setState(state);

        console.log(`[GenerationStateManager] Started tracking generation ${requestId} for model ${config.modelId}`);
        return requestId;
    }

    /**
     * Update the status of an ongoing generation
     * @param {string} requestId - The request ID to update
     * @param {string} status - New status ('pending'|'completed'|'failed'|'timeout')
     * @param {object} additionalData - Additional data to merge into the record
     */
    updateGenerationStatus(requestId, status, additionalData = {}) {
        const state = this.getState();
        
        if (!state.activeGenerations[requestId]) {
            console.warn(`[GenerationStateManager] Attempted to update non-existent generation ${requestId}`);
            return;
        }

        // Update the generation record
        state.activeGenerations[requestId] = {
            ...state.activeGenerations[requestId],
            status,
            lastUpdate: Date.now(),
            ...additionalData
        };

        this.setState(state);
        console.log(`[GenerationStateManager] Updated generation ${requestId} status to ${status}`);
    }

    /**
     * Mark a generation as completed and move it to completed list
     * @param {string} requestId - The request ID to complete
     * @param {array} results - The generation results
     */
    completeGeneration(requestId, results) {
        const state = this.getState();
        const activeGeneration = state.activeGenerations[requestId];
        
        if (!activeGeneration) {
            console.warn(`[GenerationStateManager] Attempted to complete non-existent generation ${requestId}`);
            return;
        }

        // Move to completed generations
        state.completedGenerations[requestId] = {
            id: requestId,
            modelId: activeGeneration.modelId,
            prompt: activeGeneration.prompt,
            results: results,
            completionTime: Date.now(),
            duration: Date.now() - activeGeneration.startTime
        };

        // Remove from active generations
        delete state.activeGenerations[requestId];
        
        this.setState(state);
        console.log(`[GenerationStateManager] Completed generation ${requestId} with ${results.length} results`);
    }

    /**
     * Remove a generation from tracking (for failed/cancelled requests)
     * @param {string} requestId - The request ID to remove
     */
    removeGeneration(requestId) {
        const state = this.getState();
        
        if (state.activeGenerations[requestId]) {
            delete state.activeGenerations[requestId];
            this.setState(state);
            console.log(`[GenerationStateManager] Removed generation ${requestId} from tracking`);
        }
    }

    /**
     * Get all active (ongoing) generations
     * @returns {object} Active generations object
     */
    getActiveGenerations() {
        const state = this.getState();
        return state.activeGenerations || {};
    }

    /**
     * Get all completed generations
     * @returns {object} Completed generations object  
     */
    getCompletedGenerations() {
        const state = this.getState();
        return state.completedGenerations || {};
    }

    /**
     * Get a specific generation by ID (checks both active and completed)
     * @param {string} requestId - The request ID to find
     * @returns {object|null} The generation record or null if not found
     */
    getGeneration(requestId) {
        const state = this.getState();
        
        return state.activeGenerations[requestId] || 
               state.completedGenerations[requestId] || 
               null;
    }

    /**
     * Check if there are any active generations for a specific model
     * @param {string} modelId - The model ID to check
     * @returns {boolean} True if there are active generations for this model
     */
    hasActiveGenerationsForModel(modelId) {
        const activeGenerations = this.getActiveGenerations();
        return Object.values(activeGenerations).some(gen => gen.modelId === modelId);
    }

    /**
     * Get the most recent active generation (for UI restoration)
     * @returns {object|null} The most recent generation or null
     */
    getMostRecentActiveGeneration() {
        const activeGenerations = this.getActiveGenerations();
        const generations = Object.values(activeGenerations);
        
        if (generations.length === 0) return null;
        
        return generations.reduce((latest, current) => {
            return current.startTime > latest.startTime ? current : latest;
        });
    }

    /**
     * Serialize FormData object for storage
     * @param {FormData} formData - The FormData to serialize
     * @returns {object} Serialized form data
     */
    serializeFormData(formData) {
        const serialized = {};
        
        for (let [key, value] of formData.entries()) {
            if (value instanceof File) {
                // Store file metadata, not the actual file content
                serialized[key] = {
                    type: 'file',
                    name: value.name,
                    size: value.size,
                    lastModified: value.lastModified
                };
            } else {
                serialized[key] = value;
            }
        }
        
        return serialized;
    }

    /**
     * Clean up old entries from storage
     */
    cleanupOldEntries() {
        const state = this.getState();
        const now = Date.now();
        let hasChanges = false;

        // Clean up old active generations (consider them failed)
        Object.keys(state.activeGenerations).forEach(requestId => {
            const generation = state.activeGenerations[requestId];
            const age = now - generation.startTime;
            
            if (age > this.maxRetentionTime) {
                console.log(`[GenerationStateManager] Cleaning up stale generation ${requestId}`);
                delete state.activeGenerations[requestId];
                hasChanges = true;
            }
        });

        // Clean up old completed generations
        Object.keys(state.completedGenerations).forEach(requestId => {
            const generation = state.completedGenerations[requestId];
            const age = now - generation.completionTime;
            
            if (age > this.maxRetentionTime) {
                console.log(`[GenerationStateManager] Cleaning up old completed generation ${requestId}`);
                delete state.completedGenerations[requestId];
                hasChanges = true;
            }
        });

        if (hasChanges) {
            state.lastCleanup = now;
            this.setState(state);
        }
    }

    /**
     * Set up periodic cleanup of old entries
     */
    setupPeriodicCleanup() {
        // Clean up every 5 minutes
        setInterval(() => {
            this.cleanupOldEntries();
        }, 5 * 60 * 1000);
    }

    /**
     * Clear all state (for debugging/reset)
     */
    clearAllState() {
        localStorage.removeItem(this.storageKey);
        this.initializeState();
        console.log('[GenerationStateManager] Cleared all state');
    }

    /**
     * Get statistics about current state
     * @returns {object} Statistics object
     */
    getStatistics() {
        const state = this.getState();
        const activeCount = Object.keys(state.activeGenerations).length;
        const completedCount = Object.keys(state.completedGenerations).length;
        
        return {
            activeGenerations: activeCount,
            completedGenerations: completedCount,
            totalTracked: activeCount + completedCount,
            lastCleanup: state.lastCleanup
        };
    }
}

// Export for use in other files
window.GenerationStateManager = GenerationStateManager; 