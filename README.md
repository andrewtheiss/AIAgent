# ComputerAgent: AI-Driven Automation Sandboxes

## Overview
This repository provides a reference architecture for transforming a multi-GPU Windows workstation (e.g., Threadripper with NVIDIA RTX GPUs) into a scalable cluster of AI-controlled, "visible" automation environments. Powered by open-source LLMs (e.g., Qwen, LLaVA), it enables AI agents to analyze screenshots, decide actions (e.g., clicks), and interact with graphical instances in real-time. Ideal for tasks like UI automation, testing, or agentic workflows.

Key features:
- **Visible Instances**: Real-time desktop streaming for monitoring AI actions.
- **Modular AI**: Hot-swappable models for screen digestion and policy decisions.
- **Reliable Interactions**: Metadata-driven clicks with vision fallbacks.
- **GPU Efficiency**: On-demand partitioning and scaling for multiple instances.

## Purpose
Build a system where AI agents control isolated Windows sandboxes via GPU-accelerated vision and actions, supporting requirements like model updates, screenshot-based navigation, and dynamic resource allocation.

## Technologies Used
- **Hypervisor**: Microsoft Hyper-V with GPU Partitioning (GPU-P) on Windows Server 2025 or Windows 11 for native Windows VMs and GPU slicing.
- **Screen Capture**: Windows Graphics Capture (WGC) or NVIDIA NvFBC for low-latency, GPU-friendly frames via gRPC.
- **Model Serving**: NVIDIA Triton Inference Server for deploying and hot-reloading open-source LLMs/VLMs (e.g., via TensorRT-LLM or vLLM backends).
- **Actions**: pywinauto (UIA backend) for reliable clicks/keys; fallbacks like SikuliX for vision-based.
- **Scaling**: Optional Kubernetes with NVIDIA GPU Operator, DCGM/Prometheus for metrics, and KEDA for on-demand provisioning.
- **Visibility**: Parsec or RDP for streaming desktops.

## Getting Started
1. Follow the setup roadmap in `docs/roadmap.md` (or equivalent) for installation.
2. Partition GPUs and create VMs.
3. Deploy models and test AI loops.

Contributions welcome! See issues for known trade-offs (e.g., licensing, latency mitigation).


# Start
We need to make a cache folder for Hugging Face
New-Item -ItemType Directory -Force -Path C:\Users\andre\hf-cache | Out-Null

Start a long-lived, interactive dev container (no server yet)
docker run --gpus "device=1" -it -p 8010:8000 -v C:\Users\andre\hf-cache:/root/.cache/huggingface --name glm-dev --ipc=host -e CUDA_DEVICE_ORDER=PCI_BUS_ID -e CUDA_VISIBLE_DEVICES=1 -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True --entrypoint bash vllm/vllm-openai:latest

# Verify CUDA Device:
python3 -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.device_count()); print(torch.cuda.get_device_name(0))"

# Remote in box
docker exec -it glm-dev bash