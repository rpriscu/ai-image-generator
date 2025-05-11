"""
Configuration for available AI image generation models.
Each model has specific settings for API endpoints and parameters.
"""

AVAILABLE_MODELS = {
    'flux': {
        'name': 'FLUX.1 [dev]',
        'endpoint': 'fal-ai/flux',
        'type': 'hybrid',
        'supports_image_input': True,
        'description': 'Specialized in high-quality images with great prompt adherence. Supports both text prompts and image inputs.',
        'detailed_info': {
            'what_is': '🧠 What Is FLUX.1 [dev]?\n\nFLUX.1 [dev] is a 12-billion-parameter flow transformer model developed by Black Forest Labs. It specializes in generating high-quality images from text prompts, offering capabilities comparable to leading models like Midjourney v6.1 and DALL·E 3. Trained using guidance distillation, FLUX.1 [dev] ensures efficient and accurate prompt adherence. The model is accessible through platforms like fal.ai and Hugging Face, making it accessible for various applications.',
            'use_cases': '🎯 Best Use Cases\n\nFLUX.1 [dev] is versatile and caters to a wide range of creative needs:\n• Concept Art & Illustration: Generate detailed visuals for characters, environments, and props.\n• Product Design: Visualize product concepts or packaging designs.\n• Marketing & Advertising: Create compelling visuals for campaigns and promotions.\n• Educational Content: Develop illustrative materials for learning resources.\n• Personal Projects: Bring imaginative ideas to life with high-quality imagery.\n\nNote: FLUX.1 [dev] is intended for non-commercial use. For commercial applications, consider using FLUX.1 [pro].',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of FLUX.1 [dev], consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about the subject, style, and environment.\n• Use Modifiers: Incorporate terms like "photorealistic," "digital painting," or "cinematic lighting" to guide the model\'s output.\n• Structure: Organize prompts in segments, such as subject, style, and background, to enhance clarity.'
        }
    },
    'flux_pro': {
        'name': 'FLUX.1 [pro] Fill',
        'endpoint': 'fal-ai/flux-pro/v1/fill',  # Updated for Fill API
        'type': 'hybrid',
        'supports_image_input': True,  # Updated to support image input
        'description': 'Premium Fill version of FLUX optimized for inpainting/outpainting with high-quality style transfers and image modifications.',
        'use_rest_api': True,  # Flag to use REST API directly rather than fal_client
        'api_format': 'flux-pro-fill',  # Special format for this model
        'params': {
            'safety_tolerance': '2',  # Default safety tolerance
            'output_format': 'jpeg',  # Default output format
            'num_images': 1,          # Default number of images
            'sync_mode': True         # Wait for the result
        },
        'alt_formats': [
            {
                'endpoint': 'fal-ai/flux-pro/v1/fill',
                'payload': {
                    'prompt': '{prompt}',
                    'image_url': '{image_url}',
                    'mask_url': '{mask_url}',
                    'safety_tolerance': '2',
                    'output_format': 'jpeg',
                    'num_images': 1,
                    'sync_mode': True
                }
            }
        ],
        'detailed_info': {
            'what_is': '🧠 What Is FLUX.1 [pro] Fill?\n\nFLUX.1 [pro] Fill is a high-performance endpoint for the FLUX.1 [pro] model that enables rapid transformation of existing images, delivering high-quality style transfers and image modifications with the core FLUX capabilities. It is specifically designed for inpainting and outpainting tasks, allowing you to seamlessly modify parts of existing images while maintaining consistency.',
            'use_cases': '🎯 Best Use Cases\n\nFLUX.1 [pro] Fill is ideal for various professional applications:\n• Image Editing: Modify or remove specific elements from photos while preserving the overall visual quality.\n• Creative Transformations: Apply targeted style changes to defined areas of images.\n• Content Completion: Fill in missing areas or extend images beyond their original boundaries.\n• Brand Adaptation: Update product visuals by changing specific elements while maintaining brand consistency.',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of FLUX.1 [pro] Fill, consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about what you want to appear in the masked area.\n• Maintain Consistency: Ensure your prompt aligns with the visual style of the unmasked areas for seamless integration.\n• Consider Context: Reference surrounding elements to create a cohesive overall image.\n\n2. Creating Effective Masks\n• Clear Boundaries: Define mask edges clearly to control precisely where modifications occur.\n• Appropriate Coverage: Mask only the areas you want to change, leaving the rest untouched.\n• Feathering: Consider slight feathering at mask edges for smoother transitions.'
        }
    },
    'recraft': {
        'name': 'Recraft V3',
        'endpoint': 'fal-ai/recraft-v3',
        'type': 'text-to-image',
        'supports_image_input': False,
        'description': 'Creates vector-art style images with clean lines and shapes. Text-to-image only.',
        'params': {
            'style': 'vector_illustration'
        },
        'detailed_info': {
            'what_is': '🧠 What Is Recraft V3?\n\nRecraft V3 is a state-of-the-art AI model developed by Recraft, specializing in text-to-image generation with a focus on design language. It excels in creating high-quality images, including vector graphics, from textual prompts. Recraft V3 is renowned for its ability to generate images with precise text placement, brand style consistency, and support for various artistic styles.',
            'use_cases': '🎯 Best Use Cases\n\nRecraft V3 is versatile and caters to a wide range of creative needs:\n• Branding & Marketing: Generate logos, icons, and promotional materials that align with brand aesthetics.\n• Product Design: Visualize product concepts, packaging designs, and prototypes.\n• Editorial & Publishing: Create compelling visuals for articles, book covers, and digital publications.\n• Web & App Design: Develop UI elements, illustrations, and other assets tailored to specific design languages.\n• Educational Content: Produce illustrative materials for learning resources.',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of Recraft V3, consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about the subject, style, and environment.\n• Use Structured Prompts: Follow a structure like: "A [style] of [main content]. [Detailed description]. [Background details]. [Style modifiers]."\n• Specify Text Elements: If incorporating text into images, clearly define the text content, size, and placement.'
        }
    },
    'stable_diffusion': {
        'name': 'Stable Diffusion V3',
        'endpoint': 'fal-ai/stable-diffusion-v3-medium',
        'type': 'hybrid',
        'description': 'Creates detailed images with high fidelity. Supports both text prompts and image inputs.',
        'supports_image_input': True,
        'params': {
            'num_inference_steps': 30,
            'guidance_scale': 7.5,
            'strength': 0.75
        },
        'detailed_info': {
            'what_is': '🧠 What Is Stable Diffusion V3?\n\nStable Diffusion V3 is a state-of-the-art text-to-image generative AI model developed by Stability AI. It employs a Multimodal Diffusion Transformer (MMDiT) architecture, enabling the generation of high-quality images from textual prompts. The model excels in understanding complex prompts, rendering detailed images, and handling typography effectively.\n\nThrough fal.ai, users can access Stable Diffusion V3 via API, facilitating seamless integration into applications and workflows.',
            'use_cases': '🎯 Best Use Cases\n\nStable Diffusion V3 is versatile and caters to a wide range of creative needs:\n• Concept Art & Illustration: Generate detailed visuals for characters, environments, and props.\n• Product Design: Visualize product concepts, packaging designs, and prototypes.\n• Marketing & Advertising: Create compelling visuals for campaigns and promotions.\n• Entertainment Industry: Produce assets for movies, TV shows, video games, and animations.\n• Educational Content: Develop illustrative materials for learning resources.\n• Typography & Graphic Design: Design posters, logos, and other materials requiring precise text rendering.',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of Stable Diffusion V3 via fal.ai, consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about the subject, style, and environment.\n• Use Structured Prompts: Follow a structure like: "A [style] of [main content]. [Detailed description]. [Background details]. [Style modifiers]."\n• Specify Text Elements: If incorporating text into images, clearly define the text content, size, and placement.\n\n2. Utilizing Negative Prompts\n\nNegative prompts allow you to specify elements you want to avoid in the generated image. For example, adding "blurry, low quality" to the negative prompt can help produce sharper images.\n\n3. Adjusting Parameters\n• CFG Scale (Classifier-Free Guidance Scale): Controls how closely the image adheres to the prompt. Higher values (e.g., 7-12) make the image more aligned with the prompt, while lower values allow for more creativity.\n• Sampling Steps: Increasing the number of steps can lead to more detailed images but will take longer to generate.\n\n4. Leveraging Advanced Features\n• Inpainting: Edit specific parts of an image by masking and providing a new prompt.\n• Outpainting: Extend an image beyond its original borders to create a larger scene.\n• ControlNet: Incorporate additional conditions like pose or depth maps to guide image generation more precisely.'
        }
    }
} 