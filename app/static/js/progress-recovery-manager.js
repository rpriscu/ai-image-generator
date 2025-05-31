/**
 * Progress Recovery Manager
 * ========================
 * 
 * Handles restoration of generation progress when users navigate back to the generator.
 * Works in conjunction with GenerationStateManager to provide seamless cross-page
 * generation tracking and automatic UI state recovery.
 * 
 * Key Features:
 * - Automatic progress restoration on page load
 * - Background completion checking via polling
 * - Smart UI restoration based on generation state
 * - Conflict prevention for overlapping requests
 * - Integration with existing generation workflows
 * 
 * Integration Points:
 * - GenerationStateManager: For persistent state tracking
 * - Dashboard UI: For progress indicator restoration
 * - Generation API: For checking completion status
 */

class ProgressRecoveryManager {
    constructor(generationStateManager, uiManager) {
        this.stateManager = generationStateManager;
        this.uiManager = uiManager;
        this.pollingInterval = 3000; // Check every 3 seconds
        this.activePolling = false;
        this.pollingTimer = null;
        
        // Bind methods to preserve context
        this.checkForCompletions = this.checkForCompletions.bind(this);
        this.restoreProgressUI = this.restoreProgressUI.bind(this);
        
        console.log('[ProgressRecoveryManager] Initialized');
    }

    /**
     * Initialize progress recovery on page load
     * Should be called when the generator page loads
     */
    async initialize() {
        console.log('[ProgressRecoveryManager] Starting initialization...');
        
        try {
            // Get any active generations
            const activeGenerations = this.stateManager.getActiveGenerations();
            const activeCount = Object.keys(activeGenerations).length;
            
            if (activeCount > 0) {
                console.log(`[ProgressRecoveryManager] Found ${activeCount} active generation(s), restoring UI...`);
                
                // Restore UI for the most recent generation
                await this.restoreProgressUI();
                
                // Start polling for completions
                this.startPolling();
                
                // Check for any completions immediately
                await this.checkForCompletions();
            } else {
                console.log('[ProgressRecoveryManager] No active generations found');
            }
            
            // Check for any recently completed generations to display
            this.checkForUnshownCompletions();
            
        } catch (error) {
            console.error('[ProgressRecoveryManager] Error during initialization:', error);
        }
    }

