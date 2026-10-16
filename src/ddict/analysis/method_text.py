"""The paragraphs of the Method (v0.12, step 7, D-097), written by templates from the
codebook and the facts of `ddict.analysis.method`, as the validated sheet
`docs/methode-gabarits.md` gives them (§ 5 to 7): Participants (P1 to P4), Instruments (I1
to I6, one paragraph per scored group) and Analyses (A1 to A5).

Each sentence is whole, translated as one. A fact the codebook does not hold becomes a
hole, "[à compléter : …]", never a guess; no wording judges ("excellent reliability").
"""

from __future__ import annotations

from ddict.analysis.apa import Run, Text, hole, it, marked, rich
from ddict.analysis.book import Codebook
from ddict.analysis.data import PreparedData
from ddict.analysis.method import Facts
from ddict.analysis.report import versions
from ddict.analysis.results import bounded, number
from ddict.export import wording as w
from ddict.i18n import _, semicolon
from ddict.project import scoring as scorings
from ddict.project.decisions import is_accepted
from ddict.project.model import Group, Project


def _lower(text: str) -> str:
    """A label inside a sentence: its first letter in lower case, unless it begins an
    acronym ("QFS")."""
    if len(text) > 1 and text[1].isupper():
        return text
    return text[:1].lower() + text[1:]


def _join(parts: list[Text], separator: str) -> Text:
    found: list[Run] = []
    for i, part in enumerate(parts):
        if i:
            found.append(Run(separator))
        found.extend(part)
    return tuple(found)


def _sentences(parts: list[Text]) -> Text:
    return _join([p for p in parts if p], " ")


def _whole(value: float) -> str:
    return number(value, 0) if float(value).is_integer() else number(value)


def _percent(value: float) -> str:
    shown = number(value, 1)
    if shown.endswith((",0", ".0")):  # "50 %", not "50,0 %"
        shown = shown[:-2]
    return _("{value} %").format(value=shown)


# --- Participants (P1 to P4). ---


def participants(project: Project, found: Facts, figure: int | None) -> Text:
    flow = found.flow
    reasons = {r.id: r.reason for r in project.exclusions.rules}
    parts = [marked(_("Au total, {n} personnes ont répondu au questionnaire."), n=str(flow.start))]
    if flow.excluded:
        listed = [
            marked(
                _("{reason} ({n} = {count})"),
                reason=_lower(reasons.get(rule, rule)),
                n=it("n"),
                count=str(count),
            )
            for rule, count in flow.excluded
        ]
        parts.append(
            marked(
                _(
                    "{n} ont été exclues, pour les raisons suivantes, dans cet ordre : {reasons} "
                    "(Figure {figure})."
                ),
                n=str(flow.start - flow.analysed),
                reasons=_join(listed, semicolon()),
                figure=str(figure),
            )
        )
    parts.append(marked(_("L'échantillon analysé compte {n} personnes."), n=str(flow.analysed)))
    if found.described:
        items = []
        for d in found.described:
            label = _lower(d.label)
            if d.categories:
                shares = [
                    rich(f"{_lower(category)}, {_percent(percent)}")
                    for _code, category, percent in d.categories
                ]
                items.append(
                    marked(_("{label} ({shares})"), label=label, shares=_join(shares, semicolon()))
                )
            else:
                template = (
                    _("{label} ({m} = {mean}, {sd} = {sdv})")
                    if d.n == flow.analysed
                    else _("{label} ({m} = {mean}, {sd} = {sdv}, {n} = {count})")
                )
                items.append(
                    marked(
                        template,
                        label=label,
                        m=it("M"),
                        mean=number(d.mean),
                        sd=it(_("ÉT")),
                        sdv=number(d.sd),
                        n=it("n"),
                        count=str(d.n),
                    )
                )
        parts.append(
            marked(
                _("Elles sont décrites par les variables suivantes : {items}."),
                items=_join(items, semicolon()),
            )
        )
    return _sentences(parts)


# --- Instruments (I1 to I6). ---


def _what(group: Group) -> Text:
    """What the group measures: its label, given or accepted by a person; the label the
    tool writes ("6 items, codes de 1 à 4") says nothing of it."""
    label = group.descriptive_label
    if is_accepted(label) and label.origin != "computed" and label.value:
        return rich(_lower(label.value))
    return (hole(_("ce que mesure le groupe {group}").format(group=group.group_id)),)


