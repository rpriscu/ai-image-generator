/**
 * Dashboard API Module
 * ====================
 * 
 * This module handles all API interactions for the dashboard.
 * It provides a clean interface for:
 * - Image/video generation
 * - Asset management (download, delete)
 * - Model information fetching
 * 
 * All API calls return promises and include proper error handling.
 * 
 * @module DashboardAPI
 */

class DashboardAPI {
    /**
     * Generate images or videos using the selected model.
     * 
     * @param {FormData} formData - Form data including prompt, model, and files
     * @returns {Promise<Object>} Response containing generated assets
     * @throws {Error} If the API request fails
     * 
     * @example
     * const formData = new FormData(document.getElementById('promptForm'));
     * try {
     *     const result = await DashboardAPI.generate(formData);
     *     console.log('Generated:', result.results);
     * } catch (error) {
     *     console.error('Generation failed:', error.message);
     * }
     */
    static async generate(formData) {
        try {
            // Check if this is a video model that needs async processing
            const modelName = formData.get('model');
            const isVideoModel = await this.isVideoModel(modelName);
            
            if (isVideoModel) {
                // Use async generation for video models to avoid 30s timeout
                return await this.generateAsync(formData);
            }
            
            // Use regular generation for image models
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Generation failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error - Generate:', error);
            throw error;
        }
    }
    
    /**
     * Submit a generation job for async processing (used for video models).
     * 
     * @param {FormData} formData - Form data including prompt, model, and files
     * @returns {Promise<Object>} Final result after job completion
     * @throws {Error} If the job fails
     */
    static async generateAsync(formData) {
        try {
            // Submit the job
            const response = await fetch('/api/generate-async', {
                method: 'POST',
                body: formData
            });
            
            const submitData = await response.json();
            
            if (!response.ok) {
                throw new Error(submitData.error || 'Failed to submit generation job');
            }
            
            const jobId = submitData.job_id;
            
            // Poll for job completion
            return await this.pollJobStatus(jobId);
            
        } catch (error) {
            console.error('API Error - Async Generate:', error);
            throw error;
        }
    }
    
    /**
     * Poll job status until completion.
     * 
     * @param {string} jobId - The job ID to poll
     * @returns {Promise<Object>} Final job result
     */
    static async pollJobStatus(jobId) {
        const pollInterval = 2000; // Poll every 2 seconds
        const maxWaitTime = 600000; // 10 minutes max
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWaitTime) {
            try {
                const response = await fetch(`/api/job-status/${jobId}`);
                const jobStatus = await response.json();
                
                if (!response.ok) {
                    throw new Error(jobStatus.error || 'Failed to get job status');
                }
                
                // Update UI with progress if available
                if (this.onJobProgress) {
                    this.onJobProgress(jobStatus);
                }
                
                if (jobStatus.status === 'completed') {
                    // Return result in same format as regular generation
                    return {
                        success: true,
                        results: [jobStatus.result]
                    };
                } else if (jobStatus.status === 'failed') {
                    throw new Error(jobStatus.message || 'Job failed');
                }
                
                // Job still processing, wait before next poll
                await new Promise(resolve => setTimeout(resolve, pollInterval));
                
            } catch (error) {
                if (error.message.includes('Failed to get job status')) {
                    // Continue polling for network issues
                    await new Promise(resolve => setTimeout(resolve, pollInterval));
                    continue;
                }
                throw error;
            }
        }
        
