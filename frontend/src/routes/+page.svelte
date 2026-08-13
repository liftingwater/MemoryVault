<script lang="ts">
	import { getHealth } from '$lib/api';
	import { onMount } from 'svelte';

	let backendStatus = $state('checking');

	onMount(async () => {
		try {
			const health = await getHealth();
			backendStatus = health.status;
		} catch {
			backendStatus = 'unreachable';
		}
	});
</script>

<main>
	<h1>MemoryVault</h1>
	<p>AI-coached flashcards you write yourself.</p>
	<p>Backend: {backendStatus}</p>
</main>