def _ends(book: Codebook, first: str, low: float, high: float) -> tuple[str, str] | None:
    labels = book.value_labels(first)
    found = labels.get(low, labels.get(int(low))), labels.get(high, labels.get(int(high)))
    return found if all(found) else None


def _instrument(project: Project, prepared: PreparedData, found: Facts, group: Group) -> Text:
    scoring = group.scoring
    names = w.names_of(project)
    if not scorings.structured(scoring):
        return rich(
            hole(_("description de l'instrument du groupe {group}").format(group=group.group_id)),
            " ",
            _("« {note} »").format(note=scoring.note),
        )
    book = Codebook(project, prepared)
    k = len(scoring.items)
    low, high = scoring.scale_min, scoring.scale_max
    if group.instrument_name is not None:
        named = rich(group.instrument_name.value, f" ({group.instrument_name.source})")
    else:
        named = (
            hole(_("nom et source de l'instrument du groupe {group}").format(group=group.group_id)),
        )
    ends = _ends(book, names[scoring.items[0]], low, high)
    if ends is not None:
        first = marked(
            _(
                "L'instrument {instrument} mesure {what} au moyen de {k} items, notés de {low} "
                "({low_label}) à {high} ({high_label})."
            ),
            instrument=named,
            what=_what(group),
            k=str(k),
            low=_whole(low),
            low_label=_lower(ends[0]),
            high=_whole(high),
            high_label=_lower(ends[1]),
        )
    else:
        first = marked(
            _(
                "L'instrument {instrument} mesure {what} au moyen de {k} items, notés de {low} à "
                "{high} {missing}."
            ),
            instrument=named,
            what=_what(group),
            k=str(k),
            low=_whole(low),
            high=_whole(high),
            missing=(hole(_("étiquettes des extrémités")),),
        )
    parts = [first]
    reversed_items = [names[n] for n in scorings.reversed_items(group, scoring)]
    if len(reversed_items) == 1:
        parts.append(
            rich(
                _("L'item {item} est inversé avant le calcul du score.").format(
                    item=reversed_items[0]
                )
            )
        )
    elif reversed_items:
        parts.append(
            rich(
                _("Les items {items} sont inversés avant le calcul du score.").format(
                    items=", ".join(reversed_items)
                )
            )
        )
    total = (k * low, k * high) if scoring.aggregation == "sum" else (low, high)
    template = (
        _("Le score ({name}) est la somme des items, de {low} à {high}.")
        if scoring.aggregation == "sum"
        else _("Le score ({name}) est la moyenne des items, de {low} à {high}.")
    )
    parts.append(
        rich(template.format(name=scoring.score_name, low=_whole(total[0]), high=_whole(total[1])))
    )
    if scoring.min_items_answered is not None:
        if scoring.aggregation == "mean":
            template = _(
                "Il est calculé quand au moins {m} items sur {k} sont répondus ; c'est "
                "alors la moyenne des items répondus."
            )
        elif scoring.missing_rule == "prorate":
            template = _(
                "Il est calculé quand au moins {m} items sur {k} sont répondus ; un item "
                "manquant est remplacé par la moyenne des items répondus de la "
                "personne."
            )
        else:
            template = _(
                "Il est calculé quand au moins {m} items sur {k} sont répondus ; c'est "
                "alors la somme des items répondus."
            )
        parts.append(rich(template.format(m=scoring.min_items_answered, k=k)))
    instrument_source = group.instrument_name.source if group.instrument_name else None
    if scoring.source != instrument_source:
        parts.append(rich(_("La cotation suit {source}.").format(source=scoring.source)))
    reliability = next((r for r in found.reliabilities if r.group == group.group_id), None)
    if reliability is not None and reliability.alpha is not None:
        parts.append(
            marked(
                _(
                    "Sur l'échantillon analysé, l'alpha de Cronbach est de {alpha} (IC 95 % {ci}, "
                    "{n} = {count})."
                ),
                alpha=bounded(reliability.alpha),
                ci=_("[{low} ; {high}]").format(
                    low=bounded(reliability.low), high=bounded(reliability.high)
                ),
                n=it("n"),
                count=str(reliability.n),
            )
        )
    else:
        parts.append((hole(_("fidélité, trop peu de réponses complètes")),))
    return _sentences(parts)


def instruments(project: Project, prepared: PreparedData, found: Facts) -> list[Text]:
    """One paragraph per group that has a scoring, in the order of the groups."""
    return [
        _instrument(project, prepared, found, g) for g in project.groups if g.scoring is not None
    ]


# --- Analyses (A1 to A5). ---


