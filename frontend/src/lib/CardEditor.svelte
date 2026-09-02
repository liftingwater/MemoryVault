<script lang="ts">
	import { renderMarkdown } from '$lib/markdown';
	import type { Card, CardCreateInput, CardType } from '$lib/api';

	type Props = {
		card?: Card | null;
		saving?: boolean;
		onsave: (input: CardCreateInput) => void;
		oncancel?: () => void;
	};

	let { card = null, saving = false, onsave, oncancel }: Props = $props();

	// Snapshot the incoming card once into editable local state. Each list row
	// mounts a fresh CardEditor (keyed by card id), so re-initialising on prop
	// change is unnecessary; the plain `initial` read makes that intent explicit.
	const initial = card;

	let cardType = $state<CardType>(initial?.card_type ?? 'front_back');
	let frontMd = $state(initial?.front_md ?? '');
	let backMd = $state(initial?.back_md ?? '');
	let clozeTextMd = $state(initial?.cloze_text_md ?? '');
	let clozeAnswer = $state(initial?.cloze_answer ?? '');
	let validationError = $state('');

	// The editing flag is true when we were handed an existing card. Card type
	// cannot change after creation, so the toggle is hidden while editing.
	const isEditing = initial !== null;

	let clozeTextarea: HTMLTextAreaElement | null = $state(null);

	function wrapSelectionAsCloze() {
		if (!clozeTextarea) {
			return;
		}
		const start = clozeTextarea.selectionStart;
		const end = clozeTextarea.selectionEnd;
		if (start === end) {
			validationError = 'Select some text to hide before marking a cloze.';
			return;
		}
		const selected = clozeTextMd.slice(start, end);
		clozeTextMd =
			clozeTextMd.slice(0, start) + `{{${selected}}}` + clozeTextMd.slice(end);
		if (!clozeAnswer) {
			clozeAnswer = selected;
		}
		validationError = '';
	}

	function validate(): CardCreateInput | null {
		validationError = '';
		if (cardType === 'front_back') {
			if (!frontMd.trim()) {
				validationError = 'Front content is required.';
				return null;
			}
			if (!backMd.trim()) {
				validationError = 'Back content is required.';
				return null;
			}
			return { card_type: 'front_back', front_md: frontMd, back_md: backMd };
		}
		if (!clozeTextMd.trim()) {
			validationError = 'Cloze text is required.';
			return null;
		}
		if (!clozeTextMd.includes('{{')) {
			validationError = 'Mark at least one cloze deletion using the highlight button.';
			return null;
		}
		return {
			card_type: 'cloze',
			front_md: clozeTextMd,
			cloze_text_md: clozeTextMd,
			cloze_answer: clozeAnswer.trim() || null
		};
	}

	function handleSubmit(event: SubmitEvent) {
		event.preventDefault();
		const input = validate();
		if (input) {
			onsave(input);
		}
	}
</script>

<form onsubmit={handleSubmit} class="card-editor">
	{#if !isEditing}
		<div class="type-toggle">
			<label>
				<input type="radio" bind:group={cardType} value="front_back" disabled={saving} />
				Front / Back
			</label>
			<label>
				<input type="radio" bind:group={cardType} value="cloze" disabled={saving} />
				Cloze
			</label>
		</div>
	{/if}

	{#if validationError}
		<p class="error">{validationError}</p>
	{/if}

	{#if cardType === 'front_back'}
		<label>
			Front (markdown)
			<textarea bind:value={frontMd} rows="3" disabled={saving}></textarea>
		</label>
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		<div class="preview">{@html renderMarkdown(frontMd)}</div>

		<label>
			Back (markdown)
			<textarea bind:value={backMd} rows="3" disabled={saving}></textarea>
		</label>
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		<div class="preview">{@html renderMarkdown(backMd)}</div>
	{:else}
		<label>
			Sentence (select text, then click "Hide selection")
			<textarea bind:this={clozeTextarea} bind:value={clozeTextMd} rows="3" disabled={saving}
			></textarea>
		</label>
		<button type="button" class="cloze-btn" onclick={wrapSelectionAsCloze} disabled={saving}>
			Hide selection
		</button>
		<label>
			Answer (optional)
			<input bind:value={clozeAnswer} disabled={saving} />
		</label>
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		<div class="preview">{@html renderMarkdown(clozeTextMd)}</div>
	{/if}

	<div class="actions">
		<button type="submit" disabled={saving}>
			{saving ? 'Saving...' : isEditing ? 'Save Card' : 'Add Card'}
		</button>
		{#if oncancel}
			<button type="button" class="secondary" onclick={oncancel} disabled={saving}>
				Cancel
			</button>
		{/if}
	</div>
</form>

<style>
	.card-editor {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.type-toggle {
		display: flex;
		gap: 1rem;
	}

	.type-toggle label {
		flex-direction: row;
		align-items: center;
		gap: 0.35rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	textarea,
	input {
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
		font-family: inherit;
	}

	.preview {
		padding: 0.5rem 0.75rem;
		border: 1px dashed #ccc;
		border-radius: 4px;
		background: #fafafa;
		min-height: 1.5rem;
	}

	.preview :global(.cloze) {
		background: #ffe08a;
		border-radius: 3px;
		padding: 0 0.2rem;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
	}

	button {
		padding: 0.5rem 1rem;
		background: #0066cc;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	button.secondary {
		background: #888;
	}

	button.cloze-btn {
		align-self: flex-start;
		background: #e0a800;
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.error {
		color: #cc0000;
		margin: 0;
	}
</style>
