<script lang="ts">
	import './layout.css';
	import { Activity, LayoutDashboard, Database, Info } from 'lucide-svelte';

	let { children } = $props();
</script>

<div class="flex flex-col min-h-screen">
	<!-- Top Navigation -->
	<header class="sticky top-0 z-50 glass border-b border-white/5 py-4 px-8 flex items-center justify-between">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 bg-brand rounded-xl flex items-center justify-center shadow-[0_0_15px_rgba(0,242,254,0.3)]">
				<Activity size={24} class="text-surface" />
			</div>
			<div>
				<h1 class="text-xl font-display font-bold tracking-tight">PolicySim</h1>
				<p class="text-[10px] text-brand uppercase tracking-[0.2em] font-bold">Predictive Engine</p>
			</div>
		</div>
		
		<nav class="flex items-center gap-8">
			<a href="/" class="text-sm font-medium text-white hover:text-brand transition-colors flex items-center gap-2">
				<LayoutDashboard size={16} />
				Dashboard
			</a>
		</nav>

		<div class="flex items-center gap-4">
			<div class="px-3 py-1 rounded-full bg-brand/10 border border-brand/20 text-[10px] text-brand font-bold uppercase tracking-wider">
				V1.0 Stable
			</div>
		</div>
	</header>

	<!-- Main Content Area -->
	<main class="flex-grow p-8 max-w-[1600px] mx-auto w-full">
		{@render children()}
	</main>

	<!-- Footer -->
	<footer class="py-8 px-8 border-t border-white/5 text-center text-white/20 text-[11px] tracking-widest uppercase">
		PolicySim &copy; 2026 &bull; Advanced Agentic Simulation Systems
	</footer>
</div>
