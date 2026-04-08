<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import * as d3 from 'd3';

	export interface AgentNode extends d3.SimulationNodeDatum {
		id: number;
		name: string;
		archetype: string;
		current_stance: number;
		is_key_figure: boolean;
		influence_score: number;
		x?: number;
		y?: number;
	}

	export interface AgentLink extends d3.SimulationLinkDatum<AgentNode> {
		source: number | AgentNode;
		target: number | AgentNode;
		type: string;
		strength: number;
	}

	let { nodes = $bindable([]), links = $bindable([]), selectedAgentId = $bindable(null) }: {
		nodes: AgentNode[];
		links: AgentLink[];
		selectedAgentId: number | null;
	} = $props();

	let svgEl: SVGSVGElement;
	let simulation: d3.Simulation<AgentNode, AgentLink> | null = null;
	let nodePositions = $state<{ id: number; x: number; y: number }[]>([]);
	let linkPositions = $state<{ x1: number; y1: number; x2: number; y2: number; type: string; strength: number }[]>([]);
	
	const width = 700;
	const height = 500;

	// Stance → color scale: red (-1) → dark gray (0) → neon cyan (+1)
	const colorScale = d3.scaleLinear<string>()
		.domain([-1, 0, 1])
		.range(['#ff4d4d', '#3a3a4a', '#00f2fe'])
		.clamp(true);

	function getNodeColor(stance: number) {
		return colorScale(stance);
	}

	function startSimulation() {
		if (!nodes.length) return;

		// Normalize stances from 0-1 space to -1 to +1 if needed
		const nodesCopy = nodes.map(n => ({ ...n }));

		simulation = d3.forceSimulation<AgentNode>(nodesCopy)
			.force('link', d3.forceLink<AgentNode, AgentLink>(links as any)
				.id(d => d.id)
				.distance(80)
				.strength(d => (d as any).strength * 0.3 || 0.2)
			)
			.force('charge', d3.forceManyBody().strength(-120))
			.force('center', d3.forceCenter(width / 2, height / 2))
			.force('collision', d3.forceCollide().radius(d => (d as AgentNode).is_key_figure ? 20 : 12))
			.on('tick', () => {
				nodePositions = nodesCopy.map(n => ({ id: n.id!, x: n.x ?? 0, y: n.y ?? 0 }));
				linkPositions = (links as any[]).map(l => {
					const src = typeof l.source === 'object' ? l.source : { x: 0, y: 0 };
					const tgt = typeof l.target === 'object' ? l.target : { x: 0, y: 0 };
					return { x1: src.x ?? 0, y1: src.y ?? 0, x2: tgt.x ?? 0, y2: tgt.y ?? 0, type: l.type, strength: l.strength };
				});
			});
	}

	onMount(() => {
		startSimulation();
	});

	onDestroy(() => {
		simulation?.stop();
	});

	// Restart sim when nodes change significantly
	$effect(() => {
		if (nodes.length > 0 && !simulation) {
			startSimulation();
		}
	});

	function getNodePosition(id: number) {
		return nodePositions.find(p => p.id === id) ?? { x: width / 2, y: height / 2 };
	}

	function getLinkColor(type: string) {
		switch (type) {
			case 'opposes': return '#ff6b6b';
			case 'supports': return '#51cf66';
			case 'follows': return '#74c0fc';
			default: return '#ffffff';
		}
	}

	function handleNodeClick(nodeId: number) {
		selectedAgentId = selectedAgentId === nodeId ? null : nodeId;
	}
</script>

<div class="relative w-full" style="height: 500px;">
	<svg
		bind:this={svgEl}
		viewBox="0 0 {width} {height}"
		class="w-full h-full"
		style="background: transparent;"
	>
		<!-- Defs for glow filter -->
		<defs>
			<filter id="glow">
				<feGaussianBlur stdDeviation="3" result="blur" />
				<feMerge>
					<feMergeNode in="blur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
			<filter id="glow-strong">
				<feGaussianBlur stdDeviation="6" result="blur" />
				<feMerge>
					<feMergeNode in="blur" />
					<feMergeNode in="SourceGraphic" />
				</feMerge>
			</filter>
		</defs>

		<!-- Links -->
		{#each linkPositions as link, i}
			<line
				x1={link.x1} y1={link.y1}
				x2={link.x2} y2={link.y2}
				stroke={getLinkColor(link.type)}
				stroke-opacity={link.strength * 0.3}
				stroke-width={link.strength * 1.5}
			/>
		{/each}

		<!-- Nodes -->
		{#each nodes as node}
			{@const pos = getNodePosition(node.id)}
			{@const radius = node.is_key_figure ? 14 : 7}
			{@const color = getNodeColor(node.current_stance)}
			{@const isSelected = selectedAgentId === node.id}

			<!-- Key figure outer glow ring -->
			{#if node.is_key_figure}
				<circle
					cx={pos.x} cy={pos.y}
					r={radius + 6}
					fill="none"
					stroke={color}
					stroke-width="1.5"
					stroke-opacity="0.4"
					filter="url(#glow)"
				/>
			{/if}

			<!-- Selection ring -->
			{#if isSelected}
				<circle
					cx={pos.x} cy={pos.y}
					r={radius + 4}
					fill="none"
					stroke="white"
					stroke-width="2"
					stroke-dasharray="4 2"
				/>
			{/if}

			<!-- Main node circle -->
			<circle
				cx={pos.x} cy={pos.y}
				r={radius}
				fill={color}
				stroke={isSelected ? 'white' : 'rgba(255,255,255,0.2)'}
				stroke-width={isSelected ? 2 : 1}
				filter={node.is_key_figure ? 'url(#glow)' : 'none'}
				style="cursor: pointer; transition: fill 0.8s ease;"
				onclick={() => handleNodeClick(node.id)}
				role="button"
				tabindex="0"
				onkeydown={(e) => e.key === 'Enter' && handleNodeClick(node.id)}
			/>

			<!-- Key figure label -->
			{#if node.is_key_figure}
				<text
					x={pos.x} y={pos.y + radius + 14}
					text-anchor="middle"
					fill="rgba(255,255,255,0.7)"
					font-size="9"
					font-family="Inter, sans-serif"
				>
					{node.name.split(' ')[0]}
				</text>
			{/if}
		{/each}
	</svg>

	<!-- Legend -->
	<div class="absolute bottom-3 left-3 flex items-center gap-4 text-[10px] text-white/30">
		<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full inline-block" style="background:#ff4d4d"></span>Oppose</span>
		<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full inline-block" style="background:#3a3a4a; border:1px solid #666"></span>Neutral</span>
		<span class="flex items-center gap-1"><span class="w-2 h-2 rounded-full inline-block" style="background:#00f2fe"></span>Support</span>
		<span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full inline-block border-2" style="border-color:#00f2fe; background: transparent"></span>Key Figure</span>
	</div>
</div>
