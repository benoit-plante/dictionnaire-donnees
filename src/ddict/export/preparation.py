"""The preparation scripts (v0.8, step 7, D-062, D-068): SPSS syntax and an R script that
create new variables from the team's decisions, without any model: the reversed items
(`<item>_inv`) and the scores of the structured scorings. No original variable is changed.
Since v0.15 (D-120), the recodings come after the scores, each a new variable with its
value labels. Since v0.12 (D-094), the exclusion rules follow: `ddict_exclusion` (0 for a
person kept, otherwise the rank of the first rule that excludes them), its counts, then only
the people kept remain, as in the tool (`ddict.analysis.exclusions`).

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
from ddict.project.exclusions import members
from ddict.project.model import (
    ClassesRecode,
    CompletenessRule,
    ConditionRule,
    DuplicateRule,
    DurationRule,
    Group,
    NoDatabase,
    Project,
    Recode,
    StraightliningRule,
    VariableEntry,
)

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
                if e.profile is not None and e.profile.sum_of_group}  # fmt: skip
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
    """Whether the project has anything to prepare: a reversed item, a scoring, a recoding
    or an exclusion rule."""
    return bool(project.exclusions.rules or project.recodes.rules) or any(
        g.reverse_items or g.scoring is not None for g in project.groups
    )


def _header(project: Project, comment: str, today: str) -> list[str]:
    if project.source is None:
        raise NoDatabase("preparation")
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
            "Crée de nouvelles variables (items inversés, scores, recodages) selon les "
            "décisions de l'équipe ; aucune variable d'origine n'est modifiée."
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
    lines += _spss_recodes(project)
    lines += _spss_exclusions(project, scores)
    lines.append("EXECUTE.")
    return "\n".join(lines) + "\n"


# --- Exclusions (v0.12, D-094) ----------------------------------------------------------


def _final(project: Project, scores: list[Score]) -> dict[str, tuple[str, bool]]:
    """Original name (or "score:<group>") -> final name, and whether it holds text."""
    names = w.names_of(project)
    found = {e.name: (names[e.name], e.file.storage_type != "numeric") for e in project.variables}
    found |= {f"score:{s.group}": (s.name, False) for s in scores}
    found |= {f"recode:{r.id}": (r.name, False) for r in project.recodes.rules}
    return found


def _key(rule: ConditionRule) -> str:
    """The key of `_final` a condition is about."""
    if rule.recode is not None:
        return f"recode:{rule.recode}"
    return f"score:{rule.score}" if rule.score else rule.variable or ""


# --- Recodings (v0.15, D-120) -----------------------------------------------------------


def _recode_source(project: Project, rule: Recode) -> tuple[str, bool]:
    """The final name of a recoding's source, and whether it holds text."""
    from ddict.project.recodes import source_name

    name = source_name(project, rule.source) or ""
    if rule.source.variable is None:
        return name, False
    return name, project.variable(rule.source.variable).file.storage_type != "numeric"


def recode_labels(rule: Recode) -> list[tuple[int, str]]:
    """The codes and labels of a recoded variable, in order."""
    if isinstance(rule, ClassesRecode):
        return [(i + 1, label) for i, label in enumerate(rule.labels)]
    return [(g.code, g.label) for g in sorted(rule.groups, key=lambda g: g.code)]


