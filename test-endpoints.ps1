#!/usr/bin/env powershell

Write-Host "Testing WakeDock API endpoints through Caddy proxy..."
Write-Host ""

# Test 1: Health check
Write-Host "1. Testing health endpoint:"
try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)"
    Write-Host "   Content: $($response.Content)"
} catch {
    Write-Host "   Error: $($_.Exception.Message)"
}
Write-Host ""

# Test 2: API services endpoint
Write-Host "2. Testing /api/v1/services:"
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/v1/services" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)"
    Write-Host "   Content: $($response.Content)"
} catch {
    Write-Host "   Error: $($_.Exception.Message)"
}
Write-Host ""

# Test 3: API system overview endpoint
Write-Host "3. Testing /api/v1/system/overview:"
try {
    $response = Invoke-WebRequest -Uri "http://localhost/api/v1/system/overview" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)"
    Write-Host "   Content: $($response.Content)"
} catch {
    Write-Host "   Error: $($_.Exception.Message)"
}
Write-Host ""

# Test 4: Dashboard
Write-Host "4. Testing dashboard (should return HTML):"
try {
    $response = Invoke-WebRequest -Uri "http://localhost/" -UseBasicParsing
    Write-Host "   Status: $($response.StatusCode)"
    Write-Host "   Content-Type: $($response.Headers['Content-Type'])"
    if ($response.Content.Length -gt 100) {
        Write-Host "   Content preview: $($response.Content.Substring(0, 100))..."
    } else {
        Write-Host "   Content: $($response.Content)"
    }
} catch {
    Write-Host "   Error: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "Test complete."
