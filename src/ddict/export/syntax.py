"""Command files that apply the accepted decisions to the team's data (v0.4, D-025).

One file per program: SPSS syntax and an R script (haven); no Stata do-file, which could
not be tried in Stata (D-030). They hold only
decisions: variable labels, value labels (from the file or accepted), missing codes
(declared in the file or confirmed by the team, D-028), measure levels in force (v0.8).
Nothing proposed, no participant value. Values are never recoded; the reversed items the
team confirmed are only suggested in comments. The new names a person accepted (v0.7) are
applied first; everything after is written with them. Renaming is not recoding (D-025).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ddict import __version__
from ddict.export import wording as w
from ddict.i18n import _, in_language
from ddict.io.csv_reader import MISSING_TOKENS
from ddict.project import fingerprint, measure
from ddict.project.model import Code, Project, VariableEntry
from ddict.questionnaire.labels import accepted_labels

SUFFIXES = {"spss": ".sps", "r": ".R"}
SPSS_MAX_DISCRETE = 3


@dataclass(frozen=True)
class Decisions:
    """What a command file applies to one variable."""

    name: str
    string: bool
    label: str
    labels: list[tuple[Code, str]]
    missing: list[Code]  # single codes
    missing_range: tuple[Code, Code] | None
    measure: str | None


def decisions(entry: VariableEntry) -> Decisions:
    singles: list[Code] = []
    ranges = []
    for item in entry.file.declared_missing:
        if item.low == item.high:
            singles.append(item.low)
        else:
            ranges.append((item.low, item.high))
    singles += [c for c in w.confirmed_missing(entry) if c not in singles]
    return Decisions(
        name=w.final_name(entry),
        string=entry.file.storage_type == "string",
        label=_one_line(w.label_text(entry, "final")),
        labels=[(lab.code, _one_line(lab.label)) for lab in accepted_labels(entry)],
        missing=singles,
        missing_range=ranges[0] if ranges else None,
        measure=measure.level(entry),
    )


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _number(code: Code) -> str:
    return w.code_text(code)


def _reversed(project: Project) -> list[tuple[str, VariableEntry]]:
    """Items the team marked as reversed, with their group."""
    found = []
    names = {e.name for e in project.variables}
    for group in project.groups:
        for name in group.reverse_items:
            if name in names:
                found.append((group.group_id, project.variable(name)))
    return found


def _header(project: Project, comment: str, today: str) -> list[str]:
    lines = [
        _("Métadonnées de {name}, produites par dictionnaire-donnees {version} le {date}.").format(
            name=project.source.name, version=__version__, date=today
        ),
        _("Encodage : UTF-8.")
        + " "
        + _("Empreinte du codebook : {fingerprint}.").format(
            fingerprint=fingerprint.short(project)
        ),
        _(
            "Seulement les décisions acceptées : libellés, étiquettes de valeurs, codes "
            "manquants (déclarés ou confirmés par l'équipe), niveaux de mesure."
        ),
        _("Aucune valeur n'est modifiée. Appliquez ce fichier à une copie de vos données."),
    ]
    return [f"{comment} {line}" for line in lines]


# --- SPSS ---------------------------------------------------------------------------------

SPSS_NAME = re.compile(r"^[^\W\d_][\w.@#$]{0,63}$")
SPSS_LEVELS = {"nominal": "NOMINAL", "ordinal": "ORDINAL", "scale": "SCALE"}


def _spss_text(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def _spss_code(code: Code, string: bool) -> str:
    return _spss_text(str(code)) if string else _number(code)


def _renames(project: Project) -> list[tuple[str, str]]:
    """(original name, accepted new name) for the variables renamed (v0.7)."""
    return [(e.name, w.final_name(e)) for e in project.variables if w.final_name(e) != e.name]


def spss(project: Project, today: str) -> str:
    lines = ["* Encoding: UTF-8.", *_header(project, "*", today), ""]
    renames = [
        (old, new)
        for old, new in _renames(project)
        if SPSS_NAME.match(old) and SPSS_NAME.match(new)
    ]
    if renames:
        lines += [
            _("* Nouveaux noms acceptés, en premier : la suite porte sur ces noms."),
            "RENAME VARIABLES",
            *(f"  ({old} = {new})" for old, new in renames[:-1]),
            f"  ({renames[-1][0]} = {renames[-1][1]}).",
            "",
        ]
    for entry in project.variables:
        d = decisions(entry)
        if not SPSS_NAME.match(d.name) or d.name.endswith("."):
            lines.append(
                _("* {name} : nom de variable non valide pour SPSS, omise.").format(name=d.name)
            )
            continue
        block = []
        if d.label:
            block.append(f"VARIABLE LABELS {d.name} {_spss_text(d.label)}.")
        if d.labels:
            pairs = " ".join(
                f"{_spss_code(code, d.string)} {_spss_text(label)}" for code, label in d.labels
            )
            block.append(f"VALUE LABELS {d.name} {pairs}.")
        missing = _spss_missing(d)
        if missing:
            block.append(missing)
        if d.measure:
            block.append(f"VARIABLE LEVEL {d.name} ({SPSS_LEVELS[d.measure]}).")
        if block:
            lines += [*block, ""]
    lines += _spss_reversed(project)
    return "\n".join(lines).rstrip("\n") + "\n"


def _spss_missing(d: Decisions) -> str:
    if not d.missing and d.missing_range is None:
        return ""
    allowed = 1 if d.missing_range else SPSS_MAX_DISCRETE
    if d.string and d.missing_range:
        return _("* {name} : intervalle de codes manquants impossible pour un texte.").format(
            name=d.name
        )
    if len(d.missing) > allowed:
        return _(
            "* {name} : SPSS accepte au plus {n} codes manquants ; à déclarer à la main : {codes}."
        ).format(name=d.name, n=allowed, codes=w.codes(d.missing))
    parts = []
    if d.missing_range:
        low, high = d.missing_range
        parts.append(f"{_number(low)} THRU {_number(high)}")
    parts += [_spss_code(c, d.string) for c in d.missing]
    return f"MISSING VALUES {d.name} ({', '.join(parts)})."


def _spss_reversed(project: Project) -> list[str]:
    items = _reversed(project)
    if not items:
        return []
    lines = [_("* Items inversés selon l'équipe : non recodés. Suggestion, à faire vous-même.")]
    for group_id, entry in items:
        lines.append(_reversed_line("*", group_id, entry, _spss_compute))
    return [*lines, ""]


def _spss_compute(name: str, total: str) -> str:
    return f"COMPUTE {name}_inv = {total} - {name}."


# --- R --------------------------------------------------------------------------------------


def _r_text(text: str) -> str:
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _r_code(code: Code, string: bool) -> str:
    return _r_text(str(code)) if string else _number(code)


R_ENCODINGS = {"utf-8": "UTF-8", "utf-8-sig": "UTF-8-BOM", "cp1252": "CP1252"}


def _r_csv(project: Project, name: str) -> str:
    """read.csv as the tool read the file (v0.13): its separator, decimal mark and encoding,
    the names as they are, an empty cell or a missing-value token as NA, and the columns the
    tool read as text kept as text (a code "007" stays "007")."""
    source = project.source
    encoding = source.encoding or "utf-8"
    parts = [name]
    if source.delimiter and source.delimiter != ",":
        parts.append(f"sep = {_r_text(source.delimiter)}")
    if source.decimal and source.decimal != ".":
        parts.append(f"dec = {_r_text(source.decimal)}")
    parts.append(f"fileEncoding = {_r_text(R_ENCODINGS.get(encoding.lower(), encoding))}")
    tokens = ", ".join(_r_text(t) for t in ("", *MISSING_TOKENS))
    parts += [f"na.strings = c({tokens})", "check.names = FALSE"]
    strings = [e.name for e in project.variables if e.file.storage_type == "string"]
    if strings:
        classes = ", ".join(f'{_r_text(n)} = "character"' for n in strings)
        parts.append(f"colClasses = c({classes})")
    return f"read.csv({', '.join(parts)})"


def _r_reader(project: Project) -> str:
    name = _r_text(project.source.name)
    return {
        "sav": f"haven::read_sav({name}, user_na = TRUE)",
        "dta": f"haven::read_dta({name})",
        "sas7bdat": f"haven::read_sas({name})",
        "xlsx": f"readxl::read_excel({name})",
    }.get(project.source.format) or _r_csv(project, name)


def r_script(project: Project, today: str) -> str:
    lines = [
        *_header(project, "#", today),
        _("# Avant : chargez vos données dans un objet nommé « donnees », par exemple"),
        f"#   donnees <- {_r_reader(project)}",
        *(
            [
                _(
                    "# user_na = TRUE garde les codes manquants déjà déclarés dans le fichier ; "
                    "sans lui, haven les remplace par NA."
                )
            ]
            if project.source.format == "sav"
            else []
        ),
        _('# Après : haven::write_sav(donnees, "copie-documentee.sav") pour une copie.'),
        _("# Les niveaux de mesure ne sont pas appliqués : haven ne les écrit pas."),
        "",
        "library(haven)",
        "",
        "ddict_vecteur <- function(x) {",
        '  if (inherits(x, "haven_labelled")) x <- vctrs::vec_data(x)',
        "  x",
        "}",
        "",
    ]
    renames = _renames(project)
    if renames:
        lines += [
            _("# Nouveaux noms acceptés, en premier : la suite porte sur ces noms."),
            "ddict_noms <- c(",
            *(f"  {_r_text(old)} = {_r_text(new)}," for old, new in renames[:-1]),
            f"  {_r_text(renames[-1][0])} = {_r_text(renames[-1][1])}",
            ")",
            "names(donnees)[match(names(ddict_noms), names(donnees))] <- ddict_noms",
            "",
        ]
    for entry in project.variables:
        d = decisions(entry)
        column = f"donnees[[{_r_text(d.name)}]]"
        if d.labels or d.missing or d.missing_range:
            arguments = [f"ddict_vecteur({column})"]
            if d.labels:
                pairs = ", ".join(
                    f"{_r_text(label)} = {_r_code(code, d.string)}" for code, label in d.labels
                )
                arguments.append(f"labels = c({pairs})")
            if d.missing:
                codes = ", ".join(_r_code(c, d.string) for c in d.missing)
                arguments.append(f"na_values = c({codes})")
            if d.missing_range:
                low, high = d.missing_range
                arguments.append(f"na_range = c({_number(low)}, {_number(high)})")
            if d.label:
                arguments.append(f"label = {_r_text(d.label)}")
            lines.append(f"{column} <- labelled_spss(")
            lines += [f"  {a}," for a in arguments[:-1]] + [f"  {arguments[-1]}", ")"]
        elif d.label:
            lines.append(f'attr({column}, "label") <- {_r_text(d.label)}')
    items = _reversed(project)
    if items:
        lines += [
            "",
            _("# Items inversés selon l'équipe : non recodés. Suggestion, à faire vous-même :"),
        ]
        lines += [_reversed_line("#", g, e, _r_compute) for g, e in items]
    return "\n".join(lines).rstrip("\n") + "\n"


def _r_compute(name: str, total: str) -> str:
    column = f"donnees[[{_r_text(name)}]]"
    return f"donnees[[{_r_text(name + '_inv')}]] <- {total} - {column}"


# --- Shared ---------------------------------------------------------------------------------


def _reversed_line(
    comment: str, group_id: str, entry: VariableEntry, compute: Callable[[str, str], str]
) -> str:
    r = entry.theoretical_range
    if r is None:
        return _("{c} {name} ({group}) : étendue théorique non renseignée.").format(
            c=comment, name=w.final_name(entry), group=group_id
        )
    total = w.number(r.min + r.max).replace(",", ".")
    return f"{comment} {compute(w.final_name(entry), total)}"


WRITERS = {"spss": spss, "r": r_script}


@in_language
def render_syntax(project: Project, program: str, today: str | None = None) -> str:
    return WRITERS[program](project, today or date.today().isoformat())


@in_language
def write_syntax(project: Project, paths: dict[str, Path], today: str | None = None) -> None:
    for program, path in paths.items():
        with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(render_syntax(project, program, today))
