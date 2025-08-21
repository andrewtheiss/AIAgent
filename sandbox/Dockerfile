FROM nvcr.io/nvidia/cuda:13.0.0-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y wget && \
    install -d -m 0755 /etc/apt/keyrings && \
    wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O- | tee /etc/apt/keyrings/packages.mozilla.org.asc > /dev/null && \
    echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" | tee -a /etc/apt/sources.list.d/mozilla.list > /dev/null && \
    echo '\
Package: *\
Pin: origin packages.mozilla.org\
Pin-Priority: 1000\
\
Package: firefox*\
Pin: release o=Ubuntu\
Pin-Priority: -1\
' | tee /etc/apt/preferences.d/mozilla && \
    apt-get update && \
    apt-get install -y \
    firefox-esr \
    python3-pip \
    libopencv-dev python3-opencv \
    python3-grpcio \
    wine64 \
    x11-apps

RUN pip3 install pywinauto opencv-python grpcio tritonclient[all]

CMD ["bash"]
