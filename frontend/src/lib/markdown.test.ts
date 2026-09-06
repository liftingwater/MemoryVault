import { describe, expect, it } from 'vitest';
import { renderMarkdown } from './markdown';

describe('renderMarkdown', () => {
	it('wraps plain text in a paragraph', () => {
		expect(renderMarkdown('hello')).toBe('<p>hello</p>');
	});

	it('renders headings by level', () => {
		expect(renderMarkdown('## Title')).toBe('<h2>Title</h2>');
	});

	it('renders bold, italic, and inline code', () => {
		expect(renderMarkdown('**b** *i* `c`')).toBe(
			'<p><strong>b</strong> <em>i</em> <code>c</code></p>'
		);
	});

	it('escapes HTML so raw markup cannot be injected', () => {
		expect(renderMarkdown('<script>alert(1)</script>')).toBe(
			'<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
		);
	});

	it('renders cloze markers as a blank', () => {
		expect(renderMarkdown('The capital is {{Paris}}')).toBe(
			'<p>The capital is <span class="cloze">[...]</span></p>'
		);
	});

	it('ignores blank lines', () => {
		expect(renderMarkdown('a\n\nb')).toBe('<p>a</p>\n<p>b</p>');
	});
});
