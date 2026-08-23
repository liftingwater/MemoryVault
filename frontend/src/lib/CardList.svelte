<script lang="ts">
	import { listCards, deleteCard } from './api';
	import type { Card } from './api';
	import { onMount } from 'svelte';

	interface Props {
		deckId: string;
	}

	let { deckId }: Props = $props();

	let cards: Card[] = $state([]);
	let loading = $state(false);
	let error: string | null = $state(null);
	let searchQuery = $state('');
	let editingCardId: string | null = $state(null);

	async function loadCards(search?: string) {
		loading = true;
		error = null;
		try {
			cards = await listCards(deckId, search);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load cards';
		}
		loading = false;
	}

	async function handleSearch() {
		await loadCards(searchQuery || undefined);
	}

	async function handleDelete(cardId: string) {
		if (!confirm('Delete this card?')) return;
		try {
			await deleteCard(cardId);
			await loadCards(searchQuery || undefined);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete card';
		}
	}

	function editCard(cardId: string) {
		editingCardId = cardId;
	}

	onMount(() => loadCards());
</script>

<div class="card-list">
	<div class="search-bar">
		<input
			type="text"
			placeholder="Search cards..."
			bind:value={searchQuery}
			onkeyup={(e) => e.key === 'Enter' && handleSearch()}
		/>
		<button onclick={handleSearch}>Search</button>
		<button onclick={() => loadCards()}>Clear</button>
	</div>

	{#if error}
		<div class="error">{error}</div>
	{/if}

	{#if loading}
		<p>Loading cards...</p>
	{:else if cards.length === 0}
		<p class="empty">No cards yet. Create your first card!</p>
	{:else}
		<div class="cards">
			{#each cards as card (card.id)}
				<div class="card-item">
					<div class="card-header">
						<span class="card-type">{card.card_type}</span>
						<div class="card-actions">
							<button onclick={() => editCard(card.id)} class="btn-edit">Edit</button>
							<button onclick={() => handleDelete(card.id)} class="btn-delete">Delete</button>
						</div>
					</div>
					<div class="card-content">
						{#if card.card_type === 'front_back'}
							<p><strong>Q:</strong> {card.front_md}</p>
							{#if card.back_md}
								<p><strong>A:</strong> {card.back_md}</p>
							{/if}
						{:else}
							<p>{card.cloze_text_md}</p>
							{#if card.cloze_answer}
								<p class="answer">Answer: {card.cloze_answer}</p>
							{/if}
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>

<style>
	.card-list {
		margin: 2rem 0;
	}

	.search-bar {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
	}

	.search-bar input {
		flex: 1;
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
	}

	.search-bar button {
		padding: 0.5rem 1rem;
		background: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	.search-bar button:hover {
		background: #0056b3;
	}

	.error {
		color: #d32f2f;
		padding: 1rem;
		background: #ffebee;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	.empty {
		text-align: center;
		color: #666;
		padding: 2rem;
	}

	.cards {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.card-item {
		border: 1px solid #ddd;
		border-radius: 4px;
		padding: 1rem;
		background: #f9f9f9;
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.card-type {
		font-size: 0.85rem;
		background: #e3f2fd;
		color: #1976d2;
		padding: 0.25rem 0.5rem;
		border-radius: 3px;
	}

	.card-actions {
		display: flex;
		gap: 0.5rem;
	}

	.card-actions button {
		padding: 0.25rem 0.75rem;
		font-size: 0.85rem;
		border: none;
		border-radius: 3px;
		cursor: pointer;
	}

	.btn-edit {
		background: #4caf50;
		color: white;
	}

	.btn-delete {
		background: #f44336;
		color: white;
	}

	.btn-edit:hover {
		background: #388e3c;
	}

	.btn-delete:hover {
		background: #d32f2f;
	}

	.card-content p {
		margin: 0.5rem 0;
		line-height: 1.5;
	}

	.answer {
		color: #666;
		font-style: italic;
	}
</style>
