<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import {
		createCard,
		deleteCard,
		deleteDeck,
		getDeck,
		listCards,
		updateCard,
		updateDeck,
		type Card,
		type CardCreateInput,
		type Deck
	} from '$lib/api';
	import CardEditor from '$lib/CardEditor.svelte';
	import { renderMarkdown } from '$lib/markdown';

	// This route always provides the `id` param.
	const deckId = page.params.id as string;

	let token = $state('');
	let loading = $state(true);
	let deck = $state<Deck | null>(null);
	let error = $state('');

	let name = $state('');
	let description = $state('');
	let tagsInput = $state('');
	let saving = $state(false);
	let deleting = $state(false);

	let cards = $state<Card[]>([]);
	let cardsError = $state('');
	let search = $state('');
	let searchTimer: ReturnType<typeof setTimeout> | null = null;
	let creatingCard = $state(false);
	let editingCardId = $state<string | null>(null);
	let savingCard = $state(false);

	function parseTags(value: string): string[] {
		return value
			.split(',')
			.map((tag) => tag.trim())
			.filter((tag) => tag.length > 0);
	}

	function syncForm(d: Deck) {
		name = d.name;
		description = d.description ?? '';
		tagsInput = d.tags.join(', ');
	}

	onMount(async () => {
		const {
			data: { session }
		} = await supabase.auth.getSession();

		if (!session) {
			goto('/login');
			return;
		}

		token = session.access_token;
		try {
			deck = await getDeck(token, deckId);
			syncForm(deck);
			await loadCards();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load deck';
		} finally {
			loading = false;
		}
	});

	async function loadCards() {
		cardsError = '';
		try {
			cards = await listCards(token, deckId, search.trim() || undefined);
		} catch (e) {
			cardsError = e instanceof Error ? e.message : 'Failed to load cards';
		}
	}

	function handleSearchInput() {
		if (searchTimer) {
			clearTimeout(searchTimer);
		}
		searchTimer = setTimeout(loadCards, 250);
	}

	async function handleCreateCard(input: CardCreateInput) {
		cardsError = '';
		savingCard = true;
		try {
			const card = await createCard(token, deckId, input);
			cards = [card, ...cards];
			creatingCard = false;
		} catch (e) {
			cardsError = e instanceof Error ? e.message : 'Failed to create card';
		} finally {
			savingCard = false;
		}
	}

	async function handleUpdateCard(cardId: string, input: CardCreateInput) {
		cardsError = '';
		savingCard = true;
		try {
			const updated = await updateCard(token, cardId, {
				front_md: input.front_md,
				back_md: input.back_md ?? null,
				cloze_text_md: input.cloze_text_md ?? null,
				cloze_answer: input.cloze_answer ?? null
			});
			cards = cards.map((c) => (c.id === cardId ? updated : c));
			editingCardId = null;
		} catch (e) {
			cardsError = e instanceof Error ? e.message : 'Failed to update card';
		} finally {
			savingCard = false;
		}
	}

	async function handleDeleteCard(cardId: string) {
		if (!confirm('Delete this card? This cannot be undone.')) {
			return;
		}
		cardsError = '';
		try {
			await deleteCard(token, cardId);
			cards = cards.filter((c) => c.id !== cardId);
		} catch (e) {
			cardsError = e instanceof Error ? e.message : 'Failed to delete card';
		}
	}

	async function handleSave(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		saving = true;
		try {
			deck = await updateDeck(token, deckId, {
				name,
				description: description.trim() || null,
				tags: parseTags(tagsInput)
			});
			syncForm(deck);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to update deck';
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		if (!confirm('Delete this deck and all its cards? This cannot be undone.')) {
			return;
		}
		error = '';
		deleting = true;
		try {
			await deleteDeck(token, deckId);
			goto('/dashboard');
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to delete deck';
			deleting = false;
		}
	}
</script>

<main>
	<p><a href="/dashboard">← Back to dashboard</a></p>

	{#if loading}
		<p>Loading...</p>
	{:else if deck}
		<h1>{deck.name}</h1>
		<p class="meta">{deck.card_count} cards</p>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		<section>
			<h2>Edit Deck</h2>
			<form onsubmit={handleSave}>
				<label>
					Name
					<input bind:value={name} required disabled={saving} />
				</label>
				<label>
					Description
					<input bind:value={description} disabled={saving} />
				</label>
				<label>
					Tags (comma-separated)
					<input bind:value={tagsInput} disabled={saving} />
				</label>
				<button type="submit" disabled={saving}>
					{saving ? 'Saving...' : 'Save Changes'}
				</button>
			</form>
		</section>

		<section>
			<h2>Cards</h2>

			{#if cardsError}
				<p class="error">{cardsError}</p>
			{/if}

			<div class="card-toolbar">
				<input
					class="search"
					placeholder="Search cards..."
					bind:value={search}
					oninput={handleSearchInput}
				/>
				{#if !creatingCard && editingCardId === null}
					<button onclick={() => (creatingCard = true)}>Add Card</button>
				{/if}
			</div>

			{#if creatingCard}
				<div class="card-form">
					<CardEditor
						saving={savingCard}
						onsave={handleCreateCard}
						oncancel={() => (creatingCard = false)}
					/>
				</div>
			{/if}

			{#if cards.length === 0}
				<p>No cards yet. Add your first card above.</p>
			{:else}
				<ul class="cards">
					{#each cards as card (card.id)}
						<li>
							{#if editingCardId === card.id}
								<CardEditor
									{card}
									saving={savingCard}
									onsave={(input) => handleUpdateCard(card.id, input)}
									oncancel={() => (editingCardId = null)}
								/>
							{:else}
								<span class="badge">{card.card_type}</span>
								<!-- eslint-disable-next-line svelte/no-at-html-tags -->
								<div class="card-preview">{@html renderMarkdown(card.front_md)}</div>
								{#if card.card_type === 'front_back' && card.back_md}
									<!-- eslint-disable-next-line svelte/no-at-html-tags -->
									<div class="card-preview back">{@html renderMarkdown(card.back_md)}</div>
								{/if}
								<div class="card-actions">
									<button class="link" onclick={() => (editingCardId = card.id)}>Edit</button>
									<button class="link delete" onclick={() => handleDeleteCard(card.id)}>
										Delete
									</button>
								</div>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
		</section>

		<section class="danger">
			<h2>Danger Zone</h2>
			<button class="delete" onclick={handleDelete} disabled={deleting}>
				{deleting ? 'Deleting...' : 'Delete Deck'}
			</button>
		</section>
	{:else}
		<p class="error">{error || 'Deck not found.'}</p>
	{/if}
</main>

<style>
	main {
		max-width: 800px;
		margin: 2rem auto;
		padding: 1rem;
	}

	.meta {
		color: #666;
	}

	section {
		margin: 2rem 0;
		padding: 1rem;
		border: 1px solid #eee;
		border-radius: 8px;
	}

	section.danger {
		border-color: #f0c0c0;
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

	button {
		padding: 0.5rem 1rem;
		background: #0066cc;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	button.delete {
		background: #cc0000;
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: #cc0000;
	}

	.card-toolbar {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.search {
		flex: 1;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	.card-form {
		margin-bottom: 1rem;
		padding: 1rem;
		border: 1px solid #ddd;
		border-radius: 6px;
	}

	ul.cards {
		list-style: none;
		padding: 0;
		margin: 0;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	ul.cards li {
		padding: 0.75rem;
		border: 1px solid #eee;
		border-radius: 6px;
	}

	.badge {
		display: inline-block;
		font-size: 0.7rem;
		text-transform: uppercase;
		background: #eef;
		color: #336;
		padding: 0.1rem 0.4rem;
		border-radius: 3px;
		margin-bottom: 0.5rem;
	}

	.card-preview.back {
		color: #555;
		border-top: 1px dashed #ddd;
		margin-top: 0.5rem;
		padding-top: 0.5rem;
	}

	.card-preview :global(.cloze) {
		background: #ffe08a;
		border-radius: 3px;
		padding: 0 0.2rem;
	}

	.card-actions {
		display: flex;
		gap: 0.75rem;
		margin-top: 0.5rem;
	}

	button.link {
		background: none;
		color: #0066cc;
		padding: 0;
		font-size: 0.85rem;
	}

	button.link.delete {
		background: none;
		color: #cc0000;
	}
</style>
