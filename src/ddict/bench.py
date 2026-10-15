"""The model bench (v0.4, step 6): how an installed model does on the fictional bases (two
in French, and one in English since v0.5).

For each base, built as a team would build it (CSV, then its questionnaire), the bench
measures the links the model proposes against the answer key, the computed links alone
for comparison, then, with the right links, what the labels and descriptions invent:
the signals of the tool (citation, threshold, instrument, acronym, observed range) and
code meanings stated for codes that have no label. Only fictional data is sent; the
projects stay in memory; nothing is downloaded (D-023).
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from ddict import __version__, naming
from ddict.i18n import N_, Texts, _, colon, field_label, semicolon
from ddict.io import read_database
from ddict.llm.link import DEFAULT_LINK_BLOCK_SIZE, LINK_PROMPT_VERSION, NEIGHBOUR_PROMPT_VERSION
from ddict.llm.messages import DEFAULT_BLOCK_SIZE, PROMPT_VERSION
from ddict.project import build_project
from ddict.project.model import Project
from ddict.questionnaire import link
from ddict.questionnaire.labels import accepted_labels
from ddict.review import logic
from ddict.workflow import add_questionnaire

KEY_FILE = "corrige-banc.json"
SIGNAL_CODES = ("citation", "threshold", "instrument", "acronym", "observed_range")
SIGNAL_NAMES = Texts(
    {
        "citation": N_("citation"),
        "threshold": N_("seuil"),
        "instrument": N_("nom d'instrument"),
        "acronym": N_("sens d'un sigle"),
        "observed_range": N_("étendue observée"),
    }
)
# "1 = Oui", "0 : jamais", "2 pour Homme": the meaning of a code.
CODE_MEANING = re.compile(r"(?<![\w.,])-?\d+\s*(?:=|:|pour|for)\s*[«\"]?[A-Za-zÀ-ÿ]", re.IGNORECASE)


@dataclass
class BaseResult:
    name: str
    n_variables: int
    n_key: int
    model_right: int = 0
    computed_right: int = 0
    model_wrong: list[str] = field(default_factory=list)
    link_failures: int = 0
    link_seconds: float = 0.0
    n_enriched: int = 0
    signals: dict[str, list[str]] = field(default_factory=dict)
    invented_codes: list[str] = field(default_factory=list)
    enrich_failures: int = 0
    enrich_seconds: float = 0.0
    failure_detail: str | None = None  # the reason of the first failed block
    # Why each missed link was missed (v0.6, step 2): see MISS_CAUSES.
    missed: dict[str, list[str]] = field(default_factory=dict)
    # Right first choices of the computation that the model did not keep.
    computed_undone: list[str] = field(default_factory=list)


MISS_CAUSES = Texts(
    {
        "no_candidate": N_("Bonne question absente des candidates"),
        "wrong_choice": N_("Bonne candidate mal choisie"),
        "not_asked": N_("Variable sans question rattachée"),
        "no_answer": N_("Sans proposition"),
    }
)


def classify_misses(
    key: dict[str, str],
    candidates: dict[str, list[str]],
    proposed: dict[str, str | None],
    computed: dict[str, str],
) -> tuple[dict[str, list[str]], list[str]]:
    """Why each link of the key was missed, and the computation's right choices undone.

    `candidates`: what the model could choose from; `proposed`: what it answered (None when
    it gave nothing); `computed`: the computation's first choice."""
    missed: dict[str, list[str]] = {cause: [] for cause in MISS_CAUSES}
    undone = []
    for name, target in key.items():
        answer = proposed.get(name)
        if answer == target:
            continue
        offered = candidates.get(name, [])
        # A variable without candidates is not sent to the model: it undoes nothing.
        if offered and computed.get(name) == target:
            undone.append(name)
        if target == link.NO_QUESTION and answer not in (None, link.NO_QUESTION):
            cause = "not_asked"
        elif target != link.NO_QUESTION and target not in offered:
            cause = "no_candidate"
        elif answer is None:
            cause = "no_answer"
        else:
            cause = "wrong_choice"
        missed[cause].append(name)
    return missed, undone


def data_dir() -> Path:
    """The fictional bases: shipped in the package, or the repository's examples."""
    shipped = Path(__file__).resolve().parent / "banc"
    if (shipped / KEY_FILE).is_file():
        return shipped
    return Path(__file__).resolve().parents[2] / "exemples" / "bases-fictives"


