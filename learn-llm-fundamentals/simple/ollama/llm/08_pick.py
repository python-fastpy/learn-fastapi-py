r"""08 -- PICK: choosing ONE token from the probabilities
======================================================

CONCEPT IN ONE LINE:
  The model gives a probability for every token (07). PICKING is a separate, small step
  that YOU control with settings: always take the top one, or roll a weighted dice.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── [08 pick] ◀── 07 softmax

WHAT HAPPENS -- a real distribution (llama3.2, prompt "Name a color. Answer with one word."):

   from 07 softmax                      settings filter + reshape it            one token
   ┌──────────────────────────┐         ┌──────────────────────────┐
   │ 'Blue'    0.8261         │         │ repeat_penalty           │
   │ 'Red'     0.0649         │         │ top_k        keep top K  │         ┌──────────┐
   │ 'Purple'  0.0596         │  ───▶   │ temperature  sharpen /   │  ───▶   │ 'Purple' │
   │ 'Green'   0.0157         │         │              flatten     │  dice   └──────────┘
   │ 'Yellow'  0.0065         │         │ top_p        keep top P% │  (seed)
   │ (128,251 more)           │         │ min_p        drop tiny   │
   └──────────────────────────┘         └──────────────────────────┘
      the MODEL's output                   the SAMPLER (no weights, plain code in Ollama)

  The model does NOT pick. It only produces the probabilities. The picking is ~20 lines of
  ordinary code -- the same model gives different answers only because of THIS step.

THE SETTINGS, ONE BY ONE (Ollama names, all go inside "options"):

  1. temperature 0  ->  GREEDY: always take the top one       'Blue' every time
     Deterministic: same prompt = same answer (up to tiny GPU/CPU maths noise).

  2. temperature T  ->  reshape the probabilities, then roll the dice
        new_p  =  p ^ (1/T)   then re-normalise so they add up to 1
        (same as dividing the scores by T before softmax, see 07)

        token      T = 0.5      T = 1 (as is)    T = 1.5      T = 2
        'Blue'     0.988        0.836            0.631        0.482
        'Red'      0.006        0.066            0.116        0.135
        'Purple'   0.005        0.060            0.109        0.130
        'Green'    0.000        0.016            0.045        0.067
        (computed by main() from the real top-10 -- see PART 2 of the output)
        T < 1  sharper -> safer, more repetitive
        T > 1  flatter -> more varied, more mistakes (odd pieces like 'Te', 'N' get more chance)

  3. top_k K  ->  keep only the K most likely tokens, throw the rest away
        top_k 1  = greedy again (only 'Blue' survives)       top_k 40 = a common default

  4. top_p P  ->  keep the SMALLEST set of top tokens whose probabilities add up to P
        top_p 0.9:  'Blue' 0.836 + 'Red' 0.066 = 0.902 >= 0.9  ->  keep only Blue, Red
        adapts: a confident model keeps 1-2 tokens, an unsure one keeps many

  5. min_p M  ->  drop tokens less likely than M x (the top token's probability)
        min_p 0.05:  cut-off = 0.05 x 0.836 = 0.042  ->  keep Blue, Red, Purple

  6. seed S  ->  fixes the dice. Same seed + same settings + same prompt = same answer.
        Not a "setting of the model" -- just the starting point of the random number generator.

  7. repeat_penalty R  ->  make tokens that already appeared recently LESS likely
        (looks at the last repeat_last_n tokens; a score s becomes s / R if positive,
         s x R if negative -- illustrative: R 1.1 turns a score of +11.0 into +10.0)

  ORDER: engines apply these in slightly different orders (llama.cpp, for example, applies
  temperature near the END). A common teaching order:
     repeat_penalty -> top_k -> temperature -> top_p -> min_p -> dice
  main() applies each setting ON ITS OWN so you can see what each one does.
  Ollama's documented defaults (Modelfile docs; may change between versions):
     temperature 0.8   top_k 40   top_p 0.9   min_p 0.0   repeat_penalty 1.1   repeat_last_n 64
  /api/show "parameters" for llama3.2 only sets the stop words (11), so those defaults apply.

THE DICE, EXACTLY:
   probabilities after filtering:   Blue 0.836 | Red 0.066 | Purple 0.060 | Green 0.016 |
                                    Yellow 0.007 | Brown, N, Orange, Pink, Te 0.015 together
   lay them end to end on a line from 0 to 1:
      0 ├──────────── Blue ────────────┤ Red ├ Purple ┤ Green, Yellow and the other 5 ┤ 1
                                     0.836  0.902   0.962
   draw a random number r in [0, 1):   r = 0.93  -> lands in Purple -> pick 'Purple'
   Over many draws each token wins about as often as its probability (PART 3 checks this).

WHERE THIS COMES FROM:
   the probabilities     the MODEL (weights trained by Meta) -- 07 softmax
   the settings          YOU (your request) -> or Ollama's defaults if you don't send them
   the sampler code      Ollama's server (built on llama.cpp's sampler) -- not in the GGUF file
   the random numbers    a pseudo-random generator on the server, started from "seed"

IS IT OLLAMA-SPECIFIC?
   The idea is universal; the knobs and their names differ (hedged -- check each API's docs):
   who                 greedy             temperature   top_k   top_p   min_p   seed
   the model itself    -- (it never picks; it only outputs probabilities)
   Ollama              temperature: 0     0 - 2+        yes     yes     yes     yes
   OpenAI              temperature: 0     0 - 2         no      yes     no      yes (best effort)
   Anthropic           temperature: 0     0 - 1         yes     yes     no      no
   Hugging Face        do_sample=False    yes           yes     yes     yes     torch.manual_seed
   (Hugging Face: model.generate(input_ids, do_sample=True, temperature=0.8, top_k=40, top_p=0.9))

COMMON CONFUSIONS:
   - "temperature makes the model smarter/dumber"  -> no, the model's output is identical;
     only the PICK changes. At T 0 you see the model's single most likely answer.
   - "temperature 0 = correct"  -> it's the MOST LIKELY token, which can still be wrong.
   - "seed makes it deterministic everywhere"  -> only with the same model, settings, prompt,
     and (ideally) hardware. Hosted APIs often only promise "best effort".
   - top_k / top_p don't add randomness; they REMOVE options before the dice roll.

SEE IT VISUALLY:
   https://poloclub.github.io/transformer-explainer/   (temperature slider, live probabilities)
"""

