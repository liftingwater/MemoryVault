<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
	import CardList from '$lib/CardList.svelte';
	import CardEditor from '$lib/CardEditor.svelte';
	import ClozeEditor from '$lib/ClozeEditor.svelte';
	import { onMount } from 'svelte';

	let deckId: string | undefined = $state();
	let showEditor = $state(false);
	let showClozeEditor = $state(false);

	onMount(async () => {
		const {
			data: { session }
		} = await supabase.auth.getSession();
		if (!session) {
			goto('/login');
			return;
		}

		deckId = $page.params.id;
	});

	function toggleEditor() {
		showEditor = !showEditor;
	}

	function toggleClozeEditor() {
		showClozeEditor = !showClozeEditor;
	}

	function handleCardSaved() {
		showEditor = false;
		showClozeEditor = false;
	}
</script>

{#if deckId}
	<main>
		<div class="header">
			<h1>Deck: {deckId}</h1>
			<div class="actions">
				<button onclick={toggleEditor} class="btn-primary">
					{showEditor ? 'Close Editor' : 'Add Front/Back Card'}
				</button>
				<button onclick={toggleClozeEditor} class="btn-primary">
					{showClozeEditor ? 'Close Cloze' : 'Add Cloze Card'}
				</button>
			</div>
		</div>

		{#if showEditor}
			<CardEditor {deckId} onSaved={handleCardSaved} />
		{/if}

		{#if showClozeEditor}
			<div class="cloze-section">
				<ClozeEditor />
			</div>
		{/if}

		{#key deckId}
			<CardList {deckId} />
		{/key}
	</main>
{/if}

<style>
	main {
		max-width: 1000px;
		margin: 2rem auto;
		padding: 1rem;
	}

	.header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
		border-bottom: 2px solid #ddd;
		padding-bottom: 1rem;
	}

	h1 {
		margin: 0;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
	}

	.btn-primary {
		padding: 0.75rem 1.5rem;
		background: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
	}

	.btn-primary:hover {
		background: #0056b3;
	}

	.cloze-section {
		margin: 2rem 0;
	}
</style>
