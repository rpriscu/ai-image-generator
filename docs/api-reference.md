# AI Image Generator API Reference

## Overview

The AI Image Generator provides a RESTful API for generating images and videos using various AI models. All endpoints require authentication except for the login endpoint.

## Base URL

- Development: `http://localhost:8080`
- Production: `https://your-domain.com`

## Authentication

The API uses session-based authentication. You must be logged in to access most endpoints.

## Endpoints

### Authentication

#### POST `/auth/login`

Login with Google OAuth or admin credentials.

**Request Body:**
```json
{
  "credential": "google_oauth_token"
}
```
or
```json
{
  "username": "admin_username",
  "password": "admin_password"
}
```

**Response:**
```json
{
  "success": true,
  "redirect_url": "/dashboard"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

#### GET `/auth/logout`

Logout the current user.

**Response:**
Redirects to login page

---

### Generation

#### POST `/api/generate`

Generate images or videos using AI models.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Authentication: Required

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| prompt | string | Yes* | Text description for generation |
| model | string | Yes | Model ID (e.g., 'flux', 'stable_diffusion') |
| image | file | No* | Reference image for img2img or video models |
| mask | file | No* | Mask image for inpainting models |

*Requirements vary by model type:
- Text-to-image models: `prompt` required
- Image-to-video models: `image` required, `prompt` optional
- Inpainting models: `prompt`, `image`, and `mask` required

**Supported Models:**
- `flux` - FLUX.1 [dev] (text-to-image)
- `recraft` - Recraft V3 (vector illustrations)
- `stable_diffusion` - Stable Diffusion V3 (hybrid)
- `stable_video` - Stable Video Diffusion (image-to-video)
- `flux_pro` - FLUX.1 [pro] Fill (inpainting)

**Success Response:**
```json
{
  "results": [
    {
      "url": "/static/generated/img_20240101_123456.png",
      "id": 123,
      "type": "image",
      "thumbnail_url": null
    }
  ]
}
```

**Video Response:**
```json
{
  "results": [
    {
      "url": "/video/short_key_123456",
      "id": 124,
      "type": "video",
      "thumbnail_url": "/static/generated/thumbnails/video_124_thumb.jpg"
    }
  ]
}
```

**Error Response:**
```json
{
  "error": "Invalid model selected"
}
```

---

### Assets

#### GET `/library`

Get all user's generated assets.

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| type | string | "all" | Filter by type: "all", "image", "video" |
| sort | string | "newest" | Sort order: "newest", "oldest" |

**Response:**
HTML page with asset library

#### GET `/asset/{asset_id}`

Get details for a specific asset.

**Parameters:**
- `asset_id` (int): The asset ID

**Response:**
HTML page with asset details

#### GET `/asset/{asset_id}/download`

Download an asset file.

**Parameters:**
- `asset_id` (int): The asset ID

**Response:**
Binary file download

#### DELETE `/api/assets/{asset_id}`

Delete an asset.

**Parameters:**
- `asset_id` (int): The asset ID

**Success Response:**
```json
{
  "success": true,
  "message": "Asset deleted successfully"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Asset not found"
}
```

---

### Model Information

#### GET `/api/model-info/{model_id}`

Get detailed information about a specific model.

**Parameters:**
- `model_id` (string): The model ID

**Success Response:**
```json
{
  "name": "FLUX.1 [dev]",
  "info": {
    "what_is": "Description of the model...",
    "use_cases": "Perfect for...",
    "tips": "For best results..."
  }
}
```

**Error Response:**
```json
{
  "error": "Invalid model ID"
}
```

---

### Generation Status

#### GET `/api/generation-status/{request_id}`

Check the status of an ongoing generation request.

**Parameters:**
- `request_id` (string): The generation request ID

**Success Response (Completed):**
```json
{
  "status": "completed",
  "results": [
    {
      "url": "/static/generated/img_123.png",
      "id": 125,
      "type": "image",
      "thumbnail_url": null
    }
  ]
}
```

**Pending Response:**
```json
{
  "status": "pending"
}
```

**Error Response:**
```json
{
  "error": "Generation likely failed or timed out"
}
```

---

### Utility Endpoints

#### POST `/api/delete-image`

Delete an image by URL (legacy endpoint).

**Request Body:**
```json
{
  "url": "/static/generated/img_123.png"
}
```

**Response:**
```json
{
  "success": true
}
```

#### POST `/api/clear-generation-state`

Clear generation state (debugging endpoint).

**Response:**
```json
{
  "success": true,
  "message": "Generation state cleared successfully"
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input parameters |
| 401 | Unauthorized - Not logged in |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |
| 502 | Bad Gateway - External API error |

## Rate Limiting

- Maximum 100 requests per hour per user
- Maximum 50 generations per day per user

## Examples

### Generate Images with FLUX

```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Cookie: session=your-session-cookie" \
  -F "prompt=A beautiful sunset over mountains" \
  -F "model=flux"
```

### Generate Video from Image

```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Cookie: session=your-session-cookie" \
  -F "model=stable_video" \
  -F "image=@/path/to/image.jpg"
```

### Inpainting with FLUX Pro

```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Cookie: session=your-session-cookie" \
  -F "prompt=Replace with a red car" \
  -F "model=flux_pro" \
  -F "image=@/path/to/image.jpg" \
  -F "mask=@/path/to/mask.png"
```

## Notes

1. All file uploads are limited to 10MB for images and 50MB for videos
2. Generated content URLs may be shortened for videos
3. Session cookies expire after 24 hours of inactivity
4. Some models may have additional parameters not documented here 