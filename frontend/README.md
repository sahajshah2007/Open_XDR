# TwinTrace Lab interface

React/TypeScript interface for an educational cyber defense simulation project.
Includes Lab overview, Investigations, Lab assets, Evidence explorer, seeded
experiments, A/B run comparison and saved detection configurations, Flow studio,
Twin & response, a six-chapter Interview guide, Project notebook, and Lab settings. Stored dataset totals are displayed as lab
observations, not detection-accuracy or containment claims.

```sh
npm ci
npm run dev
npm run lint
npm run build
```

The development server proxies `/api` and WebSockets to localhost:8000. Set
`VITE_API_URL` only when the API is hosted at a different origin. The Docker build
serves static assets through Nginx and proxies the same paths to the backend.
See the [project README](../README.md) for credentials, services, and digital twin
configuration. Real response actions are not implemented; the defense view clearly
records simulations.
