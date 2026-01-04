# MemoryVault Backend Architecture

## Overview

The backend consists of two main components:
1. **Database** - PostgreSQL/SQLite for structured metadata
2. **File Storage** - Local filesystem or cloud storage (S3/Azure/GCS) for media files

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Client (Browser)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     Flask Application                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   API Routes │  │ File Upload  │  │ Auth/Session │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                  │                                 │
│  ┌──────▼──────────────────▼──────┐                         │
│  │      Business Logic Layer       │                         │
│  │  - Card Management              │                         │
│  │  - File Processing              │                         │
│  │  - Leitner Algorithm            │                         │
│  └──────┬──────────────────┬───────┘                         │
└─────────┼──────────────────┼─────────────────────────────────┘
          │                  │
          ▼                  ▼
┌──────────────────┐  ┌──────────────────┐
│    Database      │  │  File Storage    │
│   (PostgreSQL)   │  │  (Local/S3/etc)  │
│                  │  │                  │
│  - cards         │  │  /uploads/       │
│  - card_content  │  │    /images/      │
│  - media_files   │  │    /audio/       │
│  - boxes         │  │    /thumbnails/  │
│  - review_history│  │                  │
└──────────────────┘  └──────────────────┘
```

## Database Design

### Technology Choice

**Option 1: SQLite** (Recommended for MVP/Single User)
- ✅ No setup required
- ✅ File-based, portable
- ✅ Perfect for development and small deployments
- ❌ Limited concurrent writes
- ❌ Not ideal for multi-user production

**Option 2: PostgreSQL** (Recommended for Production)
- ✅ Robust, scalable
- ✅ Excellent for multi-user
- ✅ Advanced features (JSON, full-text search)
- ✅ Better for cloud deployment
- ❌ Requires setup and maintenance

### Database Schema

#### 1. `users` Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

#### 2. `decks` Table (Card Collections)
```sql
CREATE TABLE decks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `cards` Table
```sql
CREATE TABLE cards (
    id SERIAL PRIMARY KEY,
    deck_id INTEGER REFERENCES decks(id) ON DELETE CASCADE,
    box_number INTEGER DEFAULT 1 CHECK (box_number BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_reviewed TIMESTAMP,
    review_count INTEGER DEFAULT 0,
    next_review_date TIMESTAMP,
    ease_factor FLOAT DEFAULT 2.5,  -- For spaced repetition
    interval_days INTEGER DEFAULT 1
);
```

#### 4. `card_content` Table
```sql
CREATE TABLE card_content (
    id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
    side VARCHAR(10) NOT NULL CHECK (side IN ('front', 'back')),
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('text', 'image', 'audio')),
    text_content TEXT,  -- For text content
    media_file_id INTEGER REFERENCES media_files(id) ON DELETE SET NULL,  -- For media
    display_order INTEGER DEFAULT 0,  -- Support multiple content items per side
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. `media_files` Table
```sql
CREATE TABLE media_files (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('image', 'audio')),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) UNIQUE NOT NULL,  -- UUID-based filename
    file_path VARCHAR(500) NOT NULL,  -- Relative path in storage
    file_size INTEGER,  -- In bytes
    mime_type VARCHAR(100),
    alt_text TEXT,  -- For images (accessibility)
    duration_seconds FLOAT,  -- For audio files
    thumbnail_path VARCHAR(500),  -- For images
    storage_provider VARCHAR(50) DEFAULT 'local',  -- 'local', 's3', 'azure', 'gcs'
    storage_url TEXT,  -- Full URL if using cloud storage
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checksum VARCHAR(64)  -- SHA-256 for deduplication
);
```

#### 6. `review_history` Table
```sql
CREATE TABLE review_history (
    id SERIAL PRIMARY KEY,
    card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    was_correct BOOLEAN NOT NULL,
    previous_box INTEGER,
    new_box INTEGER,
    response_time_ms INTEGER,  -- Time taken to answer
    difficulty_rating INTEGER CHECK (difficulty_rating BETWEEN 1 AND 5)
);
```

#### 7. `tags` Table (Optional - for categorization)
```sql
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7),  -- Hex color code
    UNIQUE(user_id, name)
);

