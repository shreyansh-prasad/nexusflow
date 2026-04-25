# NexusFlow UI Redesign

## Files
- `index.html` — landing page
- `dashboard.html` — dashboard
- `config.js` — backend config

## Run locally
```bash
python3 -m http.server 3000
```
Then open:

- http://localhost:3000/index.html
- http://localhost:3000/dashboard.html

## Backend
Set `config.js`:

```js
window.NEXUSFLOW_BACKEND = 'http://localhost:8001';
```

If using Supabase:
```js
window.NEXUSFLOW_SUPABASE_URL = 'https://xxx.supabase.co';
window.NEXUSFLOW_SUPABASE_KEY = 'anon-key-here';
```

## Notes
The redesign keeps the dark blueprint look, truck-first visual language, orange accents, and vertical storytelling style.