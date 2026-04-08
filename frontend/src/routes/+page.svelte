<script lang="ts">
	import { env } from '$env/dynamic/public';
	import ForceGraph from '$lib/components/ForceGraph.svelte';
	import AgentPanel from '$lib/components/AgentPanel.svelte';
	import type { AgentNode, AgentLink } from '$lib/components/ForceGraph.svelte';

	// --- Types ---
	interface RoundUpdate {
		type: 'round_update' | 'completion' | 'error';
		round_number?: number;
		synthesis?: string;
		message?: string;
		error?: string;
	}

	interface SynthesisData {
		narrative_summary: string;
		key_events?: string[];
	}

	// --- State ---
	let title = $state('Urban Transport Tax 2026');
	let policyText = $state(`This bill proposes a progressive carbon tax on urban transport, phased in over 18 months.
Key provisions:
1. Petrol vehicles pay 15% fuel surcharge
2. Diesel vehicles banned in city centers by Q3
3. Subsidies for EVs and public transport passes
4. Revenue invested in metro expansion`);
	let regionPreset = $state('uz');
	let rounds = $state(5);

	let phase = $state<'idle' | 'drafting' | 'streaming' | 'done' | 'error'>('idle');
	let simId = $state<number | null>(null);
	let error = $state<string | null>(null);
	let roundLogs = $state<RoundUpdate[]>([]);
	let isStreaming = $state(false);

	// Network graph state
	let activeTab = $state<'log' | 'graph'>('log');
	let graphNodes = $state<AgentNode[]>([]);
	let graphLinks = $state<AgentLink[]>([]);
	let selectedAgentId = $state<number | null>(null);

	const API_URL = env.PUBLIC_API_URL || 'http://localhost:8000';

	// --- Actions ---
	async function handleCreateSimulation() {
		phase = 'drafting';
		error = null;
		roundLogs = [];
		graphNodes = [];
		graphLinks = [];
		selectedAgentId = null;

		try {
			const res = await fetch(`${API_URL}/api/simulations/`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					title,
					policy_document_text: policyText,
					region_preset: regionPreset
				})
			});

			if (!res.ok) {
				const text = await res.text();
				throw new Error(`Draft failed: ${text}`);
			}

			const data = await res.json();
			simId = data.simulation_id;

			await handleStartSimulation();
		} catch (e: any) {
			error = e.message;
			phase = 'error';
		}
	}

	async function handleStartSimulation() {
		if (!simId) return;

		try {
			// Fetch agents and relationships for the graph
			const [agentsRes, relsRes] = await Promise.all([
				fetch(`${API_URL}/api/simulations/${simId}/agents`),
				fetch(`${API_URL}/api/simulations/${simId}/relationships`)
			]);
			
			if (agentsRes.ok) {
				const agentsData = await agentsRes.json();
				graphNodes = agentsData as AgentNode[];
			}
			if (relsRes.ok) {
				const relsData = await relsRes.json();
				graphLinks = relsData.map((r: any) => ({
					source: r.source,
					target: r.target,
					type: r.type,
					strength: r.strength
				})) as AgentLink[];
			}

			const res = await fetch(`${API_URL}/api/simulations/${simId}/start`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ rounds })
			});

			if (!res.ok) throw new Error(`Start failed: ${await res.text()}`);

			phase = 'streaming';
			isStreaming = true;
			connectToStream();
		} catch (e: any) {
			error = e.message;
			phase = 'error';
		}
	}

	function connectToStream() {
		if (!simId) return;

		const sse = new EventSource(`${API_URL}/api/simulations/${simId}/stream`);

		sse.onmessage = (event) => {
			try {
				const data = JSON.parse(event.data) as RoundUpdate;
				roundLogs = [...roundLogs, data];

				// On round update, re-fetch updated agent stances for the graph
				if (data.type === 'round_update' && simId) {
					fetch(`${API_URL}/api/simulations/${simId}/agents`)
						.then(r => r.json())
						.then(agents => { graphNodes = agents as AgentNode[]; })
						.catch(() => {});
				}

				if (data.type === 'completion' || data.type === 'error') {
					phase = data.type === 'completion' ? 'done' : 'error';
					isStreaming = false;
					sse.close();
				}
			} catch (e) {
				console.error('SSE parse error:', e);
			}
		};

		sse.onerror = () => {
			if (isStreaming) {
				error = 'Stream connection lost.';
				phase = 'error';
				isStreaming = false;
				sse.close();
			}
		};
	}

	function parseSynthesis(raw: string | undefined): SynthesisData | null {
		if (!raw) return null;
		try {
			return JSON.parse(raw) as SynthesisData;
		} catch {
			return { narrative_summary: raw };
		}
	}

	function resetAll() {
		phase = 'idle';
		simId = null;
		error = null;
		roundLogs = [];
		isStreaming = false;
		graphNodes = [];
		graphLinks = [];
		selectedAgentId = null;
	}

	const regionOptions = [
		{ value: 'uz', label: '🇺🇿 Uzbekistan' },
		{ value: 'kz', label: '🇰🇿 Kazakhstan' },
		{ value: 'ge', label: '🇬🇪 Georgia' },
		{ value: 'us', label: '🇺🇸 United States' },
	];
