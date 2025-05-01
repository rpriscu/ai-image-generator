"""
Configuration for available AI image generation models.
Each model has specific settings for API endpoints and parameters.
"""

AVAILABLE_MODELS = {
    'flux': {
        'name': 'FLUX.1 [dev]',
        'endpoint': 'fal-ai/flux',
        'type': 'text-to-image',
        'description': 'Specialized in high-quality images with great prompt adherence.',
        'detailed_info': {
            'what_is': '🧠 What Is FLUX.1 [dev]?\n\nFLUX.1 [dev] is a 12-billion-parameter flow transformer model developed by Black Forest Labs. It specializes in generating high-quality images from text prompts, offering capabilities comparable to leading models like Midjourney v6.1 and DALL·E 3. Trained using guidance distillation, FLUX.1 [dev] ensures efficient and accurate prompt adherence. The model is accessible through platforms like fal.ai and Hugging Face, making it accessible for various applications.',
            'use_cases': '🎯 Best Use Cases\n\nFLUX.1 [dev] is versatile and caters to a wide range of creative needs:\n• Concept Art & Illustration: Generate detailed visuals for characters, environments, and props.\n• Product Design: Visualize product concepts or packaging designs.\n• Marketing & Advertising: Create compelling visuals for campaigns and promotions.\n• Educational Content: Develop illustrative materials for learning resources.\n• Personal Projects: Bring imaginative ideas to life with high-quality imagery.\n\nNote: FLUX.1 [dev] is intended for non-commercial use. For commercial applications, consider using FLUX.1 [pro].',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of FLUX.1 [dev], consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about the subject, style, and environment.\n• Use Modifiers: Incorporate terms like "photorealistic," "digital painting," or "cinematic lighting" to guide the model\'s output.\n• Structure: Organize prompts in segments, such as subject, style, and background, to enhance clarity.'
        }
    },
    'flux_pro': {
        'name': 'FLUX.1 [pro]',
        'endpoint': 'fal-ai/flux',  # Try standard flux endpoint with pro params
        'type': 'text-to-image',
        'description': 'Premium version of FLUX optimized for commercial use with advanced capabilities.',
        'use_rest_api': True,  # Flag to use REST API directly rather than fal_client
        'api_format': 'flux-pro',  # Special format for this model
        'params': {
            'model_version': 'v1.1-ultra-finetuned',  # This specifies that we want the Pro version
            'image_size': '1024x1024',  # Default size
            'num_inference_steps': 30    # Default steps
        },
        'alt_formats': [
            {
                'endpoint': 'fal-ai/flux-pro',
                'payload': {
                    'prompt': '{prompt}',
                    'finetune_id': ''
                }
            },
            {
                'endpoint': 'fal-ai/flux-pro-v1.1',
                'payload': {
                    'prompt': '{prompt}'
                }
            }
        ],
        'detailed_info': {
            'what_is': '🧠 What Is FLUX.1 [pro]?\n\nFLUX.1 [pro] is a state-of-the-art text-to-image model developed by Black Forest Labs, designed specifically for commercial and professional creative workflows. It excels in generating high-quality images from textual prompts, offering superior prompt adherence, visual fidelity, and output diversity. The model is accessible via API through platforms like fal.ai.\n\nAn enhanced version, FLUX1.1 [pro], offers:\n• Faster Generation: Up to six times faster than its predecessor, improving workflow efficiency.\n• Improved Image Quality: Enhanced composition, detail, and artistic fidelity.\n• High-Resolution Outputs: Supports ultra-high-resolution images up to 4 megapixels in Ultra mode.',
            'use_cases': '🎯 Best Use Cases\n\nFLUX.1 [pro] is versatile and suitable for various commercial applications:\n• Marketing & Advertising: Create compelling visuals for campaigns, social media, and promotional materials.\n• Product Design: Visualize product concepts, packaging designs, and prototypes.\n• Entertainment Industry: Generate assets for movies, TV shows, video games, and animations.\n• Art & Design: Produce unique artwork, explore new creative directions, and experiment with styles.\n• Education & Research: Develop illustrative materials and explore AI-driven creative processes.',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of FLUX.1 [pro], consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about the subject, style, and environment.\n• Use Modifiers: Incorporate terms like "photorealistic," "digital painting," or "cinematic lighting" to guide the model\'s output.\n• Structure: Organize prompts in segments, such as subject, style, and background, to enhance clarity.\n\nFor more detailed guidance, refer to the <a href="https://www.reddit.com/r/FluxAI/comments/1imha0t/flux1_prompt_manual_a_foundational_guide/" target="_blank">FLUX.1 Prompt Manual</a>.'
        }
    },
    'recraft': {
        'name': 'Recraft V3',
        'endpoint': 'fal-ai/recraft-v3',
        'type': 'text-to-image',
        'description': 'Creates vector-art style images with clean lines and shapes.',
        'params': {
            'style_name': 'vector-art'
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
        'type': 'text-to-image',
        'description': 'Creates detailed images with high fidelity.',
        'params': {
            'num_inference_steps': 30,
            'guidance_scale': 7.5
        },
        'detailed_info': {
            'what_is': '🧠 What Is Stable Diffusion V3?\n\nStable Diffusion V3 is a state-of-the-art text-to-image generative AI model developed by Stability AI. It employs a Multimodal Diffusion Transformer (MMDiT) architecture, enabling the generation of high-quality images from textual prompts. The model excels in understanding complex prompts, rendering detailed images, and handling typography effectively.\n\nThrough fal.ai, users can access Stable Diffusion V3 via API, facilitating seamless integration into applications and workflows.',
            'use_cases': '🎯 Best Use Cases\n\nStable Diffusion V3 is versatile and caters to a wide range of creative needs:\n• Concept Art & Illustration: Generate detailed visuals for characters, environments, and props.\n• Product Design: Visualize product concepts, packaging designs, and prototypes.\n• Marketing & Advertising: Create compelling visuals for campaigns and promotions.\n• Entertainment Industry: Produce assets for movies, TV shows, video games, and animations.\n• Educational Content: Develop illustrative materials for learning resources.\n• Typography & Graphic Design: Design posters, logos, and other materials requiring precise text rendering.',
            'tips': '💡 Tips & Tricks\n\nTo maximize the potential of Stable Diffusion V3 via fal.ai, consider the following strategies:\n\n1. Crafting Effective Prompts\n• Be Descriptive: Include specific details about the subject, style, and environment.\n• Use Structured Prompts: Follow a structure like: "A [style] of [main content]. [Detailed description]. [Background details]. [Style modifiers]."\n• Specify Text Elements: If incorporating text into images, clearly define the text content, size, and placement.\n\n2. Utilizing Negative Prompts\n\nNegative prompts allow you to specify elements you want to avoid in the generated image. For example, adding "blurry, low quality" to the negative prompt can help produce sharper images.\n\n3. Adjusting Parameters\n• CFG Scale (Classifier-Free Guidance Scale): Controls how closely the image adheres to the prompt. Higher values (e.g., 7-12) make the image more aligned with the prompt, while lower values allow for more creativity.\n• Sampling Steps: Increasing the number of steps can lead to more detailed images but will take longer to generate.\n\n4. Leveraging Advanced Features\n• Inpainting: Edit specific parts of an image by masking and providing a new prompt.\n• Outpainting: Extend an image beyond its original borders to create a larger scene.\n• ControlNet: Incorporate additional conditions like pose or depth maps to guide image generation more precisely.'
        }
    }
} 