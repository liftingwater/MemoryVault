import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		// The app is a static SPA served from S3 + CloudFront; all dynamic
		// content comes from the FastAPI backend at runtime.
		adapter: adapter({ fallback: 'index.html' }),
		prerender: {
			// Handle routes that can't be prerendered (dynamic routes like /dashboard/decks/[id])
			// They will be served via the fallback (index.html) and rendered client-side
			handleUnseenRoutes: 'ignore'
		}
	}
};

export default config;
