<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { deleteDeck, getDeck, updateDeck, type Deck } from '$lib/api';

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
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load deck';
		} finally {
			loading = false;
		}
	});

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
</style>
