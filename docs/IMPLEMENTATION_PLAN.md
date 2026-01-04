# MemoryVault Implementation Plan

## Phase 1: Database Setup (Week 1)

### 1.1 Choose ORM and Database
- **ORM**: SQLAlchemy (Python standard)
- **Database**: Start with SQLite, migrate to PostgreSQL later
- **Migrations**: Alembic for schema versioning

### 1.2 Install Dependencies
```bash
pip install sqlalchemy alembic psycopg2-binary python-dotenv
```

### 1.3 Create Database Models
- Create `models/database.py` with SQLAlchemy models
- Define all tables (users, decks, cards, card_content, media_files, review_history)
- Set up relationships and constraints

### 1.4 Initialize Database
- Create Alembic migration scripts
- Run initial migration
- Create seed data for testing

### 1.5 Update Card Model
- Refactor existing Card model to use database
- Add database persistence methods
- Maintain backward compatibility

---

## Phase 2: File Storage System (Week 2)

### 2.1 Install File Handling Dependencies
```bash
pip install pillow pydub werkzeug python-magic
```

### 2.2 Create File Storage Module
- Create `services/file_storage.py`
- Implement local filesystem storage
- Add file validation and processing

### 2.3 Image Processing
- Implement image upload handler
- Add thumbnail generation
- Image optimization and compression
- EXIF data stripping

### 2.4 Audio Processing
- Implement audio upload handler
- Add audio validation
- Format conversion (to MP3)
- Duration extraction

### 2.5 File Deduplication
- Implement checksum calculation
- Add duplicate detection
- Create file reference counting

---

## Phase 3: API Endpoints (Week 3)

### 3.1 File Upload Endpoints
```
POST /api/upload/image
POST /api/upload/audio
GET  /api/files/{file_id}
DELETE /api/files/{file_id}
```

### 3.2 Enhanced Card Endpoints
```
POST /api/cards - Create card with media support
PUT  /api/cards/{id} - Update card with media
GET  /api/cards/{id} - Get card with media URLs
```

### 3.3 Deck Management Endpoints
```
GET    /api/decks - List all decks
POST   /api/decks - Create deck
GET    /api/decks/{id} - Get deck details
PUT    /api/decks/{id} - Update deck
DELETE /api/decks/{id} - Delete deck
GET    /api/decks/{id}/cards - Get cards in deck
```

### 3.4 Review Endpoints
```
GET  /api/review/due - Get cards due for review
POST /api/review/{card_id} - Submit review result
GET  /api/review/stats - Get review statistics
```

---

## Phase 4: Frontend Integration (Week 4)

### 4.1 Update Card Creation UI
- Add file upload buttons
- Implement drag-and-drop for images
- Add audio recording capability (optional)
- Show upload progress

### 4.2 Create Card List View
- Display all cards in a deck
- Show thumbnails for image cards
- Add search and filter
- Pagination

### 4.3 Build Review Interface
- Create study session UI
- Implement card flip animation
- Add audio playback controls
- Track review results

### 4.4 Add Deck Management UI
- Create deck list view
- Add deck creation form
- Deck statistics dashboard

---

## Phase 5: Advanced Features (Week 5+)

### 5.1 User Authentication
- Implement user registration
- Add login/logout
- Session management
- Password reset

### 5.2 Spaced Repetition Algorithm
- Implement SM-2 algorithm (or similar)
- Calculate optimal review intervals
- Adjust difficulty based on performance

### 5.3 Statistics and Analytics
- Review history visualization
- Learning progress charts
- Box distribution graphs
- Study streak tracking

### 5.4 Cloud Storage Integration (Optional)
- Add AWS S3 support
- Implement signed URLs
- CDN integration
- Migration tool from local to cloud

---

## Technology Stack Summary

### Backend
- **Framework**: Flask
- **ORM**: SQLAlchemy
- **Database**: SQLite → PostgreSQL
- **Migrations**: Alembic
- **File Processing**: Pillow (images), pydub (audio)
- **Validation**: python-magic, werkzeug

### Frontend
- **HTML/CSS/JavaScript** (vanilla)
- **Future**: Consider React/Vue for complex UI

### Storage
- **Development**: Local filesystem
- **Production**: AWS S3 / Azure Blob / GCS

### Deployment
- **Development**: Local Flask server
- **Production**: Gunicorn + Nginx
- **Hosting**: Heroku / AWS / DigitalOcean / Render

---

## File Structure (After Implementation)

```
MemoryVault/
├── app.py                      # Main Flask app
├── config.py                   # Configuration
├── requirements.txt            # Dependencies
├── .env                        # Environment variables
├── models/
│   ├── __init__.py
│   ├── card.py                 # Card business logic
│   ├── content.py              # Content types
│   └── database.py             # SQLAlchemy models
├── services/
│   ├── __init__.py
│   ├── file_storage.py         # File upload/storage
│   ├── image_processor.py      # Image processing
│   ├── audio_processor.py      # Audio processing
│   └── leitner.py              # Leitner algorithm
├── routes/
│   ├── __init__.py
│   ├── cards.py                # Card endpoints
│   ├── files.py                # File endpoints
│   ├── decks.py                # Deck endpoints
│   └── review.py               # Review endpoints
├── migrations/                 # Alembic migrations
├── uploads/                    # Local file storage
│   ├── images/
│   └── audio/
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/                # Public file access
├── templates/
│   ├── index.html
│   ├── cards.html
│   └── review.html
└── docs/
    ├── BACKEND_ARCHITECTURE.md
    ├── IMPLEMENTATION_PLAN.md
    └── API_DOCUMENTATION.md
```

