#!/usr/bin/env pwsh
# Script de nettoyage rapide WakeDock

Write-Host "Nettoyage rapide WakeDock" -ForegroundColor Blue

$PROJECT_ROOT = $PSScriptRoot | Split-Path -Parent
Set-Location $PROJECT_ROOT

Write-Host "Dossier du projet: $PROJECT_ROOT" -ForegroundColor Cyan

# Compter les elements avant nettoyage
$beforeSize = (Get-ChildItem -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Taille avant: $([math]::Round($beforeSize, 2)) MB" -ForegroundColor Yellow

# Nettoyer les caches Python
Write-Host "Nettoyage des caches Python..." -ForegroundColor Green
$pyCacheCount = 0
Get-ChildItem -Recurse -Name "__pycache__" -Directory -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
    $pyCacheCount++
}
Get-ChildItem -Recurse -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
    $pyCacheCount++
}
Write-Host "   - $pyCacheCount elements Python supprimes"

# Nettoyer les fichiers de build
Write-Host "Nettoyage des fichiers de build..." -ForegroundColor Green
$buildCount = 0
$buildPaths = @(".svelte-kit", "build", "dist", ".vite", ".pytest_cache", ".mypy_cache", ".tox", "htmlcov")
foreach ($path in $buildPaths) {
    Get-ChildItem -Recurse -Name $path -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path $_ -Recurse -Force -ErrorAction SilentlyContinue
        $buildCount++
    }
}
Write-Host "   - $buildCount dossiers de build supprimes"

# Nettoyer les fichiers temporaires
Write-Host "Nettoyage des fichiers temporaires..." -ForegroundColor Green
$tempCount = 0
$tempPatterns = @("*.tmp", "*.temp", "*.bak", ".coverage", "coverage.xml")
foreach ($pattern in $tempPatterns) {
    Get-ChildItem -Recurse -Include $pattern -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
        $tempCount++
    }
}
Write-Host "   - $tempCount fichiers temporaires supprimes"

# Nettoyer les anciens logs (> 7 jours)
Write-Host "Nettoyage des anciens logs..." -ForegroundColor Green
$logCount = 0
$cutoffDate = (Get-Date).AddDays(-7)
Get-ChildItem -Recurse -Include "*.log", "*.log.*" -ErrorAction SilentlyContinue | 
Where-Object { $_.LastWriteTime -lt $cutoffDate } | ForEach-Object {
    Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
    $logCount++
}
Write-Host "   - $logCount anciens logs supprimes"

# Taille apres nettoyage
$afterSize = (Get-ChildItem -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
$saved = $beforeSize - $afterSize
Write-Host "Taille apres: $([math]::Round($afterSize, 2)) MB" -ForegroundColor Yellow
Write-Host "Espace libere: $([math]::Round($saved, 2)) MB" -ForegroundColor Magenta

Write-Host "`nNettoyage termine!" -ForegroundColor Green
