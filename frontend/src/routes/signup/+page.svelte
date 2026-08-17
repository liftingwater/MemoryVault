<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';

	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let error = $state('');
	let loading = $state(false);
	let success = $state(false);

	async function handleSignup(event: SubmitEvent) {
		event.preventDefault();
		error = '';
		loading = true;

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			loading = false;
			return;
		}

		if (password.length < 6) {
			error = 'Password must be at least 6 characters';
			loading = false;
			return;
		}

		try {
			const { error: authError } = await supabase.auth.signUp({
				email,
				password
			});

			if (authError) {
				error = authError.message;
			} else {
				success = true;
			}
		} catch (e) {
			error = 'An unexpected error occurred';
		} finally {
			loading = false;
		}
	}
</script>

<main>
	<h1>Sign Up</h1>

	{#if success}
		<p class="success">Check your email for a confirmation link!</p>
		<p><a href="/login">Go to login</a></p>
	{:else}
		<form onsubmit={handleSignup}>
			<label>
				Email
				<input type="email" bind:value={email} required disabled={loading} />
			</label>

			<label>
				Password
				<input type="password" bind:value={password} required disabled={loading} />
			</label>

			<label>
				Confirm Password
				<input type="password" bind:value={confirmPassword} required disabled={loading} />
			</label>

			{#if error}
				<p class="error">{error}</p>
			{/if}

			<button type="submit" disabled={loading}>
				{loading ? 'Creating account...' : 'Sign Up'}
			</button>
		</form>

		<p>Already have an account? <a href="/login">Log in</a></p>
	{/if}
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

	.success {
		color: #008800;
		font-weight: bold;
	}
</style>
