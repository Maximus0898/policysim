<script lang="ts">
	import { env } from '$env/dynamic/public';
	import ForceGraph from '$lib/components/ForceGraph.svelte';
	import AgentPanel from '$lib/components/AgentPanel.svelte';
	import SentimentHeatmap from '$lib/components/SentimentHeatmap.svelte';
	import BacktestReport from '$lib/components/BacktestReport.svelte';
	import CoalitionExplorer from '$lib/components/CoalitionExplorer.svelte';
	import { Upload, Download, FileText } from 'lucide-svelte';



	import type { AgentNode, AgentLink } from '$lib/components/ForceGraph.svelte';

	// --- Types ---
	interface RoundUpdate {
		type: 'round_update' | 'completion' | 'error';
		round_number?: number;
		synthesis?: string;
		injected_event?: string;
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

	// Network graph & Reporting state
	let activeTab = $state<'log' | 'graph' | 'report'>('log');

	let graphNodes = $state<AgentNode[]>([]);
	let graphLinks = $state<AgentLink[]>([]);
	let selectedAgentId = $state<number | null>(null);
	let injectionText = $state('');
	let isInjecting = $state(false);

	let heatmapData = $state<{ archetype: string, values: number[] }[]>([]);
	let briefSummary = $state<string | null>(null);
	let isGeneratingReport = $state(false);
	interface BacktestAnalysis {
		total_score: number;
		outcome_score: number;
		trajectory_score: number;
		outcome_details: any[];
		trajectory_details: any[];
		divergence_log: string[];
		historical_data: any[];
	}

	interface Coalition {
		label: string;
		avg_stance: number;
		members: {name: string; archetype: string}[];
		size: number;
	}

	let backtestAnalysis = $state<BacktestAnalysis | null>(null);
	let isBacktest = $state(false);
	let coalitions = $state<Coalition[]>([]);
	let isIngesting = $state(false);





	const API_URL = env.PUBLIC_API_URL || 'http://localhost:8000';

	// --- Actions ---
	async function handleLaunchBacktest(scenarioId: string) {
		phase = 'drafting';
		error = null;
		isBacktest = true;
		try {
			const res = await fetch(`${API_URL}/api/simulations/backtest/${scenarioId}`, { method: 'POST' });
			if (!res.ok) throw new Error('Failed to launch backtest');
			const data = await res.json();
			simId = data.simulation_id;
			await handleStartSimulation();
		} catch (e: any) {
			error = e.message;
			phase = 'error';
		}
	}

	async function handleIngestFile(e: Event) {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		isIngesting = true;
		error = null;
		const formData = new FormData();
		formData.append('file', file);

		try {
			const res = await fetch(`${API_URL}/api/simulations/ingest`, {
				method: 'POST',
				body: formData
			});
			if (!res.ok) throw new Error('Failed to parse document');
			const data = await res.json();
			policyText = data.text;
			if (!title) title = data.filename.split('.')[0];
		} catch (e: any) {
			error = e.message;
		} finally {
			isIngesting = false;
		}
	}

	function handleDownloadJSON() {
		if (!simId) return;
		window.open(`${API_URL}/api/simulations/${simId}/export`, '_blank');
	}

	async function handleCreateSimulation() {

		phase = 'drafting';
		error = null;
		isBacktest = false;

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
					if (data.type === 'completion' && isBacktest) {
						fetchBacktestResults();
					}
				}

			} catch (e) {
				console.error('SSE parse error:', e);
			}
		};

		sse.onerror = () => {
			if (isStreaming) {
				console.log("SSE error, attempting to reconnect...");
				sse.close();
				setTimeout(() => connectToStream(), 2000);
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

	async function handleInjectEvent() {
		if (!simId || !injectionText.trim()) return;
		isInjecting = true;

		try {
			const res = await fetch(`${API_URL}/api/simulations/${simId}/inject`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ event_text: injectionText })
			});
			if (res.ok) {
				injectionText = '';
			} else {
				throw new Error('Injection failed');
			}
		} catch (e: any) {
			alert(e.message);
		} finally {
			isInjecting = false;
		}
	}

	async function handleGenerateBrief() {
		if (!simId) return;
		isGeneratingReport = true;
		try {
			const res = await fetch(`${API_URL}/api/simulations/${simId}/report/summary`, { method: 'POST' });
			if (res.ok) {
				const data = await res.json();
				briefSummary = data.summary;
			}
		} catch (e) {
			console.error(e);
		} finally {
			isGeneratingReport = false;
		}
	}

	async function fetchBacktestResults() {
		if (!simId) return;
		try {
			const res = await fetch(`${API_URL}/api/simulations/${simId}/backtest`);
			if (res.ok) {
				backtestAnalysis = await res.json();
			}
		} catch (e) {
			console.error(e);
		}
	}

	async function fetchReportData() {
		if (!simId) return;
		if (isBacktest && !backtestAnalysis) fetchBacktestResults();
		try {
			const [heatRes, coalRes] = await Promise.all([
				fetch(`${API_URL}/api/simulations/${simId}/report/heatmap`),
				fetch(`${API_URL}/api/simulations/${simId}/report/coalitions`)
			]);
			if (heatRes.ok) heatmapData = await heatRes.json();
			if (coalRes.ok) coalitions = await coalRes.json();
		} catch (e) {
			console.error(e);
		}
	}

	function handleDownloadPDF() {
		if (!simId) return;
		window.open(`${API_URL}/api/simulations/${simId}/report/pdf`, '_blank');
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
		isBacktest = false;
		backtestAnalysis = null;
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

	<!-- Backtest Scenario Discovery -->
	<div class="mt-12 flex justify-center gap-4">
		<button 
			onclick={() => handleLaunchBacktest('kazakhstan_2022')}
			class="glass text-left p-4 rounded-2xl border border-white/5 hover:border-brand/30 hover:bg-brand/5 transition-all group max-w-[300px]"
		>
			<div class="flex items-center justify-between mb-2">
				<span class="text-xs font-bold uppercase tracking-widest text-[#51cf66]">Model Calibration</span>
				<span class="text-lg group-hover:translate-x-1 transition-transform">→</span>
			</div>
			<p class="text-sm font-semibold mb-1">Bloody January 2022</p>
			<p class="text-[11px] text-white/40 leading-relaxed">Backtest the engine against the fuel price removal crisis in Kazakhstan.</p>
		</button>
	</div>
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
						style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); outline: none; min-height: 200px; resize: none;"
					></textarea>
				</div>

				<div class="flex items-center gap-3">
					<label class="flex-1 cursor-pointer">
						<div class="w-full flex items-center justify-center gap-2 py-3 border border-white/10 hover:border-brand/30 rounded-xl bg-white/5 transition-all">
							<Upload size={14} class={isIngesting ? 'animate-bounce' : ''} />
							<span class="text-[11px] font-bold uppercase tracking-widest">{isIngesting ? 'Reading...' : 'Upload PDF/DOCX'}</span>
						</div>
						<input type="file" class="hidden" accept=".pdf,.docx,.txt" onchange={handleIngestFile} disabled={phase !== 'idle' || isIngesting} />
					</label>
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

				<!-- God-Mode Intervention -->
				<div class="mt-8 pt-8 space-y-4" style="border-top: 1px solid rgba(255,255,255,0.05);">
					<div class="flex items-center gap-2 mb-2">
						<span class="text-lg">🕹️</span>
						<h3 class="text-xs font-bold uppercase tracking-widest" style="color: #00f2fe;">God-Mode: Intervene</h3>
					</div>
					<p class="text-[11px]" style="color: rgba(255,255,255,0.4);">Inject a global event to steer the simulation narrative. Queues for the next round.</p>
					
					<textarea
						bind:value={injectionText}
						placeholder="E.g. The opposition leader calls for a general strike..."
						rows={3}
						class="w-full rounded-xl px-4 py-3 text-sm text-white resize-none transition-all"
						style="background: rgba(0,242,254,0.03); border: 1px solid rgba(0,242,254,0.15); outline: none;"
					></textarea>
					
					<button 
						onclick={handleInjectEvent}
						disabled={isInjecting || !injectionText.trim()}
						class="w-full py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest transition-all {injectionText.trim() ? 'bg-brand text-black' : 'opacity-30'}"
						style="background: {injectionText.trim() ? '#00f2fe' : 'rgba(255,255,255,0.1)'}; color: {injectionText.trim() ? '#000' : 'white'};"
					>
						{isInjecting ? 'Processing...' : '⚡ Fire Event'}
					</button>
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
					onclick={() => { activeTab = 'report'; fetchReportData(); }}
					class="flex-1 py-2 text-xs font-semibold rounded-lg transition-all"
					style="background: {activeTab === 'report' ? 'rgba(81, 207, 102, 0.1)' : 'transparent'}; color: {activeTab === 'report' ? '#51cf66' : 'rgba(255,255,255,0.4)'};"
				>
					📊 Prediction Report
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
									<div class="flex items-center gap-2">
										{#if log.injected_event}
											<span class="text-xs px-2 py-0.5 rounded bg-brand/10 border border-brand/20 text-brand" title="User Intervention: {log.injected_event}" style="color: #00f2fe;">🕹️ Intervention</span>
										{/if}
										<span class="text-[10px]" style="color: rgba(255,255,255,0.2);">✓ committed</span>
									</div>
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
		{:else if activeTab === 'report'}

			<div class="space-y-6">
				<!-- Historical Comparison (If Backtest) -->
				{#if isBacktest}
					<div class="glass-card p-6 border-brand/20">
						<div class="flex items-center gap-2 mb-8">
							<span class="text-xl">⚖️</span>
							<h3 class="text-xs font-bold uppercase tracking-widest text-brand">Historical Calibration Audit</h3>
						</div>
						<BacktestReport analysis={backtestAnalysis} />
					</div>
				{/if}

				<!-- Executive Brief Section -->
				<div class="glass-card p-6">
					<div class="flex items-center justify-between mb-6">
						<div class="flex items-center gap-2">
							<span class="text-xl">📄</span>
							<h3 class="text-xs font-bold uppercase tracking-widest text-brand">Institutional Prediction Report</h3>
						</div>
						<div class="flex items-center gap-2">
							<button 
								onclick={handleDownloadJSON}
								class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 hover:border-white/20 transition-all text-[10px] font-bold uppercase tracking-widest opacity-60 hover:opacity-100"
							>
								<Download size={12} /> JSON
							</button>
							<button 
								onclick={handleDownloadPDF}
								class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-brand/10 border border-brand/20 hover:bg-brand/20 transition-all text-[10px] font-bold uppercase tracking-widest text-brand"
							>
								<Download size={12} /> PDF Report
							</button>
						</div>
					</div>
					
					{#if briefSummary}
						<div class="prose prose-invert prose-sm max-w-none text-white/50 leading-relaxed italic text-[13px]">
							{briefSummary}
						</div>
					{:else}
						<button 
							onclick={handleGenerateBrief}
							disabled={isGeneratingReport}
							class="w-full py-12 border-2 border-dashed border-white/5 rounded-2xl hover:border-brand/20 hover:bg-brand/5 transition-all text-sm text-white/20"
						>
							{isGeneratingReport ? 'Synthesizing executive brief...' : 'Click to Generate Executive Summary'}
						</button>
					{/if}

				</div>

				<!-- Coalition Explorer (New v1.0 Polish) -->
				<div class="glass-card p-6">
					<CoalitionExplorer {coalitions} />
				</div>

				<!-- Demographic Heatmap Section -->
				<div class="glass-card p-6">
					<div class="flex items-center gap-2 mb-8">
						<span class="text-xl">🔥</span>
						<h3 class="text-xs font-bold uppercase tracking-widest text-white/40">Demographic Sentiment Trajectory</h3>
					</div>
					
					<SentimentHeatmap data={heatmapData} />
				</div>

				<!-- Key Figures Spotlight -->
				<div class="glass-card p-6">
					<div class="flex items-center gap-2 mb-6">
						<span class="text-xl">🌟</span>
						<h3 class="text-xs font-bold uppercase tracking-widest text-white/40">Key Figure Final Stances</h3>
					</div>
					
					<div class="grid grid-cols-2 md:grid-cols-3 gap-4">
						{#each graphNodes.filter(n => n.is_key_figure) as figure}
							<div class="p-4 rounded-xl border border-white/5" style="background: rgba(255,255,255,0.02);">
								<p class="text-xs font-bold text-white mb-1">{figure.name}</p>
								<p class="text-[10px] text-white/30 uppercase mb-3">{figure.archetype}</p>
								<div class="flex items-center gap-2">
									<div class="flex-1 h-1.5 rounded-full overflow-hidden bg-white/5">
										<div class="h-full" style="width: {((figure.current_stance + 1) / 2) * 100}%; background: {figure.current_stance < 0 ? '#ff4747' : '#00f2fe'};"></div>
									</div>
									<span class="text-[10px] font-mono {figure.current_stance < 0 ? 'text-[#ff4747]' : 'text-[#00f2fe]'}">
										{(figure.current_stance * 100).toFixed(0)}%
									</span>
								</div>
							</div>
						{/each}
					</div>
				</div>
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
