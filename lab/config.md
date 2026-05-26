# Systems
Ubuntu 24 LTS
MacOS 26.x

# Core inference  
ollama (stable, systemd service)  
llama.cpp (compiled with Vulkan backend: cmake -DGGML_VULKAN=ON | Docker container on MacOS)  
python3.11+ with venv / Nix / conda
  
# Training / fine-tuning  
torch (ROCm wheel from pytorch.org/get-started/locally/)  
transformers, peft, bitsandbytes (for QLoRA)  
trl (for SFT, DPO, GRPO trainers)
mlx_lm tools
datasets, accelerate  
  
# Agent orchestration  
langgraph >= 0.2  
langchain-community  
pydantic >= 2.0  
utcp (pip install utcp utcp-http)  
  
# Vector store  
qdrant (Docker image: qdrant/qdrant)  
nomic-embed-text (via Ollama)  
  
# Observability  
opentelemetry-sdk, opentelemetry-exporter-otlp  
prometheus_client  
grafana + loki (Docker Compose stack)  
  
# Security / sandboxing  
docker (rootless mode)
gvisor (runsc runtime)  
firejail (for CLI tool isolation)  
auditd + falco (syscall anomaly detection)
