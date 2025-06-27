# WakeDock Quick Deploy Guide 🐳

## For Git Clone Deployment (Dokploy, etc.)

### 1. Clone the repository
```bash
git clone https://github.com/your-repo/WakeDock.git
cd WakeDock
```

### 2. Initialize the environment (optional, but recommended)
```bash
# Make the init script executable (Linux/Mac)
chmod +x init.sh
./init.sh

# Or manually create directories
mkdir -p /Docker/config/wakedock/caddy-data
mkdir -p /Docker/config/wakedock/caddy-config
docker network create caddy_net
```

### 3. Deploy with Docker Compose
```bash
docker-compose up -d --build
```

## Key Features

- ✅ **Auto-Caddy Configuration**: WakeDock automatically creates and manages Caddyfile
- ✅ **Shared Volume**: Caddy and WakeDock share configuration via Docker volume
- ✅ **Default Fallback**: Starts with a basic Caddyfile that gets replaced
- ✅ **Auto-Reload**: Caddy automatically reloads when configuration changes
- ✅ **Health Checks**: All services have proper health monitoring

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│    WakeDock     │    │  Shared Volume   │    │      Caddy      │
│  (writes config)│───▶│ /etc/caddy/      │◀───│ (reads config)  │
│                 │    │  Caddyfile       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                                               │
         │              HTTP POST /load                  │
         └───────────────────────────────────────────────┘
                        (reload trigger)
```

## Troubleshooting

### Caddy Config Issues
- Check logs: `docker logs wakedock-caddy`
- Manual reload: `curl -X POST http://localhost:2019/load`
- Reset config: `docker restart wakedock-core`

### Store Subscribe Errors (Fixed)
- Fixed `Writable` import in `StatsCards.svelte`
- Fixed store binding in `+layout.svelte`
- Fixed store usage in `Sidebar.svelte` and `Header.svelte`

## API Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/system/caddy/reload` - Force Caddy reload
- `GET /api/v1/system/caddy/status` - Caddy status

## Default Ports

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:8000  
- **Caddy Admin**: http://localhost:2019
- **Caddy HTTP**: http://localhost:80
- **Caddy HTTPS**: http://localhost:443

Happy deploying! 🚀
