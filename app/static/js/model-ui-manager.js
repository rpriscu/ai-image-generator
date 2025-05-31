/**
 * Model UI Manager - Handles UI updates based on model configuration
 * This separates UI logic from the main application code
 */

class ModelUIManager {
    constructor(modelConfigs) {
        this.modelConfigs = modelConfigs;
        this.currentModel = null;
        this.uiElements = this.cacheUIElements();
    }

    /**
     * Cache DOM elements for better performance
     */
    cacheUIElements() {
        return {
            promptSection: document.getElementById('promptSection'),
            promptTextarea: document.getElementById('prompt'),
            promptNotRequired: document.getElementById('promptNotRequired'),
            imageUploadSection: document.getElementById('imageUploadSection'),
            imageInput: document.getElementById('image'),
            optionalImageText: document.getElementById('optionalImageText'),
            maskUploadSection: document.getElementById('maskUploadSection'),
            sdParamsSection: document.getElementById('sdParamsSection'),
            generateBtn: document.getElementById('generateBtn')
        };
    }

    /**
     * Update UI based on selected model
     */
    updateUI(modelId) {
        const config = this.modelConfigs[modelId];
        if (!config) {
            console.error(`No configuration found for model: ${modelId}`);
            return;
        }

        this.currentModel = modelId;
        const uiConfig = config.ui_config || {};

        // Reset all sections to default state
        this.resetUI();

        // Update prompt section with advanced logic
        this.updatePromptSection(config);

        // Apply model-specific UI configuration (excluding prompt which is handled above)
        this.applyUIConfig(uiConfig);

        // Update button text
        this.updateButtonText(uiConfig.button_text || 'Generate');

        // Setup dynamic parameters if needed
        if (uiConfig.show_params && config.param_config) {
            this.setupDynamicParameters(config.param_config);
        }
    }

    /**
     * Reset UI to default state
     */
    resetUI() {
        const { 
            promptSection, promptTextarea, promptNotRequired,
            imageUploadSection, imageInput, optionalImageText,
            maskUploadSection, sdParamsSection 
        } = this.uiElements;

        // Show prompt section by default
        if (promptSection) {
            promptSection.style.display = 'block';
            promptSection.style.visibility = 'visible';
        }

        // Reset prompt requirements - don't automatically add required attribute
        if (promptTextarea) {
            promptTextarea.removeAttribute('required');
        }
        if (promptNotRequired) {
            promptNotRequired.style.display = 'none';
        }

        // Hide optional sections
        if (imageUploadSection) {
            imageUploadSection.style.display = 'none';
        }
        if (maskUploadSection) {
            maskUploadSection.style.display = 'none';
        }
        if (sdParamsSection) {
            sdParamsSection.style.display = 'none';
        }

        // Reset image requirements
        if (imageInput) {
            imageInput.removeAttribute('required');
        }
        if (optionalImageText) {
            optionalImageText.style.display = 'inline';
        }
    }

    /**
     * Apply UI configuration
     */
    applyUIConfig(uiConfig) {
        const { 
            imageUploadSection, imageInput, optionalImageText,
            maskUploadSection, sdParamsSection 
        } = this.uiElements;

        // Note: Prompt handling is now done in updatePromptSection()

        // Handle image upload
        if (uiConfig.show_image_upload && imageUploadSection) {
            imageUploadSection.style.display = 'block';
            
            if (uiConfig.image_required && imageInput) {
                imageInput.setAttribute('required', 'required');
                if (optionalImageText) {
                    optionalImageText.style.display = 'none';
                }
            }
        }

        // Handle mask upload
        if (uiConfig.show_mask_upload && maskUploadSection) {
            maskUploadSection.style.display = 'block';
        }

        // Handle parameters section
        if (uiConfig.show_advanced_params && sdParamsSection) {
            sdParamsSection.style.display = 'block';
        }
    }

    /**
     * Update generate button text
     */
    updateButtonText(text) {
        if (this.uiElements.generateBtn) {
            this.uiElements.generateBtn.textContent = text;
        }
    }

    /**
     * Setup dynamic parameters based on configuration
     */
    setupDynamicParameters(paramConfig) {
        // This would dynamically create parameter inputs based on configuration
        // For now, we'll use the existing parameter sections
        console.log('Setting up parameters:', paramConfig);
    }

    /**
     * Get current form data formatted for API
     */
    getFormData() {
        const formData = new FormData(document.getElementById('promptForm'));
        
        // Add model ID
        formData.append('model', this.currentModel);

        // Add any model-specific parameters
        const config = this.modelConfigs[this.currentModel];
        if (config && config.default_params) {
            // Parameters would be collected from the form
            // This is a placeholder for the actual implementation
        }

        return formData;
    }

    /**
     * Validate form based on current model requirements
     */
    validateForm() {
        const config = this.modelConfigs[this.currentModel];
        if (!config) return { valid: false, errors: ['No model selected'] };

        const validation = config.validation || {};
        const errors = [];

        // Validate prompt
        if (validation.prompt && validation.prompt.required) {
            const prompt = this.uiElements.promptTextarea?.value.trim();
            if (!prompt) {
                errors.push('Prompt is required');
            } else if (prompt.length < validation.prompt.min_length) {
                errors.push(`Prompt must be at least ${validation.prompt.min_length} characters`);
            }
        }

        // Validate image
        if (validation.image && validation.image.required) {
            const imageInput = this.uiElements.imageInput;
            if (!imageInput?.files?.length) {
                errors.push('Image is required');
            }
        }

        // Validate mask
        if (validation.mask && validation.mask.required) {
            const maskInput = document.getElementById('maskImage');
            if (!maskInput?.files?.length) {
                errors.push('Mask image is required');
            }
        }

        return {
            valid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Get loading indicator count based on model
     */
    getLoadingIndicatorCount() {
        const config = this.modelConfigs[this.currentModel];
        if (!config) return 1;

        return config.default_num_outputs || 1;
    }

    updatePromptSection(modelConfig) {
        const promptSection = document.getElementById('promptSection');
        const promptInput = document.getElementById('prompt');
        const promptNotRequired = document.getElementById('promptNotRequired');
        
        if (modelConfig.ui_config?.show_prompt !== false) {
            promptSection.style.display = 'block';
            
            if (modelConfig.ui_config?.prompt_required === false) {
                // Make prompt optional and update UI
                promptInput.removeAttribute('required');
                promptNotRequired.style.display = 'block';
                
                // Update placeholder for optional prompts
                if (modelConfig.type === 'inpainting') {
                    promptInput.placeholder = "Optional: Describe what you want to fill the masked area with (leave empty for intelligent fill based on surrounding context)";
                    promptNotRequired.textContent = "Prompt is optional for inpainting. Leave empty to let AI intelligently fill based on surrounding image context.";
                } else {
                    promptInput.placeholder = "Optional: Describe what you want to see...";
                    promptNotRequired.textContent = "Prompt is optional for this model.";
                }
            } else {
                // Prompt is required
                promptInput.setAttribute('required', 'required');
                promptNotRequired.style.display = 'none';
                
                // Set appropriate placeholder for required prompts
                if (modelConfig.type === 'text-to-image') {
                    promptInput.placeholder = "e.g., A futuristic city skyline with flying cars and neon lights, photorealistic, detailed, 8k";
                } else {
                    promptInput.placeholder = "Describe what you want to see in detail...";
                }
            }
        } else {
            promptSection.style.display = 'none';
        }
    }
}

// Export for use in other files
window.ModelUIManager = ModelUIManager; 