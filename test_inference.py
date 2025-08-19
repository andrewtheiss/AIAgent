import os
import sys
import io
import re
import json
import base64
import queue
from functools import partial

import numpy as np
import tritonclient.grpc as grpcclient


class UserData:
    def __init__(self):
        self._completed_requests = queue.Queue()


def completion_callback(user_data, result, error):
    if error:
        user_data._completed_requests.put((None, error))
    else:
        user_data._completed_requests.put((result, None))


def read_image_bytes(image_path):
    with open(image_path, "rb") as f:
        return f.read()


if __name__ == "__main__":
    url = os.environ.get("TRITON_URL", "localhost:8001")

    try:
        client = grpcclient.InferenceServerClient(url=url, verbose=False)
    except Exception as e:
        print("client creation failed: " + str(e))
        sys.exit(1)

    model_name = os.environ.get("TRITON_MODEL", "glm45v.vllm")

    # Resolve path to test.png located next to this script
    base_dir = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    image_path = os.path.join(base_dir, "test.png")
    if not os.path.isfile(image_path):
        print(f"Could not find test.png at {image_path}. Place your image there and rerun.")
        sys.exit(1)

    # Load and base64-encode image WITHOUT a data URI prefix
    image_bytes = read_image_bytes(image_path)
    base64_image = base64.b64encode(image_bytes).decode("utf-8")

    # Optional: print model metadata to verify tensor names
    try:
        metadata = client.get_model_metadata(model_name=model_name)
        input_names = [i.name for i in metadata.inputs]
        output_names = [o.name for o in metadata.outputs]
        print(f"Model {model_name} inputs: {input_names}; outputs: {output_names}")
    except Exception as e:
        print(f"Warning: could not fetch model metadata: {e}")

    def build_inputs(include_image: bool) -> list:
        items = []
        # Prompt
        if include_image:
            prompt = "<image>\nDescribe this image in detail."
        else:
            prompt = "The server's current model does not support images. Reply with a short message acknowledging that limitation."
        text_input_local = grpcclient.InferInput("text_input", [1], "BYTES")
        text_input_local.set_data_from_numpy(np.array([prompt.encode("utf-8")], dtype=object))
        items.append(text_input_local)

        # Image (optional)
        if include_image:
            image_input_local = grpcclient.InferInput("image", [1], "BYTES")
            image_input_local.set_data_from_numpy(np.array([base64_image.encode("utf-8")], dtype=object))
            items.append(image_input_local)

        # Generation params
        sampling_params = {"max_tokens": 256, "temperature": 0.2}
        sampling_input_local = grpcclient.InferInput("sampling_parameters", [1], "BYTES")
        sampling_input_local.set_data_from_numpy(np.array([json.dumps(sampling_params).encode("utf-8")], dtype=object))
        items.append(sampling_input_local)

        # Stream flag (some deployments expect it)
        stream_flag_local = grpcclient.InferInput("stream", [1], "BOOL")
        stream_flag_local.set_data_from_numpy(np.array([True]))
        items.append(stream_flag_local)

        # Optional return flags if supported by the model
        try:
            exclude_in = grpcclient.InferInput("exclude_input_in_output", [1], "BOOL")
            exclude_in.set_data_from_numpy(np.array([True]))
            items.append(exclude_in)
        except Exception:
            pass

        try:
            ret_finish = grpcclient.InferInput("return_finish_reason", [1], "BOOL")
            ret_finish.set_data_from_numpy(np.array([True]))
            items.append(ret_finish)
        except Exception:
            pass

        try:
            ret_num_in = grpcclient.InferInput("return_num_input_tokens", [1], "BOOL")
            ret_num_in.set_data_from_numpy(np.array([True]))
            items.append(ret_num_in)
        except Exception:
            pass

        try:
            ret_num_out = grpcclient.InferInput("return_num_output_tokens", [1], "BOOL")
            ret_num_out.set_data_from_numpy(np.array([True]))
            items.append(ret_num_out)
        except Exception:
            pass

        return items

    def run_once(target_model: str, include_image: bool) -> tuple:
        user_data_local = UserData()
        outputs_local = [
            grpcclient.InferRequestedOutput("text_output"),
            grpcclient.InferRequestedOutput("finish_reason"),
            grpcclient.InferRequestedOutput("num_input_tokens"),
            grpcclient.InferRequestedOutput("num_output_tokens"),
        ]
        try:
            client.start_stream(callback=partial(completion_callback, user_data_local))
            client.async_stream_infer(
                model_name=target_model,
                inputs=build_inputs(include_image),
                outputs=outputs_local,
                request_id="1",
                enable_empty_final_response=True,
            )

            accumulated_output_local = ""
            while True:
                result, error = user_data_local._completed_requests.get()

                if error is not None:
                    return "", str(error)

                if result is None:
                    continue

                output_data = result.as_numpy("text_output")
                if output_data is not None and len(output_data) > 0:
                    try:
                        chunk = output_data[0].decode("utf-8")
                    except Exception:
                        chunk = str(output_data[0])
                    accumulated_output_local += chunk
                    print(chunk, end="", flush=True)

                parameters = result.get_response().parameters
                if "triton_final_response" in parameters:
                    print("\nFinal response received.")
                    break

            if not accumulated_output_local:
                # Try to extract finish reason and token counts for debugging
                try:
                    fr = result.as_numpy("finish_reason")
                    no = result.as_numpy("num_output_tokens")
                    ni = result.as_numpy("num_input_tokens")
                    dbg = f" finish_reason={fr[0] if fr is not None else None}, num_output_tokens={no[0] if no is not None else None}, num_input_tokens={ni[0] if ni is not None else None}"
                    print(dbg)
                except Exception:
                    pass
            return accumulated_output_local, None
        finally:
            try:
                client.stop_stream()
            except Exception:
                pass

    def find_candidate_vlm_models() -> list:
        try:
            idx = client.get_model_repository_index()
        except Exception:
            return []

        names = []
        # Prefer models whose metadata show an image-like input
        for m in getattr(idx, "models", []):
            name = getattr(m, "name", None)
            if not name:
                continue
            try:
                md = client.get_model_metadata(model_name=name)
                in_names = [i.name.lower() for i in getattr(md, "inputs", [])]
                if any(x in in_names for x in ["image", "image_data", "multi_modal_data"]):
                    names.append(name)
            except Exception:
                continue
        return names

    # Try current model with image
    print(f"\nAttempting multimodal inference with model '{model_name}'...")
    output, err = run_once(model_name, include_image=True)
    if err and ("not a multimodal model" in err.lower() or "does not support image" in err.lower()):
        print("Model is text-only. Searching for a vision-capable model in the repository...")
        candidates = find_candidate_vlm_models()
        tried = set()
        for cand in candidates:
            if cand in tried or cand == model_name:
                continue
            print(f"\nTrying candidate vision model '{cand}'...")
            out2, err2 = run_once(cand, include_image=True)
            tried.add(cand)
            if not err2:
                print("\nInferred image description:", out2)
                sys.exit(0)
            else:
                print(f"Candidate '{cand}' failed: {err2}")

        # Fallback to text-only on original model
        print("No working vision model found. Falling back to text-only inference on the current model.")
        out3, err3 = run_once(model_name, include_image=False)
        if err3:
            print(f"Text-only inference also failed: {err3}")
            sys.exit(1)
        print("\nText-only model response:", out3)
        sys.exit(0)
    elif err:
        print(f"Inference failed: {err}")
        sys.exit(1)
    else:
        print("\nInferred image description:", output)