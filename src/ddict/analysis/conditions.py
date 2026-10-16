"""The conditions of an analysis (v0.9, step 3, D-074): what the codebook allows, checked
before any computation. A condition not met refuses the analysis, with its reason; a fragile
one is a warning, and the person decides. Thresholds validated with the catalogue (D-077).

The checks that need the computation itself (normality, Levene, VIF, expected counts of a
chi-square) come with the analyses.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ddict.analysis.catalogue import CATALOGUE, ROLES, SCALE, Analysis
from ddict.analysis.data import PreparedData
from ddict.export import wording as w
from ddict.export.preparation import plan
from ddict.i18n import _
from ddict.project import measure
from ddict.project.model import Project
from ddict.questionnaire.labels import accepted_labels

SENSITIVE = measure.SENSITIVE
GROUP_LEAST = 2  # people per group, or the analysis is refused
SMALL = 5  # a group or a modality below this is flagged
PER_PREDICTOR_LEAST = 10  # observations per predictor, or the regression is refused
PER_PREDICTOR_WARN = 20


@dataclass
class Check:
    refusals: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.refusals


class AnalysisRefused(Exception):
    """The conditions refuse the analysis; `check` holds the reasons."""

    def __init__(self, check: Check) -> None:
        super().__init__("; ".join(check.refusals))
        self.check = check


def levels(project: Project) -> dict[str, str | None]:
    """The measure level of each variable an analysis may use, by final name: the level in
    force, and "scale" for a score of a structured scoring."""
    found = {w.final_name(e): measure.level(e) for e in project.variables}
    for score in plan(project)[1]:
        found[score.name] = SCALE
    return found


def _sensitive(project: Project) -> set[str]:
    return {
        w.final_name(e)
        for e in project.variables
        if (e.privacy.privacy_class.value or "ordinary") in SENSITIVE
        or e.profile.inferred_type in ("text", "empty", "mixed", "date", "datetime")
    }


def candidates(project: Project, analysis: Analysis, role: str) -> list[str]:
    """The variables a role may take, by final name, in the order of the codebook."""
    allowed = analysis.role(role).levels
    excluded = _sensitive(project)
    return [n for n, lv in levels(project).items() if lv in allowed and n not in excluded]


def check(
    project: Project,
    analysis_key: str,
    chosen: dict[str, list[str]],
    options: dict[str, str] | None = None,
    data: PreparedData | None = None,
) -> Check:
    """Whether this analysis may run with these variables and options."""
    analysis = CATALOGUE[analysis_key]
    options = {k: v[0] for k, v in analysis.options.items()} | (options or {})
    found = Check()
    known = levels(project)
    excluded = _sensitive(project)
    for role in analysis.roles:
        names = chosen.get(role.key, [])
        if not role.least <= len(names) <= role.most:
            found.refusals.append(
                _("{role} : de {least} à {most} variables.").format(
                    role=_role(role.key), least=role.least, most=role.most
                )
            )
        for name in names:
            if name not in known:
                found.refusals.append(_("{name} : variable inconnue.").format(name=name))
            elif name in excluded:
                found.refusals.append(
                    _("{name} : identifiant, texte ou date, exclu des analyses.").format(name=name)
                )
            elif known[name] is None:
                found.refusals.append(
                    _("{name} : niveau de mesure non décidé ; décidez-le sur la page Base.").format(
                        name=name
                    )
                )
            elif known[name] not in role.levels:
                found.refusals.append(
                    _("{name} : niveau « {level} », ne convient pas au rôle « {role} ».").format(
                        name=name, level=w.MEASURES[known[name]], role=_role(role.key)
                    )
                )
    if analysis.independent and _long_format(project):
        found.warnings.append(
            _(
                "La base est en format long (plusieurs lignes par personne) : cette analyse "
                "suppose des observations indépendantes."
            )
        )
    if analysis_key == "correlation" and options.get("method") == "pearson":
        ordinal = [n for n in chosen.get("variables", []) if known.get(n) == "ordinal"]
        if ordinal:
            found.warnings.append(
                _(
                    "{names} : variable ordinale ; la corrélation de Spearman convient mieux."
                ).format(names=", ".join(ordinal))
            )
    if data is not None and found.ok:
        _with_data(project, analysis, chosen, options, data.table, found)
    return found


def _role(key: str) -> str:
    return ROLES[key].lower()


def _long_format(project: Project) -> bool:
    structure = project.dataset.structure
    return structure.value == "long" and structure.status != "proposed"


def _with_data(project, analysis, chosen, options, table: pd.DataFrame, found: Check) -> None:
    """The conditions that need the data: modalities, people per group, per predictor."""
    used = [n for names in chosen.values() for n in names]
    complete = table[used].dropna() if analysis.key != "table1" else table
    for role in analysis.roles:
        if role.modalities is None:
            continue
        for name in chosen.get(role.key, []):
            counts = complete[name].value_counts()
            if analysis.key == "t_test" and options.get("levels"):
                wanted = [float(c) for c in str(options["levels"]).split(",")]
                counts = counts[counts.index.isin(wanted)]
            low, high = role.modalities
            n = len(counts)
            if analysis.key == "t_test" and n != 2:
                found.refusals.append(
                    _("{name} : {n} modalités ; choisissez-en deux.").format(name=name, n=n)
                )
                continue
            if not low <= n <= high:
                found.refusals.append(
                    _("{name} : {n} modalités observées ; il en faut de {low} à {high}.").format(
                        name=name, n=n, low=low, high=high
                    )
                )
                continue
            tiny = counts[counts < GROUP_LEAST]
            if len(tiny) and analysis.key in ("t_test", "anova"):
                found.refusals.append(
                    _("{name} : un groupe de moins de {n} personnes ({codes}).").format(
                        name=name, n=GROUP_LEAST, codes=_codes(project, name, tiny.index)
                    )
                )
            small = counts[counts < SMALL]
            if len(small):
                found.warnings.append(
                    _("{name} : moins de {n} personnes dans {codes}.").format(
                        name=name, n=SMALL, codes=_codes(project, name, small.index)
                    )
                )
    if analysis.key == "regression":
        predictors = chosen.get("predictors", [])
        terms = sum(
            max(complete[n].nunique() - 1, 1) if _levels_of(project, n) == "nominal" else 1
            for n in predictors
        )
        per = len(complete) / max(terms, 1)
        if per < PER_PREDICTOR_LEAST:
            found.refusals.append(
                _(
                    "{n} observations pour {k} prédicteurs : il en faut au moins {least} par "
                    "prédicteur."
                ).format(n=len(complete), k=terms, least=PER_PREDICTOR_LEAST)
            )
        elif per < PER_PREDICTOR_WARN:
            found.warnings.append(
                _("{n} observations pour {k} prédicteurs : moins de {warn} par prédicteur.").format(
                    n=len(complete), k=terms, warn=PER_PREDICTOR_WARN
                )
            )


def _levels_of(project: Project, name: str) -> str | None:
    return levels(project).get(name)


def _codes(project: Project, name: str, codes) -> str:
    """Codes of a variable with their labels: "4 Ouest"."""
    labels = {}
    for entry in project.variables:
        if w.final_name(entry) == name:
            labels = {lab.code: lab.label for lab in accepted_labels(entry)}
    return ", ".join(
        f"{w.code_text(c)} {labels[c]}" if c in labels else w.code_text(c) for c in codes
    )
