<script lang="ts">
	import { getHealth } from '$lib/api';
	import { supabase } from '$lib/supabase';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import type { User } from '@supabase/supabase-js';

	let backendStatus = $state('checking');
	let user: User | null = $state(null);
	let authLoading = $state(true);

	onMount(async () => {
		// Check backend health
		try {
			const health = await getHealth();
			backendStatus = health.status;
		} catch {
			backendStatus = 'unreachable';
		}

		// Check auth status
		const {
			data: { session }
		} = await supabase.auth.getSession();
		user = session?.user ?? null;
		authLoading = false;
	});
</script>

<main>
	<h1>MemoryVault</h1>
	<p>AI-coached flashcards you write yourself.</p>

	<nav>
		{#if authLoading}
			<p>Loading...</p>
		{:else if user}
			<a href="/dashboard">Go to Dashboard</a>
		{:else}
			<a href="/login">Log In</a>
			<a href="/signup">Sign Up</a>
		{/if}
	</nav>

	<p class="status">Backend: {backendStatus}</p>
</main>

<style>
	main {
		max-width: 600px;
		margin: 2rem auto;
		padding: 1rem;
		text-align: center;
	}

	nav {
		margin: 2rem 0;
		display: flex;
		gap: 1rem;
		justify-content: center;
	}

	nav a {
		padding: 0.75rem 1.5rem;
		background: #0066cc;
		color: white;
		text-decoration: none;
		border-radius: 4px;
	}

	.status {
		color: #666;
		font-size: 0.875rem;
	}
</style>
