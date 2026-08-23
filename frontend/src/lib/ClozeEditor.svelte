<script lang="ts">
	let textInput = $state('');
	let clozeAnswer = $state('');
	let selectedText = $state('');
	let preview = $state('');

	function handleTextSelect() {
		selectedText = window.getSelection()?.toString() ?? '';
	}

	function handleMarkCloze() {
		if (!selectedText) {
			alert('Please select text to mark as cloze deletion');
			return;
		}

		// Replace selected text with cloze syntax {{answer}}
		const startIndex = textInput.indexOf(selectedText);
		if (startIndex === -1) return;

		const before = textInput.substring(0, startIndex);
		const after = textInput.substring(startIndex + selectedText.length);

		textInput = `${before}{{${selectedText}}}${after}`;
		clozeAnswer = selectedText;
		selectedText = '';
		updatePreview();
	}

	function updatePreview() {
		// Show preview with cloze deletions as blanks
		preview = textInput.replace(/\{\{[^}]+\}\}/g, '[...]');
	}

	function handleTextChange() {
		updatePreview();
	}
</script>

<div class="cloze-editor">
	<h3>Cloze Editor - Select text and click "Mark as Cloze"</h3>

	<div class="editor-section">
		<label for="cloze-text">Your Text (select text to hide)</label>
		<textarea
			id="cloze-text"
			bind:value={textInput}
			onselect={handleTextSelect}
			onchange={handleTextChange}
			oninput={handleTextChange}
			placeholder="Type or paste your text here. Then select text and click 'Mark as Cloze'..."
			rows="6"
		></textarea>

		<div class="selected-info">
			{#if selectedText}
				<p>Selected: <strong>{selectedText}</strong></p>
				<button onclick={handleMarkCloze} class="btn-mark">Mark as Cloze</button>
			{/if}
		</div>
	</div>

	{#if textInput}
		<div class="preview-section">
			<label>Preview (with deletions hidden)</label>
			<div class="preview">{preview}</div>
		</div>

		{#if clozeAnswer}
			<div class="answer-section">
				<label>Hidden Answer</label>
				<p class="answer">{clozeAnswer}</p>
			</div>
		{/if}
	{/if}

	<div class="output-section">
		<label>Output for Card</label>
		<div class="output-fields">
			<div>
				<strong>Cloze Text (ready to save):</strong>
				<code>{textInput || '(empty)'}</code>
			</div>
			<div>
				<strong>Answer:</strong>
				<code>{clozeAnswer || '(no answer selected)'}</code>
			</div>
		</div>
	</div>
</div>

<style>
	.cloze-editor {
		background: #f5f5f5;
		border: 2px solid #2196f3;
		border-radius: 8px;
		padding: 1.5rem;
		margin: 1rem 0;
	}

	h3 {
		margin-top: 0;
		color: #1976d2;
	}

	.editor-section,
	.preview-section,
	.answer-section,
	.output-section {
		margin-bottom: 1.5rem;
	}

	label {
		display: block;
		font-weight: 600;
		margin-bottom: 0.5rem;
		color: #333;
	}

	textarea {
		width: 100%;
		padding: 0.75rem;
		border: 1px solid #ddd;
		border-radius: 4px;
		font-family: 'Courier New', monospace;
		font-size: 1rem;
		resize: vertical;
	}

	.selected-info {
		margin-top: 0.75rem;
		padding: 0.75rem;
		background: #e3f2fd;
		border-radius: 4px;
	}

	.selected-info p {
		margin: 0 0 0.5rem 0;
	}

	.btn-mark {
		padding: 0.5rem 1rem;
		background: #4caf50;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-weight: 500;
	}

	.btn-mark:hover {
		background: #388e3c;
	}

	.preview {
		background: white;
		border: 1px solid #ddd;
		border-radius: 4px;
		padding: 1rem;
		line-height: 1.6;
		min-height: 80px;
	}

	.answer {
		background: white;
		padding: 0.75rem;
		border-left: 3px solid #4caf50;
		font-weight: 500;
		margin: 0;
	}

	.output-section {
		background: white;
		border: 1px solid #ddd;
		border-radius: 4px;
		padding: 1rem;
	}

	.output-fields {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	code {
		display: block;
		background: #f5f5f5;
		padding: 0.5rem;
		border-radius: 3px;
		word-break: break-word;
		font-size: 0.9rem;
		margin-top: 0.25rem;
	}
</style>
