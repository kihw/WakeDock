#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script de nettoyage WakeDock pour Windows
.DESCRIPTION
    Nettoie automatiquement les fichiers temporaires et inutiles du projet WakeDock
.PARAMETER Auto
    Exécute le nettoyage sans confirmation interactive
.EXAMPLE
    .\cleanup-windows.ps1
.EXAMPLE
    .\cleanup-windows.ps1 -Auto
#>

param(
    [switch]$Auto = $false
)

# Configuration
$PROJECT_ROOT = Split-Path -Parent $PSScriptRoot
$LOG_FILE = Join-Path $PROJECT_ROOT "logs\cleanup.log"
$BACKUP_RETENTION_DAYS = 30
$LOG_RETENTION_DAYS = 7

# Créer le dossier de logs s'il n'existe pas
$LogDir = Split-Path -Parent $LOG_FILE
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Fonction de logging
function Write-Log {
    param(
        [string]$Level,
        [string]$Message
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "$timestamp [$Level] $Message"
    Write-Output $logEntry | Tee-Object -FilePath $LOG_FILE -Append
}

# Fonction pour afficher un en-tête
function Write-Header {
    param([string]$Title)
    Write-Host "`n=== $Title ===" -ForegroundColor Blue
}

# Fonction pour confirmer une action
function Confirm-Action {
    param([string]$Message)
    if ($Auto) {
        return $true
    }
    $response = Read-Host "$Message (o/N)"
    return $response -match "^[oO]$"
}

# Fonction pour afficher l'utilisation du disque
function Show-DiskUsage {
    param([string]$Label)
    Write-Header "Utilisation du disque ($Label)"
    $size = (Get-ChildItem -Path $PROJECT_ROOT -Recurse -ErrorAction SilentlyContinue | 
             Measure-Object -Property Length -Sum).Sum
    $sizeMB = [math]::Round($size / 1MB, 2)
    Write-Host "Taille du projet: $sizeMB MB"
}

# Fonction pour nettoyer les dossiers __pycache__
function Clean-PythonCache {
    Write-Header "Nettoyage des caches Python"
    
    $cacheCount = 0
    Get-ChildItem -Path $PROJECT_ROOT -Recurse -Name "__pycache__" -Directory -ErrorAction SilentlyContinue | 
    ForEach-Object {
        $fullPath = Join-Path $PROJECT_ROOT $_
        Write-Host "Suppression: $_" -ForegroundColor Yellow
        Remove-Item -Path $fullPath -Recurse -Force -ErrorAction SilentlyContinue
        $cacheCount++
    }
    
    # Supprimer les fichiers .pyc et .pyo
    $pycCount = 0
    Get-ChildItem -Path $PROJECT_ROOT -Recurse -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue | 
    ForEach-Object {
        Write-Host "Suppression: $($_.Name)" -ForegroundColor Yellow
        Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
        $pycCount++
    }
    
    Write-Log "INFO" "Nettoyé $cacheCount dossiers __pycache__ et $pycCount fichiers .pyc/.pyo"
    Write-Host "✓ Nettoyage Python terminé" -ForegroundColor Green
}

# Fonction pour nettoyer les fichiers de build du dashboard
function Clean-DashboardBuild {
    Write-Header "Nettoyage des fichiers de build du dashboard"
    
    $dashboardPath = Join-Path $PROJECT_ROOT "dashboard"
    if (-not (Test-Path $dashboardPath)) {
        Write-Host "⚠ Dossier dashboard non trouvé" -ForegroundColor Yellow
        return
    }
    
    Push-Location $dashboardPath
    try {
        $cleanPaths = @(".svelte-kit", "build", "dist", ".vite")
        
        foreach ($path in $cleanPaths) {
            if (Test-Path $path) {
                Write-Host "Suppression: $path" -ForegroundColor Yellow
                Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
        
        Write-Log "INFO" "Nettoyé les fichiers de build du dashboard"
        Write-Host "✓ Nettoyage dashboard terminé" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
}

# Fonction pour nettoyer les anciens logs
function Clean-OldLogs {
    Write-Header "Nettoyage des anciens logs"
    
    $logDirs = @(
        (Join-Path $PROJECT_ROOT "logs"),
        (Join-Path $PROJECT_ROOT "data\logs"),
        (Join-Path $PROJECT_ROOT "dashboard\logs")
    )
    
    $cutoffDate = (Get-Date).AddDays(-$LOG_RETENTION_DAYS)
    $cleanedCount = 0
    
    foreach ($logDir in $logDirs) {
        if (Test-Path $logDir) {
            Write-Host "Nettoyage des logs dans: $logDir"
            Get-ChildItem -Path $logDir -Include "*.log*" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -lt $cutoffDate } |
            ForEach-Object {
                Write-Host "Suppression: $($_.Name)" -ForegroundColor Yellow
                Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
                $cleanedCount++
            }
        }
    }
    
    Write-Log "INFO" "Nettoyé $cleanedCount anciens fichiers de log"
    Write-Host "✓ Nettoyage des logs terminé" -ForegroundColor Green
}

# Fonction pour nettoyer les anciennes sauvegardes
function Clean-OldBackups {
    Write-Header "Nettoyage des anciennes sauvegardes"
    
    $backupDirs = @(
        (Join-Path $PROJECT_ROOT "backup"),
        (Join-Path $PROJECT_ROOT "backups"),
        (Join-Path $PROJECT_ROOT "data\backups")
    )
    
    $cutoffDate = (Get-Date).AddDays(-$BACKUP_RETENTION_DAYS)
    $cleanedCount = 0
    
    foreach ($backupDir in $backupDirs) {
        if (Test-Path $backupDir) {
            Write-Host "Nettoyage des sauvegardes dans: $backupDir"
            Get-ChildItem -Path $backupDir -Include "*.tar.gz", "*.sql", "backup-*" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -lt $cutoffDate } |
            ForEach-Object {
                Write-Host "Suppression: $($_.Name)" -ForegroundColor Yellow
                if ($_.PSIsContainer) {
                    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                } else {
                    Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
                }
                $cleanedCount++
            }
        }
    }
    
    Write-Log "INFO" "Nettoyé $cleanedCount anciennes sauvegardes"
    Write-Host "✓ Nettoyage des sauvegardes terminé" -ForegroundColor Green
}

# Fonction pour nettoyer les fichiers temporaires
function Clean-TempFiles {
    Write-Header "Nettoyage des fichiers temporaires"
    
    $tempPatterns = @(
        "tmp\*",
        ".tmp\*",
        "*.tmp",
        ".pytest_cache",
        ".coverage",
        "coverage.xml",
        "htmlcov",
        ".tox",
        ".mypy_cache"
    )
    
    $cleanedCount = 0
    foreach ($pattern in $tempPatterns) {
        Get-ChildItem -Path $PROJECT_ROOT -Include $pattern -Recurse -Force -ErrorAction SilentlyContinue |
        ForEach-Object {
            Write-Host "Suppression: $($_.Name)" -ForegroundColor Yellow
            if ($_.PSIsContainer) {
                Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            } else {
                Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
            }
            $cleanedCount++
        }
    }
    
    Write-Log "INFO" "Nettoyé $cleanedCount fichiers temporaires"
    Write-Host "✓ Nettoyage des fichiers temporaires terminé" -ForegroundColor Green
}

# Fonction pour nettoyer l'environnement virtuel Python
function Clean-VirtualEnv {
    Write-Header "Nettoyage de l'environnement virtuel Python"
    
    if (Confirm-Action "Supprimer l'environnement virtuel Python (.venv)?") {
        $venvPath = Join-Path $PROJECT_ROOT ".venv"
        if (Test-Path $venvPath) {
            Write-Host "Suppression: .venv" -ForegroundColor Yellow
            Remove-Item -Path $venvPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "INFO" "Environnement virtuel Python supprimé"
            Write-Host "✓ Environnement virtuel supprimé" -ForegroundColor Green
        } else {
            Write-Host "⚠ Environnement virtuel non trouvé" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ Nettoyage de l'environnement virtuel annulé" -ForegroundColor Yellow
    }
}

# Fonction pour nettoyer node_modules
function Clean-NodeModules {
    Write-Header "Nettoyage des node_modules"
    
    if (Confirm-Action "Supprimer node_modules du dashboard?") {
        $nodeModulesPath = Join-Path $PROJECT_ROOT "dashboard\node_modules"
        if (Test-Path $nodeModulesPath) {
            Write-Host "Suppression: dashboard/node_modules" -ForegroundColor Yellow
            Remove-Item -Path $nodeModulesPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "INFO" "node_modules supprimé"
            Write-Host "✓ node_modules supprimé" -ForegroundColor Green
        } else {
            Write-Host "⚠ node_modules non trouvé" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ Nettoyage de node_modules annulé" -ForegroundColor Yellow
    }
}

# Fonction pour afficher le résumé
function Show-Summary {
    Write-Header "Résumé du nettoyage"
    
    Write-Host "Opérations de nettoyage terminées:"
    Write-Host "- Caches Python (__pycache__, *.pyc, *.pyo)"
    Write-Host "- Fichiers de build du dashboard"
    Write-Host "- Anciens logs (> $LOG_RETENTION_DAYS jours)"
    Write-Host "- Anciennes sauvegardes (> $BACKUP_RETENTION_DAYS jours)"
    Write-Host "- Fichiers temporaires"
    Write-Host "- Environnement virtuel (si confirmé)"
    Write-Host "- node_modules (si confirmé)"
    
    Write-Host "`n✓ Toutes les opérations de nettoyage sont terminées" -ForegroundColor Green
    Write-Log "INFO" "Script de nettoyage terminé avec succès"
}

# Fonction principale
function Main {
    Write-Host "Script de nettoyage WakeDock pour Windows" -ForegroundColor Blue
    Write-Host "Ce script va nettoyer les fichiers temporaires et inutiles." -ForegroundColor Cyan
    Write-Host ""
    
    # Afficher l'utilisation du disque avant
    Show-DiskUsage "Avant nettoyage"
    
    # Démarrer le logging
    Write-Log "INFO" "Démarrage du script de nettoyage"
    
    # Exécuter les opérations de nettoyage
    Clean-PythonCache
    Clean-DashboardBuild
    Clean-OldLogs
    Clean-OldBackups
    Clean-TempFiles
    
    # Opérations optionnelles nécessitant confirmation
    if (-not $Auto) {
        Clean-VirtualEnv
        Clean-NodeModules
    } else {
        Write-Host "`n⚠ Mode automatique activé, opérations interactives ignorées" -ForegroundColor Yellow
    }
    
    # Afficher l'utilisation du disque après
    Show-DiskUsage "Après nettoyage"
    
    # Afficher le résumé
    Show-Summary
}

# Gestion des erreurs
try {
    Main
}
catch {
    Write-Error "Erreur lors du nettoyage: $_"
    Write-Log "ERROR" "Erreur lors du nettoyage: $_"
    exit 1
}
