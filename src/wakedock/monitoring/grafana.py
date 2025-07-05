"""
Grafana Dashboard Integration

Provides Grafana dashboard provisioning and management:
- Dashboard JSON generation
- Automated dashboard deployment
- Template management
- Data source configuration
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import yaml

logger = logging.getLogger(__name__)


@dataclass
class Panel:
    """Grafana dashboard panel configuration"""
    id: int
    title: str
    type: str
    targets: List[Dict[str, Any]]
    gridPos: Dict[str, int]
    options: Dict[str, Any] = None
    fieldConfig: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert panel to Grafana JSON format"""
        panel = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "targets": self.targets,
            "gridPos": self.gridPos
        }
        
        if self.options:
            panel["options"] = self.options
        if self.fieldConfig:
            panel["fieldConfig"] = self.fieldConfig
            
        return panel


@dataclass
class Dashboard:
    """Grafana dashboard configuration"""
    title: str
    uid: str
    tags: List[str]
    panels: List[Panel]
    time_from: str = "now-1h"
    time_to: str = "now"
    refresh: str = "5s"
    editable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert dashboard to Grafana JSON format"""
        return {
            "dashboard": {
                "id": None,
                "uid": self.uid,
                "title": self.title,
                "tags": self.tags,
                "timezone": "browser",
                "panels": [panel.to_dict() for panel in self.panels],
                "time": {
                    "from": self.time_from,
                    "to": self.time_to
                },
                "timepicker": {},
                "templating": {"list": []},
                "annotations": {"list": []},
                "refresh": self.refresh,
                "schemaVersion": 30,
                "version": 0,
                "links": [],
                "editable": self.editable
            },
            "overwrite": True
        }


class GrafanaDashboard:
    """Grafana dashboard generator"""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        
    def create_system_dashboard(self) -> Dashboard:
        """Create system monitoring dashboard"""
        panels = [
            # CPU Usage Panel
            Panel(
                id=1,
                title="System CPU Usage",
                type="stat",
                targets=[{
                    "expr": "wakedock_system_cpu_usage_percent",
                    "refId": "A"
                }],
                gridPos={"h": 8, "w": 6, "x": 0, "y": 0},
                options={
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto"
                },
                fieldConfig={
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 70},
                                {"color": "red", "value": 90}
                            ]
                        },
                        "unit": "percent"
                    }
                }
            ),
            
            # Memory Usage Panel
            Panel(
                id=2,
                title="System Memory Usage",
                type="stat",
                targets=[{
                    "expr": "wakedock_system_memory_usage_percent",
                    "refId": "A"
                }],
                gridPos={"h": 8, "w": 6, "x": 6, "y": 0},
                options={
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto"
                },
                fieldConfig={
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 80},
                                {"color": "red", "value": 95}
                            ]
                        },
                        "unit": "percent"
                    }
                }
            ),
            
            # Docker Containers Panel
            Panel(
                id=3,
                title="Docker Containers",
                type="stat",
                targets=[{
                    "expr": "sum(wakedock_docker_containers_total)",
                    "refId": "A"
                }],
                gridPos={"h": 8, "w": 6, "x": 12, "y": 0},
                options={
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "none",
                    "justifyMode": "auto"
                }
            ),
            
            # API Requests Panel
            Panel(
                id=4,
                title="API Requests Rate",
                type="stat",
                targets=[{
                    "expr": "rate(wakedock_api_requests_total[5m])",
                    "refId": "A"
                }],
                gridPos={"h": 8, "w": 6, "x": 18, "y": 0},
                options={
                    "reduceOptions": {
                        "values": False,
                        "calcs": ["lastNotNull"],
                        "fields": ""
                    },
                    "orientation": "auto",
                    "textMode": "auto",
                    "colorMode": "value",
                    "graphMode": "area",
                    "justifyMode": "auto"
                },
                fieldConfig={
                    "defaults": {
                        "unit": "reqps"
                    }
                }
            ),
            
            # CPU Usage Timeline
            Panel(
                id=5,
                title="CPU Usage Over Time",
                type="timeseries",
                targets=[{
                    "expr": "wakedock_system_cpu_usage_percent",
                    "refId": "A",
                    "legendFormat": "CPU Usage"
                }],
                gridPos={"h": 8, "w": 12, "x": 0, "y": 8},
                fieldConfig={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {
                                "legend": False,
                                "tooltip": False,
                                "vis": False
                            },
                            "lineInterpolation": "linear",
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "max": 100,
                        "min": 0,
                        "unit": "percent"
                    }
                }
            ),
            
            # Memory Usage Timeline
            Panel(
                id=6,
                title="Memory Usage Over Time",
                type="timeseries",
                targets=[{
                    "expr": "wakedock_system_memory_usage_percent",
                    "refId": "A",
                    "legendFormat": "Memory Usage"
                }],
                gridPos={"h": 8, "w": 12, "x": 12, "y": 8},
                fieldConfig={
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {
                            "axisLabel": "",
                            "axisPlacement": "auto",
                            "barAlignment": 0,
                            "drawStyle": "line",
                            "fillOpacity": 10,
                            "gradientMode": "none",
                            "hideFrom": {
                                "legend": False,
                                "tooltip": False,
                                "vis": False
                            },
                            "lineInterpolation": "linear",
                            "lineWidth": 1,
                            "pointSize": 5,
                            "scaleDistribution": {"type": "linear"},
                            "showPoints": "never",
                            "spanNulls": False,
                            "stacking": {"group": "A", "mode": "none"},
                            "thresholdsStyle": {"mode": "off"}
                        },
                        "mappings": [],
                        "max": 100,
                        "min": 0,
                        "unit": "percent"
                    }
                }
            )
        ]
        
        return Dashboard(
            title="WakeDock System Monitoring",
            uid="wakedock-system",
            tags=["wakedock", "system", "monitoring"],
            panels=panels
        )
    
    def create_services_dashboard(self) -> Dashboard:
        """Create services monitoring dashboard"""
        panels = [
            # Running Services
            Panel(
                id=1,
                title="Running Services",
                type="stat",
                targets=[{
                    "expr": "count(wakedock_service_status == 1)",
                    "refId": "A"
                }],
                gridPos={"h": 6, "w": 4, "x": 0, "y": 0}
            ),
            
            # Service Status Table
            Panel(
                id=2,
                title="Service Status",
                type="table",
                targets=[{
                    "expr": "wakedock_service_status",
                    "refId": "A",
                    "format": "table",
                    "instant": True
                }],
                gridPos={"h": 10, "w": 20, "x": 4, "y": 0},
                options={
                    "showHeader": True
                },
                fieldConfig={
                    "defaults": {
                        "custom": {
                            "align": "auto",
                            "displayMode": "auto"
                        },
                        "mappings": [
                            {
                                "options": {
                                    "0": {"text": "Stopped", "color": "red"},
                                    "1": {"text": "Running", "color": "green"}
                                },
                                "type": "value"
                            }
                        ]
                    }
                }
            ),
            
            # Service CPU Usage
            Panel(
                id=3,
                title="Service CPU Usage",
                type="timeseries",
                targets=[{
                    "expr": "wakedock_service_cpu_usage_percent",
                    "refId": "A",
                    "legendFormat": "{{service_name}}"
                }],
                gridPos={"h": 8, "w": 12, "x": 0, "y": 10},
                fieldConfig={
                    "defaults": {
                        "unit": "percent"
                    }
                }
            ),
            
            # Service Memory Usage
            Panel(
                id=4,
                title="Service Memory Usage",
                type="timeseries",
                targets=[{
                    "expr": "wakedock_service_memory_usage_bytes",
                    "refId": "A",
                    "legendFormat": "{{service_name}}"
                }],
                gridPos={"h": 8, "w": 12, "x": 12, "y": 10},
                fieldConfig={
                    "defaults": {
                        "unit": "bytes"
                    }
                }
            )
        ]
        
        return Dashboard(
            title="WakeDock Services Monitoring",
            uid="wakedock-services",
            tags=["wakedock", "services", "docker"],
            panels=panels
        )
    
    def create_api_dashboard(self) -> Dashboard:
        """Create API monitoring dashboard"""
        panels = [
            # Request Rate
            Panel(
                id=1,
                title="Request Rate",
                type="stat",
                targets=[{
                    "expr": "sum(rate(wakedock_api_requests_total[5m]))",
                    "refId": "A"
                }],
                gridPos={"h": 6, "w": 6, "x": 0, "y": 0},
                fieldConfig={
                    "defaults": {
                        "unit": "reqps"
                    }
                }
            ),
            
            # Error Rate
            Panel(
                id=2,
                title="Error Rate",
                type="stat",
                targets=[{
                    "expr": "sum(rate(wakedock_api_requests_total{status_code=~\"4..|5..\"}[5m])) / sum(rate(wakedock_api_requests_total[5m])) * 100",
                    "refId": "A"
                }],
                gridPos={"h": 6, "w": 6, "x": 6, "y": 0},
                fieldConfig={
                    "defaults": {
                        "unit": "percent",
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "steps": [
                                {"color": "green", "value": None},
                                {"color": "yellow", "value": 1},
                                {"color": "red", "value": 5}
                            ]
                        }
                    }
                }
            ),
            
            # Average Response Time
            Panel(
                id=3,
                title="Average Response Time",
                type="stat",
                targets=[{
                    "expr": "sum(rate(wakedock_api_request_duration_seconds_sum[5m])) / sum(rate(wakedock_api_request_duration_seconds_count[5m]))",
                    "refId": "A"
                }],
                gridPos={"h": 6, "w": 6, "x": 12, "y": 0},
                fieldConfig={
                    "defaults": {
                        "unit": "s"
                    }
                }
            ),
            
            # Active Connections
            Panel(
                id=4,
                title="Active Connections",
                type="stat",
                targets=[{
                    "expr": "wakedock_api_active_connections",
                    "refId": "A"
                }],
                gridPos={"h": 6, "w": 6, "x": 18, "y": 0}
            ),
            
            # Request Rate by Endpoint
            Panel(
                id=5,
                title="Request Rate by Endpoint",
                type="timeseries",
                targets=[{
                    "expr": "sum(rate(wakedock_api_requests_total[5m])) by (endpoint)",
                    "refId": "A",
                    "legendFormat": "{{endpoint}}"
                }],
                gridPos={"h": 8, "w": 12, "x": 0, "y": 6},
                fieldConfig={
                    "defaults": {
                        "unit": "reqps"
                    }
                }
            ),
            
            # Response Time Percentiles
            Panel(
                id=6,
                title="Response Time Percentiles",
                type="timeseries",
                targets=[
                    {
                        "expr": "histogram_quantile(0.50, sum(rate(wakedock_api_request_duration_seconds_bucket[5m])) by (le))",
                        "refId": "A",
                        "legendFormat": "50th percentile"
                    },
                    {
                        "expr": "histogram_quantile(0.95, sum(rate(wakedock_api_request_duration_seconds_bucket[5m])) by (le))",
                        "refId": "B",
                        "legendFormat": "95th percentile"
                    },
                    {
                        "expr": "histogram_quantile(0.99, sum(rate(wakedock_api_request_duration_seconds_bucket[5m])) by (le))",
                        "refId": "C",
                        "legendFormat": "99th percentile"
                    }
                ],
                gridPos={"h": 8, "w": 12, "x": 12, "y": 6},
                fieldConfig={
                    "defaults": {
                        "unit": "s"
                    }
                }
            )
        ]
        
        return Dashboard(
            title="WakeDock API Monitoring",
            uid="wakedock-api",
            tags=["wakedock", "api", "performance"],
            panels=panels
        )


class DashboardProvisioner:
    """Grafana dashboard provisioning service"""
    
    def __init__(self, grafana_url: str = "http://localhost:3000", 
                 api_key: Optional[str] = None,
                 output_dir: str = "/etc/grafana/provisioning/dashboards"):
        self.grafana_url = grafana_url
        self.api_key = api_key
        self.output_dir = output_dir
        self.dashboard_generator = GrafanaDashboard()
    
    def provision_dashboards(self):
        """Provision all WakeDock dashboards"""
        try:
            # Ensure output directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            # Generate dashboards
            dashboards = [
                self.dashboard_generator.create_system_dashboard(),
                self.dashboard_generator.create_services_dashboard(),
                self.dashboard_generator.create_api_dashboard()
            ]
            
            # Save dashboard files
            for dashboard in dashboards:
                self._save_dashboard(dashboard)
            
            # Create provisioning config
            self._create_provisioning_config()
            
            logger.info(f"Provisioned {len(dashboards)} dashboards to {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to provision dashboards: {e}")
            raise
    
    def _save_dashboard(self, dashboard: Dashboard):
        """Save dashboard to file"""
        filename = f"{dashboard.uid}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(dashboard.to_dict(), f, indent=2)
        
        logger.debug(f"Saved dashboard: {filepath}")
    
    def _create_provisioning_config(self):
        """Create Grafana provisioning configuration"""
        config = {
            "apiVersion": 1,
            "providers": [
                {
                    "name": "wakedock",
                    "orgId": 1,
                    "folder": "WakeDock",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 10,
                    "allowUiUpdates": True,
                    "options": {
                        "path": self.output_dir
                    }
                }
            ]
        }
        
        config_dir = os.path.dirname(self.output_dir)
        config_file = os.path.join(config_dir, "dashboard.yml")
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.debug(f"Created provisioning config: {config_file}")
    
    def create_datasource_config(self, prometheus_url: str = "http://localhost:9090"):
        """Create Prometheus datasource configuration"""
        config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": prometheus_url,
                    "isDefault": True,
                    "editable": True
                }
            ]
        }
        
        config_dir = os.path.dirname(self.output_dir)
        datasources_dir = os.path.join(config_dir, "datasources")
        os.makedirs(datasources_dir, exist_ok=True)
        
        config_file = os.path.join(datasources_dir, "prometheus.yml")
        
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        logger.info(f"Created datasource config: {config_file}")


# Global provisioner instance
_dashboard_provisioner: Optional[DashboardProvisioner] = None


def get_dashboard_provisioner() -> Optional[DashboardProvisioner]:
    """Get global dashboard provisioner instance"""
    return _dashboard_provisioner


def init_dashboard_provisioner(grafana_url: str = "http://localhost:3000",
                             api_key: Optional[str] = None,
                             output_dir: str = "/etc/grafana/provisioning/dashboards") -> DashboardProvisioner:
    """Initialize global dashboard provisioner"""
    global _dashboard_provisioner
    _dashboard_provisioner = DashboardProvisioner(
        grafana_url=grafana_url,
        api_key=api_key,
        output_dir=output_dir
    )
    return _dashboard_provisioner