import { describe, expect, it, vi } from 'vitest';
import {
	API_BASE_URL,
	createCard,
	createDeck,
	deleteCard,
	deleteDeck,
	getDeck,
	getHealth,
	listCards,
	listDecks,
	updateCard,
	updateDeck,
	type Card,
	type Deck
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
