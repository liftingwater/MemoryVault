export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export type Health = {
	status: string;
};

export type Deck = {
	id: string;
	name: string;
	description?: string;
	tags: string[];
	created_at: string;
	updated_at: string;
	card_count: number;
};

export type Card = {
	id: string;
	deck_id: string;
	card_type: 'front_back' | 'cloze';
	front_md?: string;
	back_md?: string;
	cloze_text_md?: string;
	cloze_answer?: string;
	created_at: string;
	updated_at: string;
};

export async function getHealth(fetchFn: typeof fetch = fetch): Promise<Health> {
	const response = await fetchFn(`${API_BASE_URL}/health`);

	if (!response.ok) {
		throw new Error(`Health check failed with status ${response.status}`);
	}

	return (await response.json()) as Health;
}

async function getAuthToken(): Promise<string | null> {
	// Get token from Supabase session
	const { supabase } = await import('$lib/supabase');
	const {
		data: { session }
	} = await supabase.auth.getSession();
	return session?.access_token ?? null;
}

export async function listDecks(fetchFn: typeof fetch = fetch): Promise<Deck[]> {
	const token = await getAuthToken();
	if (!token) throw new Error('Not authenticated');

	const response = await fetchFn(`${API_BASE_URL}/decks`, {
		headers: { Authorization: `Bearer ${token}` }
	});

	if (!response.ok) {
		throw new Error(`Failed to list decks: ${response.status}`);
	}

	const data = (await response.json()) as { decks: Deck[] };
	return data.decks;
}

export async function listCards(
	deckId: string,
	search?: string,
	fetchFn: typeof fetch = fetch
): Promise<Card[]> {
	const token = await getAuthToken();
	if (!token) throw new Error('Not authenticated');

	const url = new URL(`${API_BASE_URL}/decks/${deckId}/cards`);
	if (search) url.searchParams.set('search', search);

	const response = await fetchFn(url.toString(), {
		headers: { Authorization: `Bearer ${token}` }
	});

	if (!response.ok) {
		throw new Error(`Failed to list cards: ${response.status}`);
	}

	const data = (await response.json()) as { cards: Card[] };
	return data.cards;
}

export async function createCard(
	deckId: string,
	card: Omit<Card, 'id' | 'deck_id' | 'created_at' | 'updated_at'>,
	fetchFn: typeof fetch = fetch
): Promise<Card> {
	const token = await getAuthToken();
	if (!token) throw new Error('Not authenticated');

	const response = await fetchFn(`${API_BASE_URL}/decks/${deckId}/cards`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(card)
	});

	if (!response.ok) {
		throw new Error(`Failed to create card: ${response.status}`);
	}

	return (await response.json()) as Card;
}

export async function updateCard(
	cardId: string,
	updates: Partial<Omit<Card, 'id' | 'deck_id' | 'created_at' | 'updated_at'>>,
	fetchFn: typeof fetch = fetch
): Promise<Card> {
	const token = await getAuthToken();
	if (!token) throw new Error('Not authenticated');

	const response = await fetchFn(`${API_BASE_URL}/decks/cards/${cardId}`, {
		method: 'PUT',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(updates)
	});

	if (!response.ok) {
		throw new Error(`Failed to update card: ${response.status}`);
	}

	return (await response.json()) as Card;
}

export async function deleteCard(cardId: string, fetchFn: typeof fetch = fetch): Promise<void> {
	const token = await getAuthToken();
	if (!token) throw new Error('Not authenticated');

	const response = await fetchFn(`${API_BASE_URL}/decks/cards/${cardId}`, {
		method: 'DELETE',
		headers: { Authorization: `Bearer ${token}` }
	});

	if (!response.ok) {
		throw new Error(`Failed to delete card: ${response.status}`);
	}
}
