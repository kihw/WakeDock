"""
OpenTelemetry Tracing Integration

Provides distributed tracing capabilities using OpenTelemetry:
- Request tracing
- Service tracing  
- Custom spans
- Trace export
"""

import logging
from typing import Dict, Optional, Any
from contextlib import contextmanager

try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    # Fallback implementations
    class Span:
        def set_attribute(self, *args): pass
        def set_status(self, *args): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class Tracer:
        def start_span(self, *args, **kwargs): return Span()
    
    trace = type('trace', (), {'get_tracer': lambda *args: Tracer()})()

logger = logging.getLogger(__name__)


class OTelTracer:
    """OpenTelemetry tracer wrapper"""
    
    def __init__(self, service_name: str = "wakedock"):
        self.service_name = service_name
        self.tracer = None
        self._initialized = False
        
        if OPENTELEMETRY_AVAILABLE:
            self._setup_tracing()
        else:
            logger.warning("OpenTelemetry not available, tracing disabled")
    
    def _setup_tracing(self):
        """Setup OpenTelemetry tracing"""
        try:
            # Create resource
            resource = Resource.create({"service.name": self.service_name})
            
            # Set up tracer provider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            self._initialized = True
            logger.info(f"OpenTelemetry tracer initialized for service: {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to setup OpenTelemetry tracing: {e}")
    
    def is_available(self) -> bool:
        """Check if tracing is available"""
        return OPENTELEMETRY_AVAILABLE and self._initialized
    
    @contextmanager
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Start a new span"""
        if not self.is_available():
            yield None
            return
            
        span = self.tracer.start_span(name)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        
        try:
            yield span
        except Exception as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise
        finally:
            span.end()
    
    def add_jaeger_exporter(self, endpoint: str = "http://localhost:14268/api/traces"):
        """Add Jaeger exporter"""
        if not self.is_available():
            return
            
        try:
            jaeger_exporter = JaegerExporter(endpoint=endpoint)
            span_processor = BatchSpanProcessor(jaeger_exporter)
            trace.get_tracer_provider().add_span_processor(span_processor)
            logger.info(f"Jaeger exporter added: {endpoint}")
        except Exception as e:
            logger.error(f"Failed to add Jaeger exporter: {e}")


class TracingService:
    """High-level tracing service"""
    
    def __init__(self, service_name: str = "wakedock"):
        self.tracer = OTelTracer(service_name)
        self._instrumentors = []
    
    def instrument_fastapi(self, app):
        """Instrument FastAPI application"""
        if not OPENTELEMETRY_AVAILABLE:
            return
            
        try:
            FastAPIInstrumentor.instrument_app(app)
            self._instrumentors.append("fastapi")
            logger.info("FastAPI instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument FastAPI: {e}")
    
    def instrument_requests(self):
        """Instrument HTTP requests"""
        if not OPENTELEMETRY_AVAILABLE:
            return
            
        try:
            RequestsInstrumentor().instrument()
            self._instrumentors.append("requests")
            logger.info("Requests instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument requests: {e}")
    
    def instrument_sqlalchemy(self, engine):
        """Instrument SQLAlchemy"""
        if not OPENTELEMETRY_AVAILABLE:
            return
            
        try:
            SQLAlchemyInstrumentor().instrument(engine=engine)
            self._instrumentors.append("sqlalchemy")
            logger.info("SQLAlchemy instrumentation enabled")
        except Exception as e:
            logger.error(f"Failed to instrument SQLAlchemy: {e}")
    
    def trace_api_request(self, method: str, endpoint: str, user_id: Optional[str] = None):
        """Trace an API request"""
        attributes = {
            "http.method": method,
            "http.route": endpoint
        }
        
        if user_id:
            attributes["user.id"] = user_id
            
        return self.tracer.start_span(f"API {method} {endpoint}", attributes)
    
    def trace_docker_operation(self, operation: str, container_id: Optional[str] = None):
        """Trace a Docker operation"""
        attributes = {"docker.operation": operation}
        
        if container_id:
            attributes["docker.container.id"] = container_id
            
        return self.tracer.start_span(f"Docker {operation}", attributes)
    
    def trace_database_query(self, query_type: str, table: Optional[str] = None):
        """Trace a database query"""
        attributes = {"db.operation": query_type}
        
        if table:
            attributes["db.table"] = table
            
        return self.tracer.start_span(f"DB {query_type}", attributes)
    
    def get_instrumentors(self) -> list:
        """Get list of active instrumentors"""
        return self._instrumentors.copy()


# Global tracing service instance
_tracing_service: Optional[TracingService] = None


def get_tracing_service() -> Optional[TracingService]:
    """Get global tracing service instance"""
    return _tracing_service


def init_tracing_service(service_name: str = "wakedock") -> TracingService:
    """Initialize global tracing service"""
    global _tracing_service
    _tracing_service = TracingService(service_name)
    return _tracing_service