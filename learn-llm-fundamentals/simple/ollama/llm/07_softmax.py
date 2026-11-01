r"""07 -- SOFTMAX: from 128,256 scores to probabilities that add up to 1
=====================================================================

CONCEPT IN ONE LINE:
  softmax(score) = e^score / (sum of e^score over all 128,256 tokens) -- every token gets a
  probability between 0 and 1, bigger score = bigger share, and all shares add up to 1.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── [07 softmax]

  IN:   128,256 scores (any number, + or -)                       from 06
  OUT:  128,256 probabilities (0 to 1, sum = 1)                   to 08 (pick one)

WHAT HAPPENS -- THREE STEPS, WORKED ON REAL NUMBERS (01b prompt, top 4 of 128,256):

   token      score*     1. e^score        2. add up          3. divide
   'Paris'      0.00     e^0.00  = 1.0000                       1.0000 / 1.0011 = 0.9988
   'Par'       -7.14     e^-7.14 = 0.00079                      0.00079 / 1.0011 = 0.0008
   'France'    -9.82     e^-9.82 = 0.00005                      ...              = 0.00005
   ' Paris'    -9.82     e^-9.82 = 0.00005                      ...              = 0.00005
   ... 128,252 more tokens, each adding a tiny bit ...
                                   ─────────────
                                   sum ≈ 1.0011               all results add up to 1

   * the real score GAPS (06): Ollama gives logprobs, and only gaps matter -- shifting every
     score by the same amount gives the exact same probabilities.

WHY e^x (and not just "score / total")?

   - e^x is ALWAYS positive -- scores can be negative, probabilities can't
   - a score GAP becomes a RATIO:  e^(a-b) = e^a / e^b
        'Paris' vs 'Par':  gap 7.14  ->  e^7.14 ≈ 1,270x more likely
        every +1 of score  = x2.7 more likely;   +2.3 = x10;   +4.6 = x100;   +6.9 = x1,000
   - so a few points of score difference already mean "almost certain" -- that's why
     'Paris' gets 99.88% while 'Par' is only 7 points behind

LOGPROB = THE LOG OF THE PROBABILITY (what Ollama/OpenAI actually return):

     logprob = log(probability)              probability = e^logprob
     logprob = score - log(sum of e^score)   ("log-sum-exp": the same for every token)

     'Paris'   logprob -0.0012   ->  e^-0.0012 = 0.9988
     'Par'     logprob -7.1457   ->  e^-7.1457 = 0.00079

   Why logs? Tiny probabilities like 0.000000002 become readable numbers (-20.0), and the
   probability of a whole sentence = product of token probabilities = SUM of logprobs.

   logprob  0    = 100% sure         logprob -0.7  ≈ 50%        logprob -2.3 ≈ 10%
   logprob -4.6  ≈ 1%                logprob -6.9  ≈ 0.1%       always <= 0

TEMPERATURE (one line here, the full story in 08_pick.py):
   probability = softmax(score / T) -- it's YOUR setting, applied right here, before the pick.

WHERE THIS COMES FROM:

  what                          who                     where
  the softmax formula           standard maths          the same in every LLM
  the scores it runs on         06 (the model)          inside Ollama
  the logprobs you see          Ollama, after softmax   "logprobs": true, "top_logprobs": N

IS IT OLLAMA-SPECIFIC?

  the model itself   softmax is how every LLM turns scores into probabilities
  Ollama             logprobs + top_logprobs (we use 20)
  OpenAI             logprobs + top_logprobs (Chat Completions, up to 20)
  Anthropic          no logprobs in the API
  Hugging Face       torch.softmax(logits, dim=-1) yourself

COMMON CONFUSIONS:

  - a probability of 0.9988 is not "the model is 99.88% sure it's correct" -- it means
    'Paris' is by far the most likely CONTINUATION of this text. Wrong tokens can get high
    probabilities too (hallucinations).
  - top 20 is not everything: 128,236 more tokens share the rest. Here that rest is tiny
    (~0.0001), which is why the top 20 add up to ~0.9999.

SEE IT VISUALLY:
   https://poloclub.github.io/transformer-explainer/   has a temperature slider on the probs
"""

import math
import sys

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

