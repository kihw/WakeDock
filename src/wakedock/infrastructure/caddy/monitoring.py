"""
Caddy Health Monitor

Monitoring santé et métriques Caddy.
Extrait de la classe monolithique CaddyManager.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from .types import CaddyStatus, HealthStatus, CaddyMetrics, DiagnosticReport
from .api import CaddyApiClient

logger = logging.getLogger(__name__)


class CaddyHealthMonitor:
    """Monitoring de santé et métriques Caddy"""
    
    def __init__(self, api_client: CaddyApiClient):
        """Initialiser le monitor"""
        self.api = api_client
        self.health_history: List[HealthStatus] = []
        self.max_history = 100
        
        # Seuils d'alerte
        self.error_threshold = 5  # Nombre d'erreurs consécutives
        self.response_time_threshold = 5000  # 5 secondes
        
        # État interne
        self.consecutive_errors = 0
        self.last_check_time = None
    
    async def check_health(self) -> HealthStatus:
        """Vérification complète de santé"""
        start_time = datetime.now()
        
        try:
            # Récupérer le statut de base
            status = await self.api.get_status()
            
            # Ajouter des vérifications supplémentaires
            await self._enhance_health_status(status)
            
            # Mettre à jour l'historique
            self._update_health_history(status)
            
            # Réinitialiser le compteur d'erreurs si succès
            if status.status == CaddyStatus.HEALTHY:
                self.consecutive_errors = 0
            else:
                self.consecutive_errors += 1
            
            self.last_check_time = start_time
            
            logger.debug(f"Health check completed: {status.status.value}")
            return status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.consecutive_errors += 1
            
            # Créer un statut d'erreur
            error_status = HealthStatus(
                status=CaddyStatus.UNHEALTHY,
                version="unknown",
                uptime=0.0,
                active_routes=0,
                errors=[f"Health check exception: {str(e)}"],
                warnings=[]
            )
            
            self._update_health_history(error_status)
            return error_status
    
    async def _enhance_health_status(self, status: HealthStatus) -> None:
        """Enrichir le statut de santé avec des vérifications supplémentaires"""
        try:
            # Test de connectivité API
            if not await self.api.is_healthy():
                status.errors.append("API connectivity test failed")
                status.status = CaddyStatus.UNHEALTHY
            
            # Vérifier la cohérence de configuration
            config_issues = await self._check_config_issues()
            if config_issues:
                status.warnings.extend(config_issues)
            
            # Vérifier les métriques si disponibles
            metrics_warnings = await self._check_metrics_warnings()
            if metrics_warnings:
                status.warnings.extend(metrics_warnings)
                
        except Exception as e:
            status.warnings.append(f"Enhanced checks failed: {str(e)}")
    
    async def _check_config_issues(self) -> List[str]:
        """Vérifier les problèmes de configuration"""
        warnings = []
        
        try:
            config = await self.api.get_current_config()
            if config:
                # Vérifier la structure de base
                apps = config.get("apps", {})
                if "http" not in apps:
                    warnings.append("No HTTP app configured")
                
                # Vérifier les serveurs
                http_app = apps.get("http", {})
                servers = http_app.get("servers", {})
                if not servers:
                    warnings.append("No HTTP servers configured")
                
                # Vérifier les routes
                total_routes = 0
                for server in servers.values():
                    routes = server.get("routes", [])
                    total_routes += len(routes)
                
                if total_routes == 0:
                    warnings.append("No routes configured")
                    
        except Exception as e:
            warnings.append(f"Config check failed: {str(e)}")
        
        return warnings
    
    async def _check_metrics_warnings(self) -> List[str]:
        """Vérifier les avertissements basés sur les métriques"""
        warnings = []
        
        try:
            metrics = await self.get_metrics()
            
            # Vérifier le taux d'erreur
            if metrics.error_rate > 5.0:  # 5%
                warnings.append(f"High error rate: {metrics.error_rate:.1f}%")
            
            # Vérifier le temps de réponse
            if metrics.response_time_avg > 1000:  # 1 seconde
                warnings.append(f"High response time: {metrics.response_time_avg:.0f}ms")
            
            # Vérifier l'utilisation CPU/mémoire si disponible
            if metrics.cpu_usage > 80:
                warnings.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
            
            if metrics.memory_usage > 80:
                warnings.append(f"High memory usage: {metrics.memory_usage:.1f}%")
                
        except Exception as e:
            warnings.append(f"Metrics check failed: {str(e)}")
        
        return warnings
    
    def _update_health_history(self, status: HealthStatus) -> None:
        """Mettre à jour l'historique de santé"""
        self.health_history.append(status)
        
        # Maintenir la taille maximale
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
    
    async def get_metrics(self) -> CaddyMetrics:
        """Récupérer les métriques Caddy"""
        try:
            # Récupérer les métriques brutes
            raw_metrics = await self.api.get_metrics()
            
            # Récupérer le statut pour les routes actives
            status = await self.api.get_status()
            
            # Parser les métriques (format Prometheus si disponible)
            parsed_metrics = self._parse_raw_metrics(raw_metrics)
            
            return CaddyMetrics(
                active_routes=status.active_routes,
                requests_per_minute=parsed_metrics.get("requests_per_minute", 0.0),
                response_time_avg=parsed_metrics.get("response_time_avg", 0.0),
                error_rate=parsed_metrics.get("error_rate", 0.0),
                uptime_seconds=status.uptime,
                memory_usage=parsed_metrics.get("memory_usage", 0.0),
                cpu_usage=parsed_metrics.get("cpu_usage", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            # Retourner des métriques par défaut
            return CaddyMetrics(
                active_routes=0,
                requests_per_minute=0.0,
                response_time_avg=0.0,
                error_rate=0.0,
                uptime_seconds=0.0,
                memory_usage=0.0,
                cpu_usage=0.0
            )
    
    def _parse_raw_metrics(self, raw_metrics: Dict) -> Dict[str, float]:
        """Parser les métriques brutes"""
        parsed = {}
        
        try:
            # Si les métriques sont au format Prometheus
            if "raw_metrics" in raw_metrics:
                raw_text = raw_metrics["raw_metrics"]
                
                # Exemple de parsing simple (à adapter selon le format réel)
                lines = raw_text.split('\n')
                for line in lines:
                    if line.startswith('caddy_'):
                        # Format: metric_name value
                        parts = line.split()
                        if len(parts) >= 2:
                            metric_name = parts[0]
                            try:
                                value = float(parts[1])
                                
                                # Mapper vers nos métriques
                                if "request" in metric_name:
                                    parsed["requests_per_minute"] = value
                                elif "response_time" in metric_name:
                                    parsed["response_time_avg"] = value
                                elif "error" in metric_name:
                                    parsed["error_rate"] = value
                                    
                            except ValueError:
                                continue
                                
        except Exception as e:
            logger.error(f"Failed to parse metrics: {e}")
        
        return parsed
    
    async def diagnose_issues(self) -> DiagnosticReport:
        """Diagnostic complet des problèmes"""
        timestamp = datetime.now().isoformat()
        checks_passed = 0
        checks_total = 0
        issues = []
        recommendations = []
        
        try:
            # Test 1: Connectivité API
            checks_total += 1
            if await self.api.is_healthy():
                checks_passed += 1
            else:
                issues.append({
                    "type": "connectivity",
                    "severity": "high",
                    "description": "Cannot connect to Caddy admin API",
                    "suggestion": "Check if Caddy is running and admin port is accessible"
                })
            
            # Test 2: Configuration valide
            checks_total += 1
            config = await self.api.get_current_config()
            if config:
                checks_passed += 1
            else:
                issues.append({
                    "type": "configuration",
                    "severity": "high", 
                    "description": "Cannot retrieve current configuration",
                    "suggestion": "Check Caddy configuration file syntax"
                })
            
            # Test 3: Routes actives
            checks_total += 1
            status = await self.api.get_status()
            if status.active_routes > 0:
                checks_passed += 1
            else:
                issues.append({
                    "type": "routes",
                    "severity": "medium",
                    "description": "No active routes configured",
                    "suggestion": "Add service routes or check service configurations"
                })
            
            # Test 4: Historique d'erreurs
            checks_total += 1
            if self.consecutive_errors < self.error_threshold:
                checks_passed += 1
            else:
                issues.append({
                    "type": "stability",
                    "severity": "high",
                    "description": f"Too many consecutive errors ({self.consecutive_errors})",
                    "suggestion": "Check Caddy logs and restart if necessary"
                })
            
            # Test 5: Métriques de performance
            checks_total += 1
            try:
                metrics = await self.get_metrics()
                if metrics.error_rate < 5.0 and metrics.response_time_avg < 1000:
                    checks_passed += 1
                else:
                    issues.append({
                        "type": "performance",
                        "severity": "medium",
                        "description": f"Performance issues detected (error rate: {metrics.error_rate:.1f}%, response time: {metrics.response_time_avg:.0f}ms)",
                        "suggestion": "Monitor resource usage and optimize configuration"
                    })
            except:
                issues.append({
                    "type": "metrics",
                    "severity": "low",
                    "description": "Cannot retrieve performance metrics",
                    "suggestion": "Enable metrics collection if needed"
                })
            
            # Générer des recommandations
            if len(issues) == 0:
                recommendations.append("Caddy is running optimally")
            else:
                if any(issue["severity"] == "high" for issue in issues):
                    recommendations.append("Address high-severity issues immediately")
                
                if any(issue["type"] == "performance" for issue in issues):
                    recommendations.append("Monitor system resources and consider scaling")
                
                if any(issue["type"] == "configuration" for issue in issues):
                    recommendations.append("Review and validate Caddy configuration")
            
            # Déterminer le statut global
            if checks_passed == checks_total:
                overall_status = CaddyStatus.HEALTHY
            elif checks_passed >= checks_total * 0.7:  # 70% des tests passent
                overall_status = CaddyStatus.UNHEALTHY
            else:
                overall_status = CaddyStatus.UNKNOWN
            
            return DiagnosticReport(
                timestamp=timestamp,
                status=overall_status,
                checks_passed=checks_passed,
                checks_total=checks_total,
                issues=issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Diagnostic failed: {e}")
            return DiagnosticReport(
                timestamp=timestamp,
                status=CaddyStatus.UNKNOWN,
                checks_passed=0,
                checks_total=checks_total,
                issues=[{
                    "type": "diagnostic",
                    "severity": "high",
                    "description": f"Diagnostic process failed: {str(e)}",
                    "suggestion": "Check system logs and Caddy status manually"
                }],
                recommendations=["Manual investigation required"]
            )
    
    def get_health_trend(self, hours: int = 24) -> Dict:
        """Analyser la tendance de santé sur les dernières heures"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filtrer l'historique récent
        recent_history = [
            status for status in self.health_history 
            if hasattr(status, 'timestamp') and 
            datetime.fromisoformat(getattr(status, 'timestamp', datetime.now().isoformat())) > cutoff_time
        ]
        
        if not recent_history:
            return {
                "trend": "unknown",
                "healthy_percentage": 0.0,
                "total_checks": 0,
                "avg_errors": 0.0
            }
        
        # Calculer les statistiques
        healthy_count = sum(1 for status in recent_history if status.status == CaddyStatus.HEALTHY)
        total_checks = len(recent_history)
        healthy_percentage = (healthy_count / total_checks) * 100
        
        avg_errors = sum(len(status.errors) for status in recent_history) / total_checks
        
        # Déterminer la tendance
        if healthy_percentage >= 90:
            trend = "excellent"
        elif healthy_percentage >= 75:
            trend = "good"
        elif healthy_percentage >= 50:
            trend = "degraded"
        else:
            trend = "poor"
        
        return {
            "trend": trend,
            "healthy_percentage": healthy_percentage,
            "total_checks": total_checks,
            "avg_errors": avg_errors,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None
        }
    
    async def start_continuous_monitoring(self, interval: int = 30) -> None:
        """Démarrer le monitoring continu"""
        logger.info(f"Starting continuous Caddy monitoring (interval: {interval}s)")
        
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Continuous monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(interval)  # Continue monitoring même en cas d'erreur