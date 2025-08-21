export CUDA_VISIBLE_DEVICES=1 && export SGLANG_VLM_CACHE_SIZE_MB=2048 && python3 -m sglang.launch_server --model-path zai-org/GLM-4.5V-FP8 --tp-size 1 --host 0.0.0.0 --port 8000 --served-model-name glm-4.5v --tool-call-parser glm45 --reasoning-parser glm45 --attention-backend flashinfer --mm-attention-backend fa3 --enable-multimodal --mem-fraction-static 0.9 --kv-cache-dtype fp8_e5m2 --max-total-tokens 8192 --max-prefill-tokens 4096  


# Testable
--cpu-offload-gb 40
