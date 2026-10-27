# /// script
# requires-python = ">=3.11"
# dependencies = ["transformers>=4.45", "torch", "accelerate"]
# ///
"""Lesson 15b -- Run a cloned Hugging Face model with transformers (PATH B)
==========================================================================

The hands-on half of lesson 15 part 5: load the weights you cloned and
generate text, watching every step from earlier lessons happen for real.

    model folder (cloned)
        │  AutoTokenizer        tokenizer.json            (lesson 01)
        ▼
    chat messages ──apply_chat_template──▶ one token stream  (lesson 03)
        │  AutoModelForCausalLM model.safetensors + config (lesson 12)
        ▼
    model.generate(temperature, top_p, max_new_tokens)    (lesson 02)
        │
        ▼
    decode new tokens ──▶ text                  + tokens/sec on YOUR CPU

The `# /// script` block at the top tells uv which packages to install
into a throwaway environment, so this doesn't touch the lesson project.
First run downloads torch + transformers (~1 GB).

Level: ADVANCED
Clone first (see lesson 15 part 5), then:
Run:  uv run advanced/15b_run_with_transformers.py             (from learn-llm-fundamentals)
      uv run advanced/15b_run_with_transformers.py --model-dir path\\to\\model --prompt "Hi"
      uv run advanced/15b_run_with_transformers.py --model-dir Qwen/Qwen2.5-0.5B-Instruct  (download on the fly)
"""

import argparse
import time
from pathlib import Path

DEFAULT_DIR = Path(__file__).parent / "models" / "Qwen2.5-0.5B-Instruct"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default=str(DEFAULT_DIR),
                    help="local folder from git clone / hf download, or a Hub repo id")
    ap.add_argument("--prompt", default="In one sentence, what is a token in an LLM?")
    ap.add_argument("--max-new-tokens", type=int, default=80)
    args = ap.parse_args()

    if not Path(args.model_dir).exists() and "/" not in args.model_dir:
        raise SystemExit(f"No model at {args.model_dir}. Clone one first (lesson 15, part 5).")

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    t0 = time.perf_counter()
    tok = AutoTokenizer.from_pretrained(args.model_dir)
    model = AutoModelForCausalLM.from_pretrained(args.model_dir, torch_dtype="auto")
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    print(f"loaded in {time.perf_counter() - t0:.1f}s: {n_params / 1e9:.2f}B params, "
          f"dtype {next(model.parameters()).dtype}, device {next(model.parameters()).device}")

    # 1) tokens -- lesson 01
    ids = tok.encode("Tokenization is not splitting on spaces.")
    print("\ntokens:", [tok.decode([i]) for i in ids])

    # 2) chat template -- lesson 03: messages become ONE token stream
    messages = [{"role": "system", "content": "You are concise."},
                {"role": "user", "content": args.prompt}]
    text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    print("\nwhat the model actually sees:\n" + text)

    # 3) next-token probabilities -- lesson 01/02, from the real model
    inputs = tok(text, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1]
    probs = torch.softmax(logits, dim=-1)
    top = torch.topk(probs, 5)
    print("top-5 next tokens:", [(tok.decode([i]), round(p.item(), 3)) for p, i in zip(top.values, top.indices)])

    # 4) generate -- lesson 02's knobs, then measure speed
    t0 = time.perf_counter()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                             do_sample=True, temperature=0.3, top_p=0.9)
    dt = time.perf_counter() - t0
    new = out[0, inputs["input_ids"].shape[1]:]
    print("\nanswer:", tok.decode(new, skip_special_tokens=True).strip())
    print(f"{len(new)} new tokens in {dt:.1f}s = {len(new) / dt:.1f} tokens/sec on this machine")


if __name__ == "__main__":
    main()
