# Locked Community Benchmark models (ART)

Frozen from `kaggle b t models` on 2026-09-24 after `kaggle b init -y`.
Use **only** these bare canonical slugs for all `kaggle b t run -m …` commands.

| Slug | Tier | Role in matrix |
| --- | --- | --- |
| `gemini-3.5-flash` | flash | Primary fast Gemini |
| `gemini-2.5-pro` | heavy | Strong Gemini baseline |
| `claude-haiku-4-5-20251001` | flash | Cheap Claude |
| `claude-sonnet-4-5-20250929` | mid | Strong Claude |
| `gemma-4-31b-it` | mid | Open instruct (replaces qwen — 429 rate limits on 2026-09-24) |
| `gpt-5.4-nano-2026-03-17` | flash | Nano baseline |
| `gemini-3.7-flash` | flash | Added 2026-09-24 (auto-selected by a task push); kept in results as a 7th locked model |

Note: `qwen3-next-80b-a3b-instruct` was attempted but returned 429 heavy-load errors on all three core tasks; swapped to `gemma-4-31b-it`.

## Run snippet (repeat `-m`, never space-separate)

```bash
kaggle b t run art-label-triage \
  -m gemini-3.5-flash \
  -m gemini-2.5-pro \
  -m gemini-3.7-flash \
  -m claude-haiku-4-5-20251001 \
  -m claude-sonnet-4-5-20250929 \
  -m gemma-4-31b-it \
  -m gpt-5.4-nano-2026-03-17 \
  --wait
```

If a slug disappears later, replace with the closest family member and note the swap here + in the DEV post. Do not expand beyond 7.
