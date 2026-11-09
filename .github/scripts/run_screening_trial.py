#!/usr/bin/env python3
"""选股试跑入口，供 .github/workflows/01-screening-trial.yml 调用。

用法：python .github/scripts/run_screening_trial.py <strategy>
策略缺省为 oversold_reversal。仅使用 Gemini 直连，无备用模型。
"""

import json
import sys
import time
from dataclasses import asdict

from src.services.screening.config import Config
from src.services.screening.pipeline import screen

t0 = time.time()

strategy = sys.argv[1] if len(sys.argv) > 1 else "oversold_reversal"

cfg = Config.from_env()
print(f"LLM model: {cfg.llm_model}")
print(f"LLM configured: {cfg.has_llm_config()} key_set={'yes' if cfg.llm_api_key else 'no'}")
print(f"llm_rank_weight={cfg.llm_rank_weight} llm_min_coverage={cfg.llm_min_coverage}")


def progress(pct, msg):
    print(f"[{time.time() - t0:7.1f}s] {pct:3d}% {msg}", flush=True)


result = screen(
    strategy,
    market="cn",
    max_output=20,
    use_llm=True,
    progress_callback=progress,
)
elapsed = time.time() - t0
print(f"ELAPSED {elapsed:.1f}s")
print(f"strategy={result.strategy} version={result.strategy_version} "
      f"category={result.strategy_category} market={result.market}")
print(f"snapshot_count={result.snapshot_count} after_filter={result.after_filter_count} "
      f"picks={len(result.picks)} llm_ranked={result.llm_ranked} "
      f"ranking_mode={result.ranking_mode} model={result.llm_model_used}")
print(f"llm_coverage={result.llm_coverage} failure={result.llm_failure_reason!r}")
print(f"snapshot_source={result.snapshot_source}")
for d in result.degradation:
    print(f"degradation: {d}")
for d in result.portfolio_concentration_notes:
    print(f"concentration: {d}")
print(f"market_view: {result.llm_market_view[:500]}")
print(f"selection_logic: {result.llm_selection_logic[:500]}")
print(f"portfolio_risk: {result.llm_portfolio_risk[:500]}")
for p in result.picks:
    print(f"#{p.rank:2d} {p.code} {p.name} final={p.final_score:.1f} "
          f"screen={p.screen_score:.1f} llm={p.llm_score} "
          f"sector={p.llm_sector} theme={p.llm_theme} risk={p.risk_level}")

out = asdict(result)
out["_elapsed_sec"] = elapsed
with open("screening-trial/result.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=str)
print("saved screening-trial/result.json")
