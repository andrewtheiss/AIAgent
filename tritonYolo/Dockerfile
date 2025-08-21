# Stage 1: The Builder - Convert PyTorch model to ONNX
# We use a PyTorch container because it has all the necessary Python libraries.
FROM nvcr.io/nvidia/pytorch:24.07-py3 AS builder

# --- FIX: Upgrade pip and numpy BEFORE installing other packages ---
# This prevents version conflicts with pre-installed libraries in the base image.
RUN pip install --upgrade pip numpy

# Install the ultralytics library for YOLO
RUN pip install ultralytics

# Set a working directory
WORKDIR /build

# Run the export command. This will now run with a clean NumPy installation.
RUN yolo export model=yolov8s.pt format=onnx imgsz=640 opset=11


# Stage 2: The Converter - Convert ONNX to a highly optimized TensorRT engine
# We use a TensorRT container which has the 'trtexec' tool needed for conversion.
FROM nvcr.io/nvidia/tensorrt:24.07-py3 AS converter

WORKDIR /build

# Copy the ONNX model from the previous builder stage
COPY --from=builder /build/yolov8s.onnx .

# Run the conversion. This creates a 'model.plan' file optimized for the GPU
# available at build time. It's best to build this on the target GPU machine.
# We enable FP16 for a significant performance boost.
RUN /usr/src/tensorrt/bin/trtexec --onnx=yolov8s.onnx --saveEngine=model.plan --fp16


# Stage 3: The Final Image - A clean Triton Server
# We start from the official Triton container, which is optimized for serving.
FROM nvcr.io/nvidia/tritonserver:24.07-py3

# Set up the model repository structure required by Triton
RUN mkdir -p /models/yolov8/1

# Copy the model configuration file into the model's directory
COPY config.pbtxt /models/yolov8/

# Copy the final, optimized TensorRT engine from the converter stage
COPY --from=converter /build/model.plan /models/yolov8/1/

# Expose Triton's standard ports
# HTTP port
EXPOSE 8000
# gRPC port
EXPOSE 8001
# Metrics port
EXPOSE 8002

# Set the command to start the Triton server when the container runs
CMD ["tritonserver", "--model-repository=/models"]
