# Use vLLM base image with CUDA support
FROM vllm/vllm-openai:v0.10.2

# Set working directory
WORKDIR /app

# Install additional dependencies
RUN pip install --no-cache-dir requests

# Environment variables
ENV VLLM_USE_FLASHINFER_SAMPLER=0
ENV PYTHONUNBUFFERED=1

# Configuration (can be overridden in docker-compose.yml)
ENV API_KEY=qiCwgirvWt4XCA4S2jekdTJruXXmb08K
ENV EMBEDDING_MODEL=Qwen/Qwen3-Embedding-4B
ENV LLM_MODEL=openai/gpt-oss-20b
ENV EMBEDDING_PORT=8002
ENV LLM_PORT=8000

# Copy deployment script
COPY deploy_docker.py /app/deploy.py

# Expose ports
EXPOSE 8000 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run deployment
CMD ["python", "/app/deploy.py"]
