# Docker Hub Automated Build Setup

## Option A: Docker Hub Automated Builds (No Local Build Required)

### Steps:

1. **Create GitHub Repository**
   - Create a new repo (e.g., `vllm-dual-a40`)
   - Push all files (Dockerfile, docker-compose.yml, deploy_docker.py, .dockerignore)

2. **Connect to Docker Hub**
   - Go to https://hub.docker.com
   - Click "Create Repository"
   - Name: `vllm-dual-a40`
   - Click "Builds" tab
   - Connect your GitHub account
   - Select your repository
   - Configure build settings:
     * Source: `main` or `master` branch
     * Dockerfile location: `/Dockerfile`
     * Build context: `/`

3. **Trigger Build**
   - Docker Hub will automatically build when you push to GitHub
   - Build happens on Docker Hub servers (no local resources used)

---

## Option B: GitHub Actions (Recommended)

### Setup:

1. **Add Docker Hub Secrets to GitHub**
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Add two secrets:
     * `DOCKER_USERNAME` (your Docker Hub username)
     * `DOCKER_PASSWORD` (your Docker Hub access token)

2. **Create Access Token on Docker Hub**
   - Go to Docker Hub → Account Settings → Security
   - Click "New Access Token"
   - Name it (e.g., "GitHub Actions")
   - Copy the token (use this as DOCKER_PASSWORD)

3. **Push Code with GitHub Actions Workflow**
   - Create `.github/workflows/docker-build.yml` (already created)
   - Commit and push to GitHub
   - GitHub Actions will build and push automatically

4. **Edit Workflow File**
   - Change `yourusername/vllm-dual-a40` to your actual Docker Hub username

---

## Option C: Build Remotely with Docker Buildx

If you must build from Codespaces, use remote builder:

```bash
# Install buildx
docker buildx create --use --name remote-builder

# Build and push without storing locally
docker buildx build \
  --platform linux/amd64 \
  --tag yourusername/vllm-dual-a40:latest \
  --push \
  --no-cache \
  .
```

This builds in a remote environment and pushes directly to Docker Hub without storing the image locally.

---

## Option D: Slim Down the Image

Create a lighter Dockerfile that pulls the deployment script only:

```dockerfile
FROM vllm/vllm-openai:v0.10.2
WORKDIR /app
RUN pip install --no-cache-dir requests && \
    rm -rf /root/.cache/pip
ENV VLLM_USE_FLASHINFER_SAMPLER=0
ENV PYTHONUNBUFFERED=1
COPY deploy_docker.py /app/deploy.py
EXPOSE 8000 8002
HEALTHCHECK --interval=30s --timeout=10s --start-period=300s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "/app/deploy.py"]
```

---

## Recommended Approach

**Use GitHub Actions (Option B)** - it's free, automatic, and uses zero local resources.

### Quick Setup:

1. Create GitHub repo
2. Add Docker Hub secrets to GitHub
3. Push code with `.github/workflows/docker-build.yml`
4. Watch it build and push automatically

Your image will be at: `yourusername/vllm-dual-a40:latest`

### Then users can pull with:
```bash
docker pull yourusername/vllm-dual-a40:latest
```
