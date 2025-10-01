#!/usr/bin/env python3
"""Docker-based vLLM Deployment for Dual A40 GPUs"""
import subprocess, time, os, requests, sys, signal

# Configuration from environment variables
API_KEY = os.getenv("API_KEY", "qiCwgirvWt4XCA4S2jekdTJruXXmb08K")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-4B")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
EMBEDDING_PORT = int(os.getenv("EMBEDDING_PORT", "8002"))
LLM_PORT = int(os.getenv("LLM_PORT", "8000"))

# Process tracking for graceful shutdown
processes = []

def signal_handler(sig, frame):
    """Handle graceful shutdown on Ctrl+C or SIGTERM"""
    print("\n\nShutting down gracefully...")
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=10)
        except:
            proc.kill()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def print_banner():
    print("\n" + "="*70)
    print(" DUAL A40 DOCKER DEPLOYMENT")
    print("="*70)
    print(f" Embedding: {EMBEDDING_MODEL.split('/')[-1]} (Port {EMBEDDING_PORT})")
    print(f" LLM: {LLM_MODEL.split('/')[-1]} (Port {LLM_PORT})")
    print(f" Context: 32K tokens (YaRN RoPE scaling)")
    print("="*70)

def check_gpu():
    """Verify GPU availability"""
    result = subprocess.run("nvidia-smi --list-gpus", 
                          shell=True, capture_output=True)
    if result.returncode != 0:
        print("ERROR: No NVIDIA GPU detected")
        return 0
    
    gpu_count = len(result.stdout.decode().strip().split('\n'))
    print(f"✓ Detected {gpu_count} GPU(s)")
    return gpu_count

def start_embedding_server(gpu_count):
    """Start embedding model on GPU 0"""
    print("\n[1/2] Starting embedding server on GPU 0...")
    
    memory_util = "0.45" if gpu_count == 1 else "0.90"
    
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", EMBEDDING_MODEL,
        "--host", "0.0.0.0",
        "--port", str(EMBEDDING_PORT),
        "--api-key", API_KEY,
        "--served-model-name", "qwen3-embedding",
        "--enforce-eager",
        "--gpu-memory-utilization", memory_util,
        "--max-model-len", "8192",
        "--max-num-seqs", "32",
        "--disable-custom-all-reduce"
    ]
    
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "0"  # Use GPU 0
    
    proc = subprocess.Popen(cmd, env=env, 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT)
    processes.append(proc)
    print(f" Embedding server started (PID: {proc.pid})")
    return proc

def start_llm_server(gpu_count):
    """Start LLM on GPU 1 with 32K context"""
    print("\n[2/2] Starting LLM server on GPU 1...")
    
    memory_util = "0.45" if gpu_count == 1 else "0.90"
    gpu_id = "0" if gpu_count < 2 else "1"
    
    # Model has built-in YaRN RoPE (factor=32.0, max=131K)
    # Just set max_model_len to control context
    max_model_len = 32768  # Change to 65536 or 131072 if needed
    
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", LLM_MODEL,
        "--host", "0.0.0.0",
        "--port", str(LLM_PORT),
        "--api-key", API_KEY,
        "--served-model-name", "gpt-oss-20b",
        "--enforce-eager",
        "--gpu-memory-utilization", memory_util,
        "--max-model-len", str(max_model_len),
        "--max-num-seqs", "16",
        "--disable-custom-all-reduce"
    ]
    
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = gpu_id  # Use GPU 1
    
    proc = subprocess.Popen(cmd, env=env,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    processes.append(proc)
    print(f" LLM server started (PID: {proc.pid})")
    return proc

def wait_for_server(port, name, max_wait=300):
    """Wait for server to be ready"""
    print(f" Waiting for {name} to initialize...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:{port}/health", 
                                  timeout=3)
            if response.status_code == 200:
                elapsed = int(time.time() - start_time)
                print(f" ✓ {name} ready ({elapsed}s)")
                return True
        except:
            pass
        
        elapsed = int(time.time() - start_time)
        if elapsed % 30 == 0 and elapsed > 0:
            print(f" Initializing... ({elapsed}s elapsed)")
        time.sleep(5)
    
    print(f" ✗ {name} failed to start")
    return False

def test_apis():
    """Test both APIs"""
    print("\n" + "="*70)
    print(" TESTING APIs")
    print("="*70)
    
    # Test embedding
    print("\n■ Embedding API:")
    try:
        r = requests.post(
            f"http://localhost:{EMBEDDING_PORT}/v1/embeddings",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={"model": "qwen3-embedding", "input": ["test"]},
            timeout=15
        )
        if r.status_code == 200:
            print(f" ✓ ONLINE - Port {EMBEDDING_PORT}")
        else:
            print(f" ■ Status: {r.status_code}")
    except Exception as e:
        print(f" ✗ Error: {str(e)}")
    
    # Test LLM
    print("\n■ LLM API:")
    try:
        r = requests.post(
            f"http://localhost:{LLM_PORT}/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "gpt-oss-20b",
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            },
            timeout=15
        )
        if r.status_code == 200:
            print(f" ✓ ONLINE - Port {LLM_PORT}")
            print(f" Context: 32K tokens")
        else:
            print(f" ■ Status: {r.status_code}")
    except Exception as e:
        print(f" ✗ Error: {str(e)}")
    
    print("\n" + "="*70)
    print("■ Deployment complete! Press Ctrl+C to stop.")
    print("="*70)

def main():
    print_banner()
    
    # Check GPUs
    gpu_count = check_gpu()
    if gpu_count == 0:
        sys.exit(1)
    
    # Start embedding server
    embedding_proc = start_embedding_server(gpu_count)
    
    # Wait if sharing single GPU
    if gpu_count == 1:
        print("\n (Sharing GPU - waiting 30s...)")
        time.sleep(30)
    
    # Start LLM server
    llm_proc = start_llm_server(gpu_count)
    
    # Wait for servers
    embedding_ready = wait_for_server(EMBEDDING_PORT, "Embedding", 300)
    llm_ready = wait_for_server(LLM_PORT, "LLM", 300)
    
    if not embedding_ready or not llm_ready:
        print("\n✗ Server startup failed")
        sys.exit(1)
    
    # Test APIs
    test_apis()
    
    # Keep running and monitor
    print("\nMonitoring services (Ctrl+C to stop)...")
    try:
        while True:
            for proc in processes:
                if proc.poll() is not None:
                    print(f"\n■ Process {proc.pid} died!")
                    sys.exit(1)
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nReceived shutdown signal")
        signal_handler(None, None)

if __name__ == "__main__":
    main()
