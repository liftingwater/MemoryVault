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

export type Rating = 'got_it' | 'need_review';

export type FSRSState = {
	card_id: string;
	stability: number;
	difficulty: number;
	due_date: string;
	last_review: string | null;
	reps: number;
	lapses: number;
	state: string;
};

export type Dashboard = {
	message: string;
	user_id: string;
	email: string | null;
	cards_due: number;
	streak: number;
};

export async function getDueCards(
	token: string,
	deckId?: string,
	fetchFn: typeof fetch = fetch
): Promise<Card[]> {
	const url = new URL(`${API_BASE_URL}/api/review/due`);
	if (deckId) {
		url.searchParams.set('deck_id', deckId);
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

export async function gradeCard(
	token: string,
	cardId: string,
	rating: Rating,
	fetchFn: typeof fetch = fetch
): Promise<FSRSState> {
	const response = await fetchFn(`${API_BASE_URL}/api/review/${cardId}`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ rating })
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as FSRSState;
}

export async function getDashboard(
	token: string,
	fetchFn: typeof fetch = fetch
): Promise<Dashboard> {
	const response = await fetchFn(`${API_BASE_URL}/api/dashboard`, {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as Dashboard;
}

export type CoachingSessionStatus = 'active' | 'archived';
export type CoachingMessageRole = 'user' | 'assistant';
export type CoachingErrorCode =
	| 'timeout'
	| 'throttled'
	| 'service_unavailable'
	| 'context_store_unavailable';

export type CoachingError = {
	code: CoachingErrorCode;
	message: string;
};

export type CoachingMessage = {
	id: string;
	session_id: string;
	role: CoachingMessageRole;
	content: string;
	created_at: string;
};

export type CoachingSessionSummary = {
	id: string;
	deck_id: string;
	status: CoachingSessionStatus;
	created_at: string;
	archived_at: string | null;
};

export type CoachingSession = CoachingSessionSummary & {
	messages: CoachingMessage[];
};

type CoachingStartResponse = {
	session: CoachingSessionSummary;
	assistant_message: CoachingMessage;
};

type CoachingSessionDetailResponse = {
	session: CoachingSessionSummary;
	messages: CoachingMessage[];
};

export type CoachingSessionListResponse = {
	sessions: CoachingSessionSummary[];
	total: number;
};

export type OutlineItem = {
	id: string;
	outline_id: string;
	section: string;
	title: string;
	description: string | null;
	position: number;
	card_id: string | null;
};

export type DeckOutline = {
	id: string;
	deck_id: string;
	generated_at: string;
	status: 'active' | 'archived';
	items: OutlineItem[];
};

export type CoachingMessageResponse = {
	user_message: CoachingMessage;
	assistant_message: CoachingMessage | null;
	outline: DeckOutline | null;
	error: CoachingError | null;
};

export type EndCoachingSessionResponse = {
	session: CoachingSessionSummary;
	context_saved: boolean;
	error: CoachingError | null;
};

export async function startCoachingSession(
	token: string,
	deckId: string,
	fetchFn: typeof fetch = fetch
): Promise<CoachingSession> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${deckId}/coaching/start`, {
		method: 'POST',
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	const body = (await response.json()) as CoachingStartResponse;
	return { ...body.session, messages: [body.assistant_message] };
}

export async function sendCoachingMessage(
	token: string,
	sessionId: string,
	content: string,
	fetchFn: typeof fetch = fetch
): Promise<CoachingMessageResponse> {
	const response = await fetchFn(`${API_BASE_URL}/api/coaching/${sessionId}/message`, {
		method: 'POST',
		headers: authHeaders(token),
		body: JSON.stringify({ content })
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as CoachingMessageResponse;
}

export async function listCoachingSessions(
	token: string,
	deckId: string,
	fetchFn: typeof fetch = fetch
): Promise<CoachingSessionListResponse> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${deckId}/coaching/sessions`, {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as CoachingSessionListResponse;
}

export async function getCoachingSession(
	token: string,
	sessionId: string,
	fetchFn: typeof fetch = fetch
): Promise<CoachingSession> {
	const response = await fetchFn(`${API_BASE_URL}/api/coaching/${sessionId}`, {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	const body = (await response.json()) as CoachingSessionDetailResponse;
	return { ...body.session, messages: body.messages };
}

export async function endCoachingSession(
	token: string,
	sessionId: string,
	fetchFn: typeof fetch = fetch
): Promise<EndCoachingSessionResponse> {
	const response = await fetchFn(`${API_BASE_URL}/api/coaching/${sessionId}/end`, {
		method: 'POST',
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	return (await response.json()) as EndCoachingSessionResponse;
}

export async function getDeckOutline(
	token: string,
	deckId: string,
	fetchFn: typeof fetch = fetch
): Promise<DeckOutline | null> {
	const response = await fetchFn(`${API_BASE_URL}/api/decks/${deckId}/outline`, {
		headers: authHeaders(token)
	});

	if (!response.ok) {
		throw new Error(await readError(response));
	}

	const body = (await response.json()) as { outline: DeckOutline | null };
	return body.outline;
}
