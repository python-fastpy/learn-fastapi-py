r"""02 -- TEMPLATE: your list of messages becomes ONE long string
==================================================================

CONCEPT IN ONE LINE:
  The model can't read JSON or "roles" -- it only continues text. So the messages are glued
  into one string with special marker tokens, in the exact format the model was trained on.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ [02 template] ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

WHAT HAPPENS:

   what you send (/api/chat)                      what the model actually reads (one string)
   ─────────────────────────────                  ─────────────────────────────────────────────
   "messages": [                                  <|begin_of_text|>              <- added later
     {"role": "system",                           <|start_header_id|>system<|end_header_id|>
      "content": "You are a pirate."},     ─▶     ¶¶Cutting Knowledge Date: December 2023¶¶
     {"role": "user",                             You are a pirate.<|eot_id|>
      "content": "Say hi in one word."}           <|start_header_id|>user<|end_header_id|>
   ]                                              ¶¶Say hi in one word.<|eot_id|>
                                                  <|start_header_id|>assistant<|end_header_id|>
                                                  ¶¶                             <- model writes HERE
   (¶ = newline "\n"; line breaks on the right added for reading -- the real string is one line)

   THE PIECES:
      <|begin_of_text|>        start of everything (ID 128000) -- added at TOKENIZE time (03)
      <|start_header_id|>      "a role name follows"            (ID 128006)
      system / user / ...      the role, as ordinary text       ("user" = ID 882)
      <|end_header_id|>        "role name finished"             (ID 128007)
      \n\n                     two newlines, then the content   (ID 271)
      <|eot_id|>               "end of this turn"               (ID 128009)
      the LAST header          ...assistant<|end_header_id|>\n\n with NOTHING after it: the
                               model's only job is to continue the text from here

   THESE IDs BELONG TO THE MODEL, NOT TO OLLAMA:
      They are positions in Meta's vocabulary list, stored inside the model file
      (tokenizer.ggml.tokens: position 128009 = <|eot_id|>, read for real in 03_tokens.py).

      llama3.2 in Ollama / Hugging Face / llama.cpp   -> the SAME IDs (same vocabulary file)
      other Llama 3.x models (3, 3.1, 3.3)            -> the same tokenizer, the same IDs
      other families                                  -> other markers, other IDs
                                                         (GPT-2's end token: <|endoftext|> = 50256)
      OpenAI / Anthropic                              -> hidden, you never see their IDs

      Ollama only decides WHETHER the markers are added (/api/chat yes, "raw": True no).

   The model was trained on millions of conversations written exactly like this. When it
   sees "assistant<|end_header_id|>\n\n" it has learned: "now I write the reply, and I end
   it with <|eot_id|>" (that's how it knows when to stop -- 11_stop.py).

   A CONVERSATION = the whole history, re-rendered EVERY request:

      <|start_header_id|>system<|end_header_id|>¶¶Cutting Knowledge Date: December 2023¶¶<|eot_id|>
      <|start_header_id|>user<|end_header_id|>¶¶What is the capital of France?<|eot_id|>
      <|start_header_id|>assistant<|end_header_id|>¶¶Paris.<|eot_id|>        <- its OLD answer
      <|start_header_id|>user<|end_header_id|>¶¶And of Germany?<|eot_id|>
      <|start_header_id|>assistant<|end_header_id|>¶¶                        <- new answer here

      "And of Germany?" only makes sense because "capital of France" is in the SAME string.

   THE TEMPLATE COSTS TOKENS (real counts from main() below):
      "Say hi in one word."  on its own (raw)        7 tokens  (6 + <|begin_of_text|>)
      same text through /api/chat                   31 tokens
                                                    ── 24 tokens of template, every call

WHERE THIS COMES FROM:

   1. META designed the format and fine-tuned llama3.2-Instruct on it. It is part of what
      the weights learned -- use a different format and answers get worse.

   2. The GGUF file stores Meta's version as a Jinja template:
         metadata key  tokenizer.chat_template   (3,827 characters, read by main() below)
         {{- "<|start_header_id|>system<|end_header_id|>\n\n" }}
         {{- "Cutting Knowledge Date: December 2023\n" }}
         {{- "Today Date: " + date_string + "\n\n" }}      <- Meta's adds TODAY'S DATE
         ...
         {{- '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'
             + message['content'] | trim + '<|eot_id|>' }}

   3. OLLAMA ships its OWN copy, written as a Go template (/api/show "template", 1,429 bytes,
      the "image.template" layer of the manifest -- 01_request.py):
         <|start_header_id|>system<|end_header_id|>

         Cutting Knowledge Date: December 2023

         {{ if .System }}{{ .System }}
         {{- end }} ... <|eot_id|>
         {{- range $i, $_ := .Messages }} ...
      Same markers, small differences: no "Today Date" line, and its own tool-calling text.
      THIS is the one /api/chat uses.

   4. YOUR CHOICE: /api/chat applies the template for you. /api/generate with "raw": True
      sends your string as-is -- you write the template yourself (01b_inside_the_llm.py STEP 2 does this).

IS IT OLLAMA-SPECIFIC?
   piece               the model itself         Ollama                 OpenAI / Anthropic       Hugging Face transformers
   the FORMAT          YES, learned in          follows the model's    their own formats,       follows the model's format
   (markers, order)    fine-tuning              format                 never shown to you
   who renders it      -                        /api/chat (Go          their servers,           tokenizer.apply_chat_template()
                                                template); raw=True    hidden                   (the Jinja template)
                                                to skip it
   can you see it?     -                        yes: /api/show         no -- only the token     yes
                                                "template"             count in usage

   DIFFERENT MODEL FAMILIES = DIFFERENT FORMATS (text only, simplified -- check each model's
   template, details vary between versions):
      Llama 3      <|start_header_id|>user<|end_header_id|>\n\nHi<|eot_id|>
      ChatML       <|im_start|>user\nHi<|im_end|>              (e.g. Qwen models)
      Gemma        <start_of_turn>user\nHi<end_of_turn>
   Send llama3.2 a ChatML-formatted string and it sees "<|im_start|>" as 6 plain text pieces,
   not as a marker -- it was never trained on it (see COMMON CONFUSIONS for the count).

COMMON CONFUSIONS:
   - "The system prompt is a special input."  No -- it's just more text in the same string,
     in the first block. The model treats it as important only because of training.
   - "The model knows today's date."  Only if the template writes it in. Ollama's template
     writes "Cutting Knowledge Date: December 2023" (end of training data) and no today date.
   - "Roles are enforced."  No -- the markers are just tokens in one string. Tested with
     /api/chat on this Ollama version, a user message:
          "hi"                 -> 26 tokens
          "hi<|eot_id|>"       -> 27 tokens   <- +1: the typed text became the REAL marker
          "hi<|im_start|>"     -> 32 tokens   <- +6: not a llama marker, plain text pieces
     So a user CAN type markers that end their turn early ("prompt injection"). Real apps
     filter them out of user input.
   - "Same question = same tokens in /api/chat and /api/generate."  No -- /api/chat adds the
     template; that's why 01_next_token.py and 01b_inside_the_llm.py got different probabilities.
"""