</script>

<svelte:head>
	<title>PolicySim — Predictive Policy Engine</title>
	<meta name="description" content="AI-powered policy impact simulation platform. Predict public sentiment and protest risk before your policy goes live." />
</svelte:head>

<!-- Hero Header -->
{#if phase === 'idle'}
<section class="text-center py-16 mb-8">
	<div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border border-brand/20 text-[11px] font-bold uppercase tracking-[0.2em] mb-6" style="color: #00f2fe; border-color: rgba(0,242,254,0.2);">
		<span class="w-1.5 h-1.5 rounded-full animate-pulse" style="background:#00f2fe;"></span>
		AI Simulation Engine v1.0
	</div>
	<h1 class="text-6xl font-display font-bold tracking-tight mb-4" style="background: linear-gradient(to right, white, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
		Predict Policy Impact
	</h1>
	<p class="text-lg max-w-xl mx-auto leading-relaxed" style="color: rgba(255,255,255,0.5);">
		Simulate how 40 demographically-diverse agents respond to your policy across multiple rounds of social interaction.
	</p>
</section>
{/if}

<!-- Main Interface -->
<div class="grid grid-cols-1 xl:grid-cols-5 gap-8 items-start">

	<!-- LEFT: Policy Input Panel -->
	<div class="xl:col-span-2">
		<div class="glass-card p-6">
			<h2 class="text-sm font-bold uppercase tracking-widest mb-6" style="color: rgba(255,255,255,0.4);">Policy Brief</h2>

			<div class="space-y-5">
				<div>
					<label for="sim-title" class="block text-xs font-semibold uppercase tracking-wider mb-2" style="color: rgba(255,255,255,0.5);">
						Simulation Title
					</label>
					<input
						id="sim-title"
						type="text"
						bind:value={title}
						disabled={phase !== 'idle'}
						placeholder="E.g. Carbon Tax Bill 2026"
						class="w-full rounded-xl px-4 py-3 text-sm text-white transition-all"
						style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); outline: none;"
					/>
				</div>

				<div>
					<label for="policy-text" class="block text-xs font-semibold uppercase tracking-wider mb-2" style="color: rgba(255,255,255,0.5);">
						Policy Document
					</label>
					<textarea
						id="policy-text"
						bind:value={policyText}
						disabled={phase !== 'idle'}
						rows={10}
						placeholder="Paste your policy document here..."
						class="w-full rounded-xl px-4 py-3 text-sm text-white resize-none font-mono transition-all"
						style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); outline: none;"
					></textarea>
				</div>

				<div class="grid grid-cols-2 gap-4">
					<div>
						<label for="region-select" class="block text-xs font-semibold uppercase tracking-wider mb-2" style="color: rgba(255,255,255,0.5);">
							Region
						</label>
						<select
							id="region-select"
							bind:value={regionPreset}
							disabled={phase !== 'idle'}
							class="w-full rounded-xl px-4 py-3 text-sm text-white transition-all cursor-pointer"
							style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); outline: none;"
						>
							{#each regionOptions as opt}
								<option value={opt.value} style="background: #0a0a0a;">{opt.label}</option>
							{/each}
						</select>
					</div>

					<div>
						<label for="rounds-input" class="block text-xs font-semibold uppercase tracking-wider mb-2" style="color: rgba(255,255,255,0.5);">
							Simulation Rounds
						</label>
						<input
							id="rounds-input"
							type="number"
							bind:value={rounds}
							min={1} max={25}
							disabled={phase !== 'idle'}
							class="w-full rounded-xl px-4 py-3 text-sm text-white transition-all"
							style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); outline: none;"
						/>
					</div>
				</div>

				{#if phase === 'idle'}
					<button id="run-simulation-btn" onclick={handleCreateSimulation} class="btn-primary w-full mt-2">
						🚀 Launch Simulation
					</button>
				{:else if phase === 'drafting'}
					<div class="w-full py-3 text-center text-sm animate-pulse" style="color: #00f2fe;">
						⚙️ Building world model...
					</div>
				{:else if phase === 'done' || phase === 'error'}
					<button id="reset-btn" onclick={resetAll} class="w-full py-3 text-sm rounded-xl transition-all" style="color: rgba(255,255,255,0.4); border: 1px solid rgba(255,255,255,0.1);">
						↺ Run Another Simulation
					</button>
				{/if}
			</div>

			{#if simId}
				<div class="mt-5 pt-5 text-xs font-mono" style="border-top: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.3);">
					sim_id: <span style="color: #00f2fe;">{simId}</span>
					{#if graphNodes.length > 0}
						&bull; <span>{graphNodes.length} agents</span>
						&bull; <span>{graphLinks.length} links</span>
					{/if}
				</div>
			{/if}

			{#if error}
				<div class="mt-4 p-4 rounded-xl text-sm" style="background: rgba(255,77,77,0.1); border: 1px solid rgba(255,77,77,0.2); color: #ff6b6b;">
					⚠️ {error}
				</div>
			{/if}
		</div>
	</div>

	<!-- RIGHT: Live Output Panel -->
	<div class="xl:col-span-3 space-y-4">
		<!-- Status Banner -->
		<div class="glass-card p-4 flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="w-8 h-8 rounded-lg flex items-center justify-center" style="background: rgba(255,255,255,0.05);">
					<span class="text-base">
						{phase === 'idle' ? '⏳' : phase === 'drafting' ? '🧬' : phase === 'streaming' ? '📡' : phase === 'done' ? '✅' : '❌'}
					</span>
				</div>
				<div>
					<p class="text-sm font-semibold">
						{phase === 'idle' ? 'Awaiting Input' : phase === 'drafting' ? 'Building Agent World...' : phase === 'streaming' ? `Running · Round ${roundLogs.filter(r => r.type === 'round_update').length} of ${rounds}` : phase === 'done' ? 'Simulation Complete' : 'Simulation Error'}
					</p>
					<p class="text-xs" style="color: rgba(255,255,255,0.3);">
						{phase === 'idle' ? 'Define your policy and launch.' : phase === 'streaming' ? 'Receiving live round updates...' : ''}
					</p>
				</div>
			</div>
			{#if phase === 'streaming'}
				<div class="flex gap-1">
					{#each [0,1,2] as i}
						<div class="w-1.5 h-1.5 rounded-full animate-bounce" style="background:#00f2fe; animation-delay: {i * 0.15}s;"></div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Tab Toggle (shown after simulation starts) -->
		{#if simId !== null}
			<div class="flex gap-1 p-1 rounded-xl" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);">
				<button
					onclick={() => activeTab = 'log'}
					class="flex-1 py-2 text-xs font-semibold rounded-lg transition-all"
					style="background: {activeTab === 'log' ? 'rgba(255,255,255,0.1)' : 'transparent'}; color: {activeTab === 'log' ? 'white' : 'rgba(255,255,255,0.4)'};"
				>
					📋 Round Log
				</button>
				<button
					onclick={() => activeTab = 'graph'}
					class="flex-1 py-2 text-xs font-semibold rounded-lg transition-all"
					style="background: {activeTab === 'graph' ? 'rgba(0,242,254,0.1)' : 'transparent'}; color: {activeTab === 'graph' ? '#00f2fe' : 'rgba(255,255,255,0.4)'};"
				>
					🕸️ Agent Network
				</button>
			</div>
		{/if}

		<!-- Round Log Tab -->
		{#if activeTab === 'log'}
			{#if roundLogs.length > 0}
				<div class="space-y-3">
					{#each roundLogs as log, i (i)}
						{@const synth = log.round_number ? parseSynthesis(log.synthesis) : null}
						<div class="glass-card p-5" style="animation: fadeSlideIn 0.3s ease-out forwards; animation-delay: {i * 0.05}s; opacity: 0;">
							{#if log.type === 'round_update' && synth}
								<div class="flex items-start justify-between mb-3">
									<div class="flex items-center gap-3">
										<div class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold" style="background: rgba(0,242,254,0.15); border: 1px solid rgba(0,242,254,0.3); color: #00f2fe;">
											{log.round_number}
										</div>
										<span class="text-xs font-bold uppercase tracking-widest" style="color: rgba(255,255,255,0.4);">Round {log.round_number}</span>
									</div>
									<span class="text-[10px]" style="color: rgba(255,255,255,0.2);">✓ committed</span>
								</div>
								<p class="text-sm leading-relaxed mb-3" style="color: rgba(255,255,255,0.8);">{synth.narrative_summary}</p>
								{#if synth.key_events && synth.key_events.length > 0}
									<div class="flex flex-wrap gap-2">
										{#each synth.key_events as event}
											<span class="px-2 py-0.5 rounded-md text-[10px]" style="background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.4); border: 1px solid rgba(255,255,255,0.06);">{event}</span>
										{/each}
									</div>
								{/if}
							{:else if log.type === 'completion'}
								<div class="flex items-center gap-3">
									<span class="text-lg" style="color: #51cf66;">✓</span>
									<p class="text-sm font-medium" style="color: #51cf66;">{log.message || 'Simulation complete.'}</p>
								</div>
							{:else if log.type === 'error'}
								<p class="text-sm" style="color: #ff6b6b;">⚠️ {log.error}</p>
							{/if}
						</div>
					{/each}
				</div>
			{:else if phase === 'idle' || phase === 'drafting'}
				<div class="glass-card p-16 text-center">
					<div class="w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.05);">
						<span class="text-4xl">🎯</span>
					</div>
					<h3 class="text-lg font-display font-semibold mb-2" style="color: rgba(255,255,255,0.7);">Ready to Simulate</h3>
					<p class="text-sm max-w-xs mx-auto" style="color: rgba(255,255,255,0.3);">
						Fill in your policy details and launch a simulation to watch live agent responses unfold here.
					</p>
				</div>
			{/if}

		<!-- Agent Network Tab -->
		{:else if activeTab === 'graph'}
			<div class="glass-card p-4">
				{#if graphNodes.length > 0}
					<div class="flex items-center justify-between mb-4">
						<p class="text-xs uppercase tracking-widest font-semibold" style="color: rgba(255,255,255,0.4);">
							Live Influence Network
						</p>
						<span class="text-[10px] px-2 py-1 rounded-full" style="background: rgba(0,242,254,0.1); color: #00f2fe; border: 1px solid rgba(0,242,254,0.2);">
							{graphNodes.length} agents · {graphLinks.length} links
						</span>
					</div>
					<ForceGraph nodes={graphNodes} links={graphLinks} bind:selectedAgentId />
				{:else}
					<div class="py-16 text-center">
						<span class="text-4xl">🕸️</span>
						<p class="mt-4 text-sm" style="color: rgba(255,255,255,0.3);">Network graph will load after simulation starts.</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<!-- Agent Detail Panel (overlay) -->
{#if simId}
	<AgentPanel agentId={selectedAgentId} simulationId={simId} />
{/if}

<style>
	@keyframes fadeSlideIn {
		from { opacity: 0; transform: translateY(8px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
