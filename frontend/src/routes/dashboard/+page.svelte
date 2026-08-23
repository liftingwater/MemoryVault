<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';
	import { listDecks, type Deck } from '$lib/api';
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';

	let user: User | null = $state(null);
	let decks: Deck[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);

	onMount(async () => {
		const {
			data: { session }
		} = await supabase.auth.getSession();

		if (!session) {
			goto('/login');
			return;
		}

		user = session.user;
		await loadDecks();
	});

	async function loadDecks() {
		try {
			decks = await listDecks();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load decks';
		}
		loading = false;
	}

	function viewDeck(deckId: string) {
		goto(`/dashboard/decks/${deckId}`);
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
		<h1>Dashboard</h1>
		<p>Welcome, {user.email}!</p>

		{#if error}
			<div class="error">{error}</div>
		{/if}

		<section>
			<h2>Your Decks</h2>
			{#if decks.length === 0}
				<p>No decks yet. Create your first deck to get started!</p>
			{:else}
				<div class="decks-grid">
					{#each decks as deck (deck.id)}
						<button class="deck-card" onclick={() => viewDeck(deck.id)} type="button">
							<h3>{deck.name}</h3>
							{#if deck.description}
								<p>{deck.description}</p>
							{/if}
							<p class="card-count">{deck.card_count} cards</p>
						</button>
					{/each}
				</div>
			{/if}
		</section>

		<button onclick={handleLogout}>Log Out</button>
	{/if}
</main>

<style>
	main {
		max-width: 1000px;
		margin: 2rem auto;
		padding: 1rem;
	}

	.error {
		color: #d32f2f;
		background: #ffebee;
		padding: 1rem;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	section {
		margin: 2rem 0;
		padding: 1rem;
		border: 1px solid #eee;
		border-radius: 8px;
	}

	.decks-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
		margin: 1rem 0;
	}

	.deck-card {
		border: 1px solid #ddd;
		border-radius: 8px;
		padding: 1.5rem;
		background: white;
		cursor: pointer;
		text-align: left;
		transition: all 0.2s;
	}

	.deck-card:hover {
		border-color: #007bff;
		box-shadow: 0 2px 8px rgba(0, 123, 255, 0.1);
	}

	.deck-card h3 {
		margin: 0 0 0.5rem 0;
		color: #333;
	}

	.deck-card p {
		margin: 0.25rem 0;
		color: #666;
		font-size: 0.9rem;
	}

	.card-count {
		margin-top: 1rem;
		font-weight: 500;
		color: #1976d2;
	}

	button {
		padding: 0.75rem 1.5rem;
		background: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
	}

	button:hover {
		background: #0056b3;
	}
</style>
