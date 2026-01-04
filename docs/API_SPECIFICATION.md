# MemoryVault API Specification

## Base URL
```
Development: http://localhost:5000/api
Production: https://api.memoryvault.com/api
```

## Authentication
```
Authorization: Bearer {token}
```

---

## File Upload Endpoints

### Upload Image
```http
POST /api/upload/image
Content-Type: multipart/form-data

Parameters:
- file: File (required) - Image file (JPEG, PNG, WebP, GIF)
- alt_text: String (optional) - Alternative text for accessibility

Response 201:
{
  "file_id": 123,
  "file_type": "image",
  "url": "/api/files/123",
  "thumbnail_url": "/api/files/123/thumbnail",
  "original_filename": "photo.jpg",
  "file_size": 245678,
  "mime_type": "image/jpeg"
}

Errors:
- 400: Invalid file type or size
- 413: File too large (max 10MB)
- 507: User storage quota exceeded
```

### Upload Audio
```http
POST /api/upload/audio
Content-Type: multipart/form-data

Parameters:
- file: File (required) - Audio file (MP3, WAV, OGG, M4A)

Response 201:
{
  "file_id": 124,
  "file_type": "audio",
  "url": "/api/files/124",
  "original_filename": "pronunciation.mp3",
  "file_size": 512000,
  "mime_type": "audio/mpeg",
  "duration_seconds": 3.5
}

Errors:
- 400: Invalid file type or size
- 413: File too large (max 25MB)
- 422: Audio duration exceeds limit (max 5 minutes)
```

### Get File
```http
GET /api/files/{file_id}

Response 200:
- Returns the actual file with appropriate Content-Type header
- Supports range requests for audio streaming

Errors:
- 404: File not found
- 403: Unauthorized access
```

### Delete File
```http
DELETE /api/files/{file_id}

Response 204: No content

Errors:
- 404: File not found
- 403: Unauthorized
- 409: File is in use by cards
```

---

## Card Endpoints

### Create Card
```http
POST /api/cards
Content-Type: application/json

Request Body:
{
  "deck_id": 1,
  "front": [
    {
      "type": "text",
      "value": "What is this?"
    },
    {
      "type": "image",
      "file_id": 123
    }
  ],
  "back": [
    {
      "type": "text",
      "value": "The Eiffel Tower"
    },
    {
      "type": "audio",
      "file_id": 124
    }
  ]
}

Response 201:
{
  "id": 456,
  "deck_id": 1,
  "box_number": 1,
  "front": [
    {
      "type": "text",
      "value": "What is this?"
    },
    {
      "type": "image",
      "file_id": 123,
      "url": "/api/files/123",
      "thumbnail_url": "/api/files/123/thumbnail"
    }
  ],
  "back": [
    {
      "type": "text",
      "value": "The Eiffel Tower"
    },
    {
      "type": "audio",
      "file_id": 124,
      "url": "/api/files/124",
      "duration_seconds": 3.5
    }
  ],
  "created_at": "2026-01-04T10:30:00Z",
  "last_reviewed": null,
  "review_count": 0,
  "next_review_date": "2026-01-04T10:30:00Z"
}
```

### Get Card
```http
GET /api/cards/{card_id}

Response 200:
{
  "id": 456,
  "deck_id": 1,
  "box_number": 1,
  "front": [...],
  "back": [...],
  "created_at": "2026-01-04T10:30:00Z",
  "last_reviewed": "2026-01-05T14:20:00Z",
  "review_count": 3,
  "next_review_date": "2026-01-08T10:30:00Z",
  "ease_factor": 2.5,
  "interval_days": 3
}
```

### Update Card
```http
PUT /api/cards/{card_id}
Content-Type: application/json

Request Body:
{
  "front": [...],  // Optional
  "back": [...]    // Optional
}

Response 200:
{
  "id": 456,
  "deck_id": 1,
  // ... updated card data
}
```

### Delete Card
```http
DELETE /api/cards/{card_id}

Response 204: No content

Note: Associated media files are NOT deleted (may be used by other cards)
```

### List Cards
```http
GET /api/cards?deck_id={deck_id}&box={box}&page={page}&limit={limit}

Query Parameters:
- deck_id: Integer (optional) - Filter by deck
- box: Integer (optional) - Filter by box number (1-5)
- page: Integer (default: 1)
- limit: Integer (default: 20, max: 100)

Response 200:
{
  "cards": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

---

## Deck Endpoints

### Create Deck
```http
POST /api/decks
Content-Type: application/json

