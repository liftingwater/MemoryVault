# MemoryVault Backend Design - Executive Summary

## Overview

This document provides a high-level overview of the MemoryVault backend architecture designed to support card metadata storage, image files, and audio files.

## Key Design Decisions

### 1. Database: PostgreSQL (Production) / SQLite (Development)

**Why PostgreSQL?**
- Robust and scalable for multi-user applications
- Excellent support for complex queries and relationships
- Built-in JSON support for flexible data structures
- Strong ACID compliance for data integrity
- Easy migration path from SQLite

**Development Strategy:**
- Start with SQLite for rapid development
- Use SQLAlchemy ORM for database abstraction
- Migrate to PostgreSQL for production deployment

### 2. File Storage: Hybrid Approach

**Local Filesystem (Development/MVP)**
- Simple setup, no external dependencies
- Fast for development and testing
- Easy to migrate to cloud storage later

**Cloud Storage (Production)**
- AWS S3, Azure Blob, or Google Cloud Storage
- Scalable and reliable
- Built-in CDN support
- Geographic distribution

### 3. ORM: SQLAlchemy

**Benefits:**
- Database-agnostic (works with SQLite and PostgreSQL)
- Powerful query API
- Built-in migration support via Alembic
- Excellent documentation and community support

## Database Schema Highlights

### Core Tables

1. **users** - User accounts and authentication
2. **decks** - Card collections/categories
3. **cards** - Individual flashcards with Leitner box tracking
4. **card_content** - Flexible content storage (text, images, audio)
5. **media_files** - File metadata and storage information
6. **review_history** - Learning progress tracking
7. **tags** - Card categorization (optional)

### Key Features

- **Multi-content support**: Cards can have multiple content items per side
- **File deduplication**: Checksum-based to save storage
- **Reference counting**: Track file usage across cards
- **Soft deletion**: Preserve data integrity
- **Audit trails**: Track creation and modification times

## File Storage Architecture

### Upload Flow

```
Client → Validation → Temp Storage → Processing → Permanent Storage → Database Record
```

### File Processing

**Images:**
- Validation (type, size, dimensions)
- Thumbnail generation (200x200, 400x400)
- Compression (quality 85%)
- EXIF stripping (privacy)
- Formats: JPEG, PNG, WebP, GIF
- Max size: 10MB

**Audio:**
- Validation (type, duration, size)
- Format conversion (to MP3)
- Audio normalization
- Duration extraction
- Formats: MP3, WAV, OGG, M4A
- Max size: 25MB
- Max duration: 5 minutes

### Security Features

1. **File Validation**
   - MIME type verification
   - Magic byte checking
   - Size limits enforcement

2. **Access Control**
   - User-based file isolation
   - Signed URLs for cloud storage
   - Rate limiting on uploads

3. **Storage Quotas**
   - Per-user limits (default 1GB)
   - Automatic tracking
   - Quota enforcement

## API Design

### RESTful Endpoints

**File Management:**
- `POST /api/upload/image` - Upload image
- `POST /api/upload/audio` - Upload audio
- `GET /api/files/{id}` - Retrieve file
- `DELETE /api/files/{id}` - Delete file

**Card Management:**
- `POST /api/cards` - Create card with media
- `GET /api/cards/{id}` - Get card details
- `PUT /api/cards/{id}` - Update card
- `DELETE /api/cards/{id}` - Delete card
- `GET /api/cards` - List cards (with filters)

**Deck Management:**
- `POST /api/decks` - Create deck
- `GET /api/decks` - List decks
- `GET /api/decks/{id}` - Get deck details
- `PUT /api/decks/{id}` - Update deck
- `DELETE /api/decks/{id}` - Delete deck

**Review System:**
- `GET /api/review/due` - Get cards due for review
- `POST /api/review/{card_id}` - Submit review result
- `GET /api/review/stats` - Get statistics

## Technology Stack

### Backend
- **Framework**: Flask 3.0
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite → PostgreSQL
- **Migrations**: Alembic
- **Image Processing**: Pillow
- **Audio Processing**: pydub
- **File Validation**: python-magic
- **Security**: werkzeug, python-dotenv

### Storage
- **Development**: Local filesystem
- **Production**: AWS S3 / Azure Blob / GCS

### Deployment
- **Development**: Flask dev server
- **Production**: Gunicorn + Nginx
- **Hosting**: Heroku / AWS / DigitalOcean / Render

## Implementation Phases

### Phase 1: Database Setup (Week 1)
- Install SQLAlchemy and Alembic
- Create database models
- Set up migrations
- Initialize database

### Phase 2: File Storage (Week 2)
- Implement file upload handlers
- Add image processing
- Add audio processing
- Implement deduplication

### Phase 3: API Development (Week 3)
- Create file upload endpoints
- Enhance card endpoints
- Add deck management
- Implement review system

### Phase 4: Frontend Integration (Week 4)
- Update card creation UI
- Add file upload interface
- Create card list view
- Build review interface

### Phase 5: Advanced Features (Week 5+)
- User authentication
- Spaced repetition algorithm
- Statistics and analytics
- Cloud storage integration

## Scalability Considerations

### Database
- Indexed queries for performance
- Connection pooling
- Read replicas for scaling reads
- Partitioning for large datasets

### File Storage
- CDN integration for fast delivery
- Lazy loading for images
- Streaming for audio files
- Caching strategies

### Application
- Stateless design for horizontal scaling
- Background job processing (Celery)
- Caching layer (Redis)
- Load balancing

## Next Steps

1. **Review and approve** this design document
2. **Set up development environment** with required dependencies
3. **Implement Phase 1** - Database setup
4. **Create initial migration** and test with sample data
5. **Iterate and refine** based on testing and feedback

## Documentation

- `BACKEND_ARCHITECTURE.md` - Detailed architecture and design
- `IMPLEMENTATION_PLAN.md` - Step-by-step implementation guide
- `API_SPECIFICATION.md` - Complete API documentation
- `DATABASE_SCHEMA.sql` - SQL schema definition