def load_key(folder: Path | None = None) -> dict:
    folder = folder or data_dir()
    return json.loads((folder / KEY_FILE).read_text(encoding="utf-8"))


def _project(folder: Path, base: dict) -> Project:
    project = build_project(read_database(folder / base["data"]))
    add_questionnaire(project, folder / base["questionnaire"])
    return project


def _failures(events, result: BaseResult) -> int:
    failed = [e.result.run for e in events if e.result and e.result.run.outcome != "succeeded"]
    if failed and result.failure_detail is None:
        result.failure_detail = failed[0].detail
    return len(failed)


def invents_code_meaning(project: Project, name: str) -> bool:
    """A proposed label or description that gives the meaning of a code no label defines."""
    entry = project.variable(name)
    if accepted_labels(entry):
        return False
    texts = [t.value for t in (entry.label, entry.description) if t.origin == "ai" and t.value]
    return any(CODE_MEANING.search(t) for t in texts)


def run_base(
    folder: Path,
    base: dict,
    client,
    *,
    now: Callable[[], str],
    clock: Callable[[], float] = time.monotonic,
) -> Iterator[str | BaseResult]:
    """Measure one base; yields progress texts, then its result."""
    from ddict.llm.enrich import enrich
    from ddict.llm.link import propose_links

    key: dict[str, str] = base["links"]
    project = _project(folder, base)
    result = BaseResult(base["name"], len(project.variables), len(key))
    computed = link.best_guess(project)
    result.computed_right = sum(1 for n, t in key.items() if computed.get(n) == t)
    offered = link.candidates(project)
    offered = {**link.neighbours(project, offered), **{n: i for n, i in offered.items() if i}}

    yield _("{base} : rattachements proposés par le modèle…").format(base=base["name"])
    start = clock()
    events = list(propose_links(project, client, now=now, block_size=DEFAULT_LINK_BLOCK_SIZE))
    result.link_seconds = clock() - start
    result.link_failures = _failures(events, result)
    proposed = {name: project.variable(name).question.value for name in key}
    for name, target in key.items():
        if proposed[name] == target:
            result.model_right += 1
        else:
            result.model_wrong.append(name)
    result.missed, result.computed_undone = classify_misses(key, offered, proposed, computed)

    # The labels are measured as after a careful review: the right links, and the acronyms
    # the questionnaire defines accepted.
    for name, target in key.items():
        logic.link_question(project, name, target, now=now())
    for entry in project.glossary:
        if entry.status == "proposed":
            logic.glossary_decide(project, entry.term, "accept", now=now())
    yield _("{base} : libellés et descriptions…").format(base=base["name"])
    start = clock()
    events = list(enrich(project, client, now=now, block_size=DEFAULT_BLOCK_SIZE))
    result.enrich_seconds = clock() - start
    result.enrich_failures = _failures(events, result)
    found: dict[str, list[str]] = {}
    for entry in project.variables:
        if entry.label.origin == "ai" or entry.description.origin == "ai":
            result.n_enriched += 1
        for signal in entry.ai_signals:
            code = signal.partition(":")[2]
            if code in SIGNAL_CODES and entry.name not in found.setdefault(code, []):
                found[code].append(entry.name)
        if invents_code_meaning(project, entry.name):
            result.invented_codes.append(entry.name)
    result.signals = found
    yield result


# --- Stems of names (v0.7, D-051): the model against the rules alone. ---

NAMING_KEY_FILE = "corrige-surveymonkey.json"


@dataclass
class NamingResult:
    """The stems of the fictional SurveyMonkey export: by the rules alone, then with the
    model, against the stems of the answer key (a person's choice)."""

    name: str
    expected: dict[str, str]
    computed: dict[str, str | None] = field(default_factory=dict)
    model: dict[str, str | None] = field(default_factory=dict)
    answered: int = 0  # stems the model proposed itself
    flagged: list[str] = field(default_factory=list)  # perhaps an acronym it invented
    failures: int = 0
    seconds: float = 0.0
    failure_detail: str | None = None

    def valid(self, found: dict[str, str | None]) -> int:
        return sum(1 for k in self.expected if found.get(k) and naming.valid_stem(found[k]))

    def equal(self, found: dict[str, str | None]) -> int:
        return sum(1 for k, v in self.expected.items() if found.get(k) == v)


def _stems(project: Project, keys) -> dict[str, str | None]:
    return {k: naming.usable_stem(project, k) for k in keys}


