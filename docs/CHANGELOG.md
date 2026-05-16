# Changelog

## 2026-05-16 — Routing and cache cleanup

- Default routing updated to specialize providers:
  - `qwen-fast` → `qwen3.5-2b` (fast/small tasks)
  - `qwen-coder` → `qwen2.5-coder-7b` (coding tasks)
  - `copilot-pro` → Copilot Pro (complex planning, fallback)
- `copilot-cli` now routes to Foundry Local and falls back to `copilot-pro`.
- Added `scripts/compare_models.py` to run repeated trials and save JSON/CSV reports.
- Added `scripts/clean_model_cache.py` to purge cached model variants except specified models.
- Removed other cached variants from Foundry local runtime; verified remaining variants: `qwen3.5-2b`, `qwen2.5-coder-7b`.
