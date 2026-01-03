# MemoryVault - Quick Start Guide

## Setup

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

The app will start on `http://localhost:5000`

## Using the UI

### Creating Cards

1. **Open your browser** and go to `http://localhost:5000`

2. **Choose content type** for the front:
   - Click "📝 Text" for text content
   - Click "🖼️ Image" for image content

3. **Enter front content**:
   - For text: Type your question or prompt
   - For image: Enter an image URL and optional alt text

4. **Choose content type** for the back:
   - Same options as front

5. **Enter back content**:
   - For text: Type your answer
   - For image: Enter an image URL and optional alt text

6. **Preview your card**:
   - See live preview on the right
   - Click "Flip Card" to see both sides

7. **Create the card**:
   - Click "Create Card" button
   - Success message will appear
   - Form will clear automatically

### Example Image URLs for Testing

Try these free image URLs:
- `https://picsum.photos/400/300` - Random image
- `https://via.placeholder.com/400x300` - Placeholder image
- `https://source.unsplash.com/random/400x300` - Random Unsplash image

## API Endpoints

The backend API is available at:

- `GET /api` - API information
- `GET /api/cards` - Get all cards
- `POST /api/cards` - Create a card
- `GET /api/cards/<id>` - Get specific card
- `PUT /api/cards/<id>` - Update a card
- `DELETE /api/cards/<id>` - Delete a card
- `GET /api/boxes` - Get all boxes
- `POST /api/review` - Review a card

See `API_EXAMPLES.md` for detailed API usage.

## Current Status

✅ **Completed:**
- Card model with text/image support
- Card creation UI
- Live preview with flip animation
- API endpoints for CRUD operations

🚧 **Coming Soon:**
- Backend integration (save cards to database)
- Card review interface
- Leitner box visualization
- Study session mode
- Progress tracking

## Notes

- Currently, the UI doesn't save cards (backend integration coming next)
- Cards are stored in memory only (will be lost on server restart)
- Image URLs must be publicly accessible

