#!/bin/bash
# Build and Push to Docker Hub (Space-Efficient)

set -e

echo "======================================"
echo "Docker Build & Push (Low Memory Mode)"
echo "======================================"

# Configuration
read -p "Enter your Docker Hub username: " DOCKER_USERNAME
read -p "Enter your image name [vllm-dual-a40]: " IMAGE_NAME
IMAGE_NAME=${IMAGE_NAME:-vllm-dual-a40}
FULL_IMAGE="${DOCKER_USERNAME}/${IMAGE_NAME}"

echo ""
echo "Will build and push: ${FULL_IMAGE}:latest"
echo ""

# Clean up first
echo "[1/5] Cleaning Docker cache..."
docker system prune -af --volumes || true
df -h | grep -E 'Filesystem|/$'

# Login to Docker Hub
echo ""
echo "[2/5] Logging in to Docker Hub..."
docker login

# Use buildx with no-cache and push directly
echo ""
echo "[3/5] Setting up buildx..."
docker buildx create --use --name space-saver 2>/dev/null || docker buildx use space-saver

# Build and push in one step (doesn't store locally)
echo ""
echo "[4/5] Building and pushing (this will take 10-20 minutes)..."
docker buildx build \
  --platform linux/amd64 \
  --tag ${FULL_IMAGE}:latest \
  --tag ${FULL_IMAGE}:$(date +%Y%m%d) \
  --push \
  --no-cache \
  --progress=plain \
  .

# Final cleanup
echo ""
echo "[5/5] Final cleanup..."
docker buildx rm space-saver || true
docker system prune -af

echo ""
echo "======================================"
echo "✓ Successfully pushed to Docker Hub!"
echo "======================================"
echo ""
echo "Your image is available at:"
echo "  ${FULL_IMAGE}:latest"
echo ""
echo "To pull and use:"
echo "  docker pull ${FULL_IMAGE}:latest"
echo ""
