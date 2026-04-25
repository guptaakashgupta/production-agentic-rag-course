from src.services.langfuse.tracer import RAGTracer


class LegacyTracerWithoutRequestMethod:
    def __init__(self):
        self.flush_calls = 0

    def flush(self):
        self.flush_calls += 1


class LegacyTracerWithoutSpanHelpers:
    pass


def test_trace_request_degrades_gracefully_when_request_tracing_is_unavailable():
    tracer = LegacyTracerWithoutRequestMethod()
    rag_tracer = RAGTracer(tracer)

    with rag_tracer.trace_request("api_user", "What are transformers?") as trace:
        assert trace is None

    assert tracer.flush_calls == 0


def test_trace_embedding_degrades_gracefully_when_span_helpers_are_unavailable():
    rag_tracer = RAGTracer(LegacyTracerWithoutSpanHelpers())

    with rag_tracer.trace_embedding(None, "What are transformers?") as span:
        assert span is None