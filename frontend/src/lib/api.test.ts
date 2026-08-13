import { describe, expect, it, vi } from 'vitest';
import { API_BASE_URL, getHealth } from './api';

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
