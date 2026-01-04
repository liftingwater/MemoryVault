# MemoryVault Architecture Diagrams

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Browser    │  │ Mobile App   │  │  Desktop App │          │
│  │  (HTML/JS)   │  │ (React Native│  │   (Electron) │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┴──────────────────┘
                             │ HTTPS/REST API
          ┌──────────────────┴──────────────────┐
          │                                      │
┌─────────▼──────────────────────────────────────▼─────────────────┐
│                    Application Layer (Flask)                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                      API Routes                             │  │
│  │  /api/cards  /api/decks  /api/files  /api/review          │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐  │
│  │                  Business Logic Layer                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │  Card    │  │   File   │  │ Leitner  │  │   Auth   │  │  │
│  │  │ Manager  │  │Processor │  │Algorithm │  │ Manager  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └────────────────────────┬───────────────────────────────────┘  │
│                           │                                       │
│  ┌────────────────────────▼───────────────────────────────────┐  │
│  │                   Data Access Layer                         │  │
│  │              SQLAlchemy ORM + Models                        │  │
│  └────────────────────────┬───────────────────────────────────┘  │
└───────────────────────────┼───────────────────────────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
┌─────────▼──────────┐            ┌──────────▼──────────┐
│   Database Layer   │            │  File Storage Layer │
│                    │            │                     │
│  ┌──────────────┐  │            │  ┌──────────────┐  │
│  │  PostgreSQL  │  │            │  │    Local     │  │
│  │      or      │  │            │  │  Filesystem  │  │
│  │    SQLite    │  │            │  │      or      │  │
│  └──────────────┘  │            │  │   AWS S3     │  │
│                    │            │  │  Azure Blob  │  │
│  Tables:           │            │  │  Google GCS  │  │
│  - users           │            │  └──────────────┘  │
│  - decks           │            │                     │
│  - cards           │            │  Directories:       │
│  - card_content    │            │  - images/          │
│  - media_files     │            │  - audio/           │
│  - review_history  │            │  - thumbnails/      │
│  - tags            │            │  - temp/            │
└────────────────────┘            └─────────────────────┘
```

## Database Entity Relationship Diagram

```
┌──────────────┐
│    users     │
│──────────────│
│ id (PK)      │───┐
│ username     │   │
│ email        │   │
│ password_hash│   │
│ storage_used │   │
└──────────────┘   │
                   │
       ┌───────────┴───────────┬─────────────┐
       │                       │             │
       │                       │             │
┌──────▼──────┐         ┌──────▼──────┐     │
│    decks    │         │media_files  │     │
│─────────────│         │─────────────│     │
│ id (PK)     │───┐     │ id (PK)     │     │
│ user_id (FK)│   │     │ user_id (FK)│     │
│ name        │   │     │ file_type   │     │
│ description │   │     │ stored_name │     │
└─────────────┘   │     │ file_path   │     │
                  │     │ file_size   │     │
                  │     │ checksum    │     │
                  │     └──────┬──────┘     │
                  │            │            │
           ┌──────▼────────┐   │            │
           │     cards     │   │            │
           │───────────────│   │            │
           │ id (PK)       │───┼───┐        │
           │ deck_id (FK)  │   │   │        │
           │ box_number    │   │   │        │
           │ next_review   │   │   │        │
           │ ease_factor   │   │   │        │
           └───────────────┘   │   │        │
                  │            │   │        │
         ┌────────┴────────┐   │   │        │
         │                 │   │   │        │
  ┌──────▼──────┐   ┌──────▼───▼───▼──┐    │
  │card_content │   │ review_history  │    │
  │─────────────│   │─────────────────│    │
  │ id (PK)     │   │ id (PK)         │    │
  │ card_id (FK)│   │ card_id (FK)    │    │
  │ side        │   │ reviewed_at     │    │
  │ type        │   │ was_correct     │    │
  │ text_content│   │ previous_box    │    │
  │ media_id(FK)│   │ new_box         │    │
  └─────────────┘   └─────────────────┘    │
         │                                  │
         │          ┌───────────────┐       │
         └──────────┤  card_tags    │       │
                    │───────────────│       │
                    │ card_id (FK)  │       │
                    │ tag_id (FK)   │       │
                    └───────┬───────┘       │
                            │               │
                     ┌──────▼──────┐        │
                     │    tags     │        │
                     │─────────────│        │
                     │ id (PK)     │        │
                     │ user_id (FK)│────────┘
                     │ name        │
                     │ color       │
                     └─────────────┘
```

## File Upload Flow Diagram

```
┌─────────┐
│ Client  │
└────┬────┘
     │ 1. Select file
     │
     ▼
┌─────────────────┐
│ Upload Endpoint │
│ POST /api/upload│
└────┬────────────┘
     │ 2. Receive file
     │
     ▼
┌─────────────────┐
│   Validation    │
│ - Type check    │
│ - Size check    │
│ - Quota check   │
└────┬────────────┘
     │ 3. Valid?
     │
     ├─── No ──→ [400 Error]
     │
     │ Yes
     ▼
┌─────────────────┐
│  Temp Storage   │
│ /uploads/temp/  │
└────┬────────────┘
     │ 4. Save temporarily
     │
     ▼
┌─────────────────┐
│  Processing     │
│ - Resize (img)  │
│ - Thumbnail     │
│ - Convert (aud) │
│ - Checksum      │
└────┬────────────┘
     │ 5. Process file
     │
     ▼
┌─────────────────┐
│  Deduplication  │
│ Check checksum  │
└────┬────────────┘
     │ 6. Exists?
     │
     ├─── Yes ──→ [Reuse existing]
     │                    │
     │ No                 │
     ▼                    │
┌─────────────────┐       │
│ Permanent Store │       │
│ /uploads/images/│       │
│ /uploads/audio/ │       │
└────┬────────────┘       │
     │ 7. Move file       │
     │                    │
     └────────┬───────────┘
              │
              ▼
     ┌─────────────────┐
     │ Database Record │
     │  media_files    │
     └────┬────────────┘
          │ 8. Create record
          │
          ▼
     ┌─────────────────┐
     │ Return Metadata │
     │ - file_id       │
     │ - url           │
     │ - thumbnail_url │
     └────┬────────────┘
          │
          ▼
     ┌─────────┐
     │ Client  │
     └─────────┘
```

## Card Review Flow (Leitner System)

```
┌─────────────┐
│ Start Review│
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Get Due Cards    │
│ WHERE next_review│
│   <= NOW()       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Show Card Front  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ User Reveals     │
│ Card Back        │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ User Responds    │
│ Correct/Wrong?   │
└──────┬───────────┘
       │
       ├─── Correct ──→ ┌──────────────┐
       │                │ Move Forward │
       │                │ box = box + 1│
       │                │ (max: box 5) │
       │                └──────┬───────┘
       │                       │
       │                       ▼
       │                ┌──────────────┐
       │                │ Calculate    │
       │                │ Next Review  │
       │                │ interval *= 2│
       │                └──────┬───────┘
       │                       │
       └─── Wrong ───→ ┌───────▼──────┐
                       │ Move to Box 1│
                       │ box = 1      │
                       │ interval = 1 │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Update Card  │
                       │ - box_number │
                       │ - next_review│
                       │ - ease_factor│
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Save Review  │
                       │ History      │
                       └──────┬───────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ More Cards?  │
                       └──────┬───────┘
                              │
                    ├─── Yes ──→ [Next Card]
                    │
                    └─── No ──→ [End Session]
```

