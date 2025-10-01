# vLLM Docker Deployment - Quick Setup

## Files Included
- `Dockerfile` - Container definition
- `docker-compose.yml` - Orchestration configuration
- `deploy_docker.py` - Deployment script
- `.dockerignore` - Build exclusions

## Quick Start (3 Commands)

### 1. Install Docker (if needed)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and back in after this
```

### 2. Install NVIDIA Container Toolkit
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

### 3. Deploy
```bash
# Copy all files to your workspace
mkdir -p /workspace/vllm-docker
cd /workspace/vllm-docker
# Copy the 4 files here, then:

docker-compose up -d
docker-compose logs -f
```

## Configuration

### Change API Key (IMPORTANT!)
Edit `docker-compose.yml`:
```yaml
- API_KEY=your-secure-key-here
```

### Adjust Context Length
Edit `deploy_docker.py`, line 98:
```python
max_model_len = 32768   # 32K tokens (default)
# max_model_len = 65536   # 65K tokens
# max_model_len = 131072  # 131K tokens (max)
```

## Testing

### Test Embedding API
```bash
curl -X POST http://localhost:8002/v1/embeddings \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-embedding", "input": ["Hello world"]}'
```

### Test LLM API
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-oss-20b",
    "messages": [{"role": "user", "content": "What is Docker?"}],
    "max_tokens": 100
  }'
```

## Essential Commands

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after changes
docker-compose down
docker-compose build
docker-compose up -d

# Monitor GPU
watch -n 1 nvidia-smi

# Check status
docker-compose ps
```

## Ports
- **8000** - LLM API (GPT-OSS-20B)
- **8002** - Embedding API (Qwen3-Embedding-4B)

## First Run Timeline
- Build: 3-5 minutes
- Model Download: 5-15 minutes (first time only)
- Model Loading: 2-5 minutes
- **Total**: ~10-25 minutes first run
- **Subsequent runs**: ~5 minutes (models cached)

## Troubleshooting

### Container won't start
```bash
docker-compose logs
nvidia-smi
```

### Out of memory
Edit `deploy_docker.py`, reduce memory utilization from `0.90` to `0.70`

### Slow model download
```bash
# Pre-download models
docker run --rm -v huggingface_cache:/root/.cache/huggingface \
  vllm/vllm-openai:v0.10.2 \
  huggingface-cli download Qwen/Qwen3-Embedding-4B
```

## Support
- vLLM Docs: https://docs.vllm.ai
- Docker Docs: https://docs.docker.com
- NVIDIA Docker: https://github.com/NVIDIA/nvidia-docker
