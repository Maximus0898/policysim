# Phase 8: Frontend Dashboard - Research

## SvelteKit Initialization
- The goal is to separate the SvelteKit frontend and the FastAPI backend.
- We will initialize the frontend in `frontend/` using `npx sv create frontend --template minimal`.
- Dependencies needed: `tailwindcss@next` for V4 utility engine, `lucide-svelte` for icons, and `@tailwindcss/vite` plugin.
- A robust `.env` pattern will link `PUBLIC_API_URL` to `http://localhost:8000`.

## Svelte 5 Stores and SSE API
- Svelte 5 standardizes reactivity via Runes (`$state()`).
- Data connection to the FastAPI `text/event-stream`:
  - Standard `EventSource` web API is ideal.
  - `const sse = new EventSource('/api/simulations/{id}/stream')`.
  - Listen to `sse.onmessage` and append the results into a Svelte `$state` list of round logs.

## Premium Styling Architecture
The prompt demands a stunning application. 
- Avoid raw HTML primitives where a custom component shines.
- **Glassmorphism**: Use `bg-white/10 backdrop-blur-md` heavily with contrasting neon accents for the tech theme.
- **Micro-animations**: Use Tailwind `transition-all duration-300`, and layout shifts bounded by `hover:` triggers.

---
*Status: Complete*
