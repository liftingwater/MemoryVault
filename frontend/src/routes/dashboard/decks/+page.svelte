<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { supabase } from '$lib/supabase';
	import { listDecks, type Deck } from '$lib/api';
	import { onMount } from 'svelte';

	let decks: Deck[] = $state([]);
	let selectedDeck: Deck | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);

	async function loadDecks() {
		loading = true;
		error = null;
		try {
			const {
				data: { session }
			} = await supabase.auth.getSession();
			if (!session) {
				goto('/login');
				return;
			}

			decks = await listDecks();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load decks';
		}
		loading = false;
	}

	function selectDeck(deck: Deck) {
		selectedDeck = deck;
	}

	function deselectDeck() {
		selectedDeck = null;
	}

	onMount(() => loadDecks());
</script>

<main>
	<h1>Your Decks</h1>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	{#if loading}
		<p>Loading decks...</p>
	{:else if decks.length === 0}
		<p class="empty">No decks yet. Create your first deck to get started!</p>
	{:else}
		<div class="decks-grid">
			{#each decks as deck (deck.id)}
				<button
					class="deck-card"
					class:selected={selectedDeck?.id === deck.id}
					onclick={() => selectDeck(deck)}
				>
					<h3>{deck.name}</h3>
					{#if deck.description}
						<p>{deck.description}</p>
					{/if}
					<p class="card-count">{deck.card_count} cards</p>
				</button>
			{/each}
		</div>
	{/if}

	{#if selectedDeck}
		<div class="detail-panel">
			<div class="detail-header">
				<h2>{selectedDeck.name}</h2>
				<button onclick={deselectDeck} class="btn-close">×</button>
			</div>

			<div class="detail-content">
				{#if selectedDeck.description}
					<p>{selectedDeck.description}</p>
				{/if}

				<p>
					<strong>{selectedDeck.card_count}</strong>
					{selectedDeck.card_count === 1 ? 'card' : 'cards'} in this deck
				</p>
			</div>
		</div>
	{/if}
</main>

<style>
	main {
		max-width: 1200px;
		margin: 2rem auto;
		padding: 1rem;
	}

	h1 {
		text-align: center;
		color: #333;
	}

	.error {
		color: #d32f2f;
		background: #ffebee;
		padding: 1rem;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	.empty {
		text-align: center;
		color: #666;
		padding: 2rem;
	}

	.decks-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
		gap: 1rem;
		margin-bottom: 2rem;
	}

	.deck-card {
		border: 2px solid #ddd;
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

	.deck-card.selected {
		border-color: #007bff;
		background: #e3f2fd;
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

	.detail-panel {
		background: #f5f5f5;
		border: 1px solid #ddd;
		border-radius: 8px;
		padding: 1.5rem;
		margin-top: 2rem;
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.detail-header h2 {
		margin: 0;
	}

	.btn-close {
		background: none;
		border: none;
		font-size: 1.5rem;
		cursor: pointer;
		color: #666;
	}

	.btn-close:hover {
		color: #333;
	}

	.detail-content {
		padding: 1rem;
	}
</style>
