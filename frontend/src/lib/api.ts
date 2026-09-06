export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export type Health = {
	status: string;
};

export async function getHealth(fetchFn: typeof fetch = fetch): Promise<Health> {
	const response = await fetchFn(`${API_BASE_URL}/health`);

	if (!response.ok) {
		throw new Error(`Health check failed with status ${response.status}`);
	}

	return (await response.json()) as Health;
}

export type Deck = {
	id: string;
	name: string;
	description: string | null;
	tags: string[];
	created_at: string;
	updated_at: string;
	card_count: number;
};

export type DeckListResponse = {
	decks: Deck[];
	total: number;
};

export type DeckInput = {
	name: string;
	description?: string | null;
	tags?: string[];
};

function authHeaders(token: string): Record<string, string> {
	return {
		'Content-Type': 'application/json',
		Authorization: `Bearer ${token}`
	};
}

async function readError(response: Response): Promise<string> {
	try {
		const body = (await response.json()) as { detail?: unknown };
		if (typeof body.detail === 'string') {
			return body.detail;
		}
	} catch {
		// body was not JSON; fall through to a generic message
	}
	return `Request failed with status ${response.status}`;
}

export async function listDecks(token: string, fetchFn: typeof fetch = fetch): Promise<Deck[]> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks`, {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	const body = (await response.json()) as DeckListResponse;
	return body.decks;
}

export async function getDeck(
	token: string,
	id: string,
	fetchFn: typeof fetch = fetch
): Promise<Deck> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${id}`, {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as Deck;
}

export async function createDeck(
	token: string,
	input: DeckInput,
	fetchFn: typeof fetch = fetch
): Promise<Deck> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(input)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as Deck;
}

export async function updateDeck(
	token: string,
	id: string,
	input: DeckInput,
	fetchFn: typeof fetch = fetch
): Promise<Deck> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${id}`, {
		method: 'PUT',
		headers: authHeaders(token),
		body: JSON.stringify(input)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as Deck;
}

export async function deleteDeck(
	token: string,
	id: string,
	fetchFn: typeof fetch = fetch
): Promise<void> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${id}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}
}

export type CardType = 'front_back' | 'cloze';

export type Card = {
	id: string;
	deck_id: string;
	card_type: CardType;
	front_md: string;
	back_md: string | null;
	cloze_text_md: string | null;
	cloze_answer: string | null;
	created_at: string;
	updated_at: string;
};

export type CardListResponse = {
	cards: Card[];
	total: number;
};

export type CardCreateInput = {
	card_type: CardType;
	front_md: string;
	back_md?: string | null;
	cloze_text_md?: string | null;
	cloze_answer?: string | null;
};

export type CardUpdateInput = {
	front_md?: string | null;
	back_md?: string | null;
	cloze_text_md?: string | null;
	cloze_answer?: string | null;
};

export async function listCards(
	token: string,
	deckId: string,
	search?: string,
	fetchFn: typeof fetch = fetch
): Promise<Card[]> {
	const url = new URL(`${API_BASE_URL}/api/decks/${deckId}/cards`);
	if (search) {
		url.searchParams.set('search', search);
	}

	const response = await fetchFn(url.toString(), {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	const body = (await response.json()) as CardListResponse;
	return body.cards;
}

export async function createCard(
	token: string,
	deckId: string,
	input: CardCreateInput,
	fetchFn: typeof fetch = fetch
): Promise<Card> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${deckId}/cards`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify(input)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as Card;
}

export async function updateCard(
	token: string,
	cardId: string,
	input: CardUpdateInput,
	fetchFn: typeof fetch = fetch
): Promise<Card> {
	const response = await fetchFn(`${API_BASE_URL}/api/cards/${cardId}`, {
		method: 'PUT',
		headers: authHeaders(token),
		body: JSON.stringify(input)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as Card;
}

export async function deleteCard(
	token: string,
	cardId: string,
	fetchFn: typeof fetch = fetch
): Promise<void> {
	const response = await fetchFn(`${API_BASE_URL}/api/cards/${cardId}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}
}