        throw new Error('Job timed out after 10 minutes');
    }
    
    /**
     * Check if a model generates videos (needs async processing).
     * 
     * @param {string} modelName - The model name
     * @returns {Promise<boolean>} True if it's a video model
     */
    static async isVideoModel(modelName) {
        try {
            const modelInfo = await this.getModelInfo(modelName);
            return modelInfo.output_type === 'video';
        } catch (error) {
            // If we can't get model info, assume it's not a video model
            return false;
        }
    }
    
    /**
     * Set a callback for job progress updates.
     * 
     * @param {Function} callback - Function to call with job status updates
     */
    static setJobProgressCallback(callback) {
        this.onJobProgress = callback;
    }
    
    /**
     * Get detailed information about a model.
     * 
     * @param {string} modelId - The model identifier
     * @returns {Promise<Object>} Model information including capabilities and tips
     * @throws {Error} If the model is not found or request fails
     * 
     * @example
     * const info = await DashboardAPI.getModelInfo('flux');
     * console.log(info.name, info.description);
     */
    static async getModelInfo(modelId) {
        try {
            const response = await fetch(`/api/model-info/${modelId}`);
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to fetch model info');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error - Model Info:', error);
            throw error;
        }
    }
    
    /**
     * Delete an asset from the user's library.
     * 
     * @param {number} assetId - The asset ID to delete
     * @param {string} assetUrl - The asset URL (for legacy compatibility)
     * @returns {Promise<boolean>} True if deletion was successful
     * 
     * @example
     * if (await DashboardAPI.deleteAsset(123)) {
     *     console.log('Asset deleted successfully');
     * }
     */
    static async deleteAsset(assetId, assetUrl = null) {
        try {
            // Try new endpoint first (by ID)
            let response = await fetch(`/api/assets/${assetId}`, {
                method: 'DELETE'
            });
            
            // Fallback to legacy endpoint if needed
            if (!response.ok && assetUrl) {
                response = await fetch('/api/delete-image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ url: assetUrl })
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to delete asset');
            }
            
            return true;
        } catch (error) {
            console.error('API Error - Delete Asset:', error);
            return false;
        }
    }
    
    /**
     * Download an asset.
     * 
     * @param {number} assetId - The asset ID to download
     * @param {string} filename - Optional filename for the download
     * @returns {Promise<void>}
     * 
     * @example
     * await DashboardAPI.downloadAsset(123, 'my-image.png');
     */
    static async downloadAsset(assetId, filename = null) {
        try {
            // Create a temporary link element
            const link = document.createElement('a');
            link.href = `/assets/${assetId}/download`;
            
            if (filename) {
                link.download = filename;
            } else {
                // Generate filename from asset ID and current date
                const date = new Date().toISOString().split('T')[0];
                link.download = `asset_${assetId}_${date}`;
            }
            
            // Trigger download
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
        } catch (error) {
            console.error('API Error - Download Asset:', error);
            throw error;
        }
    }
    
    /**
     * Load an image from URL and convert to File object.
     * Used for reference image functionality.
     * 
     * @param {string} imageUrl - URL of the image to load
     * @returns {Promise<File>} File object containing the image
     * 
     * @example
     * const file = await DashboardAPI.loadImageAsFile('https://example.com/image.jpg');
     * fileInput.files = [file];
     */
    static async loadImageAsFile(imageUrl) {
        try {
            const response = await fetch(imageUrl);
            
            if (!response.ok) {
                throw new Error(`Failed to fetch image: ${response.status}`);
            }
            
            const blob = await response.blob();
            const filename = imageUrl.split('/').pop().split('?')[0] || 'reference-image.jpg';
            
            return new File([blob], filename, { 
                type: blob.type || 'image/jpeg' 
            });
            
        } catch (error) {
            console.error('API Error - Load Image:', error);
            throw error;
        }
    }
    
    /**
     * Check API health and configuration status.
     * 
     * @returns {Promise<Object>} Status information
     * 
     * @example
     * const status = await DashboardAPI.checkHealth();
     * if (!status.api_configured) {
     *     alert('API key not configured');
     * }
     */
    static async checkHealth() {
        try {
            const response = await fetch('/api/health');
            return await response.json();
        } catch (error) {
            console.error('API Error - Health Check:', error);
            return { 
                healthy: false, 
                api_configured: false,
                error: error.message 
            };
        }
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardAPI;
}

// Make available globally
window.DashboardAPI = DashboardAPI; 