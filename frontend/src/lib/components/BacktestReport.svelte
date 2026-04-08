<script lang="ts">
    import { onMount } from 'svelte';
    import * as d3 from 'd3';

    let { analysis = null } = $props();

    let chartContainer: HTMLElement;

    // Accuracy Gauge Logic
    const score = $derived(analysis?.total_score || 0);
    const dashArray = $derived((score / 100) * 283); // 283 is approx circumference of circle r=45

    onMount(() => {
        if (analysis && analysis.historical_data) {
            drawChart();
        }
    });

    function drawChart() {
        if (!chartContainer || !analysis) return;

        const margin = { top: 20, right: 30, bottom: 30, left: 40 };
        const width = chartContainer.clientWidth - margin.left - margin.right;
        const height = 250 - margin.top - margin.bottom;

        // Clear previous
        d3.select(chartContainer).selectAll('*').remove();

        const svg = d3.select(chartContainer)
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Prepare data
        const histData = analysis.historical_data.map(d => ({ round: d.round, sentiment: d.sentiment }));
        const simData = analysis.trajectory_details.map(d => ({ round: d.round, sentiment: d.sim }));

        const x = d3.scaleLinear()
            .domain([1, Math.max(d3.max(histData, d => d.round), d3.max(simData, d => d.round))])
            .range([0, width]);

        const y = d3.scaleLinear()
            .domain([-1, 1])
            .range([height, 0]);

        // Axes
        svg.append('g')
            .attr('transform', `translate(0,${height / 2})`)
            .call(d3.axisBottom(x).ticks(5).tickSize(0).tickFormat(() => ''))
            .attr('color', 'rgba(255,255,255,0.1)');

        svg.append('g')
            .call(d3.axisLeft(y).ticks(5))
            .attr('color', 'rgba(255,255,255,0.1)')
            .selectAll('text')
            .style('fill', 'rgba(255,255,255,0.3)')
            .style('font-size', '10px');

        // Line generator
        const line = d3.line()
            .x(d => x(d.round))
            .y(d => y(d.sentiment))
            .curve(d3.curveMonotoneX);

        // Historical Line (Dashed)
        svg.append('path')
            .datum(histData)
            .attr('fill', 'none')
            .attr('stroke', 'rgba(255,255,255,0.4)')
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', '5,5')
            .attr('d', line);

        // Simulated Line (Solid Cyan)
        svg.append('path')
            .datum(simData)
            .attr('fill', 'none')
            .attr('stroke', '#00f2fe')
            .attr('stroke-width', 3)
            .attr('d', line);

        // Points
        svg.selectAll('.dot-hist')
            .data(histData)
            .enter()
            .append('circle')
            .attr('cx', d => x(d.round))
            .attr('cy', d => y(d.sentiment))
            .attr('r', 4)
            .attr('fill', 'rgba(255,255,255,0.2)');

        svg.selectAll('.dot-sim')
            .data(simData)
            .enter()
            .append('circle')
            .attr('cx', d => x(d.round))
            .attr('cy', d => y(d.sentiment))
            .attr('r', 4)
            .attr('fill', '#00f2fe');
    }

    let activeAuditIndex = $state<number | null>(null);
</script>

<div class="space-y-8">
    {#if !analysis}
        <div class="py-20 text-center animate-pulse">
            <p class="text-sm text-white/20">Running historical calibration...</p>
        </div>
    {:else}
        <!-- Top Stats: Gauge + Scores -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass-card p-6 flex flex-col items-center justify-center text-center">
                <div class="relative w-32 h-32 mb-4">
                    <svg class="w-full h-full transform -rotate-90">
                        <circle cx="64" cy="64" r="45" stroke="rgba(255,255,255,0.05)" stroke-width="8" fill="transparent" />
                        <circle 
                            cx="64" cy="64" r="45" 
                            stroke={score > 80 ? '#51cf66' : score > 50 ? '#fcc419' : '#ff6b6b'} 
                            stroke-width="8" 
                            fill="transparent" 
                            stroke-dasharray="283" 
                            stroke-dashoffset={283 - dashArray}
                            class="transition-all duration-1000 ease-out"
                        />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                        <span class="text-2xl font-display font-bold">{score}%</span>
                        <span class="text-[8px] uppercase tracking-widest text-white/30">Accuracy</span>
                    </div>
                </div>
                <p class="text-xs font-bold uppercase tracking-widest text-white/40">Model Confidence</p>
            </div>

            <div class="md:col-span-2 glass-card p-6">
                <div class="flex items-center justify-between mb-6">
                    <h3 class="text-xs font-bold uppercase tracking-widest text-white/40">Evaluation Rubric</h3>
                    <span class="text-[10px] text-white/20 italic">Outcome (70%) + Trajectory (30%)</span>
                </div>
                <div class="space-y-4">
                    {#each analysis.outcome_details as criterion, i}
                        <div class="border border-white/5 rounded-xl overflow-hidden bg-white/5">
                            <button 
                                onclick={() => activeAuditIndex = activeAuditIndex === i ? null : i}
                                class="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/5 transition-all"
                            >
                                <div class="flex items-center gap-3">
                                    <div class="w-2 h-2 rounded-full" style="background: {criterion.score > 70 ? '#51cf66' : '#ff6b6b'}"></div>
                                    <span class="text-[11px] font-bold text-white/80">{criterion.label}</span>
                                </div>
                                <div class="flex items-center gap-3">
                                    <span class="text-xs font-mono text-white/50">{criterion.score}%</span>
                                    <span class="text-xs transition-transform {activeAuditIndex === i ? 'rotate-180' : ''}">↓</span>
                                </div>
                            </button>
                            {#if activeAuditIndex === i}
                                <div class="px-4 pb-4 pt-2 text-[11px] leading-relaxed text-white/40 border-t border-white/5 italic">
                                    {criterion.reasoning}
                                </div>
                            {/if}
                        </div>
                    {/each}
                </div>
            </div>
        </div>

        <!-- Trajectory Chart -->
        <div class="glass-card p-6">
            <div class="flex items-center justify-between mb-8">
                <div class="flex items-center gap-2">
                    <span class="text-xl">📈</span>
                    <h3 class="text-xs font-bold uppercase tracking-widest text-white/40">Sentiment Trajectory Alignment</h3>
                </div>
                <div class="flex items-center gap-4 text-[9px] uppercase font-bold tracking-widest">
                    <div class="flex items-center gap-2 text-white/40">
                        <span class="w-3 h-0.5 border-t-2 border-dashed border-white/40"></span> History
                    </div>
                    <div class="flex items-center gap-2 text-[#00f2fe]">
                        <span class="w-3 h-0.5 bg-[#00f2fe]"></span> Simulation
                    </div>
                </div>
            </div>
            <div bind:this={chartContainer} class="w-full"></div>
        </div>

        <!-- Divergence Log -->
        {#if analysis.divergence_log && analysis.divergence_log.length > 0}
            <div class="glass-card p-6 border-l-4 border-amber-500/30">
                <div class="flex items-center gap-2 mb-4">
                    <span class="text-lg">⚠️</span>
                    <h3 class="text-xs font-bold uppercase tracking-widest text-amber-500/80">Model Calibration Signals (Divergence)</h3>
                </div>
                <div class="space-y-2">
                    {#each analysis.divergence_log as log}
                        <p class="text-[11px] text-white/60 font-mono leading-relaxed">→ {log}</p>
                    {/each}
                </div>
                <p class="mt-4 text-[10px] italic text-white/30">Divergence points identify potential blind spots in regional archetype weights or protest thresholds.</p>
            </div>
        {/if}
    {/if}
</div>
