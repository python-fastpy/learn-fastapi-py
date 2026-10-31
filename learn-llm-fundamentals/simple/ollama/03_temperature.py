"""03 -- Temperature: why the same prompt gives different answers
=================================================================

CONCEPT IN ONE LINE:
  The model gives probabilities; TEMPERATURE decides how adventurous the pick is.
                                                               (details: simple/02)

   probabilities:   " blue" 0.60   " green" 0.25   " purple" 0.10   ...
                          │
         temperature 0 ───┼──▶ always the top one       -> same answer every time
         temperature 1 ───┼──▶ pick by probability      -> some variety
         temperature 2 ───┴──▶ flatter, rare words win  -> creative / random

  seed = fixes the random dice, so a run can be repeated exactly (good for tests).
"""

from ollama_client import ask

PROMPT = "Invent a name for a coffee shop. Reply with the name only."


def main():
    for temp in (0.0, 1.0, 1.8):
        print(f"STEP: temperature {temp}, asked 4 times")
        for i in range(4):
            # a different seed each time = different dice, but temp 0 ignores the dice
            name = ask(PROMPT, options={"temperature": temp, "seed": i, "num_predict": 20})
            print(f"   {i + 1}. {name}")
        print()

    print("STEP: same seed + same temperature = same answer (repeatable)")
    a = ask(PROMPT, options={"temperature": 1.0, "seed": 42, "num_predict": 20})
    b = ask(PROMPT, options={"temperature": 1.0, "seed": 42, "num_predict": 20})
    print(f"   {a!r} == {b!r} -> {a == b}")

    print("\nWHEN TO USE WHAT")
    print("   0.0      extraction, classification, JSON, code   (you want the SAME answer)")
    print("   0.7-1.0  chat, writing                            (natural variety)")
    print("   >1.2     brainstorming only                       (more mistakes too)")


if __name__ == "__main__":
    main()

# Try: add options top_p=0.5 -- it cuts away the unlikely words, so high temperature gets calmer.
