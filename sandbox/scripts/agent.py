import cv2
import numpy as np
import mss
import grpc
from tritonclient.grpc import InferenceServerClient
import subprocess
import time

def capture_screen():
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Main display
        img = sct.grab(monitor)
        img = np.array(img)  # Convert to numpy array
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)  # Convert to RGB
        return img

def mock_inference(image):
    # Placeholder: Simulates API call to Triton for bounding boxes
    # Later, replace with real gRPC call to Triton on host
    return [{"label": "button", "coords": [100, 100, 150, 150], "confidence": 0.95}]

def perform_action(box):
    # Simulate click at center of first bounding box using xdotool
    x, y = (box["coords"][0] + box["coords"][2]) // 2, (box["coords"][1] + box["coords"][3]) // 2
    subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
    print(f"Clicked at ({x}, {y})")

def main():
    # Start Firefox for testing
    subprocess.Popen(["firefox-esr", "--no-sandbox"])
    time.sleep(2)  # Wait for Firefox to open
    
    while True:
        # Capture → Infer → Act loop
        img = capture_screen()
        boxes = mock_inference(img)
        if boxes:
            perform_action(boxes[0])  # Act on first box
        time.sleep(1)  # Control loop speed

if __name__ == "__main__":
    main()