def _method_sentences(analysis: str, method: str, post_hoc: str) -> list[Text]:
    t, d, v, b = it("t"), it("d"), it("V"), it("b")
    if analysis == "table1":
        return [
            rich(
                _(
                    "Les caractéristiques des participants sont décrites par la moyenne et "
                    "l'écart-type, ou par l'effectif et le pourcentage."
                )
            )
        ]
    if analysis == "t_test" and method == "mann_whitney":
        return [
            rich(
                _(
                    "Deux distributions ont été comparées par le test de Mann-Whitney ; la "
                    "taille d'effet est la corrélation bisériale des rangs."
                )
            )
        ]
    if analysis == "t_test":
        template = (
            _(
                "Deux moyennes ont été comparées par le test {t} de Student, qui suppose des "
                "variances égales ; la taille d'effet est le {d} de Cohen, avec son intervalle de "
                "confiance à 95 %."
            )
            if method == "student"
            else _(
                "Deux moyennes ont été comparées par le test {t} de Welch, qui ne suppose "
                "pas des variances égales ; la taille d'effet est le {d} de Cohen, avec son "
                "intervalle de confiance à 95 %."
            )
        )
        return [marked(template, t=t, d=d)]
    if analysis == "anova" and method == "kruskal_wallis":
        return [
            rich(
                _(
                    "Plusieurs distributions ont été comparées par le test de Kruskal-Wallis ; "
                    "la taille d'effet est ε²."
                )
            )
        ]
    if analysis == "anova":
        found = [
            rich(
                _(
                    "Plusieurs moyennes ont été comparées par une analyse de variance à un "
                    "facteur ; les tailles d'effet sont η² et ω²."
                )
            )
        ]
        if post_hoc == "tukey":
            found.append(
                rich(_("Les groupes ont été comparés deux à deux par la méthode de Tukey."))
            )
        return found
    if analysis == "chi_square" and method == "fisher":
        return [
            rich(
                _(
                    "L'association entre deux variables catégorielles a été testée par le "
                    "test exact de Fisher."
                )
            )
        ]
    if analysis == "chi_square":
        return [
            marked(
                _(
                    "L'association entre deux variables catégorielles a été testée par le "
                    "khi-carré de Pearson ; la taille d'effet est le {v} de Cramér."
                ),
                v=v,
            )
        ]
    if analysis == "correlation" and method == "spearman":
        return [rich(_("Les liens entre variables sont décrits par la corrélation de Spearman."))]
    if analysis == "correlation":
        return [
            rich(
                _(
                    "Les liens entre variables continues sont décrits par la corrélation de "
                    "Pearson, avec son intervalle de confiance à 95 %."
                )
            )
        ]
    return [
        marked(
            _(
                "Les liens entre une variable dépendante et ses prédicteurs ont été estimés "
                "par une régression linéaire ; les coefficients sont donnés bruts ({b}, avec "
                "leur intervalle de confiance à 95 %) et standardisés (β)."
            ),
            b=b,
        )
    ]


def analyses(found: Facts, script: str) -> Text:
    parts: list[Text] = []
    codes = [
        f"{', '.join(w.code_text(c) if not isinstance(c, str) else c for c in listed)} ({name})"
        for name, listed in found.missing
    ]
    if codes:
        many = len(codes) > 1 or len(found.missing[0][1]) > 1
        template = (
            _("Les codes {codes} ont été traités comme des valeurs manquantes.")
            if many
            else _("Le code {codes} a été traité comme une valeur manquante.")
        )
        parts.append(rich(template.format(codes=semicolon().join(codes))))
    parts.append(
        rich(
            _(
                "Les valeurs manquantes ont été retirées analyse par analyse : chaque "
                "analyse porte sur les personnes qui ont répondu à toutes ses "
                "variables."
            )
        )
    )
    for analysis, method, post_hoc in found.methods:
        parts += _method_sentences(analysis, method, post_hoc)
    parts.append(
        marked(
            _("Les valeurs de {p} sont données exactes, à trois décimales ({p} < ,001 en deçà)."),
            p=it("p"),
        )
    )
    made = versions()
    others = ", ".join(f"{k} {v}" for k, v in made.items() if k != "dictionnaire-donnees")
    parts.append(
        rich(
            _(
                "Les analyses ont été faites avec dictionnaire-donnees {version} "
                "({others}) ; un script R joint ({script}) les refait et donne les mêmes "
                "valeurs."
            ).format(version=made["dictionnaire-donnees"], others=others, script=script)
        )
    )
    return _sentences(parts)