    /**
     * Restore the progress UI based on active generations
     */
    async restoreProgressUI() {
        const mostRecent = this.stateManager.getMostRecentActiveGeneration();
        
        if (!mostRecent) {
            console.log('[ProgressRecoveryManager] No active generation to restore');
            return;
        }

        console.log(`[ProgressRecoveryManager] Restoring UI for generation ${mostRecent.id}`);
        
        try {
            // Clear any existing results
            const resultsContainer = document.getElementById('results');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }

            // Restore loading indicators
            this.createRestoredLoadingIndicators(mostRecent);
            
            // Update UI to match the generation's model and settings
            await this.restoreModelSelection(mostRecent);
            
            // Show restoration notification
            this.showRestorationNotification(mostRecent);
            
        } catch (error) {
            console.error('[ProgressRecoveryManager] Error restoring progress UI:', error);
        }
    }

    /**
     * Create loading indicators for restored generation
     * @param {object} generation - The generation record to restore
     */
    createRestoredLoadingIndicators(generation) {
        const resultsContainer = document.getElementById('results');
        if (!resultsContainer) return;

        const elapsedTime = Math.floor((Date.now() - generation.startTime) / 1000);
        
        for (let i = 0; i < generation.numOutputs; i++) {
            const loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'image-result loading restored';
            loadingIndicator.setAttribute('data-generation-id', generation.id);
            
            if (generation.modelId === 'stable_video') {
                loadingIndicator.innerHTML = `
                    <div class="loading-spinner"></div>
                    <div class="loading-progress">
                        <div class="progress-text">Resuming video generation...</div>
                        <div class="progress-subtext">Generation in progress</div>
                        <div class="progress-timer" id="restored-timer-${i}">${elapsedTime}s</div>
                        <div class="restored-indicator">
                            <i class="fas fa-history"></i> Restored from navigation
                        </div>
                    </div>
                `;
            } else {
                loadingIndicator.innerHTML = `
                    <div class="loading-spinner"></div>
                    <div class="loading-progress">
                        <div class="progress-text">Resuming generation...</div>
                        <div class="progress-timer" id="restored-timer-${i}">${elapsedTime}s</div>
                        <div class="restored-indicator">
                            <i class="fas fa-history"></i> Restored
                        </div>
                    </div>
                `;
            }
            
            resultsContainer.appendChild(loadingIndicator);
        }

        // Start updating the restored timers
        this.startRestoredTimers(generation);
    }

    /**
     * Start timer updates for restored progress indicators
     * @param {object} generation - The generation record
     */
    startRestoredTimers(generation) {
        const startTime = generation.startTime;
        
        const updateTimers = () => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            
            for (let i = 0; i < generation.numOutputs; i++) {
                const timerElement = document.getElementById(`restored-timer-${i}`);
                if (timerElement) {
                    timerElement.textContent = `${elapsed}s`;
                }
            }
        };

        // Update immediately and then every second
        updateTimers();
        const timerInterval = setInterval(() => {
            // Check if the generation is still active
            const currentGeneration = this.stateManager.getGeneration(generation.id);
            if (!currentGeneration || currentGeneration.status !== 'pending') {
                clearInterval(timerInterval);
                return;
            }
            
            updateTimers();
        }, 1000);
    }

    /**
     * Restore model selection and form state
     * @param {object} generation - The generation record
     */
    async restoreModelSelection(generation) {
        // Find and select the correct model
        const modelOption = document.querySelector(`.model-option[data-model="${generation.modelId}"]`);
        if (modelOption) {
            // Clear existing selections
            document.querySelectorAll('.model-option').forEach(el => el.classList.remove('selected'));
            
            // Select the model
            modelOption.classList.add('selected');
            
            // Update UI using the UI manager
            if (this.uiManager && typeof this.uiManager.updateUI === 'function') {
                this.uiManager.updateUI(generation.modelId);
            }
        }

        // Restore prompt if available and appropriate
        const promptElement = document.getElementById('prompt');
        if (promptElement && generation.prompt) {
            promptElement.value = generation.prompt;
        }
    }

    /**
     * Show a notification that generation was restored
     * @param {object} generation - The generation record
     */
    showRestorationNotification(generation) {
        // Create a temporary notification
        const notification = document.createElement('div');
        notification.className = 'restoration-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-history"></i>
                <span>Restored ongoing ${generation.modelId === 'stable_video' ? 'video' : 'image'} generation</span>
                <button onclick="this.parentNode.parentNode.remove()" class="dismiss-btn">×</button>
            </div>
        `;
        
        // Insert at top of generator container
        const generatorContainer = document.querySelector('.generator-container');
        if (generatorContainer) {
            generatorContainer.insertBefore(notification, generatorContainer.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 5000);
        }
    }

    /**
     * Start polling for generation completions
     */
    startPolling() {
        if (this.activePolling) {
            console.log('[ProgressRecoveryManager] Polling already active');
            return;
        }

        console.log('[ProgressRecoveryManager] Starting completion polling');
        this.activePolling = true;
        
        this.pollingTimer = setInterval(this.checkForCompletions, this.pollingInterval);
    }

    /**
     * Stop polling for generation completions
     */
    stopPolling() {
        if (this.pollingTimer) {
            clearInterval(this.pollingTimer);
            this.pollingTimer = null;
        }
        this.activePolling = false;
        console.log('[ProgressRecoveryManager] Stopped completion polling');
    }

    /**
     * Check for generation completions via API
     */
    async checkForCompletions() {
        const activeGenerations = this.stateManager.getActiveGenerations();
        const requestIds = Object.keys(activeGenerations);
        
        if (requestIds.length === 0) {
            this.stopPolling();
            return;
        }

        console.log(`[ProgressRecoveryManager] Checking completion status for ${requestIds.length} generation(s)`);
        
        for (const requestId of requestIds) {
            try {
                const response = await fetch(`/api/generation-status/${requestId}`);
                
                if (response.ok) {
                    const statusData = await response.json();
                    await this.handleStatusUpdate(requestId, statusData);
                } else if (response.status === 404) {
                    // Generation not found on server, might be completed or failed
                    console.log(`[ProgressRecoveryManager] Generation ${requestId} not found on server`);
                    this.stateManager.updateGenerationStatus(requestId, 'failed');
                    this.handleGenerationFailure(requestId);
                }
            } catch (error) {
                console.error(`[ProgressRecoveryManager] Error checking status for ${requestId}:`, error);
            }
        }
    }

    /**
     * Handle status update from server
     * @param {string} requestId - The request ID
     * @param {object} statusData - Status data from server
     */
    async handleStatusUpdate(requestId, statusData) {
        const { status, results } = statusData;
        
        switch (status) {
            case 'completed':
                console.log(`[ProgressRecoveryManager] Generation ${requestId} completed`);
                this.stateManager.completeGeneration(requestId, results);
                await this.handleGenerationCompletion(requestId, results);
                break;
                
            case 'failed':
                console.log(`[ProgressRecoveryManager] Generation ${requestId} failed`);
                this.stateManager.updateGenerationStatus(requestId, 'failed');
                this.handleGenerationFailure(requestId);
                break;
                
            case 'pending':
                // Still in progress, update timestamp
                this.stateManager.updateGenerationStatus(requestId, 'pending');
                break;
        }
    }

    /**
     * Handle successful generation completion
     * @param {string} requestId - The request ID
     * @param {array} results - Generation results
     */
    async handleGenerationCompletion(requestId, results) {
        // Remove loading indicators for this generation
        const loadingIndicators = document.querySelectorAll(`[data-generation-id="${requestId}"]`);
        loadingIndicators.forEach(indicator => indicator.remove());
        
        // Display results using existing display function
        if (typeof displayResults === 'function' && results && results.length > 0) {
            const generation = this.stateManager.getGeneration(requestId);
            const modelId = generation ? generation.modelId : 'unknown';
            displayResults(results, modelId);
        }
        
        // Show completion notification
        this.showCompletionNotification(requestId, results.length);
        
        // Stop polling if no more active generations
        const remaining = Object.keys(this.stateManager.getActiveGenerations()).length;
        if (remaining === 0) {
            this.stopPolling();
        }
    }

    /**
     * Handle generation failure
     * @param {string} requestId - The request ID
     */
    handleGenerationFailure(requestId) {
        // Remove loading indicators for this generation
        const loadingIndicators = document.querySelectorAll(`[data-generation-id="${requestId}"]`);
        loadingIndicators.forEach(indicator => indicator.remove());
        
        // Show error message
        const resultsContainer = document.getElementById('results');
        if (resultsContainer && resultsContainer.children.length === 0) {
            resultsContainer.innerHTML = `
                <div class="error-message">
                    Generation failed or was cancelled. Please try again.
                </div>
            `;
        }
        
        // Remove from state manager
        this.stateManager.removeGeneration(requestId);
    }

    /**
     * Show completion notification
     * @param {string} requestId - The request ID
     * @param {number} resultCount - Number of results generated
     */
    showCompletionNotification(requestId, resultCount) {
        const notification = document.createElement('div');
        notification.className = 'completion-notification';
        notification.innerHTML = `
            <div class="notification-content success">
                <i class="fas fa-check-circle"></i>
                <span>Generation completed! ${resultCount} asset(s) generated.</span>
                <button onclick="this.parentNode.parentNode.remove()" class="dismiss-btn">×</button>
            </div>
        `;
        
        // Insert at top of generator container
        const generatorContainer = document.querySelector('.generator-container');
        if (generatorContainer) {
            generatorContainer.insertBefore(notification, generatorContainer.firstChild);
            
            // Auto-dismiss after 8 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 8000);
        }
    }

    /**
     * Check for completed generations that haven't been shown yet
     */
    checkForUnshownCompletions() {
        const completedGenerations = this.stateManager.getCompletedGenerations();
        const recentCompletions = Object.values(completedGenerations).filter(
            gen => (Date.now() - gen.completionTime) < (5 * 60 * 1000) // Last 5 minutes
        );

        if (recentCompletions.length > 0) {
            console.log(`[ProgressRecoveryManager] Found ${recentCompletions.length} recent completion(s)`);
            
            recentCompletions.forEach(completion => {
                this.showRecentCompletionNotification(completion);
            });
        }
    }

    /**
     * Show notification for recent completion
     * @param {object} completion - The completion record
     */
    showRecentCompletionNotification(completion) {
        const notification = document.createElement('div');
        notification.className = 'recent-completion-notification';
        notification.innerHTML = `
            <div class="notification-content info">
                <i class="fas fa-info-circle"></i>
                <span>Recent generation completed: ${completion.results.length} asset(s) are in your library</span>
                <button onclick="this.parentNode.parentNode.remove()" class="dismiss-btn">×</button>
            </div>
        `;
        
        // Insert at top of generator container
        const generatorContainer = document.querySelector('.generator-container');
        if (generatorContainer) {
            generatorContainer.insertBefore(notification, generatorContainer.firstChild);
            
            // Auto-dismiss after 6 seconds
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 6000);
        }
    }

    /**
     * Cleanup and destroy the manager
     */
    destroy() {
        this.stopPolling();
        console.log('[ProgressRecoveryManager] Destroyed');
    }
}

// Export for use in other files
window.ProgressRecoveryManager = ProgressRecoveryManager; 