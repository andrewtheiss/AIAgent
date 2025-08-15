import tritonclient.grpc as grpcclient
from PIL import Image
import numpy as np
import io

client = grpcclient.InferenceServerClient("localhost:8001")

# Load a local image from Documents (replace with your file path)
local_path = r"C:\Users\andre\Documents\Git\AIAgent\test.png" 
image = Image.open(local_path)

buf = io.BytesIO()
image.save(buf, format="PNG")
image_bytes = buf.getvalue()
prompt = "<image>Describe this screenshot and suggest a click position."

inputs = [
    grpcclient.InferInput("text_input", [1], "BYTES").set_data_from_numpy(np.array([prompt.encode()], dtype=object)),
    grpcclient.InferInput("image_input", [len(image_bytes)], "UINT8").set_data_from_numpy(np.frombuffer(image_bytes, dtype=np.uint8))
]
outputs = [grpcclient.InferRequestedOutput("text_output")]

results = client.infer(model_name="glm45v.vllm", inputs=inputs, outputs=outputs)
feedback = results.as_numpy("text_output")[0].decode()
print(f"Feedback: {feedback}")