CREATE TABLE card_tags (
    card_id INTEGER REFERENCES cards(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (card_id, tag_id)
);
```

### Indexes for Performance

```sql
-- Card lookups
CREATE INDEX idx_cards_deck_id ON cards(deck_id);
CREATE INDEX idx_cards_box_number ON cards(box_number);
CREATE INDEX idx_cards_next_review ON cards(next_review_date);

-- Content lookups
CREATE INDEX idx_card_content_card_id ON card_content(card_id);
CREATE INDEX idx_card_content_media_file ON card_content(media_file_id);

-- Media file lookups
CREATE INDEX idx_media_files_user_id ON media_files(user_id);
CREATE INDEX idx_media_files_checksum ON media_files(checksum);

-- Review history
CREATE INDEX idx_review_history_card_id ON review_history(card_id);
CREATE INDEX idx_review_history_date ON review_history(reviewed_at);
```

## File Storage Design

### Storage Options

#### Option 1: Local Filesystem (Development/Small Scale)

**Directory Structure:**
```
uploads/
├── images/
│   ├── originals/
│   │   └── {user_id}/
│   │       └── {uuid}.{ext}
│   └── thumbnails/
│       └── {user_id}/
│           └── {uuid}_thumb.{ext}
├── audio/
│   └── {user_id}/
│       └── {uuid}.{ext}
└── temp/
    └── {upload_session_id}/
```

**Pros:**
- Simple setup
- No external dependencies
- Fast for local development
- No additional costs

**Cons:**
- Not scalable for multiple servers
- Backup complexity
- No CDN benefits
- Server storage limits

#### Option 2: Cloud Storage (Production)

**AWS S3 / Azure Blob / Google Cloud Storage**

**Bucket Structure:**
```
memoryvault-{env}/
├── images/
│   ├── originals/{user_id}/{uuid}.{ext}
│   └── thumbnails/{user_id}/{uuid}_thumb.{ext}
├── audio/
│   └── {user_id}/{uuid}.{ext}
└── temp/
    └── {upload_session_id}/
```

**Pros:**
- Highly scalable
- Built-in CDN integration
- Automatic backups
- Pay-as-you-go pricing
- Geographic distribution

**Cons:**
- External dependency
- Ongoing costs
- Network latency
- More complex setup

### File Upload Flow

```
1. Client initiates upload
   ↓
2. Server validates file (type, size, user quota)
   ↓
3. Generate UUID filename
   ↓
4. Save to temp storage
   ↓
5. Process file (resize images, validate audio)
   ↓
6. Generate thumbnail (for images)
   ↓
7. Calculate checksum (for deduplication)
   ↓
8. Check if file already exists (by checksum)
   ↓
9. If exists: reuse existing file
   If new: move to permanent storage
   ↓
10. Create database record in media_files table
   ↓
11. Return file metadata to client
```

### File Processing

#### Image Processing
- **Validation**: Check file type, size, dimensions
- **Formats**: JPEG, PNG, WebP, GIF
- **Max size**: 10MB per image
- **Resize**: Generate thumbnails (200x200, 400x400)
- **Optimization**: Compress images (quality 85%)
- **Security**: Strip EXIF data (privacy)

#### Audio Processing
- **Validation**: Check file type, duration, size
- **Formats**: MP3, WAV, OGG, M4A
- **Max size**: 25MB per audio file
- **Max duration**: 5 minutes
- **Normalization**: Normalize audio levels
- **Conversion**: Convert to MP3 for consistency

### File Naming Convention

```python
# Format: {uuid}_{timestamp}.{extension}
# Example: a3f2c8d1-4b5e-6f7a-8b9c-0d1e2f3a4b5c_1704384000.jpg

import uuid
import time

def generate_filename(original_filename):
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_id = uuid.uuid4()
    timestamp = int(time.time())
    return f"{unique_id}_{timestamp}.{ext}"
```

### Security Considerations

1. **File Validation**
   - Verify MIME type matches extension
   - Check magic bytes (file signature)
   - Scan for malware (optional)

2. **Access Control**
   - User can only access their own files
   - Signed URLs for temporary access (cloud storage)
   - Rate limiting on uploads

3. **Storage Limits**
   - Per-user quota (e.g., 1GB)
   - Per-file size limits
   - Total storage monitoring

4. **Privacy**
   - Strip metadata from images
   - Encrypt sensitive files (optional)
   - Secure deletion when card is deleted

### File Deduplication

```python
# Check if file already exists by checksum
def check_duplicate(file_checksum, user_id):
    existing = MediaFile.query.filter_by(
        checksum=file_checksum,
        user_id=user_id
    ).first()

    if existing:
        # Reuse existing file
        return existing
    else:
        # Upload new file
        return None
```

Benefits:
- Save storage space
- Faster uploads for duplicates
- Reduce bandwidth costs

