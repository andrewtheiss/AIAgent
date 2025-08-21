### What We've Done So Far
We've built a foundational single-instance AI agent setup in a Docker container on your Windows 11 host using WSL2, leveraging your NVIDIA GPUs (RTX 5090 as GPU0). This shifted from the original Hyper-V VM plan to containers for lighter overhead and easier scaling, while addressing compatibility (no NVIDIA signups, consumer GPUs). Key steps:

- **Prerequisites and Host Preparation**: Verified hardware/software (NVIDIA driver 580.97, WSL2, Docker Desktop with WSL2 backend, NVIDIA Container Toolkit). Enabled GPU access in containers via `--gpus 'device=0'`.
- **Container Setup**: Created a Dockerfile based on NVIDIA's CUDA 13.0 image (Ubuntu 22.04), installed tools like Firefox-ESR (via Mozilla PPA), Python libs (OpenCV, mss for captures, tritonclient for API, gRPC), xdotool for actions, and VNC/XFCE for isolated GUIs. Built/rebuild image as `ai-sandbox`.
- **Visual and Interaction Isolation**: Started with X11 forwarding (VcXsrv on host) for GUI apps (e.g., Firefox opening on host desktop). Switched to internal VNC (TigerVNC + XFCE desktop) with Xvfb for virtual displays, ensuring clicks/actions (via xdotool) are scoped to each container's window—no host mouse interference. VNC ports mapped (e.g., 5901) for viewing via RealVNC/TigerVNC Viewer.
- **Agent Loop Implementation**: Developed `agent.py` (copied into container): Captures screen (mss/OpenCV), calls a centralized API (mock Triton for bounding boxes), performs actions (clicks at mock coords). Tested loop: Firefox launches in container's desktop, clicks happen internally.
- **Mock Inference Server**: Set up `server.py` on host (in venv) as gRPC mock Triton server (port 8001), returning dummy bounding boxes. Connected from agent.py via `host.docker.internal:8001`.
- **Troubleshooting**: Fixed errors like timezone prompts (ENV vars), VNC session exits (xstartup with dbus-launch/startxfce4), auth (VncAuth config), warnings (added deps like libegl1-mesa, dbus-x11).

The single container now runs an independent AI agent: It starts a GUI (Firefox), captures its screen, "infers" via mock API, and acts (clicks) within its isolated display. You view/control via VNC without affecting the host.

### What We're Planning to Do Next
We'll expand to your long-term goal: Multiple isolated instances hitting a centralized API for bounding box inference (e.g., where to click), with low latency, monitoring, and scaling. Detailed phases (modular, test after each):

- **Phase 4 Completion: Integrate Real Inference (30-60 min)**:
  - Replace mock server with actual Triton Inference Server on host (install via Docker: `docker run --gpus all nvcr.io/nvidia/tritonserver:24.07-py3`).
  - Load a model (e.g., YOLOv8 for bounding boxes or LLaVA/Qwen for vision-language) via TensorRT (NVIDIA-optimized for your GPUs).
  - Update `agent.py` to send actual screenshots (compressed JPEG) via gRPC to Triton, parse responses (JSON boxes), act accordingly.
  - Optimize latency: Region captures (e.g., Firefox window only), FP16 quantization, batching in Triton, MPS/MIG for GPU sharing (RTX 5090 MPS, RTX 6000 MIG).

- **Phase 5: Testing and Scaling (1-2 hours+)**:
  - Test single instance: Run loop on sample task (e.g., click button in Notepad/Firefox via inferred box). Measure latency (<200ms target) with timeit, monitor GPU (nvidia-smi/DCGM).
  - Scale: Run 2+ containers (`docker run -p 5902:5901 ...` for second). Assign GPU slices dynamically (MPS for time-sharing on RTX 5090).
  - Orchestration: Use Docker Compose YAML for multi-container management (dynamic ports, volumes for logs). Intro Kubernetes if needed for advanced (e.g., on-demand spawn).
  - Monitoring: Add Prometheus/Grafana in host/container for metrics (latency, GPU usage, agent progress). Centralized logs (mount /logs volume).
  - Error Handling: Add retries in agent.py for API fails, rollback to mock if Triton issues.

- **General Enhancements**: 
  - Real models: Convert to TensorRT, hot-swap in Triton.
  - Security: API auth tokens if VMs untrusted.
  - Backup/Test: Modular—backup Dockerfile/scripts, test after each phase.

We'll proceed step-by-step, verifying with your feedback (e.g., logs, outputs).

### Overall Goal
The goal is to create a scalable system of AI agents in isolated "sandboxes" (containers) that automate UI tasks: Capture screen (e.g., app window), analyze via centralized API for actionable insights (bounding boxes for clicks), perform actions (e.g., mouse/key inputs), with low-latency loops for real-time performance. Long-term: Run multiple instances concurrently (e.g., 4-8 on your 3 GPUs), dynamically allocate resources (GPU slices via MPS/MIG), monitor progress (e.g., Prometheus dashboards), and orchestrate (e.g., start/stop via scripts/K8s). This supports your original plan: Prerequisites → Partitioning → Sandboxes → Services → Testing/Scaling, but adapted to Docker for stability on Windows 11 with consumer GPUs. End result: Efficient, modular setup for AI-driven automation (e.g., testing UIs, bots), handling fast events/multi-faceted tasks.

### Technology Stack
| Category | Components | Purpose |
|----------|------------|---------|
| **Host Environment** | Windows 11, WSL2, Docker Desktop (WSL2 backend), NVIDIA Driver 580.97 | Base for containers, GPU passthrough. |
| **Containerization** | Docker, NVIDIA Container Toolkit | Isolated instances, GPU access (`--gpus 'device=0'`). |
| **GPU Management** | CUDA 13.0, MPS (RTX 5090), MIG (RTX 6000) | Partitioning/sharing for scaling/inference. |
| **GUI/Visualization** | TigerVNC, XFCE, Xvfb | Isolated virtual desktops, VNC viewing (ports 5901+), scoped actions. |
| **Agent Logic** | Python 3 (agent.py), OpenCV/mss (captures), xdotool (actions), gRPC/tritonclient (API calls) | Capture → Infer → Act loop. |
| **Inference** | Triton Inference Server (mock → real), Models (YOLOv8/LLaVA/Qwen via TensorRT) | Centralized bounding box detection, low-latency API. |
| **Monitoring/Orchestration** | Prometheus/Grafana, Docker Compose (YAML), PowerShell/K8s scripts | Metrics, scaling, on-demand instances. |
| **Other Tools** | Firefox-ESR (test GUI), Wine (Windows app sim if needed), pywinauto (alternative actions) | Testing, compatibility. |

This stack is NVIDIA-optimized, open-source (no signups), and modular for your setup. Ready for next phase? Confirm if VNC now works fully (e.g., XFCE desktop visible, Firefox/clicks inside).

