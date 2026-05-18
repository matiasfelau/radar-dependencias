# Frontend - Dependency Radar Dashboard

React + TypeScript + Tailwind CSS application for managing dependency vulnerabilities.

## Stack

- **React 18** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Build tool (fast dev server, optimized builds)
- **Axios** - HTTP client
- **@tailwindcss/forms** - Pre-styled form elements

## Development Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Local Development

```bash
# Install dependencies
npm install

# Start development server (with hot-reload)
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Lint with ESLint (if configured)
npm run lint

# Format with Prettier (if configured)
npm run format
```

Development server runs at **http://localhost:5173** by default.

### Environment Variables

Create `.env.local`:

```
VITE_API_URL=http://localhost:8000/api/v1
```

Used to configure API client to point to backend.

## Project Structure

```
frontend/
├── src/
│   ├── App.tsx                 # Main component with tab navigation
│   ├── main.tsx                # Entry point (React 18)
│   ├── index.css               # Global Tailwind imports
│   │
│   ├── components/
│   │   ├── Inventory.tsx       # Project & dependency listing
│   │   ├── Alerts.tsx          # Vulnerability alerts display
│   │   └── Settings.tsx        # Configuration form
│   │
│   └── services/
│       ├── apiClient.ts        # Axios HTTP client
│       └── hooks.ts            # Custom React hooks (useProjects, useAlerts, useSettings)
│
├── index.html                  # HTML template
├── vite.config.ts              # Vite configuration (proxy to backend)
├── tsconfig.json               # TypeScript configuration
├── tailwind.config.js          # Tailwind CSS configuration
├── postcss.config.js           # PostCSS configuration
├── nginx.conf                  # Nginx config for production serving
├── package.json
└── .env.example                # Environment template

```

## Features

### Components

#### Inventory Tab
- Hierarchical view: Projects → Environments → Dependencies
- Displays last update timestamp
- Shows first 5 dependencies with "...and N more" truncation
- Real-time data refresh

#### Alerts Tab
- List of active vulnerabilities
- Color-coded severity badges (Critical, High, Medium, Low)
- Exploit intelligence indicator
- CVE links to external resources
- Sorted by exploit availability and detection date

#### Settings Tab
- Configure vulnerability scan interval (hours)
- Set webhook URL for notifications
- Save/load functionality with loading state
- Form validation

### API Integration

The frontend communicates with the backend via REST API:

```typescript
// Example: Get projects
GET /api/v1/projects

// Example: Get alerts
GET /api/v1/alerts/active

// Example: Get settings
GET /api/v1/settings

// Example: Update settings
PUT /api/v1/settings
```

See [../DEVOPS.md](../DEVOPS.md) for example API payloads.

## Styling

### Tailwind CSS

Tailwind is configured for content in:
- `./index.html`
- `./src/**/*.{js,ts,jsx,tsx}`

### Components

Key components use Tailwind utilities:

```tsx
// Badge with color variants
<span className="px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
  Critical
</span>

// Table styling
<table className="w-full border-collapse">
  <th className="border-b-2 border-gray-200 text-left py-2">
```

### Color Scheme

- **Critical**: red (bg-red-100, text-red-800)
- **High**: orange (bg-orange-100, text-orange-800)
- **Medium**: yellow (bg-yellow-100, text-yellow-800)
- **Low**: green (bg-green-100, text-green-800)
- **Unknown**: gray (bg-gray-100, text-gray-800)

## Build Optimization

### Vite Configuration

`vite.config.ts` includes:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

This allows `fetch('/api/v1/...')` in development to proxy to backend.

### Production Build

```bash
npm run build

# Output in dist/
# - Minified JavaScript
# - Tree-shaken CSS
# - Optimized images
# - Hash-based caching
```

Produced files are ready for static hosting (nginx, S3, Netlify, etc).

## Docker

### Development Image

```bash
docker-compose -f docker-compose.dev.yml up frontend

# Or standalone
docker build -f Dockerfile.dev -t radar-frontend-dev .
docker run -p 5173:5173 -v $(pwd):/app radar-frontend-dev npm run dev
```

Includes hot-reload via volume mount.

### Production Image

