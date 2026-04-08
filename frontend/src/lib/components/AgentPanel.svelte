<script lang="ts">
	const API_URL = 'http://localhost:8000';

	let { agentId = null, simulationId }: {
		agentId: number | null;
		simulationId: number;
	} = $props();

	interface RoundResult {
		round_number: number;
		stance_value: number;
		sentiment: number;
	}

	let results = $state<RoundResult[]>([]);
	let loading = $state(false);
	let agentName = $state('');

	// Load results when agentId changes
	$effect(() => {
		if (agentId !== null && simulationId) {
			loadResults(agentId, simulationId);
		} else {
			results = [];
		}
	});

	async function loadResults(id: number, simId: number) {
		loading = true;
		try {
			const res = await fetch(`${API_URL}/api/simulations/${simId}/agents/${id}/results`);
			results = await res.json();
		} catch (e) {
			results = [];
		} finally {
			loading = false;
		}
	}

	function stanceColor(val: number): string {
		if (val < -0.3) return '#ff6b6b';
		if (val > 0.3) return '#00f2fe';
		return '#a0a0b0';
	}

	function stanceLabel(val: number): string {
		if (val < -0.6) return 'Strongly Opposed';
		if (val < -0.2) return 'Opposed';
		if (val < 0.2) return 'Neutral';
		if (val < 0.6) return 'Supportive';
		return 'Strongly Supportive';
	}

	function stancePct(val: number): number {
		return ((val + 1) / 2) * 100;
	}
</script>

<!-- Slide-in Drawer -->
<div
	class="fixed top-0 right-0 h-full w-80 z-50 flex flex-col"
	style="
		background: rgba(10,10,15,0.97);
		backdrop-filter: blur(20px);
		border-left: 1px solid rgba(255,255,255,0.08);
		transform: translateX({agentId !== null ? '0' : '100%'});
		transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		box-shadow: -20px 0 60px rgba(0,0,0,0.5);
	"
>
	<!-- Header -->
	<div class="flex items-center justify-between p-5 border-b border-white/5">
		<div>
			<p class="text-[10px] uppercase tracking-widest text-white/30 mb-0.5">Agent Detail</p>
			<h3 class="text-base font-display font-semibold text-white">
				{agentId !== null ? `Agent #${agentId}` : 'Select an agent'}
			</h3>
		</div>
		<button
			onclick={() => agentId = null}
			class="w-8 h-8 rounded-lg flex items-center justify-center text-white/30 hover:text-white hover:bg-white/10 transition-all"
		>
			✕
		</button>
	</div>

	<!-- Stance Bar -->
	{#if results.length > 0}
		{@const latest = results[0]}
		<div class="p-5 border-b border-white/5">
			<p class="text-[10px] uppercase tracking-widest text-white/30 mb-3">Current Stance</p>
			<div class="flex items-center justify-between mb-2">
				<span class="text-sm font-semibold" style="color: {stanceColor(latest.stance_value)}">
					{stanceLabel(latest.stance_value)}
				</span>
				<span class="text-xs font-mono text-white/40">{latest.stance_value.toFixed(2)}</span>
			</div>
			<div class="w-full h-1.5 rounded-full relative" style="background: rgba(255,255,255,0.08);">
				<div
					class="absolute top-0 left-0 h-full rounded-full transition-all duration-700"
					style="width: {stancePct(latest.stance_value)}%; background: {stanceColor(latest.stance_value)}; box-shadow: 0 0 8px {stanceColor(latest.stance_value)}60;"
				></div>
				<!-- Midpoint marker -->
				<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-0.5 h-3 bg-white/20 rounded-full"></div>
			</div>
			<div class="flex justify-between mt-1 text-[9px] text-white/20">
				<span>Oppose</span><span>Support</span>
			</div>
		</div>
	{/if}

	<!-- Round History -->
	<div class="flex-grow overflow-y-auto p-5">
		<p class="text-[10px] uppercase tracking-widest text-white/30 mb-4">Round History</p>

		{#if loading}
			<div class="text-center text-white/20 text-sm animate-pulse py-8">Loading...</div>
		{:else if results.length === 0}
			<div class="text-center text-white/20 text-sm py-8">
				No round data yet.<br>
				<span class="text-[11px]">Start a simulation to see this agent's history.</span>
			</div>
		{:else}
			<div class="space-y-3">
				{#each results as result}
					<div class="glass-card p-3">
						<div class="flex items-center justify-between mb-2">
							<div class="flex items-center gap-2">
								<div
									class="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-surface"
									style="background: {stanceColor(result.stance_value)};"
								>
									{result.round_number}
								</div>
								<span class="text-xs text-white/50">Round {result.round_number}</span>
							</div>
							<span class="text-xs font-mono" style="color: {stanceColor(result.stance_value)}">
								{result.stance_value > 0 ? '+' : ''}{result.stance_value.toFixed(2)}
							</span>
						</div>
						<!-- Mini stance bar -->
						<div class="w-full h-0.5 rounded-full" style="background: rgba(255,255,255,0.06);">
							<div
								class="h-full rounded-full"
								style="width: {stancePct(result.stance_value)}%; background: {stanceColor(result.stance_value)};"
							></div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
