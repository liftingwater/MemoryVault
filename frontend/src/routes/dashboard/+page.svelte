<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import type { User } from '@supabase/supabase-js';

	let user: User | null = $state(null);
	let loading = $state(true);

	onMount(async () => {
		const {
			data: { session }
		} = await supabase.auth.getSession();

		if (!session) {
			goto('/login');
			return;
		}

		user = session.user;
		loading = false;
	});

	async function handleLogout() {
		await supabase.auth.signOut();
		goto('/');
	}
</script>

<main>
	{#if loading}
		<p>Loading...</p>
	{:else if user}
		<h1>Dashboard</h1>
		<p>Welcome, {user.email}!</p>

		<section>
			<h2>Your Decks</h2>
			<p>No decks yet. Create your first deck to get started!</p>
		</section>

		<button onclick={handleLogout}>Log Out</button>
	{/if}
</main>

<style>
	main {
		max-width: 800px;
		margin: 2rem auto;
		padding: 1rem;
	}

	section {
		margin: 2rem 0;
		padding: 1rem;
		border: 1px solid #eee;
		border-radius: 8px;
	}

	button {
		padding: 0.5rem 1rem;
		background: #666;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}
</style>