def _spss_recodes(project: Project) -> list[str]:
    lines: list[str] = []
    for rule in project.recodes.rules:
        source, text = _recode_source(project, rule)
        lines.append(f"* {rule.id} : {rule.reason}")
        if isinstance(rule, ClassesRecode):
            lines.append(f"COMPUTE {rule.name} = $SYSMIS.")
            bounds = [None, *rule.cuts, None]
            for code in range(1, len(bounds)):
                low, high = bounds[code - 1], bounds[code]
                parts = [f"NOT MISSING({source})"]
                if low is not None:
                    parts.append(f"{source} >= {_number(low)}")
                if high is not None:
                    parts.append(f"{source} < {_number(high)}")
                lines.append(f"IF ({' AND '.join(parts)}) {rule.name} = {code}.")
        else:
            pairs = " ".join(
                "(" + ", ".join(_spss_value(v, text) for v in g.values) + f"={g.code})"
                for g in rule.groups
            )
            lines.append(f"RECODE {source} {pairs} (ELSE=SYSMIS) INTO {rule.name}.")
        labels = " ".join(f"{code} {_spss_text(label)}" for code, label in recode_labels(rule))
        level = "ORDINAL" if rule.level == "ordinal" else "NOMINAL"
        lines += [
            f"VARIABLE LABELS {rule.name} {_spss_text(rule.label)}.",
            f"VALUE LABELS {rule.name} {labels}.",
            f"VARIABLE LEVEL {rule.name} ({level}).",
            "",
        ]
    return lines


def _r_recodes(project: Project) -> list[str]:
    if not project.recodes.rules:
        return []
    lines = [
        "ddict_texte <- function(x) {",
        '  x <- as.character(if (inherits(x, "vctrs_vctr")) vctrs::vec_data(x) else x)',
        '  x[!is.na(x) & trimws(x) == ""] <- NA',
        "  x",
        "}",
    ]
    for rule in project.recodes.rules:
        source, text = _recode_source(project, rule)
        x = f"ddict_texte({_r_column(source)})" if text else f"ddict_valeurs({_r_column(source)})"
        if isinstance(rule, ClassesRecode):
            cuts = ", ".join(_number(c) for c in rule.cuts)
            value = f"findInterval({x}, c({cuts})) + 1"
        else:
            sources = [v for g in rule.groups for v in g.values]
            codes = [g.code for g in rule.groups for _v in g.values]
            listed = ", ".join(_r_value(v, text) for v in sources)
            value = f"c({', '.join(str(c) for c in codes)})[match({x}, c({listed}))]"
        labels = ", ".join(f"{_r_text(label)} = {code}" for code, label in recode_labels(rule))
        lines += [
            f"# {rule.id} : {rule.reason}",
            f"{_r_column(rule.name)} <- haven::labelled({value}, labels = c({labels}), "
            f"label = {_r_text(rule.label)})",
        ]
    lines.append("")
    return lines


def _group_items(project: Project, group_id: str) -> list[str]:
    names = w.names_of(project)
    group = next(g for g in project.groups if g.group_id == group_id)
    return [names[n] for n in members(group)]


def _rule_label(rule) -> str:
    return f"{rule.id} : {rule.reason}"


def _spss_value(value, text: bool) -> str:
    return _spss_text(str(value)) if text else _number(float(value))


def _spss_condition(rule: ConditionRule, name: str, text: bool) -> str:
    present = f"RTRIM({name}) <> ''" if text else f"NOT MISSING({name})"
    if rule.operator == "missing":
        return f"NOT ({present})"
    if rule.operator == "in":
        listed = ", ".join(_spss_value(v, text) for v in rule.value)
        return f"{present} AND ANY({name}, {listed})"
    symbol = {"eq": "=", "ne": "<>", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}[rule.operator]
    return f"{present} AND {name} {symbol} {_spss_value(rule.value, text)}"


def _order(text_format: str) -> str:
    """How a date in text is written: "iso", month first ("mdy") or day first ("dmy")."""
    if text_format == "iso":
        return "iso"
    return "mdy" if text_format.startswith("%m") else "dmy"