PROMPT = ("<|start_header_id|>user<|end_header_id|>\n\n"
          "Complete the sentence with one word: The capital of France is<|eot_id|>"
          "<|start_header_id|>assistant<|end_header_id|>\n\n")       # same as 01b STEP 2


def top_logprobs(prompt, n=20):
    body = {"model": CHAT_MODEL, "prompt": prompt, "raw": True, "stream": False,
            "logprobs": True, "top_logprobs": n,
            "options": {"temperature": 0, "num_predict": 1}}
    r = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300).json()
    return [(t["token"] or "<end>", t["logprob"]) for t in r["logprobs"][0]["top_logprobs"]]
    # an empty "token" = a special token Ollama doesn't print; the top one is <|eot_id|> (01b)


def softmax(scores, temperature=1.0):
    scaled = [s / temperature for s in scores]
    top = max(scaled)                                    # subtract the max: same result,
    exps = [math.exp(s - top) for s in scaled]           # but e^x can't overflow
    total = sum(exps)
    return [e / total for e in exps]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("STEP 1: real top-20 for the 01b prompt -- softmax by hand")
    top = top_logprobs(PROMPT)
    scores = [lp - top[0][1] for _, lp in top]           # real score GAPS (06)
    exps = [math.exp(s) for s in scores]
    for (tok, lp), s, e in list(zip(top, scores, exps))[:5]:
        print(f"  {tok!r:10} score {s:7.3f}   e^score {e:.6f}   Ollama's e^logprob {math.exp(lp):.6f}")
    print(f"  sum of e^score over the top 20 = {sum(exps):.6f}")
    print(f"  'Paris' = 1 / {sum(exps):.6f} = {1 / sum(exps):.6f}")
    print(f"  top-20 probabilities from Ollama add up to {sum(math.exp(lp) for _, lp in top):.6f}")
    # -> STEP 1: real top-20 for the 01b prompt -- softmax by hand
    #      'Paris'    score   0.000   e^score 1.000000   Ollama's e^logprob 0.998841
    #      'Par'      score  -7.147   e^score 0.000788   Ollama's e^logprob 0.000787
    #      ' Paris'   score  -9.862   e^score 0.000052   Ollama's e^logprob 0.000052
    #      'France'   score  -9.916   e^score 0.000049   Ollama's e^logprob 0.000049
    #      'par'      score  -9.941   e^score 0.000048   Ollama's e^logprob 0.000048
    #      sum of e^score over the top 20 = 1.001065
    #      'Paris' = 1 / 1.001065 = 0.998936
    #      top-20 probabilities from Ollama add up to 0.999905
    # 0.998936 (top 20 only) vs Ollama's 0.998841 (all 128,256): the other 128,236 tokens
    # together take only ~0.0001 -- so 20 tokens are enough to see the real picture.
    # (the last digits wobble between runs -- GPU maths noise, see 01b)

    print("\nSTEP 2: gaps become ratios")
    gap = scores[0] - scores[1]
    print(f"  'Paris' - 'Par' = {gap:.2f}  ->  e^{gap:.2f} = {math.exp(gap):,.0f}x more likely")
    for g in [1, 2.3, 4.6, 6.9]:
        print(f"  gap {g:>3}  ->  x{math.exp(g):,.1f}")
    # -> STEP 2: gaps become ratios
    #      'Paris' - 'Par' = 7.15  ->  e^7.15 = 1,270x more likely
    #      gap   1  ->  x2.7
    #      gap 2.3  ->  x10.0
    #      gap 4.6  ->  x99.5
    #      gap 6.9  ->  x992.3

    print("\nSTEP 3: a close call -- 01b run 2, after 'Paris': '.' or stop?")
    top2 = top_logprobs(PROMPT + "Paris")
    for (tok, _), p in list(zip(top2, softmax([lp for _, lp in top2])))[:3]:
        print(f"  {tok!r:10} {p:.4f}")
    # -> STEP 3: a close call -- 01b run 2, after 'Paris': '.' or stop?
    #      '.'        0.6879
    #      '<end>'    0.3117      <- a score gap of only ~0.8 -> about 2 : 1
    #      '!'        0.0004
    # 08_pick.py shows how temperature reshapes a distribution like this.


if __name__ == "__main__":
    main()

# Try: STEP 1 with a question that has no single right answer ("Name a color") -- the top
#      probability drops and the next tokens get real shares.
