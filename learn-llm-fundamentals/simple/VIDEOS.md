# Videos and visual tools for each lesson

Watch the video, then run the lesson. The video gives you the picture, and the lesson shows
the same idea in small code you can change.

All links were checked on 2026-10-31. Lengths are approximate.

**Everything here is free.** No sign-up, no credit card, no API key needed to watch or read.

- **Practise with a real model for free:** install [Ollama](https://ollama.com). It runs open models
  (Llama, Gemma, Qwen) on your own PC, so you pay nothing per call. When a video's code uses
  a paid API (OpenAI, Anthropic), send the same request to your local Ollama model instead.
- **Watch, don't pay:** some courses below also have paid certificates. You never need them.

## Start here: the big picture (watch first)

| Video | Length | Why watch it |
|-------|--------|--------------|
| [Large Language Models explained briefly](https://www.youtube.com/watch?v=LPZh9BOjkQs) (3Blue1Brown) | ~8 min | The fastest clear picture of what an LLM is |
| [Intro to Large Language Models](https://www.youtube.com/watch?v=zjkBMFhNj_g) (Andrej Karpathy) | ~1 h | Training vs using, what the model "knows", where it fails |
| [Deep Dive into LLMs like ChatGPT](https://www.youtube.com/watch?v=7xTGNNLPyMI) (Andrej Karpathy) | ~3.5 h | The whole story: data → tokens → training → chat model → reasoning. Watch in parts |

## Video for each lesson

| Lesson | Watch | Notes |
|--------|-------|-------|
| **01** what is an LLM | [The spelled-out intro to language modeling: building makemore](https://www.youtube.com/watch?v=PaCmpygFfXo) (Karpathy) | His first model is the **same bigram word-counter as lesson 01**. Then he trains it with a neural net instead of counting |
| **01b_extra** bytes | First 20 min of [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) | Unicode and UTF-8 explained |
| **01b** tokens | [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) (Karpathy) | The full version of lesson 01b: BPE, merges, special tokens. **Tool:** paste text into [Tiktokenizer](https://tiktokenizer.vercel.app) to see real token pieces and ids |
| **02** sampling | [Transformer Explainer](https://poloclub.github.io/transformer-explainer/) (interactive, in browser) | Move the **temperature slider** and watch the probabilities change, the same as lesson 02 STEP 1 |
| **03–06** API, context, prompts, production | [How I use LLMs](https://www.youtube.com/watch?v=EWvNQjAaOHw) (Karpathy) | Context windows, new chats, tools, from a user's view. **Free reading:** [Anthropic prompt engineering tutorial](https://github.com/anthropics/prompt-eng-interactive-tutorial). Read the lessons on GitHub; running its notebooks needs a paid key, so try the prompts on Ollama instead |
| **07–08** tool calling | [Local tool calling with Ollama](https://www.ibm.com/think/tutorials/local-tool-calling-ollama-granite) (IBM, free written tutorial) | The same tool loop as lesson 07, running on a free local model. No API key |
| **09** agents | [Building more effective AI agents](https://www.youtube.com/watch?v=uhJJgc-0iTQ) (Anthropic) | From the authors of the free guide [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents). Main idea: use the simplest thing that works |
| **10** RAG | [Learn RAG From Scratch](https://www.youtube.com/watch?v=sVcwVQRHIc8) (freeCodeCamp, ~2.5 h) + [code](https://github.com/langchain-ai/rag-from-scratch) | Indexing → retrieval → generation, then advanced methods. Watch the first ~30 min for lesson 10. The code uses the OpenAI API; use Ollama to run it for free |
| **11** evals | [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/) (Hamel Husain, free article) + [Evals FAQ](https://hamel.dev/blog/posts/evals-faq/) | How a real team got unstuck by writing tests for its LLM app, like lesson 11 STEP 1 |
| **12** transformer | 3Blue1Brown: [Ch 5 Transformers](https://www.youtube.com/watch?v=wjZofJX0v4M) (~27 min), [Ch 6 Attention](https://www.youtube.com/watch?v=eMlx5fFNoYc) (~26 min), [Ch 7 How LLMs store facts](https://www.youtube.com/watch?v=9-Jl0dxWQs8) (~23 min) | Ch 6 is the visual version of lesson 12's attention grid. **Tools:** [LLM Visualization 3D](https://bbycroft.net/llm) (fly through every layer), [Transformer Explainer](https://poloclub.github.io/transformer-explainer/) |
| **13–14** reasoning, fine-tuning | [Deep Dive into LLMs](https://www.youtube.com/watch?v=7xTGNNLPyMI): the post-training parts. Also [State of GPT](https://www.youtube.com/watch?v=bZQun8Y4L2A) (Karpathy, Microsoft Build, ~42 min) | Pretraining → fine-tuning (SFT) → RLHF → thinking models. **Hands-on, free:** the [Hugging Face LLM course](https://huggingface.co/learn/llm-course) has fine-tuning chapters that run on a free Google Colab GPU |
| **15–17** local models, deploy | [Ollama](https://ollama.com) (free) + the [IBM Ollama tutorial](https://www.ibm.com/think/tutorials/local-tool-calling-ollama-granite) | Install Ollama, run `ollama run llama3.2`, then follow the lesson's "HOW TO DO IT FOR REAL" block. All free, on your own PC |

## If you want to BUILD models (the path from earlier)

Watch these in order and **type the code yourself**:

1. [But what is a neural network?](https://www.youtube.com/watch?v=aircAruvnKk) (3Blue1Brown, ~19 min): the intuition first
2. [Building micrograd](https://www.youtube.com/watch?v=VMj-3S1tku0) (Karpathy, ~2.5 h): backpropagation from zero
3. [Building makemore](https://www.youtube.com/watch?v=PaCmpygFfXo) (Karpathy, ~2 h): lesson 01, but learned
4. [Let's build GPT: from scratch, in code](https://www.youtube.com/watch?v=kCc8FmEb1nY) (Karpathy, ~2 h): a real transformer, lesson 12 for real
5. [Let's build the GPT Tokenizer](https://www.youtube.com/watch?v=zduSFxRajkE) (Karpathy, ~2 h): lesson 01b for real
6. [Let's reproduce GPT-2 (124M)](https://www.youtube.com/watch?v=l8pRSuU81PU) (Karpathy, ~4 h): training at real scale on a GPU

## A simple weekly plan

| Week | Watch | Then run |
|------|-------|----------|
| 1 | LLMs explained briefly + Intro to LLMs | `01`, `01b_extra`, `01b` |
| 2 | Tokenizer video (first hour) + Transformer Explainer | `01b`, `02`, `03` |
| 3 | How I use LLMs + Anthropic prompt tutorial (read) + install Ollama | `04`, `05`, `06` |
| 4 | IBM Ollama tool-calling tutorial + agents video | `07`, `08`, `09` |
| 5 | RAG From Scratch (first 30 min) + Hamel's evals article | `10`, `11` |
| 6 | 3Blue1Brown Ch 5–7 + LLM Visualization 3D | `12`, `13` |
| 7+ | Deep Dive (post-training) + State of GPT | `14`–`17` |