def _spss_moment(name: str, text_format: str, target: str, number: int) -> list[str]:
    """A date and time in text read into a number of SPSS (seconds), whatever the language
    of the computer: the date by its own format, the time, then the afternoon."""
    date, time = f"#ddict_d{number}", f"#ddict_t{number}"
    if text_format == "iso":
        return [
            f"COMPUTE {target} = NUMBER(SUBSTR(LTRIM({name}), 1, 10), SDATE10) + "
            f"NUMBER(SUBSTR(LTRIM({name}), 12, 8), TIME8).",
        ]
    reading = "ADATE10" if _order(text_format) == "mdy" else "EDATE10"
    lines = [
        f"STRING {date} {time} (A40).",
        f"COMPUTE {date} = SUBSTR(LTRIM({name}), 1, INDEX(LTRIM({name}), ' ') - 1).",
        f"COMPUTE {time} = LTRIM(SUBSTR(LTRIM({name}), INDEX(LTRIM({name}), ' ') + 1)).",
        f"COMPUTE {target} = NUMBER({date}, {reading}) + "
        f"NUMBER(SUBSTR({time}, 1, INDEX(CONCAT({time}, ' '), ' ') - 1), TIME8).",
    ]
    if "%p" in text_format:
        lines += [
            f"IF (INDEX(UPCASE({time}), 'PM') > 0 AND XDATE.HOUR({target}) < 12) "
            f"{target} = {target} + 43200.",
            f"IF (INDEX(UPCASE({time}), 'AM') > 0 AND XDATE.HOUR({target}) = 12) "
            f"{target} = {target} - 43200.",
        ]
    return lines


def _spss_exclusions(project: Project, scores: list[Score]) -> list[str]:
    rules = project.exclusions.rules
    if not rules:
        return []
    final = _final(project, scores)
    lines = [
        "* "
        + _(
            "Exclusions : règles de l'équipe, dans leur ordre ; ddict_exclusion vaut 0 pour une "
            "personne gardée, sinon le rang de la première règle qui l'exclut."
        ),
        "COMPUTE ddict_ordre = $CASENUM.",
    ]
    conditions, temporary = [], []
    for number, rule in enumerate(rules, start=1):
        if isinstance(rule, ConditionRule):
            name, text = final[_key(rule)]
            conditions.append(_spss_condition(rule, name, text))
        elif isinstance(rule, CompletenessRule):
            items = ", ".join(_group_items(project, rule.group))
            conditions.append(f"NVALID({items}) < {rule.min_answered}")
        elif isinstance(rule, DurationRule):
            start, end = final[rule.start][0], final[rule.end][0]
            if rule.text_format is not None:  # dates in text, read into numbers first
                read_start, read_end = f"ddict_debut{number}", f"ddict_fin{number}"
                lines += _spss_moment(start, rule.text_format, read_start, 2 * number - 1)
                lines += _spss_moment(end, rule.text_format, read_end, 2 * number)
                start, end = read_start, read_end
                temporary.extend([read_start, read_end])
            span = f"({end} - {start})"
            conditions.append(
                f"NOT MISSING({start}) AND NOT MISSING({end}) AND {span} >= 0 "
                f"AND {span} < {_number(rule.min_seconds)}"
            )
        elif isinstance(rule, StraightliningRule):
            items = ", ".join(_group_items(project, rule.group))
            conditions.append(f"NMISS({items}) = 0 AND MIN({items}) = MAX({items})")
        else:  # DuplicateRule: the first answer of each key, in the order of the file
            keys = [final[n] for n in rule.variables]
            complete = " AND ".join(
                f"RTRIM({n}) <> ''" if text else f"NOT MISSING({n})" for n, text in keys
            )
            listed = " ".join(n for n, _text in keys)
            flag = f"ddict_double{number}"
            lines += [
                f"COMPUTE ddict_complet = ({complete}).",
                f"SORT CASES BY ddict_complet {listed} ddict_ordre.",
                f"MATCH FILES /FILE = * /BY ddict_complet {listed} /FIRST = ddict_premier.",
                f"COMPUTE {flag} = (ddict_complet = 1 AND ddict_premier = 0).",
                "SORT CASES BY ddict_ordre.",
                "DELETE VARIABLES ddict_complet ddict_premier.",
            ]
            conditions.append(f"{flag} = 1")
    lines.append("COMPUTE ddict_exclusion = 0.")
    for number, (rule, condition) in enumerate(zip(rules, conditions, strict=True), start=1):
        lines += [
            f"* {_rule_label(rule)}.",
            f"IF (ddict_exclusion = 0 AND {condition}) ddict_exclusion = {number}.",
        ]
    labels = " ".join(f"{n} {_spss_text(_rule_label(r))}" for n, r in enumerate(rules, start=1))
    flags = [
        f"ddict_double{n}" for n, r in enumerate(rules, start=1) if isinstance(r, DuplicateRule)
    ]
    lines += [
        f"VALUE LABELS ddict_exclusion 0 {_spss_text(_('Gardée'))} {labels}.",
        "FREQUENCIES VARIABLES = ddict_exclusion.",
        "SELECT IF (ddict_exclusion = 0).",
        "EXECUTE.",
        "DELETE VARIABLES ddict_ordre" + "".join(f" {f}" for f in flags + temporary) + ".",
        "",
    ]
    return lines


