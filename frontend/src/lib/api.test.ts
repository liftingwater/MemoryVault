import { describe, expect, it, vi } from 'vitest';
import {
	API_BASE_URL,
	createCard,
	createDeck,
	deleteCard,
	deleteDeck,
	endCoachingSession,
	getCoachingSession,
	getDashboard,
	getDeck,
	getDeckOutline,
	getDueCards,
	getHealth,
	gradeCard,
	listCards,
	listCoachingSessions,
	listDecks,
	sendCoachingMessage,
	startCoachingSession,
	updateCard,
	updateDeck,
	type Card,
	type CoachingSession,
	type DeckOutline,
	type Deck,
	type FSRSState
} from './api';

const sampleDeck: Deck = {
	id: 'deck-1',
	name: 'French',
	description: 'Vocab',
	tags: ['lang'],
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z',
	card_count: 3
};

const sampleCard: Card = {
	id: 'card-1',
	deck_id: 'deck-1',
	card_type: 'front_back',
	front_md: 'Q',
	back_md: 'A',
	cloze_text_md: null,
	cloze_answer: null,
	created_at: '2026-01-01T00:00:00Z',
	updated_at: '2026-01-01T00:00:00Z'
};

const sampleSession: CoachingSession = {
	id: 'session-1',
	deck_id: 'deck-1',
	status: 'active',
	created_at: '2026-01-01T00:00:00Z',
	archived_at: null,
	messages: []
};

const sampleMessage = {
	id: 'message-1',
	session_id: 'session-1',
	role: 'user' as const,
	content: 'I am new to French',
	created_at: '2026-01-01T00:00:00Z'
};

const sampleOutline: DeckOutline = {
	id: 'outline-1',
	deck_id: 'deck-1',
	generated_at: '2026-01-01T00:00:00Z',
	status: 'active',
	items: []
};

describe('getHealth', () => {
	it('requests the health endpoint and returns the parsed body', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json({ status: 'ok' }));

		const health = await getHealth(fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/health`);
		expect(health).toEqual({ status: 'ok' });
	});

	it('throws when the backend responds with an error status', async () => {
		const fetchFn = vi.fn().mockResolvedValue(new Response('', { status: 503 }));

		await expect(getHealth(fetchFn)).rejects.toThrow('503');
	});
});

describe('listDecks', () => {
	it('requests decks with a Bearer token and returns the array', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ decks: [sampleDeck], total: 1 }));

		const decks = await listDecks('tok', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(decks).toEqual([sampleDeck]);
	});

	it('surfaces the backend detail message on error', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ detail: 'Invalid token' }, { status: 401 }));

		await expect(listDecks('tok', fetchFn)).rejects.toThrow('Invalid token');
	});
});

describe('getDeck', () => {
	it('requests a single deck by id', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json(sampleDeck));

		const deck = await getDeck('tok', 'deck-1', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(deck).toEqual(sampleDeck);
	});
});

describe('createDeck', () => {
	it('POSTs the deck input and returns the created deck', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json(sampleDeck, { status: 201 }));
		const input = { name: 'French', description: 'Vocab', tags: ['lang'] };

		const deck = await createDeck('tok', input, fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' },
			body: JSON.stringify(input)
		});
		expect(deck).toEqual(sampleDeck);
	});
});

describe('updateDeck', () => {
	it('PUTs the deck input for the given id', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json(sampleDeck));
		const input = { name: 'German', description: null, tags: [] };

		const deck = await updateDeck('tok', 'deck-1', input, fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' },
			body: JSON.stringify(input)
		});
		expect(deck).toEqual(sampleDeck);
	});
});

describe('deleteDeck', () => {
	it('DELETEs the given deck id', async () => {
		const fetchFn = vi.fn().mockResolvedValue({ ok: true, status: 204 } as Response);

		await deleteDeck('tok', 'deck-1', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1`, {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
	});

	it('throws on a non-ok response', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ detail: 'Deck not found' }, { status: 404 }));

		await expect(deleteDeck('tok', 'deck-1', fetchFn)).rejects.toThrow('Deck not found');
	});
});

describe('listCards', () => {
	it('requests cards for a deck and returns the array', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json({ cards: [sampleCard], total: 1 }));

		const result = await listCards('tok', 'deck-1', undefined, fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1/cards`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(result).toEqual([sampleCard]);
	});

	it('includes the search query string when provided', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json({ cards: [], total: 0 }));

		await listCards('tok', 'deck-1', 'python', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(
			`${API_BASE_URL}/api/decks/deck-1/cards?search=python`,
			{ headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' } }
		);
	});
});

describe('createCard', () => {
	it('POSTs the card input and returns the created card', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json(sampleCard, { status: 201 }));
		const input = { card_type: 'front_back' as const, front_md: 'Q', back_md: 'A' };

		const card = await createCard('tok', 'deck-1', input, fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1/cards`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' },
			body: JSON.stringify(input)
		});
		expect(card).toEqual(sampleCard);
	});

	it('surfaces the backend detail message on error', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ detail: 'Deck not found' }, { status: 404 }));

		await expect(
			createCard('tok', 'deck-1', { card_type: 'front_back', front_md: 'Q', back_md: 'A' }, fetchFn)
		).rejects.toThrow('Deck not found');
	});
});

describe('updateCard', () => {
	it('PUTs the card input for the given id', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json(sampleCard));
		const input = { front_md: 'New Q' };

		const card = await updateCard('tok', 'card-1', input, fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/cards/card-1`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' },
			body: JSON.stringify(input)
		});
		expect(card).toEqual(sampleCard);
	});
});

describe('deleteCard', () => {
	it('DELETEs the given card id', async () => {
		const fetchFn = vi.fn().mockResolvedValue({ ok: true, status: 204 } as Response);

		await deleteCard('tok', 'card-1', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/cards/card-1`, {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
	});

	it('throws on a non-ok response', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ detail: 'Card not found' }, { status: 404 }));

		await expect(deleteCard('tok', 'card-1', fetchFn)).rejects.toThrow('Card not found');
	});
});

