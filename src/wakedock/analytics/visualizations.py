"""
Analytics Visualization Data Generation

Generates data structures optimized for various chart types and visualizations:
- Time series charts
- Usage heatmaps  
- User journey flows
- Performance dashboards
- Trend analysis
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from enum import Enum

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Supported chart types"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    GAUGE = "gauge"
    TREEMAP = "treemap"


class VisualizationGenerator:
    """Generates visualization data for analytics dashboards"""
    
    def __init__(self, analytics_storage=None, usage_collector=None):
        self.storage = analytics_storage
        self.usage_collector = usage_collector
    
    async def generate_system_overview_dashboard(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive system overview dashboard"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        dashboard = {
            "title": "System Overview Dashboard",
            "period": f"Last {hours} hours",
            "generated_at": end_time.isoformat(),
            "widgets": []
        }
        
        try:
            # System metrics time series
            system_metrics = await self._generate_system_metrics_chart(start_time, end_time)
            dashboard["widgets"].append(system_metrics)
            
            # Active users gauge
            active_users = await self._generate_active_users_gauge()
            dashboard["widgets"].append(active_users)
            
            # API performance overview
            api_performance = await self._generate_api_performance_chart(hours)
            dashboard["widgets"].append(api_performance)
            
            # Top features usage
            feature_usage = await self._generate_feature_usage_pie()
            dashboard["widgets"].append(feature_usage)
            
            # Error rate trend
            error_trend = await self._generate_error_trend_chart(start_time, end_time)
            dashboard["widgets"].append(error_trend)
            
            # User activity heatmap
            activity_heatmap = await self._generate_user_activity_heatmap(hours)
            dashboard["widgets"].append(activity_heatmap)
            
        except Exception as e:
            logger.error(f"Error generating system overview dashboard: {e}")
            dashboard["error"] = str(e)
        
        return dashboard
    
    async def generate_user_analytics_dashboard(self, user_id: str = None, hours: int = 24) -> Dict[str, Any]:
        """Generate user-focused analytics dashboard"""
        dashboard = {
            "title": "User Analytics Dashboard",
            "period": f"Last {hours} hours",
            "generated_at": datetime.utcnow().isoformat(),
            "widgets": []
        }
        
        try:
            # User session timeline
            session_timeline = await self._generate_user_session_timeline(user_id, hours)
            dashboard["widgets"].append(session_timeline)
            
            # Feature usage by user
            user_features = await self._generate_user_feature_usage(user_id, hours)
            dashboard["widgets"].append(user_features)
            
            # User journey flow
            journey_flow = await self._generate_user_journey_flow(user_id, hours)
            dashboard["widgets"].append(journey_flow)
            
            # Performance metrics by user
            user_performance = await self._generate_user_performance_metrics(user_id, hours)
            dashboard["widgets"].append(user_performance)
            
        except Exception as e:
            logger.error(f"Error generating user analytics dashboard: {e}")
            dashboard["error"] = str(e)
        
        return dashboard
    
    async def generate_performance_dashboard(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance-focused dashboard"""
        dashboard = {
            "title": "Performance Analytics Dashboard",
            "period": f"Last {hours} hours",
            "generated_at": datetime.utcnow().isoformat(),
            "widgets": []
        }
        
        try:
            # Response time trends
            response_trends = await self._generate_response_time_trends(hours)
            dashboard["widgets"].append(response_trends)
            
            # Throughput analysis
            throughput = await self._generate_throughput_analysis(hours)
            dashboard["widgets"].append(throughput)
            
            # Error rate analysis
            error_analysis = await self._generate_detailed_error_analysis(hours)
            dashboard["widgets"].append(error_analysis)
            
            # Resource utilization
            resource_util = await self._generate_resource_utilization_chart(hours)
            dashboard["widgets"].append(resource_util)
            
            # Cache performance
            cache_perf = await self._generate_cache_performance_chart(hours)
            dashboard["widgets"].append(cache_perf)
            
        except Exception as e:
            logger.error(f"Error generating performance dashboard: {e}")
            dashboard["error"] = str(e)
        
        return dashboard
    
    async def _generate_system_metrics_chart(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate system metrics time series chart"""
        # Simulate system metrics data
        time_points = []
        current = start_time
        while current <= end_time:
            time_points.append(current)
            current += timedelta(hours=1)
        
        cpu_data = [{"x": t.isoformat(), "y": 20 + (i * 3) % 60} for i, t in enumerate(time_points)]
        memory_data = [{"x": t.isoformat(), "y": 45 + (i * 2) % 40} for i, t in enumerate(time_points)]
        disk_data = [{"x": t.isoformat(), "y": 35 + (i * 1.5) % 30} for i, t in enumerate(time_points)]
        
        return {
            "id": "system_metrics",
            "title": "System Resource Usage",
            "type": ChartType.LINE.value,
            "data": {
                "datasets": [
                    {
                        "label": "CPU Usage %",
                        "data": cpu_data,
                        "borderColor": "#3B82F6",
                        "backgroundColor": "rgba(59, 130, 246, 0.1)"
                    },
                    {
                        "label": "Memory Usage %", 
                        "data": memory_data,
                        "borderColor": "#10B981",
                        "backgroundColor": "rgba(16, 185, 129, 0.1)"
                    },
                    {
                        "label": "Disk Usage %",
                        "data": disk_data,
                        "borderColor": "#F59E0B",
                        "backgroundColor": "rgba(245, 158, 11, 0.1)"
                    }
                ]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "max": 100
                    }
                }
            }
        }
    
    async def _generate_active_users_gauge(self) -> Dict[str, Any]:
        """Generate active users gauge"""
        active_count = 0
        if self.usage_collector:
            active_count = len(self.usage_collector.active_sessions)
        
        return {
            "id": "active_users",
            "title": "Active Users",
            "type": ChartType.GAUGE.value,
            "data": {
                "value": active_count,
                "max": 100,
                "threshold": [
                    {"value": 20, "color": "#10B981"},
                    {"value": 50, "color": "#F59E0B"},
                    {"value": 80, "color": "#EF4444"}
                ]
            },
            "options": {
                "responsive": True
            }
        }
    
    async def _generate_api_performance_chart(self, hours: int) -> Dict[str, Any]:
        """Generate API performance overview"""
        if not self.usage_collector:
            return self._empty_widget("api_performance", "API Performance")
        
        api_data = []
        for endpoint, perf in self.usage_collector.api_performance.items():
            if perf["total_calls"] > 0:
                api_data.append({
                    "endpoint": endpoint,
                    "calls": perf["total_calls"],
                    "avg_response": round(perf["avg_response_time"], 2),
                    "error_rate": round(perf["error_count"] / perf["total_calls"] * 100, 2)
                })
        
        # Sort by total calls
        api_data.sort(key=lambda x: x["calls"], reverse=True)
        top_apis = api_data[:10]
        
        return {
            "id": "api_performance",
            "title": "Top API Endpoints Performance",
            "type": ChartType.BAR.value,
            "data": {
                "labels": [api["endpoint"] for api in top_apis],
                "datasets": [
                    {
                        "label": "Total Calls",
                        "data": [api["calls"] for api in top_apis],
                        "backgroundColor": "#3B82F6",
                        "yAxisID": "y"
                    },
                    {
                        "label": "Avg Response Time (ms)",
                        "data": [api["avg_response"] for api in top_apis],
                        "backgroundColor": "#10B981",
                        "yAxisID": "y1"
                    }
                ]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "type": "linear",
                        "display": True,
                        "position": "left"
                    },
                    "y1": {
                        "type": "linear",
                        "display": True,
                        "position": "right",
                        "grid": {"drawOnChartArea": False}
                    }
                }
            }
        }
    
    async def _generate_feature_usage_pie(self) -> Dict[str, Any]:
        """Generate feature usage pie chart"""
        if not self.usage_collector:
            return self._empty_widget("feature_usage", "Feature Usage")
        
        feature_data = []
        total_usage = 0
        
        for feature_name, feature_stats in self.usage_collector.feature_usage.items():
            feature_data.append({
                "label": feature_name,
                "value": feature_stats.total_usage
            })
            total_usage += feature_stats.total_usage
        
        # Sort by usage
        feature_data.sort(key=lambda x: x["value"], reverse=True)
        top_features = feature_data[:8]  # Top 8 features
        
        return {
            "id": "feature_usage",
            "title": "Top Feature Usage",
            "type": ChartType.PIE.value,
            "data": {
                "labels": [f["label"] for f in top_features],
                "datasets": [{
                    "data": [f["value"] for f in top_features],
                    "backgroundColor": [
                        "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
                        "#8B5CF6", "#06B6D4", "#84CC16", "#F97316"
                    ]
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "legend": {
                        "position": "right"
                    }
                }
            }
        }
    
    async def _generate_error_trend_chart(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Generate error rate trend chart"""
        # Simulate error data
        time_points = []
        current = start_time
        while current <= end_time:
            time_points.append(current)
            current += timedelta(hours=1)
        
        error_data = [{"x": t.isoformat(), "y": max(0, 5 + (i % 7) - 3)} for i, t in enumerate(time_points)]
        
        return {
            "id": "error_trend",
            "title": "Error Rate Trend",
            "type": ChartType.AREA.value,
            "data": {
                "datasets": [{
                    "label": "Errors per Hour",
                    "data": error_data,
                    "borderColor": "#EF4444",
                    "backgroundColor": "rgba(239, 68, 68, 0.2)",
                    "fill": True
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }
    
    async def _generate_user_activity_heatmap(self, hours: int) -> Dict[str, Any]:
        """Generate user activity heatmap"""
        # Generate sample heatmap data (hour vs day of week)
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        hour_labels = [f"{h:02d}:00" for h in range(24)]
        
        heatmap_data = []
        for day_idx, day in enumerate(days):
            for hour in range(24):
                # Simulate activity data with realistic patterns
                base_activity = 10
                if 9 <= hour <= 17:  # Business hours
                    base_activity = 50
                elif 19 <= hour <= 22:  # Evening
                    base_activity = 30
                
                if day_idx < 5:  # Weekdays
                    activity = base_activity + (hour * day_idx) % 20
                else:  # Weekends
                    activity = base_activity * 0.6 + (hour * day_idx) % 15
                
                heatmap_data.append({
                    "x": hour,
                    "y": day_idx,
                    "v": int(activity)
                })
        
        return {
            "id": "user_activity_heatmap",
            "title": "User Activity Heatmap",
            "type": ChartType.HEATMAP.value,
            "data": {
                "datasets": [{
                    "label": "Activity Level",
                    "data": heatmap_data,
                    "backgroundColor": lambda ctx: {
                        0: "#f3f4f6",
                        20: "#dbeafe", 
                        40: "#93c5fd",
                        60: "#3b82f6",
                        80: "#1e40af"
                    }.get(min(80, ctx.parsed.v // 20 * 20), "#1e40af")
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "x": {
                        "title": {"display": True, "text": "Hour of Day"},
                        "labels": hour_labels
                    },
                    "y": {
                        "title": {"display": True, "text": "Day of Week"},
                        "labels": days
                    }
                }
            }
        }
    
    async def _generate_user_session_timeline(self, user_id: str, hours: int) -> Dict[str, Any]:
        """Generate user session timeline"""
        if not self.usage_collector or not user_id:
            return self._empty_widget("user_sessions", "User Session Timeline")
        
        user_insights = self.usage_collector.get_user_insights(user_id)
        
        timeline_data = []
        if user_insights.get("current_session"):
            session = user_insights["current_session"]
            timeline_data.append({
                "session_id": session["session_id"],
                "start": session["start_time"],
                "duration": session["duration_minutes"],
                "pages": session["pages_visited"],
                "api_calls": session["api_calls_made"]
            })
        
        return {
            "id": "user_sessions",
            "title": f"User Session Timeline - {user_id}",
            "type": "timeline",
            "data": {
                "sessions": timeline_data
            },
            "options": {
                "responsive": True
            }
        }
    
    async def _generate_user_feature_usage(self, user_id: str, hours: int) -> Dict[str, Any]:
        """Generate user-specific feature usage"""
        # Placeholder for user-specific feature usage
        return self._empty_widget("user_features", "User Feature Usage")
    
    async def _generate_user_journey_flow(self, user_id: str, hours: int) -> Dict[str, Any]:
        """Generate user journey flow visualization"""
        # Placeholder for user journey flow
        return self._empty_widget("user_journey", "User Journey Flow")
    
    async def _generate_user_performance_metrics(self, user_id: str, hours: int) -> Dict[str, Any]:
        """Generate user-specific performance metrics"""
        # Placeholder for user performance metrics
        return self._empty_widget("user_performance", "User Performance Metrics")
    
    async def _generate_response_time_trends(self, hours: int) -> Dict[str, Any]:
        """Generate response time trend analysis"""
        # Placeholder for response time trends
        return self._empty_widget("response_trends", "Response Time Trends")
    
    async def _generate_throughput_analysis(self, hours: int) -> Dict[str, Any]:
        """Generate throughput analysis"""
        # Placeholder for throughput analysis
        return self._empty_widget("throughput", "Throughput Analysis")
    
    async def _generate_detailed_error_analysis(self, hours: int) -> Dict[str, Any]:
        """Generate detailed error analysis"""
        # Placeholder for detailed error analysis
        return self._empty_widget("error_analysis", "Detailed Error Analysis")
    
    async def _generate_resource_utilization_chart(self, hours: int) -> Dict[str, Any]:
        """Generate resource utilization chart"""
        # Placeholder for resource utilization
        return self._empty_widget("resource_util", "Resource Utilization")
    
    async def _generate_cache_performance_chart(self, hours: int) -> Dict[str, Any]:
        """Generate cache performance chart"""
        # Placeholder for cache performance
        return self._empty_widget("cache_performance", "Cache Performance")
    
    def _empty_widget(self, widget_id: str, title: str) -> Dict[str, Any]:
        """Generate empty widget placeholder"""
        return {
            "id": widget_id,
            "title": title,
            "type": "placeholder",
            "data": {"message": "No data available"},
            "options": {"responsive": True}
        }
    
    async def generate_custom_chart(self, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate custom chart based on configuration"""
        try:
            chart_type = chart_config.get("type", ChartType.LINE.value)
            metric_names = chart_config.get("metrics", [])
            time_range = chart_config.get("time_range", 24)
            
            # Basic validation
            if not metric_names:
                return self._empty_widget("custom_chart", "Custom Chart")
            
            # Generate data based on chart type and metrics
            if chart_type == ChartType.LINE.value:
                return await self._generate_custom_line_chart(metric_names, time_range)
            elif chart_type == ChartType.BAR.value:
                return await self._generate_custom_bar_chart(metric_names, time_range)
            elif chart_type == ChartType.PIE.value:
                return await self._generate_custom_pie_chart(metric_names, time_range)
            else:
                return self._empty_widget("custom_chart", "Unsupported Chart Type")
                
        except Exception as e:
            logger.error(f"Error generating custom chart: {e}")
            return {"error": str(e)}
    
    async def _generate_custom_line_chart(self, metrics: List[str], hours: int) -> Dict[str, Any]:
        """Generate custom line chart"""
        # Placeholder implementation
        return self._empty_widget("custom_line", "Custom Line Chart")
    
    async def _generate_custom_bar_chart(self, metrics: List[str], hours: int) -> Dict[str, Any]:
        """Generate custom bar chart"""
        # Placeholder implementation
        return self._empty_widget("custom_bar", "Custom Bar Chart")
    
    async def _generate_custom_pie_chart(self, metrics: List[str], hours: int) -> Dict[str, Any]:
        """Generate custom pie chart"""
        # Placeholder implementation
        return self._empty_widget("custom_pie", "Custom Pie Chart")


# Factory function
def create_visualization_generator(analytics_storage=None, usage_collector=None) -> VisualizationGenerator:
    """Create visualization generator with dependencies"""
    return VisualizationGenerator(analytics_storage, usage_collector)