# --- R --------------------------------------------------------------------------------------


def _r_text(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _r_column(name: str) -> str:
    return f"donnees[[{_r_text(name)}]]"


def r_script(project: Project, today: str) -> str:
    reversals, scores, notes = plan(project)
    used = sorted({i.name for i in reversals} | {n for s in scores for n in s.items
                                                 if not n.endswith(SUFFIX)}
                  | {s.existing for s in scores if s.existing}
                  | {_recode_source(project, r)[0] for r in project.recodes.rules
                     if r.source.variable is not None})  # fmt: skip
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
    lines += _r_recodes(project)
    lines += _r_exclusions(project, scores)
    lines.append('rm(list = ls(pattern = "^ddict_"))')
    return "\n".join(lines) + "\n"


# A date and time in text read into seconds, whatever the language of the computer (R's
# own reading of "PM" depends on it): the numbers of the date in their order, the time, the
# afternoon.
R_MOMENT = [
    "ddict_moment <- function(x, ordre, douze) {",
    "  x <- trimws(ddict_chaine(x))",
    '  motif <- "^([0-9]{1,4})[-/]([0-9]{1,2})[-/]([0-9]{1,4})[ T]([0-9]{1,2}):([0-9]{2})'
    '(:([0-9]{2}))?([.][0-9]+)? ?([AaPp][Mm])?$"',
    "  vapply(regmatches(x, regexec(motif, x)), function(p) {",
    "    if (length(p) == 0) return(NA_real_)",
    "    n <- suppressWarnings(as.numeric(p[c(2, 3, 4, 5, 6, 8)]))",
    "    if (is.na(n[6])) n[6] <- 0",
    "    jour <- switch(ordre, iso = n[c(1, 2, 3)], mdy = n[c(3, 1, 2)], dmy = n[c(3, 2, 1)])",
    "    heure <- n[4]",
    "    if (douze) {",
    '      apres <- toupper(p[10]) == "PM"',
    "      if (apres && heure < 12) heure <- heure + 12",
    "      if (!apres && heure == 12) heure <- 0",
    "    }",
    '    as.numeric(as.Date(sprintf("%04d-%02d-%02d", jour[1], jour[2], jour[3]))) * 86400 +',
    "      heure * 3600 + n[5] * 60 + n[6]",
    "  }, numeric(1))",
    "}",
]


def _r_values(name: str, text: bool) -> str:
    return f"ddict_chaine({_r_column(name)})" if text else f"ddict_valeurs({_r_column(name)})"


def _r_value(value, text: bool) -> str:
    return _r_text(str(value)) if text else _number(float(value))


def _r_condition(rule: ConditionRule, name: str, text: bool) -> str:
    x = _r_values(name, text)
    if rule.operator == "missing":
        return f"is.na({x})"
    if rule.operator == "in":
        listed = ", ".join(_r_value(v, text) for v in rule.value)
        return f"ddict_vrai({x} %in% c({listed}))"
    symbol = {"eq": "==", "ne": "!=", "lt": "<", "le": "<=", "gt": ">", "ge": ">="}[rule.operator]
    return f"ddict_vrai({x} {symbol} {_r_value(rule.value, text)})"


def _r_exclusions(project: Project, scores: list[Score]) -> list[str]:
    rules = project.exclusions.rules
    if not rules:
        return []
    final = _final(project, scores)
    lines = [
        "# "
        + _(
            "Exclusions : règles de l'équipe, dans leur ordre ; ddict_exclusion vaut 0 pour une "
            "personne gardée, sinon le rang de la première règle qui l'exclut."
        ),
        "ddict_vrai <- function(x) !is.na(x) & x",
        "ddict_chaine <- function(x) {",
        '  x <- as.character(if (inherits(x, "vctrs_vctr")) vctrs::vec_data(x) else x)',
        '  x[!is.na(x) & trimws(x) == ""] <- NA',
        "  x",
        "}",
        "ddict_exclusion <- integer(nrow(donnees))",
    ]
    if any(isinstance(r, DurationRule) and r.text_format for r in rules):
        lines += R_MOMENT
    for number, rule in enumerate(rules, start=1):
        if isinstance(rule, ConditionRule):
            name, text = final[_key(rule)]
            condition = _r_condition(rule, name, text)
        elif isinstance(rule, CompletenessRule):
            items = ", ".join(_r_values(n, False) for n in _group_items(project, rule.group))
            condition = f"rowSums(!is.na(cbind({items}))) < {rule.min_answered}"
        elif isinstance(rule, DurationRule):
            start, end = _r_column(final[rule.start][0]), _r_column(final[rule.end][0])
            if rule.text_format is not None:  # dates in text, read by their format
                order = _r_text(_order(rule.text_format))
                twelve = "TRUE" if "%p" in rule.text_format else "FALSE"
                lines.append(
                    f"ddict_secondes <- ddict_moment({end}, {order}, {twelve}) - "
                    f"ddict_moment({start}, {order}, {twelve})"
                )
            else:
                lines.append(
                    f'ddict_secondes <- as.numeric(difftime(as.POSIXct({end}, tz = "UTC"), '
                    f'as.POSIXct({start}, tz = "UTC"), units = "secs"))'
                )
            limit = _number(rule.min_seconds)
            condition = f"ddict_vrai(ddict_secondes >= 0 & ddict_secondes < {limit})"
        elif isinstance(rule, StraightliningRule):
            items = ", ".join(_r_values(n, False) for n in _group_items(project, rule.group))
            lines.append(f"ddict_grille <- cbind({items})")
            condition = (
                "rowSums(is.na(ddict_grille)) == 0 & "
                "apply(ddict_grille, 1, function(r) all(r == r[1]))"
            )
        else:  # DuplicateRule: the first answer of each key, in the order of the file
            keys = ", ".join(_r_values(*final[n]) for n in rule.variables)
            lines += [
                f"ddict_cles <- data.frame({keys})",
                "ddict_complet <- complete.cases(ddict_cles)",
                "ddict_double <- logical(nrow(donnees))",
                "ddict_double[ddict_complet] <- "
                "duplicated(ddict_cles[ddict_complet, , drop = FALSE])",
            ]
            condition = "ddict_double"
        lines += [
            f"# {_rule_label(rule)}",
            f"ddict_exclusion[ddict_exclusion == 0 & ({condition})] <- {number}L",
        ]
    labels = ", ".join([_r_text(_("Gardée")), *(_r_text(_rule_label(r)) for r in rules)])
    lines += [
        f"{_r_column('ddict_exclusion')} <- ddict_exclusion",
        f"print(table(factor(ddict_exclusion, levels = 0:{len(rules)}, labels = c({labels}))))",
        f"donnees <- donnees[{_r_column('ddict_exclusion')} == 0, , drop = FALSE]",
        "",
    ]
    return lines


WRITERS = {"spss": spss, "r": r_script}


@in_language
def render_preparation(project: Project, program: str, today: str | None = None) -> str:
    return WRITERS[program](project, today or date.today().isoformat())


@in_language
def write_preparation(project: Project, paths: dict[str, Path], today: str | None = None) -> None:
    for program, path in paths.items():
        with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(render_preparation(project, program, today))
