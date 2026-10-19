"""Bench of the AI's advice (v0.9, step 7; through the AI settings since v0.18): each
objective of `exemples/bases-fictives/objectifs-analyses.json` sent to the model, and its
proposals compared with the expected analysis and variables.

    uv run python scripts/banc_conseil.py claude-haiku-5-5 [autre-modele ...]
    uv run python scripts/banc_conseil.py --suivi claude-haiku-5-5

`--suivi` takes the objectives of the follow-up base, for the analyses of v0.14 (D-115).

The service, its address and the effort come from the AI settings of this computer, the key
from Windows' credential manager. Fictional bases only; every message is billed on the key.
Prints one line per objective and a summary per model; the exchanges are kept in a
temporary folder, given at the end.
"""

from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from ddict import ai_settings
from ddict.llm import connect
from ddict.llm.advice_bench import (
    FOLLOW_UP_FILE,
    OBJECTIVES_FILE,
    bench_project,
    load_objectives,
    run_advice_bench,
    summary,
)

FOLDER = Path(__file__).resolve().parent.parent / "exemples" / "bases-fictives"


def main(models: list[str]) -> int:
    name = FOLLOW_UP_FILE if "--suivi" in models else OBJECTIVES_FILE
    models = [m for m in models if m != "--suivi"]
    found = load_objectives(FOLDER, name)
    objectives = found["objectives"]
    project = bench_project(FOLDER, found["sav"])
    log_dir = Path(tempfile.mkdtemp(prefix="banc-conseil-"))
    saved = ai_settings.load()
    for model in models:
        settings = ai_settings.AiSettings(saved.protocol, saved.endpoint, model, saved.effort)
        with connect.client_from(settings, timeout=600) as client:
            scores = run_advice_bench(
                project,
                client,
                objectives,
                now=lambda: datetime.now().isoformat(timespec="seconds"),
                clock=time.monotonic,
                log_dir=log_dir / model.replace(":", "_"),
            )
        print(f"## {model}")
        for s in scores:
            marks = "".join(
                "x" if v else "." for v in (s.first_analysis, s.first_right, s.any_right)
            )
            method = (
                "" if s.method_right is None else f" méthode {'ok' if s.method_right else 'non'}"
            )
            print(f"{s.objective} {s.outcome:<17} {marks} conditions {s.refused_conditions}"
                  f"{method} {s.seconds:.0f} s")  # fmt: skip
        print(summary(scores), flush=True)
    print(f"Échanges : {log_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
