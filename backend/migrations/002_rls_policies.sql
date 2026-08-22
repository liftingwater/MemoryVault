-- 002_rls_policies.sql
-- Enable RLS and create policies for all tables

-- Enable RLS on all tables
ALTER TABLE public.decks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.deck_outlines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.outline_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.fsrs_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.review_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coaching_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.coaching_messages ENABLE ROW LEVEL SECURITY;

-- DECKS: Users can only see their own decks
CREATE POLICY decks_select ON public.decks FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY decks_insert ON public.decks FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY decks_update ON public.decks FOR UPDATE
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY decks_delete ON public.decks FOR DELETE
  USING (auth.uid() = user_id);

-- CARDS: Users can only access cards in their decks
CREATE POLICY cards_select ON public.cards FOR SELECT
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY cards_insert ON public.cards FOR INSERT
  WITH CHECK (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY cards_update ON public.cards FOR UPDATE
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id))
  WITH CHECK (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY cards_delete ON public.cards FOR DELETE
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

-- DECK_OUTLINES: Users can only access outlines of their decks
CREATE POLICY deck_outlines_select ON public.deck_outlines FOR SELECT
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY deck_outlines_insert ON public.deck_outlines FOR INSERT
  WITH CHECK (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY deck_outlines_update ON public.deck_outlines FOR UPDATE
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY deck_outlines_delete ON public.deck_outlines FOR DELETE
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

-- OUTLINE_ITEMS: Users can only access items in their outlines
CREATE POLICY outline_items_select ON public.outline_items FOR SELECT
  USING (outline_id IN (
    SELECT id FROM public.deck_outlines 
    WHERE deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id)
  ));

CREATE POLICY outline_items_insert ON public.outline_items FOR INSERT
  WITH CHECK (outline_id IN (
    SELECT id FROM public.deck_outlines
    WHERE deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id)
  ));

CREATE POLICY outline_items_update ON public.outline_items FOR UPDATE
  USING (outline_id IN (
    SELECT id FROM public.deck_outlines
    WHERE deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id)
  ));

CREATE POLICY outline_items_delete ON public.outline_items FOR DELETE
  USING (outline_id IN (
    SELECT id FROM public.deck_outlines
    WHERE deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id)
  ));

-- FSRS_STATES: Users can only access states for their cards
CREATE POLICY fsrs_states_select ON public.fsrs_states FOR SELECT
  USING (card_id IN (
    SELECT id FROM public.cards WHERE deck_id IN (
      SELECT id FROM public.decks WHERE auth.uid() = user_id
    )
  ));

CREATE POLICY fsrs_states_insert ON public.fsrs_states FOR INSERT
  WITH CHECK (card_id IN (
    SELECT id FROM public.cards WHERE deck_id IN (
      SELECT id FROM public.decks WHERE auth.uid() = user_id
    )
  ));

CREATE POLICY fsrs_states_update ON public.fsrs_states FOR UPDATE
  USING (card_id IN (
    SELECT id FROM public.cards WHERE deck_id IN (
      SELECT id FROM public.decks WHERE auth.uid() = user_id
    )
  ));

-- REVIEW_LOGS: Users can only access logs for their cards
CREATE POLICY review_logs_select ON public.review_logs FOR SELECT
  USING (card_id IN (
    SELECT id FROM public.cards WHERE deck_id IN (
      SELECT id FROM public.decks WHERE auth.uid() = user_id
    )
  ));

CREATE POLICY review_logs_insert ON public.review_logs FOR INSERT
  WITH CHECK (card_id IN (
    SELECT id FROM public.cards WHERE deck_id IN (
      SELECT id FROM public.decks WHERE auth.uid() = user_id
    )
  ));

-- COACHING_SESSIONS: Users can only access their deck sessions
CREATE POLICY coaching_sessions_select ON public.coaching_sessions FOR SELECT
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY coaching_sessions_insert ON public.coaching_sessions FOR INSERT
  WITH CHECK (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

CREATE POLICY coaching_sessions_update ON public.coaching_sessions FOR UPDATE
  USING (deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id));

-- COACHING_MESSAGES: Users can only access messages in their sessions
CREATE POLICY coaching_messages_select ON public.coaching_messages FOR SELECT
  USING (session_id IN (
    SELECT id FROM public.coaching_sessions
    WHERE deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id)
  ));

CREATE POLICY coaching_messages_insert ON public.coaching_messages FOR INSERT
  WITH CHECK (session_id IN (
    SELECT id FROM public.coaching_sessions
    WHERE deck_id IN (SELECT id FROM public.decks WHERE auth.uid() = user_id)
  ));