const sampleFsrsState: FSRSState = {
	card_id: 'card-1',
	stability: 2.3,
	difficulty: 5.1,
	due_date: '2026-01-03',
	last_review: '2026-01-01',
	reps: 1,
	lapses: 0,
	state: 'review'
};

describe('getDueCards', () => {
	it('requests the due queue and returns the array', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json({ cards: [sampleCard], total: 1 }));

		const result = await getDueCards('tok', undefined, fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/review/due`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(result).toEqual([sampleCard]);
	});

	it('includes the deck_id query string when provided', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json({ cards: [], total: 0 }));

		await getDueCards('tok', 'deck-1', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/review/due?deck_id=deck-1`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
	});
});

describe('gradeCard', () => {
	it('POSTs the rating and returns the updated FSRS state', async () => {
		const fetchFn = vi.fn().mockResolvedValue(Response.json(sampleFsrsState));

		const result = await gradeCard('tok', 'card-1', 'got_it', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/review/card-1`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' },
			body: JSON.stringify({ rating: 'got_it' })
		});
		expect(result).toEqual(sampleFsrsState);
	});

	it('surfaces the backend detail message on error', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ detail: 'Card not found' }, { status: 404 }));

		await expect(gradeCard('tok', 'card-1', 'need_review', fetchFn)).rejects.toThrow(
			'Card not found'
		);
	});
});

describe('getDashboard', () => {
	it('requests the dashboard summary', async () => {
		const dashboard = {
			message: 'Welcome to MemoryVault',
			user_id: 'user-1',
			email: 'test@example.com',
			cards_due: 3,
			streak: 5
		};
		const fetchFn = vi.fn().mockResolvedValue(Response.json(dashboard));

		const result = await getDashboard('tok', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/dashboard`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(result).toEqual(dashboard);
	});
});

describe('coaching API', () => {
	it('starts a coaching session for a deck', async () => {
		const fetchFn = vi.fn().mockResolvedValue(
			Response.json(
				{
					session: {
						id: sampleSession.id,
						deck_id: sampleSession.deck_id,
						status: sampleSession.status,
						created_at: sampleSession.created_at,
						archived_at: sampleSession.archived_at
					},
					assistant_message: sampleMessage
				},
				{ status: 201 }
			)
		);

		const session = await startCoachingSession('tok', 'deck-1', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1/coaching/start`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(session).toEqual({ ...sampleSession, messages: [sampleMessage] });
	});

	it('sends a message and returns persisted messages, an outline, and a provider error', async () => {
		const response = {
			user_message: sampleMessage,
			assistant_message: null,
			outline: sampleOutline,
			error: { code: 'service_unavailable' as const, message: 'Try again later.' }
		};
		const fetchFn = vi.fn().mockResolvedValue(Response.json(response));

		const result = await sendCoachingMessage('tok', 'session-1', 'I am new to French', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/coaching/session-1/message`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' },
			body: JSON.stringify({ content: 'I am new to French' })
		});
		expect(result).toEqual(response);
	});

	it('lists a deck coaching sessions including archived ones', async () => {
		const sessions = [
			{
				id: sampleSession.id,
				deck_id: sampleSession.deck_id,
				status: sampleSession.status,
				created_at: sampleSession.created_at,
				archived_at: sampleSession.archived_at
			}
		];
		const fetchFn = vi.fn().mockResolvedValue(Response.json({ sessions, total: 1 }));

		const result = await listCoachingSessions('tok', 'deck-1', fetchFn);

		expect(fetchFn).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1/coaching/sessions`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(result).toEqual({ sessions, total: 1 });
	});

	it('loads a session, ends it, and reads its deck outline', async () => {
		const sessionFetch = vi.fn().mockResolvedValue(
			Response.json({
				session: {
					id: sampleSession.id,
					deck_id: sampleSession.deck_id,
					status: sampleSession.status,
					created_at: sampleSession.created_at,
					archived_at: sampleSession.archived_at
				},
				messages: sampleSession.messages
			})
		);
		const endFetch = vi.fn().mockResolvedValue(
			Response.json({
				session: {
					id: sampleSession.id,
					deck_id: sampleSession.deck_id,
					status: 'archived',
					created_at: sampleSession.created_at,
					archived_at: '2026-01-02T00:00:00Z'
				},
				context_saved: false,
				error: { code: 'timeout', message: 'Timed out' }
			})
		);
		const outlineFetch = vi.fn().mockResolvedValue(Response.json({ outline: sampleOutline }));

		await expect(getCoachingSession('tok', 'session-1', sessionFetch)).resolves.toEqual(sampleSession);
		await expect(endCoachingSession('tok', 'session-1', endFetch)).resolves.toMatchObject({
			context_saved: false,
			error: { message: 'Timed out' }
		});
		await expect(getDeckOutline('tok', 'deck-1', outlineFetch)).resolves.toEqual(sampleOutline);

		expect(sessionFetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/coaching/session-1`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(endFetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/coaching/session-1/end`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
		expect(outlineFetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/decks/deck-1/outline`, {
			headers: { 'Content-Type': 'application/json', Authorization: 'Bearer tok' }
		});
	});

	it('surfaces backend errors from coaching requests', async () => {
		const fetchFn = vi
			.fn()
			.mockResolvedValue(Response.json({ detail: 'Session not found' }, { status: 404 }));

		await expect(getCoachingSession('tok', 'missing', fetchFn)).rejects.toThrow('Session not found');
	});
});
