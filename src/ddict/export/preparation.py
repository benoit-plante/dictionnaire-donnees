"""The preparation scripts (v0.8, step 7, D-062, D-068): SPSS syntax and an R script that
create new variables from the team's decisions, without any model: the reversed items
(`<item>_inv`) and the scores of the structured scorings. No original variable is changed.

They run after the command file of `ddict.export.syntax` (or on the documented copy): on the
final names, with the missing codes already declared, which every computation leaves out.
When the database already holds a score of a group (v0.6, D-039), the score computed again
is compared with it, and the differences counted; nothing is replaced.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ddict import __version__
from ddict.export import wording as w
from ddict.i18n import _, in_language
from ddict.project import fingerprint, scoring
from ddict.project.model import Group, Project, VariableEntry

SPSS_NAME = re.compile(r"^[^\W\d_][\w.@#$]{0,63}$")
SUFFIX = "_inv"


@dataclass(frozen=True)
class Reversal:
    """A reversed item: its final name, the new variable, the total of the scale's ends."""

    name: str
    new: str
    total: float
    source: str  # where the scale's ends come from


@dataclass(frozen=True)
class Score:
    group: str
    name: str
    items: list[str]  # final names, reversed items as their new variable
    aggregation: str
    least: int  # items answered at least
    prorate: bool  # a sum with items missing: mean times the number of items (D-068)
    label: str
    existing: str | None  # a score already in the database, to compare with


