import { getHealth } from '$lib/api';
import { render, screen } from '@testing-library/svelte';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import Page from './+page.svelte';

vi.mock('$lib/api', () => ({ getHealth: vi.fn() }));

describe('landing page', () => {
	beforeEach(() => {
		vi.mocked(getHealth).mockReset();
	});

	it('renders the MemoryVault heading', () => {
		vi.mocked(getHealth).mockResolvedValue({ status: 'ok' });

		render(Page);

		expect(screen.getByRole('heading', { name: 'MemoryVault' })).toBeInTheDocument();
	});

	it('reports the backend as reachable once the health check succeeds', async () => {
		vi.mocked(getHealth).mockResolvedValue({ status: 'ok' });

		render(Page);

		expect(await screen.findByText('Backend: ok')).toBeInTheDocument();
	});

	it('reports the backend as unreachable when the health check fails', async () => {
		vi.mocked(getHealth).mockRejectedValue(new Error('connection refused'));

		render(Page);

		expect(await screen.findByText('Backend: unreachable')).toBeInTheDocument();
	});
});
