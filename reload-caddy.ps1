#!/usr/bin/env powershell

Write-Host "Reloading Caddy configuration..."

# Method 1: API reload
Write-Host "Trying API reload..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:2019/config/reload" -Method POST -UseBasicParsing
    Write-Host "API reload successful: $($response.StatusCode)"
} catch {
    Write-Host "API reload failed: $($_.Exception.Message)"
}

# Method 2: Signal reload
Write-Host "Trying signal reload..."
try {
    docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile
    Write-Host "Signal reload completed"
} catch {
    Write-Host "Signal reload failed: $($_.Exception.Message)"
}

Write-Host "Done."
