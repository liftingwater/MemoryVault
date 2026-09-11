<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import {
		endCoachingSession,
		getCoachingSession,
		getDeckOutline,
		sendCoachingMessage,
		type CoachingSession,
		type DeckOutline
	} from '$lib/api';
	import { supabase } from '$lib/supabase';
	import { onMount } from 'svelte';

	const deckId = page.params.id as string;
	const sessionId = page.url.searchParams.get('session');
	let token = $state('');
	let loading = $state(true);
	let session = $state<CoachingSession | null>(null);
	let outline = $state<DeckOutline | null>(null);
	let content = $state('');
	let error = $state('');
	let endError = $state('');
	let sending = $state(false);
	let ending = $state(false);

	const messages = $derived(
		[...(session?.messages ?? [])].sort((a, b) => a.created_at.localeCompare(b.created_at))
	);
	const canSend = $derived(session?.status === 'active');

	onMount(async () => {
		const {
			data: { session: authSession }
		} = await supabase.auth.getSession();
		if (!authSession) {
			goto('/login');
			return;
		}
		if (!sessionId) {
			error = 'No coaching session was selected. Start or continue one from the deck.';
			loading = false;
			return;
		}

		token = authSession.access_token;
		try {
			const [loadedSession, loadedOutline] = await Promise.all([
				getCoachingSession(token, sessionId),
				getDeckOutline(token, deckId).catch(() => null)
			]);
			if (loadedSession.deck_id !== deckId) {
				throw new Error('This coaching session belongs to another deck.');
			}
			session = loadedSession;
			outline = loadedOutline;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load coaching session';
		} finally {
			loading = false;
		}
	});

	async function sendMessage(event: SubmitEvent) {
		event.preventDefault();
		const message = content.trim();
		if (!session || !message || sending || !canSend) return;

		error = '';
		sending = true;
		try {
			const response = await sendCoachingMessage(token, session.id, message);
			session = {
				...session,
				messages: [
					...session.messages,
					response.user_message,
					...(response.assistant_message ? [response.assistant_message] : [])
				]
			};
			content = '';
			outline = response.outline ?? outline;
			if (response.error) error = response.error.message;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to send message';
		} finally {
			sending = false;
		}
	}

	async function endSession() {
		if (!session || ending || !canSend) return;

		endError = '';
		ending = true;
		try {
			const response = await endCoachingSession(token, session.id);
			session = { ...session, ...response.session };
			if (response.error) {
				endError = response.error.message;
			} else if (!response.context_saved) {
				endError = 'The session ended, but the deck context could not be saved.';
			}
		} catch (e) {
			endError = e instanceof Error ? e.message : 'Failed to end coaching session';
		} finally {
			ending = false;
		}
	}
</script>

<main>
	<p><a href={`/decks/${deckId}`}>← Back to deck</a></p>
	{#if loading}
		<p>Loading coaching session...</p>
	{:else if !session}
		<p class="error">{error || 'Coaching session not found.'}</p>
	{:else}
		<header>
			<div>
				<h1>AI Coaching</h1>
				<p class="meta">{session.status === 'active' ? 'Active session' : 'Archived session'}</p>
			</div>
			{#if canSend}
				<button class="end" onclick={endSession} disabled={ending}>
					{ending ? 'Ending...' : 'End session'}
				</button>
			{/if}
		</header>

		{#if error}<p class="error">{error}</p>{/if}
		{#if endError}<p class="notice">{endError} You can still return to the deck.</p>{/if}

		<section class="conversation" aria-label="Coaching conversation">
			{#if messages.length === 0}
				<p class="meta">Tell the coach what you want to learn to begin.</p>
			{:else}
				{#each messages as message (message.id)}
					<article class:assistant={message.role === 'assistant'} class="message">
						<strong>{message.role === 'assistant' ? 'Coach' : 'You'}</strong>
						<p>{message.content}</p>
					</article>
				{/each}
			{/if}
		</section>

		{#if canSend}
			<form onsubmit={sendMessage}>
				<label for="message">Your message</label>
				<textarea id="message" bind:value={content} disabled={sending} required></textarea>
				<button type="submit" disabled={sending || !content.trim()}>
					{sending ? 'Sending...' : 'Send message'}
				</button>
			</form>
		{/if}

		{#if outline}
			<section class="outline">
				<h2>Deck outline</h2>
				<ul>
					{#each outline.items as item (item.id)}
						<li>
							<strong>{item.section}: {item.title}</strong>
							{#if item.description}<p>{item.description}</p>{/if}
						</li>
					{/each}
				</ul>
			</section>
		{/if}
	{/if}
</main>

<style>
	main { max-width: 800px; margin: 2rem auto; padding: 1rem; }
	header { display: flex; justify-content: space-between; align-items: start; gap: 1rem; }
	.meta { color: #666; }
	.error { color: #b00020; }
	.notice { color: #7a4c00; }
	.conversation, .outline { margin: 1.5rem 0; padding: 1rem; border: 1px solid #eee; border-radius: 8px; }
	.message { margin: 0.75rem 0; padding: 0.75rem; background: #eef5ff; border-radius: 6px; }
	.message.assistant { background: #f4f4f4; }
	.message p { margin: 0.35rem 0 0; white-space: pre-wrap; }
	form { display: flex; flex-direction: column; gap: 0.5rem; }
	textarea { min-height: 6rem; padding: 0.5rem; font: inherit; }
	button { align-self: start; padding: 0.5rem 1rem; background: #0066cc; color: white; border: 0; border-radius: 4px; cursor: pointer; }
	button.end { background: #555; }
	button:disabled { opacity: 0.6; cursor: not-allowed; }
	.outline ul { padding-left: 1.25rem; }
	.outline p { margin: 0.25rem 0 0; }
</style>