<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';
	import { createDeck, getDashboard, listDecks, type Dashboard, type Deck } from '$lib/api';

	let user: User | null = $state(null);
	let token = $state('');
	let loading = $state(true);
	let decks = $state<Deck[]>([]);
	let dashboard = $state<Dashboard | null>(null);
	let error = $state('');

	let name = $state('');
	let description = $state('');
	let tagsInput = $state('');
	let creating = $state(false);

	function parseTags(value: string): string[] {
		return value
			.split(',')
			.map((tag) => tag.trim())
			.filter((tag) => tag.length > 0);
	}

	async function loadDecks() {
		error = '';
		try {
			decks = await listDecks(token);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load decks';
		}
	}

	async function loadDashboard() {
		try {
			dashboard = await getDashboard(token);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load dashboard';
		}
	}

	onMount(async () => {
		const {
			data: { session }
		} = await supabase.auth.getSession();

		if (!session) {
			goto('/login');
			return;
		}

		user = session.user;
		token = session.access_token;
		await Promise.all([loadDecks(), loadDashboard()]);
		loading = false;
	});

	async function handleCreate(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		creating = true;
		try {
			const deck = await createDeck(token, {
				name,
				description: description.trim() || null,
				tags: parseTags(tagsInput)
			});
			decks = [deck, ...decks];
			name = '';
			description = '';
			tagsInput = '';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to create deck';
		} finally {
			creating = false;
		}
	}

	async function handleLogout() {
		await supabase.auth.signOut();
		goto('/');
	}
</script>

<main>
	{#if loading}
		<p>Loading...</p>
	{:else if user}
		<header>
			<h1>Dashboard</h1>
			<button onclick={handleLogout}>Log Out</button>
		</header>
		<p>Welcome, {user.email}!</p>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		{#if dashboard}
			<section class="review-summary">
				<div>
					<p class="stat">{dashboard.cards_due}</p>
					<p class="label">cards due</p>
				</div>
				<div>
					<p class="stat">{dashboard.streak}</p>
					<p class="label">day streak</p>
				</div>
				{#if dashboard.cards_due > 0}
					<a class="review-btn" href="/review">Start Review</a>
				{/if}
			</section>
		{/if}

		<section>
			<h2>Create a Deck</h2>
			<form onsubmit={handleCreate}>
				<label>
					Name
					<input bind:value={name} required disabled={creating} />
				</label>
				<label>
					Description
					<input bind:value={description} disabled={creating} />
				</label>
				<label>
					Tags (comma-separated)
					<input bind:value={tagsInput} disabled={creating} />
				</label>
				<button type="submit" disabled={creating}>
					{creating ? 'Creating...' : 'Create Deck'}
				</button>
			</form>
		</section>

		<section>
			<h2>Your Decks</h2>
			{#if decks.length === 0}
				<p>No decks yet. Create your first deck to get started!</p>
			{:else}
				<ul>
					{#each decks as deck (deck.id)}
						<li>
							<a href="/decks/{deck.id}">
								<strong>{deck.name}</strong>
							</a>
							<span class="count">{deck.card_count} cards</span>
							{#if deck.description}
								<p class="desc">{deck.description}</p>
							{/if}
							{#if deck.tags.length > 0}
								<p class="tags">{deck.tags.join(', ')}</p>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	{/if}
</main>

<style>
	main {
		max-width: 800px;
		margin: 2rem auto;
		padding: 1rem;
	}

	header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	section {
		margin: 2rem 0;
		padding: 1rem;
		border: 1px solid #eee;
		border-radius: 8px;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	input {
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	ul {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	li {
		padding: 0.75rem;
		border: 1px solid #eee;
		border-radius: 6px;
	}

	.count {
		color: #666;
		font-size: 0.85rem;
		margin-left: 0.5rem;
	}

	.desc {
		margin: 0.25rem 0 0;
	}

	.tags {
		margin: 0.25rem 0 0;
		color: #0066cc;
		font-size: 0.85rem;
	}

	.error {
		color: #cc0000;
	}

	.review-summary {
		display: flex;
		align-items: center;
		gap: 2rem;
	}

	.review-summary .stat {
		font-size: 2rem;
		font-weight: bold;
		margin: 0;
	}

	.review-summary .label {
		margin: 0;
		color: #666;
		font-size: 0.85rem;
	}

	.review-btn {
		margin-left: auto;
		padding: 0.5rem 1rem;
		background: #0066cc;
		color: white;
		border-radius: 4px;
		text-decoration: none;
	}

	button {
		padding: 0.5rem 1rem;
		background: #0066cc;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
