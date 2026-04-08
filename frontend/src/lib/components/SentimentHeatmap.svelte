<script lang="ts">
    let { data = [] } = $props();


    // Helper to get color based on sentiment: Red (-1.0) -> Gray (0) -> Cyan (+1.0)
    function getColor(val: number) {
        if (val < 0) {
            // Smoothly transition from red (hsl 0) toward gray as val approach 0
            const opacity = Math.abs(val);
            return `rgba(255, 71, 71, ${opacity * 0.8})`; 
        } else if (val > 0) {
            // Smoothly transition from cyan (hsl 180) toward gray as val approach 0
            const opacity = Math.abs(val);
            return `rgba(0, 242, 254, ${opacity * 0.8})`;
        }
        return 'rgba(255,255,255,0.05)';
    }

    let roundNumbers = $derived(data.length > 0 ? Array.from({ length: data[0].values.length }, (_, i) => i + 1) : []);

</script>

<div class="overflow-x-auto">
    {#if data.length > 0}
        <table class="w-full text-left border-separate border-spacing-1">
            <thead>
                <tr>
                    <th class="px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-white/30 truncate max-w-[150px]">Archetype</th>
                    {#each roundNumbers as r}
                        <th class="text-center px-1 text-[9px] font-bold uppercase text-white/20 min-w-[30px]">R{r}</th>
                    {/each}
                </tr>
            </thead>
            <tbody>
                {#each data as row}
                    <tr>
                        <td class="px-3 py-2 text-[11px] font-semibold text-white/60 bg-white/5 rounded-l-md truncate max-w-[150px]" title={row.archetype}>
                            {row.archetype}
                        </td>
                        {#each row.values as val}
                            <td class="p-0">
                                <div 
                                    class="w-full h-8 flex items-center justify-center rounded-sm transition-all duration-500 hover:scale-110 hover:z-10 cursor-help"
                                    style="background: {getColor(val)}; border: 1px solid rgba(255,255,255,0.05);"
                                    title="Sentiment: {val.toFixed(2)}"
                                >
                                    {#if Math.abs(val) > 0.5}
                                        <span class="text-[8px] font-bold text-white/40">{val > 0 ? '+' : '-'}</span>
                                    {/if}
                                </div>
                            </td>
                        {/each}
                    </tr>
                {/each}
            </tbody>
        </table>
    {:else}
        <div class="py-12 text-center text-white/20 text-sm">
            No heatmap data available yet.
        </div>
    {/if}
</div>

<div class="mt-4 flex items-center justify-center gap-6 text-[10px] uppercase tracking-widest font-bold text-white/30">
    <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-sm" style="background: rgba(255, 71, 71, 0.8);"></div>
        Negative Stance
    </div>
    <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-sm" style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);"></div>
        Neutral
    </div>
    <div class="flex items-center gap-2">
        <div class="w-3 h-3 rounded-sm" style="background: rgba(0, 242, 254, 0.8);"></div>
        Positive Stance
    </div>
</div>
