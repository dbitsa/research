# MLX LoRA Fine-Tuning Guide
**Platform:** macOS · Apple Silicon (M1–M4)  
**Framework:** [MLX](https://github.com/ml-explore/mlx) + [mlx-lm](https://github.com/ml-explore/mlx-examples/tree/main/llms)  
**Method:** LoRA (Low-Rank Adaptation) — parameter-efficient fine-tuning

---

## Architecture Overview

```
Your Dataset (JSONL)
       │
       ▼
 mlx_lm.lora  ──► Trains small adapter weights (LoRA)
       │             on top of a frozen base model
       ▼
  adapters/        ← Saved adapter checkpoints (~MBs)
       │
       ▼
 mlx_lm.fuse  ──► Merges adapters into full model weights
       │
       ▼
  fused_model/     ← Full fine-tuned model (ready for Ollama)
```

> **Why LoRA?** Instead of updating all model parameters (billions of weights),
> LoRA trains two small low-rank matrices per attention layer. This reduces
> memory and compute by 10–100×, making it feasible on consumer Apple Silicon.

---

## Prerequisites

- Apple Silicon Mac (M1–M4)
- miniforge / conda installed
- Ollama installed (for inference after training)
- Environment set up via `setup_mlx_env.sh`

---

## Step 1 — Activate Environment

```bash
conda activate mlx-train
```

---

## Step 2 — Choose a Base Model

Download a supported model from Hugging Face using `mlx_lm.convert`
(this downloads and converts to MLX format in one step):

```bash
# Example: Mistral 7B Instruct (good general-purpose starting point)
mlx_lm.convert \
  --hf-path mistralai/Mistral-7B-Instruct-v0.3 \
  --mlx-path ./models/mistral-7b-instruct

# Example: Llama 3.2 3B (lighter, faster on 8GB RAM Macs)
mlx_lm.convert \
  --hf-path meta-llama/Llama-3.2-3B-Instruct \
  --mlx-path ./models/llama-3.2-3b

# Example: Gemma 2 2B (very efficient, good quality/size tradeoff)
mlx_lm.convert \
  --hf-path google/gemma-2-2b-it \
  --mlx-path ./models/gemma-2-2b
```

> **Note:** Some models (e.g., Llama) require accepting a license on
> Hugging Face before downloading. Log in first with:
> ```bash
> huggingface-cli login
> ```

### Model Selection by RAM

| Mac RAM | Recommended Model        | Parameters |
|---------|--------------------------|------------|
| 8 GB    | Llama 3.2 3B, Gemma 2 2B | 2–3B       |
| 16 GB   | Mistral 7B, Llama 3.1 8B | 7–8B       |
| 32 GB+  | Llama 3.1 70B (Q4)       | 70B (quant)|

---

## Step 3 — Prepare Your Training Data

MLX-LM expects data in **JSONL format** (one JSON object per line).

### Format A — Instruction tuning (recommended)

```jsonl
{"prompt": "What is photosynthesis?", "completion": "Photosynthesis is the process by which plants convert sunlight into chemical energy..."}
{"prompt": "Summarize this article: ...", "completion": "The article describes..."}
```

### Format B — Chat / conversation format

```jsonl
{"messages": [{"role": "user", "content": "Hello!"}, {"role": "assistant", "content": "Hi there! How can I help?"}]}
```

### Required directory structure

```
data/
  train.jsonl    ← training split  (80–90% of examples)
  valid.jsonl    ← validation split (10–20% of examples)
  test.jsonl     ← optional held-out evaluation set
```

See `prepare_data.py` for a script that splits your raw data automatically.

---

## Step 4 — Run LoRA Fine-Tuning

```bash
mlx_lm.lora \
  --model ./models/mistral-7b-instruct \
  --train \
  --data ./data \
  --batch-size 4 \
  --lora-layers 16 \
  --iters 1000 \
  --steps-per-eval 100 \
  --save-every 200 \
  --adapter-path ./adapters
```

### Key parameters explained

| Parameter         | Default | Notes                                                                 |
|-------------------|---------|-----------------------------------------------------------------------|
| `--batch-size`    | 4       | Reduce to 2 or 1 if you hit memory pressure                          |
| `--lora-layers`   | 16      | Number of transformer layers to apply LoRA to; more = more capacity  |
| `--iters`         | 1000    | Total training iterations; increase for larger datasets              |
| `--learning-rate` | 1e-4    | Default is usually fine; lower (5e-5) for very small datasets        |
| `--lora-rank`     | 8       | Rank of LoRA matrices; 8–16 is typical                               |
| `--grad-checkpoint`| off   | Add `--grad-checkpoint` to trade speed for lower memory use          |

### Monitor training

You will see output like:
```
Iter 100: Train loss 1.842, Val loss 1.651, Tokens/sec 412.3
Iter 200: Train loss 1.623, Val loss 1.489, ...
```

**What to watch:** Validation loss should decrease. If it plateaus or rises
while training loss keeps falling, you are overfitting — stop early.

---

## Step 5 — Evaluate Before Fusing

Test the adapter without permanently merging it:

```bash
mlx_lm.generate \
  --model ./models/mistral-7b-instruct \
  --adapter-path ./adapters \
  --prompt "Your test prompt here" \
  --max-tokens 200
```

---

## Step 6 — Fuse Adapters into a Full Model

Once satisfied with quality, merge the LoRA adapter weights into the base model:

```bash
mlx_lm.fuse \
  --model ./models/mistral-7b-instruct \
  --adapter-path ./adapters \
  --save-path ./fused_model
```

This produces a complete model in `./fused_model/` — ready for conversion
to GGUF for use with Ollama.

---

## Step 7 — Convert to GGUF and Load into Ollama

### Convert to GGUF (requires llama.cpp)

```bash
# Install llama.cpp (if not already present)
brew install llama.cpp

# Convert fused MLX model → GGUF
python $(brew --prefix llama.cpp)/convert_hf_to_gguf.py \
  ./fused_model \
  --outfile ./fused_model/model.gguf \
  --outtype q4_k_m   # Q4 quantization — good quality/size balance
```

### Create an Ollama Modelfile

```bash
cat > Modelfile << 'EOF'
FROM ./fused_model/model.gguf

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"

SYSTEM "You are a helpful assistant fine-tuned for [your use case]."
EOF
```

### Register and run with Ollama

```bash
ollama create my-finetuned-model -f Modelfile
ollama run my-finetuned-model
```

---

## Troubleshooting

**Out of memory during training**
- Reduce `--batch-size` to 2 or 1
- Reduce `--lora-layers` to 8
- Add `--grad-checkpoint` flag
- Use a smaller base model

**Slow training (< 100 tokens/sec on M2+)**
- Confirm MLX is using Metal: `python -c "import mlx.core as mx; print(mx.default_device())"`
- Expected: `Device(gpu, 0)`

**Loss not decreasing**
- Check your JSONL format is correct (no malformed lines)
- Increase `--learning-rate` slightly (try 2e-4)
- Ensure `train.jsonl` has enough variety (minimum ~100 examples)

**Hugging Face 403 / gated model error**
- Run `huggingface-cli login` and accept the model license on hf.co

---

## File Reference

| File                     | Purpose                                    |
|--------------------------|--------------------------------------------|
| `setup_mlx_env.sh`       | One-time environment setup                 |
| `prepare_data.py`        | Converts raw data → train/valid JSONL      |
| `data/train.jsonl`       | Training examples                          |
| `data/valid.jsonl`       | Validation examples                        |
| `adapters/`              | LoRA checkpoint files (output of training) |
| `fused_model/`           | Merged model weights (ready for GGUF conv) |
| `Modelfile`              | Ollama model definition                    |
