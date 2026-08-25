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
	const response = await fetchFn(`${API_BASE_URL}/decks`, {
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
	const response = await fetchFn(`${API_BASE_URL}/decks/${id}`, {
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
	const response = await fetchFn(`${API_BASE_URL}/decks`, {
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
	const response = await fetchFn(`${API_BASE_URL}/decks/${id}`, {
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
	const response = await fetchFn(`${API_BASE_URL}/decks/${id}`, {
		method: 'DELETE',
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}
}
