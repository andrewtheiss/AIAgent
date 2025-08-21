## Installation: WSL2, Docker Desktop (WSL backend), and NVIDIA Container Toolkit

Follow these steps in order on Windows 10/11 with WSL. Commands are shown in blocks; run them exactly as written.

1) Open an elevated Windows PowerShell (Run as Administrator) and check WSL status:

```
wsl --list --verbose
```

If WSL2 is not installed or a distro shows Version 1, install/upgrade and reboot if prompted:

```
wsl --install
```

2) Enter WSL (Ubuntu by default unless you chose another distro) and complete first-time setup if prompted:

```
wsl
```

Set your Linux username/password if asked. Update the WSL kernel from Windows:

```
wsl --update
```

Verify inside WSL that the kernel is 5.10+:

```
cat /proc/version
```

3) Test GPU visibility inside WSL. In your WSL terminal, install NVIDIA utilities matching your driver series (example uses 580):

```
sudo apt update && sudo apt install -y nvidia-utils-580
```

Then verify:

```
nvidia-smi
```

Expected: Lists all GPUs, with RTX 5090 as GPU0.

4) Install Docker Desktop for Windows with WSL2 backend. Download the installer and run it (check "Use WSL2 instead of Hyper-V"):

- Download: [Docker Desktop](https://www.docker.com/products/docker-desktop)

After installation, open Docker Desktop → Settings → Resources → WSL Integration → enable integration for your distro (e.g., Ubuntu).

Verify from within WSL:

```
docker --version
```

If it fails, restart Docker Desktop (right-click tray icon → Restart or Quit and reopen).

5) Install the NVIDIA Container Toolkit inside WSL and configure Docker to use it. In your WSL terminal, add NVIDIA's apt repository and key, then install:

```
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
```

Configure the Docker runtime for NVIDIA:

```
sudo nvidia-ctk runtime configure --runtime=docker
```

Restart Docker Desktop from Windows (do not use systemctl inside WSL):

- Right-click Docker icon in the system tray → Quit Docker Desktop
- Launch Docker Desktop again from the Start menu and wait for it to be ready

6) Verify GPU access from Docker in WSL by running a CUDA base image on GPU0 only:

```
docker run --rm --gpus 'device=0' nvcr.io/nvidia/cuda:13.0.0-base-ubuntu22.04 nvidia-smi
```

Expected: Output shows only GPU0 (RTX 5090). If you see errors, try:

```
wsl --shutdown
```

Then reopen WSL and restart Docker Desktop, and re-run the test.

Notes
- If any step fails (e.g., driver mismatches), capture the exact error output for troubleshooting.
- This setup uses public downloads only—no signups needed.
- Once verification succeeds, proceed to your next step (e.g., visual output or project-specific setup).


7) Set up visual output with X11 forwarding (VcXsrv on Windows, X11 clients in WSL):

- Download and install VcXsrv for Windows: https://sourceforge.net/projects/vcxsrv/
- Launch XLaunch and choose: "Multiple windows" → Display number 0 → "Start no client" → Finish. Keep VcXsrv running in the background.
- In your WSL terminal, install X11 test tools:

```
sudo apt update && sudo apt install -y x11-apps
```

- Test forwarding from WSL to Windows (a clock should appear on your Windows desktop):

```
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0 && xclock
```

If no window appears, ensure Windows Defender Firewall allows VcXsrv, or restart XLaunch and try again. Stop the clock with Ctrl+C in the terminal.

8) Create and run a single container instance (CUDA + Python + OpenCV + gRPC + Triton client):

- In WSL, create a project directory and enter it:

```
mkdir ai-sandbox && cd ai-sandbox
```

- Create a file named Dockerfile with the following content:

```
FROM nvcr.io/nvidia/cuda:13.0.0-devel-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3-pip \
    libopencv-dev python3-opencv \
    python3-grpcio \
    wine64

RUN pip3 install pywinauto opencv-python grpcio 'tritonclient[all]'

# Entry point for interactive testing
CMD ["bash"]
```

- Build the image:

```
docker build -t ai-sandbox .
```

- Run an interactive container mapped to GPU0 and forward X11 (ensure VcXsrv is running):

```
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0.0
docker run --rm -it --gpus 'device=0' -e DISPLAY=$DISPLAY ai-sandbox
```

Inside the container you will land in a bash shell and can run your workloads. For GUI apps inside the container, confirm that the X clock test from WSL works first and that your firewall allows VcXsrv.