Request Body:
{
  "name": "French Vocabulary",
  "description": "Common French words and phrases"
}

Response 201:
{
  "id": 1,
  "name": "French Vocabulary",
  "description": "Common French words and phrases",
  "card_count": 0,
  "created_at": "2026-01-04T10:30:00Z",
  "updated_at": "2026-01-04T10:30:00Z"
}
```

### List Decks
```http
GET /api/decks

Response 200:
{
  "decks": [
    {
      "id": 1,
      "name": "French Vocabulary",
      "description": "Common French words and phrases",
      "card_count": 45,
      "created_at": "2026-01-04T10:30:00Z",
      "updated_at": "2026-01-05T14:20:00Z"
    }
  ]
}
```

### Get Deck
```http
GET /api/decks/{deck_id}

Response 200:
{
  "id": 1,
  "name": "French Vocabulary",
  "description": "Common French words and phrases",
  "card_count": 45,
  "box_distribution": {
    "1": 10,
    "2": 15,
    "3": 12,
    "4": 5,
    "5": 3
  },
  "created_at": "2026-01-04T10:30:00Z",
  "updated_at": "2026-01-05T14:20:00Z"
}
```

### Update Deck
```http
PUT /api/decks/{deck_id}
Content-Type: application/json

Request Body:
{
  "name": "Updated Name",
  "description": "Updated description"
}

Response 200:
{
  "id": 1,
  "name": "Updated Name",
  // ... updated deck data
}
```

### Delete Deck
```http
DELETE /api/decks/{deck_id}

Response 204: No content

Note: Deletes all cards in the deck
```

---

## Review Endpoints

### Get Due Cards
```http
GET /api/review/due?deck_id={deck_id}&limit={limit}

Query Parameters:
- deck_id: Integer (optional) - Filter by deck
- limit: Integer (default: 20) - Max cards to return

Response 200:
{
  "cards": [
    {
      "id": 456,
      "deck_id": 1,
      "box_number": 2,
      "front": [...],
      "back": [...],
      "next_review_date": "2026-01-04T10:30:00Z"
    }
  ],
  "total_due": 15
}
```

### Submit Review
```http
POST /api/review/{card_id}
Content-Type: application/json

Request Body:
{
  "correct": true,
  "difficulty": 3,  // 1-5 scale (optional)
  "response_time_ms": 3500  // Optional
}

Response 200:
{
  "card_id": 456,
  "previous_box": 2,
  "new_box": 3,
  "next_review_date": "2026-01-07T10:30:00Z",
  "interval_days": 3,
  "ease_factor": 2.6
}
```

### Get Review Statistics
```http
GET /api/review/stats?deck_id={deck_id}&period={period}

Query Parameters:
- deck_id: Integer (optional) - Filter by deck
- period: String (optional) - 'day', 'week', 'month', 'year', 'all'

Response 200:
{
  "total_reviews": 250,
  "correct_reviews": 200,
  "accuracy": 0.80,
  "cards_mastered": 15,  // Cards in box 5
  "current_streak": 7,  // Days
  "longest_streak": 14,
  "reviews_by_day": [
    {"date": "2026-01-01", "count": 20, "correct": 16},
    {"date": "2026-01-02", "count": 25, "correct": 21}
  ],
  "box_distribution": {
    "1": 10,
    "2": 15,
    "3": 12,
    "4": 5,
    "5": 3
  }
}
```

---

## Error Responses

All endpoints may return these standard errors:

```http
400 Bad Request
{
  "error": "Invalid request",
  "message": "Detailed error message",
  "field": "field_name"  // If applicable
}

401 Unauthorized
{
  "error": "Unauthorized",
  "message": "Authentication required"
}

403 Forbidden
{
  "error": "Forbidden",
  "message": "You don't have permission to access this resource"
}

404 Not Found
{
  "error": "Not found",
  "message": "Resource not found"
}

413 Payload Too Large
{
  "error": "File too large",
  "message": "Maximum file size is 10MB for images, 25MB for audio"
}

422 Unprocessable Entity
{
  "error": "Validation failed",
  "message": "Invalid data provided",
  "errors": {
    "field_name": ["Error message 1", "Error message 2"]
  }
}

500 Internal Server Error
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