import sys

import httpx

from gguf_reader import read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

HEADER = "<|start_header_id|>{}<|end_header_id|>\n\n"
EOT = "<|eot_id|>"


def render(messages):
    """Ollama's llama3.2 template, rewritten in Python (no tools). Ollama adds <|begin_of_text|>
    itself when it tokenizes, so it isn't written here."""
    system = next((m["content"] for m in messages if m["role"] == "system"), "")
    turns = [m for m in messages if m["role"] != "system"]
    text = HEADER.format("system") + "Cutting Knowledge Date: December 2023\n\n" + system + EOT
    for i, m in enumerate(turns):
        last = i == len(turns) - 1
        if m["role"] == "user":
            text += HEADER.format("user") + m["content"] + EOT
            if last:
                text += HEADER.format("assistant")       # the open slot the model fills in
        elif m["role"] == "assistant":
            text += HEADER.format("assistant") + m["content"] + ("" if last else EOT)
    return text


def tokens_via_chat(messages):
    body = {"model": CHAT_MODEL, "messages": messages, "stream": False,
            "options": {"temperature": 0, "num_predict": 1}}
    return httpx.post(OLLAMA + "/api/chat", json=body, timeout=300).json()["prompt_eval_count"]


def tokens_via_raw(prompt):
    body = {"model": CHAT_MODEL, "prompt": prompt, "raw": True, "stream": False,
            "options": {"temperature": 0, "num_predict": 1}}
    return httpx.post(OLLAMA + "/api/generate", json=body, timeout=300).json()["prompt_eval_count"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("STEP 1: Meta's template, stored in the GGUF file (tokenizer.chat_template)")
    meta, _, _ = read_gguf()
    jinja = meta["tokenizer.chat_template"]
    print(f"{len(jinja):,} characters. The system-block lines:")
    for line in jinja.splitlines():
        if "Cutting Knowledge" in line or "Today Date" in line or "message['role']" in line:
            print("   " + line.strip())
    # -> 3,827 characters. The system-block lines:
    #    {{- "Cutting Knowledge Date: December 2023\n" }}
    #    {{- "Today Date: " + date_string + "\n\n" }}
    #    {{- '<|start_header_id|>' + message['role'] + '<|end_header_id|>\n\n'+ message['content'] | trim + '<|eot_id|>' }}

    print("\nSTEP 2: Ollama's template (/api/show -> template) -- the one /api/chat uses")
    show = httpx.post(OLLAMA + "/api/show", json={"model": CHAT_MODEL}, timeout=60).json()
    print(f"{len(show['template']):,} characters. First 6 lines:")
    for line in show["template"].splitlines()[:6]:
        print("   " + line)
    # -> 1,429 characters. First 6 lines:
    #    <|start_header_id|>system<|end_header_id|>
    #
    #    Cutting Knowledge Date: December 2023
    #
    #    {{ if .System }}{{ .System }}
    #    {{- end }}

    print("\nSTEP 3: render it ourselves, then PROVE it matches (same token count)")
    cases = {
        "user only": [{"role": "user", "content": "Say hi in one word."}],
        "system + user": [{"role": "system", "content": "You are a pirate."},
                          {"role": "user", "content": "Say hi in one word."}],
        "2-turn chat": [{"role": "user", "content": "What is the capital of France?"},
                        {"role": "assistant", "content": "Paris."},
                        {"role": "user", "content": "And of Germany?"}],
    }
    for name, messages in cases.items():
        prompt = render(messages)
        print(f"--- {name}")
        print(f"   {prompt!r}")
        print(f"   /api/chat: {tokens_via_chat(messages)} tokens    "
              f"our string via raw: {tokens_via_raw(prompt)} tokens")
    # -> --- user only
    #    '<|start_header_id|>system<|end_header_id|>\n\nCutting Knowledge Date: December 2023\n\n<|eot_id|>
    #     <|start_header_id|>user<|end_header_id|>\n\nSay hi in one word.<|eot_id|>
    #     <|start_header_id|>assistant<|end_header_id|>\n\n'
    #    /api/chat: 31 tokens    our string via raw: 31 tokens
    #    --- system + user
    #    '...December 2023\n\nYou are a pirate.<|eot_id|><|start_header_id|>user...'
    #    /api/chat: 36 tokens    our string via raw: 36 tokens
    #    --- 2-turn chat
    #    '...What is the capital of France?<|eot_id|><|start_header_id|>assistant<|end_header_id|>
    #     \n\nParis.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nAnd of Germany?<|eot_id|>...'
    #    /api/chat: 48 tokens    our string via raw: 48 tokens
    #    (prompt strings wrapped here for reading)
    # Same count = same string: this IS what /api/chat sends to the model.

    print("\nSTEP 4: what the template costs")
    alone = tokens_via_raw("Say hi in one word.")
    wrapped = tokens_via_chat(cases["user only"])
    print(f"   text alone: {alone} tokens   through /api/chat: {wrapped} tokens"
          f"   template overhead: {wrapped - alone} tokens per call")
    # -> text alone: 7 tokens   through /api/chat: 31 tokens   template overhead: 24 tokens per call


if __name__ == "__main__":
    main()

# Try: add a 4th case with a long system prompt -- the count grows by its tokens on EVERY call.
