# MemoryVault API Examples

## Card Content Format

Cards now support both **text** and **image** content for both front and back sides.

### Content Types

#### Text Content
```json
{
  "type": "text",
  "value": "What is the capital of France?"
}
```

#### Image Content
```json
{
  "type": "image",
  "value": "https://example.com/image.jpg",
  "alt_text": "A picture of the Eiffel Tower"
}
```

## API Endpoints

### Create a Card with Text

**Request:**
```bash
curl -X POST http://localhost:5000/api/cards \
  -H "Content-Type: application/json" \
  -d '{
    "front": "What is Flask?",
    "back": "A Python web framework"
  }'
```

Or with explicit content type:
```bash
curl -X POST http://localhost:5000/api/cards \
  -H "Content-Type: application/json" \
  -d '{
    "front": {
      "type": "text",
      "value": "What is Flask?"
    },
    "back": {
      "type": "text",
      "value": "A Python web framework"
    }
  }'
```

### Create a Card with Image

**Request:**
```bash
curl -X POST http://localhost:5000/api/cards \
  -H "Content-Type: application/json" \
  -d '{
    "front": {
      "type": "image",
      "value": "https://example.com/eiffel-tower.jpg",
      "alt_text": "Eiffel Tower"
    },
    "back": {
      "type": "text",
      "value": "Paris, France"
    }
  }'
```

### Create a Card with Mixed Content

**Request:**
```bash
curl -X POST http://localhost:5000/api/cards \
  -H "Content-Type: application/json" \
  -d '{
    "front": "What landmark is this?",
    "back": {
      "type": "image",
      "value": "https://example.com/statue-of-liberty.jpg",
      "alt_text": "Statue of Liberty"
    }
  }'
```

### Update a Card

**Request:**
```bash
curl -X PUT http://localhost:5000/api/cards/1 \
  -H "Content-Type: application/json" \
  -d '{
    "front": {
      "type": "text",
      "value": "Updated question"
    }
  }'
```

### Response Format

All card responses now include structured content:

```json
{
  "card": {
    "id": 1,
    "front": {
      "type": "text",
      "value": "What is Flask?"
    },
    "back": {
      "type": "text",
      "value": "A Python web framework"
    },
    "box": 1,
    "created_at": "2026-01-03T10:30:00",
    "last_reviewed": null,
    "review_count": 0
  }
}
```

## Backward Compatibility

The API maintains backward compatibility. You can still send simple strings:

```json
{
  "front": "Question",
  "back": "Answer"
}
```

These will automatically be converted to text content internally.