def _number(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else repr(float(value))


def _bounds(project: Project, group: Group, entry: VariableEntry) -> tuple[float, str] | None:
    """The total of the scale's ends: from the scoring, the sourced range, or the labels."""
    found = group.scoring
    if scoring.structured(found):
        return found.scale_min + found.scale_max, _("cotation du groupe")
    if entry.theoretical_range is not None:
        r = entry.theoretical_range
        return r.min + r.max, _("étendue théorique")
    labels = scoring.scale_bounds(entry)
    if labels is not None:
        return labels[0] + labels[1], _("étiquettes de valeurs")
    return None


def plan(project: Project) -> tuple[list[Reversal], list[Score], list[str]]:
    """What the scripts do: reversals, scores, and notes (what they cannot do, and why)."""
    names = w.names_of(project)
    taken = {n.lower() for n in names.values()}
    reversals: dict[str, Reversal] = {}
    notes: list[str] = []
    for group in project.groups:
        for original in group.reverse_items:
            entry = project.variable(original)
            name = names[original]
            new = name + SUFFIX
            bounds = _bounds(project, group, entry)
            if bounds is None:
                notes.append(_("{name} : bornes de l'échelle inconnues, non inversé.").format(
                    name=name))  # fmt: skip
                continue
            if new.lower() in taken or not SPSS_NAME.match(new):
                notes.append(_("{name} : le nom {new} est déjà pris ou invalide, non inversé.")
                             .format(name=name, new=new))  # fmt: skip
                continue
            reversals[original] = Reversal(name, new, bounds[0], bounds[1])
    existing = {e.profile.sum_of_group: names[e.name] for e in project.variables
                if e.profile.sum_of_group}  # fmt: skip
    scores = []
    for group in project.groups:
        found = group.scoring
        if found is None:
            continue
        if not scoring.structured(found):
            notes.append(
                _("{group} : cotation décrite en note seulement, score non calculé.").format(
                    group=group.group_id
                )
            )
            continue
        reverse = set(scoring.reversed_items(group, found))
        missing = [n for n in reverse if n not in reversals]
        if missing:
            notes.append(
                _("{group} : un item inversé n'a pu être créé, score non calculé.").format(
                    group=group.group_id
                )
            )
            continue
        items = [reversals[n].new if n in reverse else names[n] for n in found.items]
        least = found.min_items_answered or len(items)
        scores.append(
            Score(
                group=group.group_id,
                name=found.score_name,
                items=items,
                aggregation=found.aggregation,
                least=least,
                prorate=scoring.partial_sum(found) and found.missing_rule == "prorate",
                label=w.scoring_text(project, group).split(" (")[0][:120],
                existing=existing.get(group.group_id) if found.aggregation == "sum" else None,
            )
        )
    return list(reversals.values()), scores, notes


def needed(project: Project) -> bool:
    """Whether the project has anything to prepare: a reversed item or a scoring."""
    return any(g.reverse_items or g.scoring is not None for g in project.groups)


def _header(project: Project, comment: str, today: str) -> list[str]:
    lines = [
        _("Préparation de {name}, produite par dictionnaire-donnees {version} le {date}.").format(
            name=project.source.name, version=__version__, date=today
        ),
        _("Encodage : UTF-8. Empreinte du codebook : {fingerprint}.").format(
            fingerprint=fingerprint.short(project)
        ),
        _(
            "À exécuter après le fichier de commandes (ou sur la copie documentée) : il porte "
            "sur les noms finaux, et les codes manquants déclarés sont exclus des calculs."
        ),
        _(
            "Crée de nouvelles variables (items inversés, scores) selon les décisions de "
            "l'équipe ; aucune variable d'origine n'est modifiée."
        ),
    ]
    return [f"{comment} {line}" for line in lines]


# --- SPSS ---------------------------------------------------------------------------------


def _spss_text(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def spss(project: Project, today: str) -> str:
    reversals, scores, notes = plan(project)
    lines = ["* Encoding: UTF-8.", *_header(project, "*", today), ""]
    lines += [f"* {note}" for note in notes]
    if notes:
        lines.append("")
    for item in reversals:
        lines += [
            _("* {name} inversé ({total} - x ; bornes : {source}).").format(
                name=item.name, total=_number(item.total), source=item.source
            ),
            f"COMPUTE {item.new} = {_number(item.total)} - {item.name}.",
            f"VARIABLE LABELS {item.new} "
            + _spss_text(_("{name} inversé").format(name=item.name))
            + ".",
            "",
        ]
    for score in scores:
        listed = ", ".join(score.items)
        function = "MEAN" if score.aggregation == "mean" or score.prorate else "SUM"
        formula = f"{function}.{score.least}({listed})"
        if score.prorate:
            formula = f"{formula} * {len(score.items)}"
        lines += [
            _("* Score de {group}.").format(group=score.group),
            f"COMPUTE {score.name} = {formula}.",
            f"VARIABLE LABELS {score.name} {_spss_text(score.label)}.",
            "",
        ]
        if score.existing:
            lines += [
                _("* Comparaison avec {existing}, déjà dans la base : écarts comptés.").format(
                    existing=score.existing
                ),
                f"COMPUTE ddict_ecart = ABS({score.name} - {score.existing}) > 0.000001.",
                "FREQUENCIES VARIABLES = ddict_ecart.",
                "DELETE VARIABLES ddict_ecart.",
                "",
            ]
    lines.append("EXECUTE.")
    return "\n".join(lines) + "\n"


# --- R --------------------------------------------------------------------------------------


def _r_text(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _r_column(name: str) -> str:
    return f"donnees[[{_r_text(name)}]]"


def r_script(project: Project, today: str) -> str:
    reversals, scores, notes = plan(project)
    used = sorted({i.name for i in reversals} | {n for s in scores for n in s.items
                                                 if not n.endswith(SUFFIX)}
                  | {s.existing for s in scores if s.existing})  # fmt: skip
    lines = [
        *_header(project, "#", today),
        _("# Avant : « donnees » chargées, puis le fichier de commandes appliqué."),
        "",
        "ddict_valeurs <- function(x) {",
        '  if (inherits(x, "haven_labelled")) x <- haven::zap_missing(x)',
        '  as.numeric(if (inherits(x, "vctrs_vctr")) vctrs::vec_data(x) else x)',
        "}",
        "ddict_attendues <- c(" + ", ".join(_r_text(n) for n in used) + ")",
        "ddict_absentes <- setdiff(ddict_attendues, names(donnees))",
        "if (length(ddict_absentes) > 0) stop(",
        "  " + _r_text(_("Variables absentes (appliquez d'abord le fichier de commandes) : ")),
        '  , paste(ddict_absentes, collapse = ", "))',
        "",
    ]
    lines += [f"# {note}" for note in notes]
    if notes:
        lines.append("")
    for item in reversals:
        lines += [
            _("# {name} inversé ({total} - x ; bornes : {source}).").format(
                name=item.name, total=_number(item.total), source=item.source
            ),
            f"{_r_column(item.new)} <- {_number(item.total)} - "
            f"ddict_valeurs({_r_column(item.name)})",
            f'attr({_r_column(item.new)}, "label") <- '
            + _r_text(_("{name} inversé").format(name=item.name)),
            "",
        ]
    for score in scores:
        columns = ", ".join(f"ddict_valeurs({_r_column(n)})" for n in score.items)
        if score.aggregation == "mean":
            value = "rowMeans(ddict_items, na.rm = TRUE)"
        elif score.prorate:
            value = f"rowMeans(ddict_items, na.rm = TRUE) * {len(score.items)}"
        else:
            value = "rowSums(ddict_items, na.rm = TRUE)"
        lines += [
            _("# Score de {group}.").format(group=score.group),
            f"ddict_items <- cbind({columns})",
            f"{_r_column(score.name)} <- ifelse(rowSums(!is.na(ddict_items)) >= {score.least}, "
            f"{value}, NA)",
            f'attr({_r_column(score.name)}, "label") <- {_r_text(score.label)}',
            "",
        ]
        if score.existing:
            lines += [
                f"ddict_ecarts <- sum(abs({_r_column(score.name)} - "
                f"ddict_valeurs({_r_column(score.existing)})) > 1e-6, na.rm = TRUE)",
                "if (ddict_ecarts > 0) warning(ddict_ecarts, "
                + _r_text(
                    _(" écarts entre {score} et {existing}, déjà dans la base.").format(
                        score=score.name, existing=score.existing
                    )
                )
                + ")",
                "",
            ]
    lines.append('rm(list = ls(pattern = "^ddict_"))')
    return "\n".join(lines) + "\n"


WRITERS = {"spss": spss, "r": r_script}


@in_language
def render_preparation(project: Project, program: str, today: str | None = None) -> str:
    return WRITERS[program](project, today or date.today().isoformat())


@in_language
def write_preparation(project: Project, paths: dict[str, Path], today: str | None = None) -> None:
    for program, path in paths.items():
        with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(render_preparation(project, program, today))
