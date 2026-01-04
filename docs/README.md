# MemoryVault Documentation

## Overview

This directory contains comprehensive documentation for the MemoryVault backend architecture and implementation.

## Quick Start

**New to the project?** Start here:
1. Read `BACKEND_DESIGN_SUMMARY.md` for a high-level overview
2. Review `ARCHITECTURE_DIAGRAMS.md` for visual understanding
3. Check `IMPLEMENTATION_PLAN.md` for the development roadmap

**Ready to implement?** Follow this order:
1. `DATABASE_SCHEMA.sql` - Understand the data model
2. `API_SPECIFICATION.md` - Learn the API endpoints
3. `IMPLEMENTATION_PLAN.md` - Follow the step-by-step guide
4. `BACKEND_ARCHITECTURE.md` - Deep dive into design decisions

## Document Index

### 📋 BACKEND_DESIGN_SUMMARY.md
**Purpose:** Executive summary of the backend design  
**Audience:** Project stakeholders, developers  
**Contents:**
- Key design decisions
- Database and storage choices
- Technology stack
- Implementation phases
- Scalability considerations

**When to read:** First document to understand the overall approach

---

### 🏗️ ARCHITECTURE_DIAGRAMS.md
**Purpose:** Visual representation of system architecture  
**Audience:** All team members  
**Contents:**
- System architecture diagram
- Database entity relationship diagram
- File upload flow
- Card review flow (Leitner system)

**When to read:** To visualize how components interact

---

### 🗄️ DATABASE_SCHEMA.sql
**Purpose:** Complete SQL schema definition  
**Audience:** Backend developers, database administrators  
**Contents:**
- Table definitions (7 core tables)
- Relationships and constraints
- Indexes for performance
- Triggers for automation

**When to read:** Before implementing database models

---

### 🔧 BACKEND_ARCHITECTURE.md
**Purpose:** Detailed technical architecture  
**Audience:** Backend developers  
**Contents:**
- Database design rationale
- File storage design
- Security considerations
- File processing details
- Deduplication strategy

**When to read:** During implementation for detailed guidance

---

### 📝 IMPLEMENTATION_PLAN.md
**Purpose:** Step-by-step implementation guide  
**Audience:** Developers  
**Contents:**
- 5-phase implementation plan
- Week-by-week breakdown
- Dependencies to install
- File structure
- Technology stack details

**When to read:** When starting development

---

### 🌐 API_SPECIFICATION.md
**Purpose:** Complete API documentation  
**Audience:** Frontend and backend developers  
**Contents:**
- All API endpoints
- Request/response formats
- Error codes
- Authentication
- Examples for each endpoint

**When to read:** When implementing or consuming the API

---

## Key Concepts

### Leitner Box System
A spaced repetition learning system with 5 boxes:
- **Box 1:** New cards, review daily
- **Box 2:** Review every 2 days
- **Box 3:** Review every 4 days
- **Box 4:** Review every 8 days
- **Box 5:** Review every 16 days (mastered)

Cards move forward on correct answers, back to Box 1 on incorrect answers.

### Multi-Content Cards
Each card side (front/back) can contain multiple content items:
- Text
- Images (with thumbnails)
- Audio files

Example: A card front could have text "What is this?" + an image, and the back could have text "Paris" + audio pronunciation.

### File Deduplication
Files are identified by SHA-256 checksum. If the same file is uploaded multiple times, only one copy is stored, saving space and bandwidth.

### Storage Quota
Each user has a storage quota (default 1GB). The system tracks usage and prevents uploads that would exceed the quota.

## Technology Stack

### Backend
- **Flask 3.0** - Web framework
- **SQLAlchemy 2.0** - ORM
- **Alembic** - Database migrations
- **Pillow** - Image processing
- **pydub** - Audio processing
- **python-magic** - File type validation

### Database
- **SQLite** - Development
- **PostgreSQL** - Production

### Storage
- **Local Filesystem** - Development
- **AWS S3 / Azure Blob / GCS** - Production

## Implementation Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1 | Week 1 | Database setup |
| Phase 2 | Week 2 | File storage system |
| Phase 3 | Week 3 | API endpoints |
| Phase 4 | Week 4 | Frontend integration |
| Phase 5 | Week 5+ | Advanced features |

## Next Steps

1. **Review all documentation** to understand the design
2. **Set up development environment** (see main README.md)
3. **Start with Phase 1** of the implementation plan
4. **Test incrementally** as you build each component
5. **Iterate and refine** based on testing

## Questions?

If you have questions about the design:
1. Check if it's answered in the relevant document
2. Review the architecture diagrams
3. Consult the API specification for endpoint details
4. Refer to the implementation plan for step-by-step guidance

## Contributing

When updating the backend:
1. Update relevant documentation
2. Keep diagrams in sync with code
3. Update API specification for new endpoints
4. Document design decisions in BACKEND_ARCHITECTURE.md

