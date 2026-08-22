-- 001_initial_schema.sql
-- Create all tables for MemoryVault with proper constraints and relationships

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for additional UUID support
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Deck table
CREATE TABLE public.decks (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  description TEXT,
  tags TEXT[] DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Card table
CREATE TABLE public.cards (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  deck_id UUID NOT NULL REFERENCES public.decks(id) ON DELETE CASCADE,
  card_type VARCHAR(20) NOT NULL CHECK (card_type IN ('front_back', 'cloze')),
  front_md TEXT NOT NULL,
  back_md TEXT,
  cloze_text_md TEXT,
  cloze_answer TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- DeckOutline table
CREATE TABLE public.deck_outlines (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  deck_id UUID NOT NULL REFERENCES public.decks(id) ON DELETE CASCADE,
  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived'))
);

-- OutlineItem table
CREATE TABLE public.outline_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  outline_id UUID NOT NULL REFERENCES public.deck_outlines(id) ON DELETE CASCADE,
  section TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  position INTEGER NOT NULL,
  card_id UUID REFERENCES public.cards(id) ON DELETE SET NULL
);

-- FSRSState table
CREATE TABLE public.fsrs_states (
  card_id UUID PRIMARY KEY REFERENCES public.cards(id) ON DELETE CASCADE,
  stability FLOAT NOT NULL,
  difficulty FLOAT NOT NULL,
  due_date DATE NOT NULL,
  last_review DATE,
  reps INTEGER NOT NULL DEFAULT 0,
  lapses INTEGER NOT NULL DEFAULT 0,
  state VARCHAR(20) NOT NULL CHECK (state IN ('new', 'learning', 'review', 'relearning'))
);

-- ReviewLog table
CREATE TABLE public.review_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  card_id UUID NOT NULL REFERENCES public.cards(id) ON DELETE CASCADE,
  rating VARCHAR(20) NOT NULL CHECK (rating IN ('got_it', 'need_review')),
  reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- CoachingSession table
CREATE TABLE public.coaching_sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  deck_id UUID NOT NULL REFERENCES public.decks(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  archived_at TIMESTAMP WITH TIME ZONE
);

-- CoachingMessage table
CREATE TABLE public.coaching_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES public.coaching_sessions(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
  content TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX idx_decks_user_id ON public.decks(user_id);
CREATE INDEX idx_cards_deck_id ON public.cards(deck_id);
CREATE INDEX idx_outline_items_outline_id ON public.outline_items(outline_id);
CREATE INDEX idx_review_logs_card_id ON public.review_logs(card_id);
CREATE INDEX idx_coaching_sessions_deck_id ON public.coaching_sessions(deck_id);
CREATE INDEX idx_coaching_messages_session_id ON public.coaching_messages(session_id);
CREATE INDEX idx_fsrs_due_date ON public.fsrs_states(due_date);