def run_naming(
    folder: Path,
    client,
    *,
    now: Callable[[], str],
    clock: Callable[[], float] = time.monotonic,
) -> Iterator[str | NamingResult]:
    """Measure the stems on the fictional SurveyMonkey export (its .sav, its Excel header as
    the questionnaire); yields progress, then the result."""
    from ddict.llm.stems import ACRONYM_SIGNAL, propose_stems

    wave = json.loads((folder / NAMING_KEY_FILE).read_text(encoding="utf-8"))["waves"]["t2"]
    result = NamingResult("travail-t2_surveymonkey", dict(wave["stems"]))

    def project() -> Project:
        found = build_project(read_database(folder / wave["sav"]))
        add_questionnaire(found, folder / wave["xlsx"])
        return found

    alone = project()
    naming.propose(alone)
    result.computed = _stems(alone, result.expected)
    yield _("{base} : noms de base proposés par le modèle…").format(base=result.name)
    with_model = project()
    start = clock()
    events = list(propose_stems(with_model, client, now=now))
    result.seconds = clock() - start
    result.failures = _failures(events, result)
    result.model = _stems(with_model, result.expected)
    for key in result.expected:
        found = naming.stem(with_model, key)
        if found is not None and found.stem.origin == "ai":
            result.answered += 1
            if ACRONYM_SIGNAL in found.ai_signals:
                result.flagged.append(key)
    yield result


def run_bench(
    client,
    *,
    now: Callable[[], str],
    clock: Callable[[], float] = time.monotonic,
    folder: Path | None = None,
) -> Iterator[str | BaseResult | NamingResult]:
    folder = folder or data_dir()
    for base in load_key(folder)["bases"]:
        yield from run_base(folder, base, client, now=now, clock=clock)
    if (folder / NAMING_KEY_FILE).is_file():
        yield from run_naming(folder, client, now=now, clock=clock)


def _seconds(value: float) -> str:
    value = round(value)
    return f"{value // 60} min {value % 60:02d} s" if value >= 60 else f"{value} s"


def _naming_section(result: NamingResult) -> list[str]:
    n = len(result.expected)
    lines = [
        "",
        _("## Noms de base des questions (v0.7)"),
        "",
        _(
            "Sur l'export SurveyMonkey fictif : le nom de base de chaque question, comparé à celui "
            "du corrigé (le choix d'une équipe). Le modèle n'est gardé dans l'interface que "
            "s'il fait mieux que les règles seules (D-051)."
        ),
        "",
        f"| | {_('Noms de base valides')} | {_('Égaux au corrigé')} | "
        f"{_('Proposés par le modèle')} | {_('Sigle possible')} | {_('Blocs en échec')} | "
        f"{_('Durée')} |",
        "|---|---|---|---|---|---|---|",
        f"| {_('Règles seules')} | {result.valid(result.computed)} / {n} | "
        f"{result.equal(result.computed)} / {n} | — | — | — | — |",
        f"| {_('Avec le modèle')} | {result.valid(result.model)} / {n} | "
        f"{result.equal(result.model)} / {n} | {result.answered} / {n} | "
        f"{len(result.flagged)} | {result.failures} | {_seconds(result.seconds)} |",
        "",
        f"| {_('Question')} | {_('Corrigé')} | {_('Règles seules')} | {_('Avec le modèle')} |",
        "|---|---|---|---|",
    ]
    for key, expected in result.expected.items():
        lines.append(
            f"| {key} | `{expected}` | `{result.computed.get(key) or '—'}` | "
            f"`{result.model.get(key) or '—'}` |"
        )
    return lines