```bash
docker build -f Dockerfile -t radar-frontend .
docker run -p 80:5173 radar-frontend
```

Multi-stage build:
1. **Build stage**: Node 18 Alpine, runs `npm ci && npm run build`
2. **Serve stage**: Node 18 Alpine, runs `serve -s dist -l 5173`

## Common Tasks

### Add a New Page

1. Create component: `src/components/NewPage.tsx`
2. Add to App.tsx tabs:
   ```tsx
   <button onClick={() => setActiveTab('newpage')}>New Page</button>
   {activeTab === 'newpage' && <NewPage />}
   ```

### Fetch from Backend

Use the apiClient:

```typescript
import { apiClient } from './services/apiClient';

const data = await apiClient.getProjects();
```

Or create custom hook:

```typescript
const useMyData = () => {
  const [data, setData] = useState(null);
  
  useEffect(() => {
    apiClient.myEndpoint().then(setData);
  }, []);
  
  return data;
};
```

### Add Styling

Global styles in `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom components */
@layer components {
  .badge {
    @apply px-3 py-1 rounded-full text-sm font-medium;
  }
}
```

Component-level styling via Tailwind classes:

```tsx
<div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
```

## Performance Tips

### Code Splitting

Vite automatically chunks code. For manual splitting:

```typescript
const HeavyComponent = React.lazy(() => import('./HeavyComponent'));
```

### Image Optimization

Place images in `src/assets/` and Vite will optimize:

```typescript
import logo from './assets/logo.svg';
<img src={logo} />
```

### API Caching

React hooks cache data in state. For persistent caching:

```typescript
// Use localStorage
const [cache, setCache] = useState(() => {
  return JSON.parse(localStorage.getItem('projects') || '[]');
});
```

## Debugging

### Browser DevTools

- **React DevTools**: [Firefox](https://addons.mozilla.org/en-US/firefox/addon/react-devtools/) / [Chrome](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi)
- **Axios Interceptor**: Log requests/responses in console

### Vite Debug

```bash
# Verbose logs
npm run dev -- --debug

# Inspect bundle
npm run build -- --debug

# Profile build
npm run build -- --profile
```

### Common Issues

**Blank page**
- Check browser console for errors
- Verify backend is running: `curl http://localhost:8000/api/v1/health`
- Check VITE_API_URL environment variable

**Hot-reload not working**
- Ensure file changes are saved
- Restart dev server: `npm run dev`
- Clear browser cache (Ctrl+Shift+Delete)

**Styles not loading**
- Run `npm install` to ensure Tailwind is installed
- Check `tailwind.config.js` includes all content paths
- Rebuild: `npm run build`

## Deployment

### Static Hosting (Netlify, Vercel, GitHub Pages)

1. Build: `npm run build`
2. Deploy `dist/` folder
3. Set environment variables:
   ```
   VITE_API_URL=https://api.example.com/api/v1
   ```

### Docker

```bash
docker build -t radar-frontend .
docker run -p 80:5173 radar-frontend
```

### Docker Compose

```bash
docker-compose up frontend
```

### Behind Reverse Proxy (nginx)

Use `frontend/nginx.conf`:

```nginx
location / {
    root /app/dist;
    try_files $uri $uri/ /index.html;
}

location /api/ {
    proxy_pass http://backend:8000;
}
```

## Testing

To add tests (optional):

```bash
npm install -D vitest @testing-library/react

# Create test file: src/App.test.tsx
npm run test
```

## Resources

- [React Docs](https://react.dev)
- [Vite Docs](https://vitejs.dev)
- [Tailwind Docs](https://tailwindcss.com)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Axios Docs](https://axios-http.com)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ENOENT` errors | Run `npm install` |
| Port 5173 in use | `npm run dev -- --port 5174` |
| Backend not found | Check `VITE_API_URL` and backend status |
| Styles not applying | Clear cache: `npm run build && rm -rf dist` |
| Module not found | Check import paths (relative vs @/) |
| Build fails | Run `npm install --save-peer-deps` |

## Contributing

1. Create feature branch
2. Make changes in `src/`
3. Test locally: `npm run dev`
4. Build: `npm run build`
5. Submit PR

For issues, see [../README.md](../README.md#Contributing).
