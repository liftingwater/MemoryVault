import { fireEvent, render, screen } from '@testing-library/svelte';
import { describe, expect, it, vi } from 'vitest';
import CardEditor from './CardEditor.svelte';

describe('CardEditor', () => {
	it('blocks submission when front content is empty', async () => {
		const onsave = vi.fn();
		render(CardEditor, { onsave });

		await fireEvent.click(screen.getByRole('button', { name: 'Add Card' }));

		expect(onsave).not.toHaveBeenCalled();
		expect(screen.getByText('Front content is required.')).toBeInTheDocument();
	});

	it('blocks submission when back content is empty', async () => {
		const onsave = vi.fn();
		render(CardEditor, { onsave });

		await fireEvent.input(screen.getByLabelText('Front (markdown)'), {
			target: { value: 'Question' }
		});
		await fireEvent.click(screen.getByRole('button', { name: 'Add Card' }));

		expect(onsave).not.toHaveBeenCalled();
		expect(screen.getByText('Back content is required.')).toBeInTheDocument();
	});

	it('emits a front_back card when both fields are filled', async () => {
		const onsave = vi.fn();
		render(CardEditor, { onsave });

		await fireEvent.input(screen.getByLabelText('Front (markdown)'), {
			target: { value: 'What is 2+2?' }
		});
		await fireEvent.input(screen.getByLabelText('Back (markdown)'), {
			target: { value: '4' }
		});
		await fireEvent.click(screen.getByRole('button', { name: 'Add Card' }));

		expect(onsave).toHaveBeenCalledWith({
			card_type: 'front_back',
			front_md: 'What is 2+2?',
			back_md: '4'
		});
	});

	it('requires a cloze marker before submitting a cloze card', async () => {
		const onsave = vi.fn();
		render(CardEditor, { onsave });

		await fireEvent.click(screen.getByLabelText('Cloze'));
		await fireEvent.input(
			screen.getByLabelText('Sentence (select text, then click "Hide selection")'),
			{ target: { value: 'The capital of France is Paris' } }
		);
		await fireEvent.click(screen.getByRole('button', { name: 'Add Card' }));

		expect(onsave).not.toHaveBeenCalled();
		expect(
			screen.getByText('Mark at least one cloze deletion using the highlight button.')
		).toBeInTheDocument();
	});

	it('wraps the selected text in cloze syntax on "Hide selection"', async () => {
		const onsave = vi.fn();
		render(CardEditor, { onsave });

		await fireEvent.click(screen.getByLabelText('Cloze'));
		const textarea = screen.getByLabelText(
			'Sentence (select text, then click "Hide selection")'
		) as HTMLTextAreaElement;
		await fireEvent.input(textarea, {
			target: { value: 'The capital of France is Paris' }
		});
		textarea.setSelectionRange(25, 30);
		await fireEvent.click(screen.getByRole('button', { name: 'Hide selection' }));

		expect(textarea.value).toBe('The capital of France is {{Paris}}');

		await fireEvent.click(screen.getByRole('button', { name: 'Add Card' }));
		expect(onsave).toHaveBeenCalledWith({
			card_type: 'cloze',
			front_md: 'The capital of France is {{Paris}}',
			cloze_text_md: 'The capital of France is {{Paris}}',
			cloze_answer: 'Paris'
		});
	});
});
