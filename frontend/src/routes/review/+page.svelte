<script lang="ts">
	import { supabase } from '$lib/supabase';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { getDashboard, getDueCards, gradeCard, type Card, type Rating } from '$lib/api';
	import { renderMarkdown } from '$lib/markdown';

	let token = $state('');
	let loading = $state(true);
	let error = $state('');

	// The due queue snapshotted at session start. Grading a card advances
	// `index` without removing it from the array, so quitting mid-session
	// simply stops rendering further cards — already-graded ones stay graded
	// server-side, and ungraded ones are picked up again on the next visit.
	let queue = $state<Card[]>([]);
	let index = $state(0);
	let showAnswer = $state(false);
	let grading = $state(false);

	let reviewedCount = $state(0);
	let correctCount = $state(0);
	let finished = $state(false);
	let streak = $state(0);

	const currentCard = $derived(queue[index] ?? null);

	onMount(async () => {
		const {
			data: { session }
		} = await supabase.auth.getSession();

		if (!session) {
			goto('/login');
			return;
		}

		token = session.access_token;
		try {
			queue = await getDueCards(token);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load due cards';
		} finally {
			loading = false;
		}
	});

	async function finishSession() {
		finished = true;
		try {
			const dashboard = await getDashboard(token);
			streak = dashboard.streak;
		} catch {
			// Streak is a nice-to-have on the summary; ignore failures here.
		}
	}

	async function grade(rating: Rating) {
		if (!currentCard || grading) {
			return;
		}
		error = '';
		grading = true;
		try {
			await gradeCard(token, currentCard.id, rating);
			reviewedCount += 1;
			if (rating === 'got_it') {
				correctCount += 1;
			}
			showAnswer = false;
			if (index + 1 >= queue.length) {
				await finishSession();
			} else {
				index += 1;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to grade card';
		} finally {
			grading = false;
		}
	}

	function quit() {
		finishSession();
	}

	const percentCorrect = $derived(
		reviewedCount === 0 ? 0 : Math.round((correctCount / reviewedCount) * 100)
	);
</script>

<main>
	<p><a href="/dashboard">← Back to dashboard</a></p>

	{#if loading}
		<p>Loading...</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else if finished || queue.length === 0}
		<section class="summary">
			<h1>{queue.length === 0 ? 'No cards due' : 'Session complete'}</h1>
			{#if queue.length > 0}
				<p>Cards reviewed: {reviewedCount}</p>
				<p>Correct: {percentCorrect}%</p>
				<p>Streak: {streak} {streak === 1 ? 'day' : 'days'}</p>
			{/if}
			<a class="link-btn" href="/dashboard">Back to dashboard</a>
		</section>
	{:else if currentCard}
		<section class="review-card">
			<p class="progress">Card {index + 1} of {queue.length}</p>

			<!-- eslint-disable-next-line svelte/no-at-html-tags -->
			<div class="face">{@html renderMarkdown(currentCard.front_md)}</div>

			{#if showAnswer}
				<!-- eslint-disable-next-line svelte/no-at-html-tags -->
				<div class="face back">
					{@html renderMarkdown(
						currentCard.card_type === 'cloze'
							? (currentCard.cloze_answer ?? '')
							: (currentCard.back_md ?? '')
					)}
				</div>
				<div class="actions">
					<button class="need-review" onclick={() => grade('need_review')} disabled={grading}>
						Need to review
					</button>
					<button class="got-it" onclick={() => grade('got_it')} disabled={grading}>
						Got it
					</button>
				</div>
			{:else}
				<div class="actions">
					<button onclick={() => (showAnswer = true)}>Show Answer</button>
				</div>
			{/if}

			<button class="quit" onclick={quit}>Quit session</button>
		</section>
	{/if}
</main>

<style>
	main {
		max-width: 600px;
		margin: 2rem auto;
		padding: 1rem;
	}

	.error {
		color: #cc0000;
	}

	.progress {
		color: #666;
		font-size: 0.85rem;
	}

	.face {
		padding: 1.5rem;
		border: 1px solid #ddd;
		border-radius: 8px;
		margin-bottom: 1rem;
		min-height: 4rem;
	}

	.face.back {
		background: #fafafa;
	}

	.face :global(.cloze) {
		background: #ffe08a;
		border-radius: 3px;
		padding: 0 0.2rem;
	}

	.actions {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 1.5rem;
	}

	button {
		padding: 0.75rem 1.5rem;
		background: #0066cc;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 1rem;
	}

	button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	button.got-it {
		background: #2e7d32;
	}

	button.need-review {
		background: #c62828;
	}

	button.quit {
		background: none;
		color: #888;
		padding: 0;
		font-size: 0.85rem;
	}

	.summary h1 {
		margin-top: 0;
	}

	.link-btn {
		display: inline-block;
		margin-top: 1rem;
		padding: 0.5rem 1rem;
		background: #0066cc;
		color: white;
		border-radius: 4px;
		text-decoration: none;
	}
</style>
