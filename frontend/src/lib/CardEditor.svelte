<script lang="ts">
	import { createCard, updateCard, type Card } from './api';

	interface Props {
		deckId: string;
		card?: Partial<Card> | null;
		onSaved?: () => void;
	}

	let { deckId, card = null, onSaved = () => {} }: Props = $props();

	let cardType = $state(card?.card_type ?? 'front_back');
	let frontMd = $state(card?.front_md ?? '');
	let backMd = $state(card?.back_md ?? '');
	let clozeTextMd = $state(card?.cloze_text_md ?? '');
	let clozeAnswer = $state(card?.cloze_answer ?? '');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit() {
		error = '';

		// Validation
		if (cardType === 'front_back') {
			if (!frontMd.trim()) {
				error = 'Question is required';
				return;
			}
		} else {
			if (!clozeTextMd.trim()) {
				error = 'Cloze text is required';
				return;
			}
		}

		loading = true;
		try {
			const cardData = {
				card_type: cardType as 'front_back' | 'cloze',
				front_md: cardType === 'front_back' ? frontMd : undefined,
				back_md: cardType === 'front_back' ? backMd : undefined,
				cloze_text_md: cardType === 'cloze' ? clozeTextMd : undefined,
				cloze_answer: cardType === 'cloze' ? clozeAnswer : undefined
			};

			if (card?.id) {
				await updateCard(card.id, cardData);
			} else {
				await createCard(deckId, cardData);
			}

			onSaved();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save card';
		}
		loading = false;
	}
</script>

<div class="editor">
	<h3>{card?.id ? 'Edit Card' : 'New Card'}</h3>

	<div class="form-group">
		<label>Card Type</label>
		<select bind:value={cardType} disabled={!!card?.id}>
			<option value="front_back">Front/Back</option>
			<option value="cloze">Cloze</option>
		</select>
	</div>

	{#if cardType === 'front_back'}
		<div class="form-group">
			<label>Question</label>
			<textarea
				bind:value={frontMd}
				placeholder="Enter the question or prompt..."
				rows="4"
			></textarea>
		</div>

		<div class="form-group">
			<label>Answer</label>
			<textarea
				bind:value={backMd}
				placeholder="Enter the answer..."
				rows="4"
			></textarea>
		</div>
	{:else}
		<div class="form-group">
			<label>Cloze Text</label>
			<textarea
				bind:value={clozeTextMd}
				placeholder="Type your sentence here. Wrap hidden text in double braces."
				rows="4"
			></textarea>
			<small>Example: The capital of France is {'{...}'}</small>
		</div>

		<div class="form-group">
			<label>Answer</label>
			<input
				type="text"
				bind:value={clozeAnswer}
				placeholder="The answer to the cloze deletion"
			/>
		</div>
	{/if}

	{#if error}
		<div class="error">{error}</div>
	{/if}

	<div class="actions">
		<button onclick={handleSubmit} disabled={loading}>
			{loading ? 'Saving...' : 'Save Card'}
		</button>
	</div>
</div>

<style>
	.editor {
		background: #f9f9f9;
		border: 1px solid #ddd;
		border-radius: 8px;
		padding: 1.5rem;
		margin: 1rem 0;
	}

	h3 {
		margin-top: 0;
	}

	.form-group {
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		font-weight: 500;
		margin-bottom: 0.5rem;
	}

	textarea,
	input[type='text'],
	select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-family: inherit;
		font-size: 1rem;
	}

	textarea {
		resize: vertical;
	}

	input[type='text']:disabled,
	select:disabled {
		background: #e0e0e0;
		cursor: not-allowed;
	}

	.error {
		color: #d32f2f;
		background: #ffebee;
		padding: 0.75rem;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
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

	button:disabled {
		background: #ccc;
		cursor: not-allowed;
	}
</style>
