# Local Setup Guide

## Before You Start

Regardless of which option you choose, you need these one-time steps after cloning:

```bash
cp .env.example .env
# Edit .env — add your Jina embeddings API key (free) and Langfuse keys (Week 6+)

uv sync   # install Python dependencies
```

---

## Option 1: GitHub Codespaces (Recommended)

Zero local resource usage, full Docker support, and a generous free tier.

1. Fork the repo at https://github.com/jamwithai/arxiv-paper-curator
2. Click **Code → Codespaces → Create codespace** (pick a **4-core / 16GB RAM** machine)
3. Inside the codespace terminal:
   ```bash
   cp .env.example .env
   uv sync
   docker compose up --build -d
   ```
4. Ports auto-forward — access all UIs (FastAPI docs, Gradio, Langfuse, etc.) from your browser

**Free tier:** 120 core-hours/month (30 hours on a 4-core machine — plenty for weekly learning). **Stop the codespace when not using it.**

---

## Option 2: Run Only the Services Each Week Needs

If you want to stay local, you don't need all containers at once. Start only what each week requires.

> **Note:** The `api` service depends on `postgres`, `opensearch`, and `redis` — all three must be included in every command or `api` won't start.

### Week 1–2: Infrastructure & Data Ingestion (~3–4 GB RAM)

```bash
docker compose up --build -d api postgres opensearch redis airflow
```

Airflow is needed in Week 2 to run the arXiv data ingestion DAGs.

### Week 3: BM25 Search (~3 GB RAM)

```bash
docker compose up --build -d api postgres opensearch redis opensearch-dashboards
```

> **Prerequisite:** Data must already be loaded from Week 2. If starting fresh, bring up Airflow briefly to run the ingestion DAG, then stop it:
> ```bash
> docker compose up -d airflow
> # Trigger the DAG from http://localhost:8080, wait for completion, then:
> docker compose stop airflow
> ```

### Week 4: Chunking & Hybrid Search (~3 GB RAM)

Same as Week 3 — Jina embeddings are a remote API, no extra local cost.

```bash
docker compose up --build -d api postgres opensearch redis
```

### Week 5: Complete RAG with Local LLM (~6–7 GB RAM)

```bash
docker compose up --build -d api postgres opensearch redis ollama
```

After services are up, pull the model:

```bash
docker exec rag-ollama ollama pull llama3.2:1b
```

Use the smallest model (`llama3.2:1b`) to minimize RAM. If your machine struggles, replace Ollama with a cloud LLM API (Groq or Together AI free tier) and skip the `ollama` service.

### Week 6: Monitoring & Caching (~7–8 GB RAM)

**Minimal** — just add Redis cache (already included) + Langfuse:

```bash
docker compose up --build -d api postgres opensearch redis ollama \
  clickhouse langfuse-web langfuse-worker langfuse-postgres langfuse-redis langfuse-minio
```

If Langfuse is too heavy, skip it and focus on the Redis caching code — you can read the Langfuse traces in the blog post screenshots instead.

### Week 7: Agentic RAG & Telegram Bot (~6–7 GB RAM)

Same services as Week 5 — the agentic logic runs inside the API container.

```bash
docker compose up --build -d api postgres opensearch redis ollama
```

### Stopping Everything

```bash
docker compose down        # stop and remove containers (keeps data)
docker compose down -v     # stop and remove containers AND volumes (fresh start)
```

---

## Option 3: Cloud VPS

If Codespaces hours run out, a cheap cloud VM works well:

| Provider | Instance | RAM | Cost |
|----------|----------|-----|------|
| Hetzner | CAX21 (4 vCPU ARM) | 8 GB | ~$7/month |
| DigitalOcean | Basic (4 vCPU) | 8 GB | ~$48/month |

Install Docker + UV, clone the repo, and run everything remotely. SSH in or use **VS Code Remote-SSH** from your Mac.

---

## Recommendation

Start with **GitHub Codespaces**. It's free, requires zero local setup, gives you 16 GB RAM machines, and you can jump right into the notebooks.

If you run through the free tier, fall back to **Option 2** on your Mac — Weeks 1–4 will run fine even on a constrained machine since they don't need Ollama or Langfuse.