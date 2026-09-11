-- Prevent concurrent active coaching sessions for the same deck.
CREATE UNIQUE INDEX IF NOT EXISTS idx_coaching_sessions_one_active_per_deck
  ON public.coaching_sessions (deck_id)
  WHERE status = 'active';