def render_report(
    results: list[BaseResult | NamingResult], *, model: str, endpoint: str, date: str
) -> str:
    naming_result = next((r for r in results if isinstance(r, NamingResult)), None)
    results = [r for r in results if isinstance(r, BaseResult)]
    total_key = sum(r.n_key for r in results)
    lines = [
        _("# Banc d'essai : {model}").format(model=model),
        "",
        f"- {field_label('Date')}{date}",
        f"- {field_label('Serveur local')}{endpoint}",
        f"- {field_label('Outil')}dictionnaire-donnees {__version__} ; prompts "
        f"{LINK_PROMPT_VERSION}, {NEIGHBOUR_PROMPT_VERSION} {_('et')} {PROMPT_VERSION}",
        "- "
        + _(
            "Bases fictives seulement : rien de réel n'a été envoyé au modèle. Les durées "
            "dépendent de l'ordinateur."
        ),
        "",
        _("## Rattachements aux questions"),
        "",
        f"| {_('Base')} | {_('Modèle')} | {_('Calcul seul')} | {_('Blocs en échec')} | "
        f"{_('Durée')} |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r.name} | {r.model_right} / {r.n_key} | {r.computed_right} / {r.n_key} | "
            f"{r.link_failures} | {_seconds(r.link_seconds)} |"
        )
    lines.append(
        f"| **{_('Total')}** | **{sum(r.model_right for r in results)} / {total_key}** | "
        f"{sum(r.computed_right for r in results)} / {total_key} | "
        f"{sum(r.link_failures for r in results)} | "
        f"{_seconds(sum(r.link_seconds for r in results))} |"
    )
    lines += [
        "",
        _("Pourquoi les rattachements du modèle ont été manqués :"),
        "",
        f"| {_('Base')} | "
        + " | ".join(MISS_CAUSES[c] for c in MISS_CAUSES)
        + f" | {_('Choix justes du calcul défaits')} |",
        "|---|" + "---|" * (len(MISS_CAUSES) + 1),
    ]
    for r in results:
        counts = " | ".join(str(len(r.missed.get(c, []))) for c in MISS_CAUSES)
        lines.append(f"| {r.name} | {counts} | {len(r.computed_undone)} |")
    lines.append("")
    for r in results:
        details = [
            f"{MISS_CAUSES[c].lower()} ({', '.join(f'`{n}`' for n in r.missed[c])})"
            for c in MISS_CAUSES
            if r.missed.get(c)
        ]
        if r.computed_undone:
            details.append(
                _("choix justes du calcul défaits ({names})").format(
                    names=", ".join(f"`{n}`" for n in r.computed_undone)
                )
            )
        if details:
            lines.append(f"- {r.name}{colon()}" + semicolon().join(details))
    lines += [
        "",
        _("## Libellés et descriptions"),
        "",
        _(
            "Proposés après les bons rattachements et les sigles du questionnaire acceptés. Une "
            "variable signalée contient peut-être "
            "une invention, à vérifier par une personne ; moins il y en a, mieux c'est."
        ),
        "",
        f"| {_('Base')} | {_('Variables enrichies')} | "
        + " | ".join(SIGNAL_NAMES[c] for c in SIGNAL_CODES)
        + f" | {_('sens de codes sans étiquette')} | {_('Blocs en échec')} | {_('Durée')} |",
        "|---|---|" + "---|" * len(SIGNAL_CODES) + "---|---|---|",
    ]
    for r in results:
        counts = " | ".join(str(len(r.signals.get(c, []))) for c in SIGNAL_CODES)
        lines.append(
            f"| {r.name} | {r.n_enriched} / {r.n_variables} | {counts} | "
            f"{len(r.invented_codes)} | {r.enrich_failures} | {_seconds(r.enrich_seconds)} |"
        )
    lines.append("")
    for r in results:
        details = [
            f"{SIGNAL_NAMES[c]} ({', '.join(f'`{n}`' for n in r.signals[c])})"
            for c in SIGNAL_CODES
            if r.signals.get(c)
        ]
        if r.invented_codes:
            details.append(
                _("sens de codes ({names})").format(
                    names=", ".join(f"`{n}`" for n in r.invented_codes)
                )
            )
        if details:
            lines.append(f"- {r.name}{colon()}" + semicolon().join(details))
    if naming_result is not None:
        lines += _naming_section(naming_result)
    return "\n".join(lines).rstrip("\n") + "\n"


def report_name(model: str, date: str) -> str:
    safe = re.sub(r"[^\w.-]+", "-", model).strip("-")
    return f"banc-essai-{safe}-{date}.md"


def write_report(text: str, folder: Path, model: str, date: str) -> Path:
    path = Path(folder) / report_name(model, date)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def totals(results: list[BaseResult | NamingResult]) -> Counter:
    """For the interface: the main figures."""
    counts: Counter = Counter()
    for r in results:
        if isinstance(r, NamingResult):
            counts["stems_model"] = r.equal(r.model)
            counts["stems_rules"] = r.equal(r.computed)
            counts["stems"] = len(r.expected)
            continue
        counts["right"] += r.model_right
        counts["key"] += r.n_key
        counts["flagged"] += len({n for names in r.signals.values() for n in names})
        counts["codes"] += len(r.invented_codes)
    return counts
