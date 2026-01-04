# MemoryVault 🧠📚

A Leitner box spaced repetition flashcard application for effective learning.

## What is MemoryVault?

MemoryVault is a modern flashcard application that uses the **Leitner box system** for spaced repetition learning. Create cards with text, images, and audio to master any subject efficiently.

### Features

✅ **Rich Content Cards** - Support for text, images, and audio
✅ **Spaced Repetition** - Leitner box algorithm for optimal learning
✅ **Beautiful UI** - Modern, responsive design with card flip animations
✅ **Multi-Content Support** - Multiple content items per card side
🚧 **Database Storage** - Coming soon (currently in-memory)
🚧 **Review System** - Coming soon
🚧 **User Authentication** - Coming soon

## Quick Start

### 1. Run Setup Script

```bash
./setup.sh
```

### 2. Start the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
python app.py
```

### 3. Open in Browser

Go to: **http://localhost:5000**

📖 **Detailed instructions:** See [START_HERE.md](START_HERE.md)

## Project Status

**Current Version:** 0.1.0 (MVP)

- ✅ Card creation UI
- ✅ Text and image content support
- ✅ Live preview with flip animation
- ✅ Backend API structure
- ✅ Comprehensive architecture documentation
- 🚧 Database integration (designed, not implemented)
- 🚧 File upload for images/audio (designed, not implemented)
- 🚧 Review interface (planned)
- 🚧 User authentication (planned)

## Documentation

- **[START_HERE.md](START_HERE.md)** - How to run the app locally
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference guide
- **[docs/](docs/)** - Complete architecture and API documentation
  - [Backend Design Summary](docs/BACKEND_DESIGN_SUMMARY.md)
  - [Architecture Diagrams](docs/ARCHITECTURE_DIAGRAMS.md)
  - [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
  - [API Specification](docs/API_SPECIFICATION.md)
  - [Database Schema](docs/DATABASE_SCHEMA.sql)

## Technology Stack

### Current (MVP)
- **Backend:** Flask 3.0
- **Frontend:** HTML, CSS, JavaScript (vanilla)
- **Storage:** In-memory (temporary)

### Planned
- **Database:** PostgreSQL (SQLite for development)
- **ORM:** SQLAlchemy
- **File Storage:** Local filesystem → AWS S3
- **Image Processing:** Pillow
- **Audio Processing:** pydub

## Development

### Project Structure

```
MemoryVault/
├── app.py              # Main Flask application
├── setup.sh            # Automated setup script
├── requirements.txt    # Python dependencies
├── models/             # Data models
│   ├── card.py
│   └── content.py
├── templates/          # HTML templates
│   └── index.html
├── static/             # CSS, JavaScript
│   ├── css/style.css
│   └── js/app.js
└── docs/               # Documentation
```

### Next Steps

See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for the full development roadmap.

**Phase 1:** Database setup (Week 1)
**Phase 2:** File storage system (Week 2)
**Phase 3:** API development (Week 3)
**Phase 4:** Frontend integration (Week 4)
**Phase 5:** Advanced features (Week 5+)

## Contributing

This project is currently in early development. Contributions welcome!

## License

TBD

