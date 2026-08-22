<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleLogin(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		loading = true;

		try {
			const { error: authError } = await supabase.auth.signInWithPassword({
				email,
				password
			});

			if (authError) {
				error = authError.message;
			} else {
				goto('/dashboard');
			}
		} catch (e) {
			error = 'An unexpected error occurred';
		} finally {
			loading = false;
		}
	}
</script>

<main>
	<h1>Log In</h1>

	<form onsubmit={handleLogin}>
		<label>
			Email
			<input type="email" bind:value={email} required disabled={loading} />
		</label>

		<label>
			Password
			<input type="password" bind:value={password} required disabled={loading} />
		</label>

		{#if error}
			<p class="error">{error}</p>
		{/if}

		<button type="submit" disabled={loading}>
			{loading ? 'Logging in...' : 'Log In'}
		</button>
	</form>

	<p>Don't have an account? <a href="/signup">Sign up</a></p>
</main>

<style>
	main {
		max-width: 400px;
		margin: 2rem auto;
		padding: 1rem;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	label {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}

	input {
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	button {
		padding: 0.75rem;
		background: #0066cc;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
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