import math
import random
import sys

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

COLOR_PROMPT = ("<|start_header_id|>user<|end_header_id|>\n\n"
                "Name a color. Answer with one word.<|eot_id|>"
                "<|start_header_id|>assistant<|end_header_id|>\n\n")


def generate(prompt, **options):
    body = {"model": CHAT_MODEL, "prompt": prompt, "raw": True, "stream": False,
            "logprobs": True, "top_logprobs": 10, "options": options}
    resp = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)
    resp.raise_for_status()
    return resp.json()


def show(dist, title):
    print(title)
    for token, p in dist[:5]:
        print(f"   {token!r:10} {p:.3f}")


def normalise(dist):
    total = sum(p for _, p in dist)
    return [(t, p / total) for t, p in dist]


def temperature(dist, t):
    return normalise([(tok, p ** (1 / t)) for tok, p in dist])     # = scores / t, then softmax


def top_k(dist, k):
    return normalise(dist[:k])                                      # dist is sorted, highest first


def top_p(dist, p_max):
    kept, total = [], 0.0
    for tok, p in dist:
        kept.append((tok, p))
        total += p
        if total >= p_max:
            break
    return normalise(kept)


def min_p(dist, m):
    cut = m * dist[0][1]
    return normalise([(t, p) for t, p in dist if p >= cut])


