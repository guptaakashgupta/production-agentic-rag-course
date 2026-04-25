"""Simple, efficient Langfuse tracing utility for RAG pipeline."""

import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from .client import LangfuseTracer


class RAGTracer:
    """Clean, purpose-built tracer for RAG operations."""

    def __init__(self, tracer: LangfuseTracer):
        self.tracer = tracer

    def _create_span(self, trace, name: str, input_data: Optional[Dict[str, Any]] = None):
        create_span = getattr(self.tracer, "create_span", None)
        if not callable(create_span):
            return None

        try:
            return create_span(trace=trace, name=name, input_data=input_data)
        except Exception:
            return None

    def _update_span(self, span, output: Optional[Dict[str, Any]] = None):
        update_span = getattr(self.tracer, "update_span", None)
        if not callable(update_span) or not span:
            return

        try:
            update_span(span=span, output=output)
        except Exception:
            pass

    def _end_span(self, span):
        if not span:
            return

        end_span = getattr(self.tracer, "end_span", None)
        if callable(end_span):
            try:
                end_span(span)
                return
            except Exception:
                pass

        try:
            span.end()
        except Exception:
            pass

    @contextmanager
    def trace_request(self, user_id: str, query: str):
        """Main request trace context manager."""
        trace = None
        trace_rag_request = getattr(self.tracer, "trace_rag_request", None)

        if not callable(trace_rag_request):
            yield None
            return

        try:
            with trace_rag_request(
                query=query, user_id=user_id, session_id=f"session_{user_id}", metadata={"simplified_tracing": True}
            ) as trace:
                yield trace
        finally:
            if trace:
                flush = getattr(self.tracer, "flush", None)
                if callable(flush):
                    try:
                        flush()
                    except Exception:
                        pass

    @contextmanager
    def trace_embedding(self, trace, query: str):
        """Query embedding operation with timing."""
        start_time = time.time()
        span = self._create_span(trace=trace, name="query_embedding", input_data={"query": query, "query_length": len(query)})
        try:
            yield span
        finally:
            duration = time.time() - start_time
            if span:
                self._update_span(span=span, output={"embedding_duration_ms": round(duration * 1000, 2), "success": True})
                self._end_span(span)

    @contextmanager
    def trace_search(self, trace, query: str, top_k: int):
        """Search operation with timing."""
        span = self._create_span(trace=trace, name="search_retrieval", input_data={"query": query, "top_k": top_k})
        try:
            yield span
        finally:
            if span:
                self._end_span(span)

    def end_search(self, span, chunks: List[Dict], arxiv_ids: List[str], total_hits: int):
        """End search span with essential results."""
        if not span:
            return

        self._update_span(
            span=span,
            output={
                "chunks_returned": len(chunks),
                "unique_papers": len(set(arxiv_ids)),
                "total_hits": total_hits,
                "arxiv_ids": list(set(arxiv_ids)),
            },
        )

    @contextmanager
    def trace_prompt_construction(self, trace, chunks: List[Dict]):
        """Prompt building with timing."""
        span = self._create_span(trace=trace, name="prompt_construction", input_data={"chunk_count": len(chunks)})
        try:
            yield span
        finally:
            if span:
                self._end_span(span)

    def end_prompt(self, span, prompt: str):
        """End prompt span with final prompt."""
        if not span:
            return

        self._update_span(
            span=span,
            output={
                "prompt_length": len(prompt),
                # Don't duplicate the full prompt here since it's in llm_generation input
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            },
        )

    @contextmanager
    def trace_generation(self, trace, model: str, prompt: str):
        """LLM generation with timing."""
        span = self._create_span(
            trace=trace, name="llm_generation", input_data={"model": model, "prompt_length": len(prompt), "prompt": prompt}
        )
        try:
            yield span
        finally:
            if span:
                self._end_span(span)

    def end_generation(self, span, response: str, model: str):
        """End generation span with response."""
        if not span:
            return

        self._update_span(span=span, output={"response": response, "response_length": len(response), "model_used": model})

    def end_request(self, trace, response: str, total_duration: float):
        """End main request trace."""
        if not trace:
            return

        try:
            trace.update(
                output={"answer": response, "total_duration_seconds": round(total_duration, 3), "response_length": len(response)}
            )
        except Exception:
            # Silently fail - don't break the request for tracing issues
            pass
