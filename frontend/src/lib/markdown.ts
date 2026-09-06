/**
 * Minimal, dependency-free Markdown renderer for card previews.
 *
 * Only a small, safe subset is supported (headings, bold, italic, inline
 * code, line breaks). Input is HTML-escaped first so rendered content can
 * never inject markup. Cloze markers ({{answer}}) render as a blank.
 */

function escapeHtml(text: string): string {
	return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderInline(text: string): string {
	return text
		.replace(/\{\{([^}]+)\}\}/g, '<span class="cloze">[...]</span>')
		.replace(/`([^`]+)`/g, '<code>$1</code>')
		.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
		.replace(/\*([^*]+)\*/g, '<em>$1</em>');
}

export function renderMarkdown(markdown: string): string {
	const escaped = escapeHtml(markdown ?? '');
	const lines = escaped.split(/\r?\n/);
	const html: string[] = [];

	for (const line of lines) {
		const trimmed = line.trim();
		if (trimmed === '') {
			continue;
		}

		const heading = /^(#{1,3})\s+(.*)$/.exec(trimmed);
		if (heading) {
			const level = heading[1].length;
			html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
		} else {
			html.push(`<p>${renderInline(trimmed)}</p>`);
		}
	}

	return html.join('\n');
}
