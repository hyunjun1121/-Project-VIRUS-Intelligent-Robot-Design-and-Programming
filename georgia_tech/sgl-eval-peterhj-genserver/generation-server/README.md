# sgl-eval generation-server

## Usage

Export env vars `DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, etc.,
then run:

```bash
python -m eval_next_generation_server.main [--host=<address>] [--port=<port>] [--max-workers=<max workers>]
```

By default the generation server will listen at http://127.0.0.1:10000

Example models query:

```bash
curl 'http://127.0.0.1:10000/v1/models'
```

Example chat completion query:

```bash
curl 'http://127.0.0.1:10000/v1/chat/completions' -X POST -H 'Content-Type: application/json' -d '{"model":"deepseek-ai/DeepSeek-V3-0324","messages":[{"role":"user","content":"hi"}]}'
```

## Model paths

Defined in eval_next_generation_server.api_registry:

### Anthropic

- anthropic/claude-4-sonnet-thinking-off
- anthropic/claude-4-sonnet-thinking-on-10k
- anthropic/claude-4-opus-thinking-off
- anthropic/claude-4-opus-thinking-on-10k

### DeepSeek

- [deepseek-ai/DeepSeek-V3-0324](https://huggingface.co/deepseek-ai/DeepSeek-V3-0324)
- [deepseek-ai/DeepSeek-R1-0528](https://huggingface.co/deepseek-ai/DeepSeek-R1-0528)

### Google DeepMind

- google/gemini-2.5-flash-thinking-off
- google/gemini-2.5-flash-thinking-on
- google/gemini-2.5-pro-thinking-off
- google/gemini-2.5-pro-thinking-on

### OpenAI

- openai/gpt-4o-mini
  - alias: gpt-4o-mini
- openai/gpt-4o-20240806
  - alias: gpt-4o-20240806
- openai/gpt-4.1-nano
- openai/gpt-4.1-mini
- openai/gpt-4.1
  - alias: gpt-4.1
- openai/o3-high
  - alias: o3-high
- openai/o4-mini-high
  - alias: o4-mini-high
- openai/gpt-5

### Together.ai

- togetherai/moonshotai/Kimi-K2-Instruct
- togetherai/Qwen/Qwen3-235B-A22B-FP8
- togetherai/Qwen/Qwen3-235B-A22B-Instruct-2507-FP8
- togetherai/Qwen/Qwen3-235B-A22B-Thinking-2507-FP8
- togetherai/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8

### xAI

- xai/grok-4
  - alias: grok-4
