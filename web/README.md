# SIGNLENS web app

React 19 + TypeScript + Tailwind CSS v4 + d3 + motion, built with Vite.

```bash
npm install
npm run dev     # http://localhost:5173, proxies /api to http://127.0.0.1:8000 (run `signlens serve`)
npm run build   # outputs dist/, which `signlens serve` serves at /
```

Pages: `/` (animated explainer), `/congress`, `/polarization`, `/individual`, `/temporal`, `/data`, `/methods`.
UI text is bilingual (EN / 中文, toggle in the nav bar); API data labels are localised in `src/lib/i18n.tsx`.
