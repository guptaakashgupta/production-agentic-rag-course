from unittest.mock import MagicMock

from src.services.langfuse.client import LangfuseTracer


def make_tracer(client):
    tracer = LangfuseTracer.__new__(LangfuseTracer)
    tracer.client = client
    tracer.settings = None
    return tracer


def test_trace_rag_request_uses_client_trace_when_available():
    client = MagicMock()
    trace = MagicMock()
    client.trace.return_value = trace
    tracer = make_tracer(client)

    with tracer.trace_rag_request(
        query="What are transformers?",
        user_id="api_user",
        session_id="session_api_user",
        metadata={"simplified_tracing": True},
    ) as current_trace:
        assert current_trace is trace

    client.trace.assert_called_once_with(
        name="rag_request",
        user_id="api_user",
        session_id="session_api_user",
        input={"query": "What are transformers?"},
        metadata={"simplified_tracing": True},
        tags=None,
    )


def test_create_span_prefers_parent_trace_span():
    client = MagicMock()
    tracer = make_tracer(client)
    parent_trace = MagicMock()
    child_span = MagicMock()
    parent_trace.span.return_value = child_span

    created_span = tracer.create_span(
        trace=parent_trace,
        name="search_retrieval",
        input_data={"query": "transformers", "top_k": 3},
    )

    assert created_span is child_span
    parent_trace.span.assert_called_once_with(
        name="search_retrieval",
        input={"query": "transformers", "top_k": 3},
        metadata={},
    )


def test_end_span_updates_then_ends():
    tracer = make_tracer(MagicMock())
    span = MagicMock()

    tracer.end_span(
        span,
        output={"success": True},
        metadata={"latency_ms": 12.5},
        level="INFO",
        status_message="ok",
    )

    span.update.assert_called_once_with(
        output={"success": True},
        metadata={"latency_ms": 12.5},
        level="INFO",
        status_message="ok",
    )
    span.end.assert_called_once_with()


def test_update_span_does_not_end_span():
    tracer = make_tracer(MagicMock())
    span = MagicMock()

    tracer.update_span(span, output={"success": True})

    span.update.assert_called_once_with(output={"success": True})
    span.end.assert_not_called()