def roll_dice(dist, rng):
    r, line = rng.random(), 0.0
    for tok, p in dist:
        line += p
        if r < line:
            return tok
    return dist[-1][0]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("PART 1: the REAL distribution from the model (top 10 of 128,256)")
    r = generate(COLOR_PROMPT, temperature=0, num_predict=1)
    real = [(t["token"], math.exp(t["logprob"])) for t in r["logprobs"][0]["top_logprobs"]]
    print("   top 10 add up to", round(sum(p for _, p in real), 4), "-> re-normalised to 1 below")
    dist = normalise(real)
    show(dist, "   as is:")
    # -> PART 1: the REAL distribution from the model (top 10 of 128,256)
    #       top 10 add up to 0.9878 -> re-normalised to 1 below
    #       as is:
    #       'Blue'     0.836
    #       'Red'      0.066
    #       'Purple'   0.060
    #       'Green'    0.016
    #       'Yellow'   0.007

    print("\nPART 2: each setting, applied in Python to that distribution")
    for t in (0.5, 1.5, 2.0):
        show(temperature(dist, t), f"   temperature {t}:")
    show(top_k(dist, 2), "   top_k 2:")
    show(top_p(dist, 0.9), "   top_p 0.9:")
    show(min_p(dist, 0.05), "   min_p 0.05:")
    # ->    temperature 0.5:
    #       'Blue'     0.988
    #       'Red'      0.006
    #       'Purple'   0.005
    #       'Green'    0.000
    #       'Yellow'   0.000
    #       temperature 1.5:
    #       'Blue'     0.631
    #       'Red'      0.116
    #       'Purple'   0.109
    #       'Green'    0.045
    #       'Yellow'   0.025
    #       temperature 2.0:
    #       'Blue'     0.482
    #       'Red'      0.135
    #       'Purple'   0.130
    #       'Green'    0.067
    #       'Yellow'   0.043
    #       top_k 2:
    #       'Blue'     0.927
    #       'Red'      0.073
    #       top_p 0.9:
    #       'Blue'     0.927
    #       'Red'      0.073
    #       min_p 0.05:
    #       'Blue'     0.869
    #       'Red'      0.068
    #       'Purple'   0.063

    print("\nPART 3: roll the dice 1,000 times at temperature 1 -- wins match probabilities")
    rng = random.Random(42)
    counts = {}
    for _ in range(1000):
        tok = roll_dice(dist, rng)
        counts[tok] = counts.get(tok, 0) + 1
    for tok, n in sorted(counts.items(), key=lambda x: -x[1])[:4]:
        print(f"   {tok!r:10} {n:4} / 1000")
    # ->    'Blue'      827 / 1000
    #       'Red'        67 / 1000
    #       'Purple'     60 / 1000
    #       'Green'      20 / 1000

    print("\nPART 4: the same thing LIVE in Ollama")
    print("   temperature 0, 3 runs:   ",
          [generate(COLOR_PROMPT, temperature=0, num_predict=4)["response"] for _ in range(3)])
    print("   temperature 1.5, seeds 1-8:",
          [generate(COLOR_PROMPT, temperature=1.5, seed=s, num_predict=4)["response"] for s in range(1, 9)])
    print("   seed 4, twice:          ",
          [generate(COLOR_PROMPT, temperature=1.5, seed=4, num_predict=4)["response"] for _ in range(2)])
    print("   top_k 1, seeds 1-4:     ",
          [generate(COLOR_PROMPT, temperature=1.5, top_k=1, seed=s, num_predict=4)["response"]
           for s in range(1, 5)])
    # ->    temperature 0, 3 runs:    ['Blue', 'Blue', 'Blue']
    #       temperature 1.5, seeds 1-8: ['Purple.', 'Blue.', 'Blue.', 'Purple', 'Blue.', 'Purple', 'Blue', 'Blue']
    #       seed 4, twice:           ['Purple', 'Purple']
    #       top_k 1, seeds 1-4:      ['Blue', 'Blue', 'Blue', 'Blue']
    #
    # WHAT THIS MEANS:
    #   - temperature 0 never varies: always the 0.826 token.
    #   - at 1.5 'Purple' (only 6% as-is, ~11% after flattening) wins 3 of 8 times.
    #   - a fixed seed repeats the same dice roll -> same answer.
    #   - top_k 1 removes every option but 'Blue', so the dice has nothing to choose from.
    #   - '.' or no '.' after the word is ALSO a pick -- every token goes through this step.


if __name__ == "__main__":
    main()

# Try: the 01b prompt + "Paris" -- '.' 0.67 vs <end> 0.33. Run it at temperature 1 with
#      seeds 1-6 and count how often the answer stops right after 'Paris'.
