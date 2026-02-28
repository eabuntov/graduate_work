from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

import os

from config.settings import settings


def setup_tracing():
    service_name = settings.SERVICE_NAME
    environment = settings.ENVIRONMENT

    sampler = ParentBased(
        TraceIdRatioBased(
            float(settings.OTEL_TRACES_SAMPLER_ARG)
        )
    )

    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": environment,
        }
    )

    provider = TracerProvider(resource=resource, sampler=sampler)
    trace.set_tracer_provider(provider)

    exporter = OTLPSpanExporter(endpoint=f"{settings.JAEGER_AGENT_HOST, 'localhost'}:{int(settings.JAEGER_AGENT_PORT)}/v1/traces")

    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
