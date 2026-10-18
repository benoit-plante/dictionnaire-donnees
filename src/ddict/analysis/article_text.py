"""The parts of the article the Method and the Results do not write (v0.13, step 5, D-106,
D-107), as the validated sheet `docs/plan-analyse-article.md` gives them: the title page
and the abstract (holes), the Introduction (N1 to N4), the paragraph "Plan d'analyse" of
the Method (PL1 to PL8), the Discussion (D1 to D8) and the References.

Each sentence is whole, translated as one. Every fact comes from the plan, the codebook or
the notebook; what the tool cannot know is a hole. No wording judges an hypothesis: the
observed direction is a fact, saying whether it supports the hypothesis is the team's.
"""

from __future__ import annotations

import unicodedata

from ddict.analysis import plan_notebook as pn
from ddict.analysis.apa import Run, Text, hole, it, marked, rich
from ddict.analysis.catalogue import CHOICES, OPTIONS, ROLES, TITLES
from ddict.analysis.method import _used
from ddict.analysis.method_text import _lower
from ddict.analysis.notebook import Notebook
from ddict.analysis.prereg import KINDS, _alpha, _families, _name, long_date
from ddict.i18n import N_, Texts, _, semicolon
from ddict.project.model import Amendment, Project, VariableRef

ORIGINS = Texts(
    {
        "primary": N_("primaires, recueillies par l'équipe pour cette étude"),
        "secondary": N_("secondaires"),
    }
)
WRITTEN = Texts(
    {
        "before_creation": N_("avant la création des données"),
        "before_observation": N_("avant que quiconque ait observé les données"),
        "before_access": N_("avant d'accéder aux données"),
        "before_analysis": N_("après avoir accédé aux données, avant de les analyser"),
        "after_analysis": N_("après une première analyse des données"),
    }
)
CORRECTIONS = Texts({"none": N_("aucune"), "holm": N_("Holm"), "bonferroni": N_("Bonferroni")})
# Numbers below ten in words (APA), in the feminine: "hypothèses", "fois".
WORDS = (
    N_("zéro"), N_("une"), N_("deux"), N_("trois"), N_("quatre"), N_("cinq"), N_("six"),
    N_("sept"), N_("huit"), N_("neuf"),
)  # fmt: skip
HOLM = (
    "Holm, S. (1979). A simple sequentially rejective multiple test procedure. ",
    "Scandinavian Journal of Statistics",
    ", ",
    "6",
    "(2), 65–70.",
)
FELDT = (
    "Feldt, L. S. (1965). The approximate sampling distribution of Kuder-Richardson "
    "reliability coefficient twenty. ",
    "Psychometrika",
    ", ",
    "30",
    "(3), 357–370. https://doi.org/10.1007/BF02289499",
)


def in_words(n: int) -> str:
    from ddict import i18n

    return i18n._translated(WORDS[n]) if 0 <= n < len(WORDS) else str(n)


def _and(items: list[str]) -> str:
    """ "H1, H2 et H3"."""
    if len(items) < 2:
        return "".join(items)
    return ", ".join(items[:-1]) + _(" et ") + items[-1]


def _sentences(parts: list[Text]) -> Text:
    found: list[Run] = []
    for part in parts:
        if part:
            if found:
                found.append(Run(" "))
            found.extend(part)
    return tuple(found)


# --- The title page, the abstract, the Introduction (§ 9). ---


def title_page() -> list[Text]:
    return [(hole(_("titre")),), (hole(_("auteurs et affiliations")),)]


def abstract() -> list[Text]:
    return [(hole(_("résumé")),), marked(_("Mots-clés : {words}"), words=hole(_("mots-clés")))]


def introduction(project: Project) -> list[Text]:
    """N1, then the hypotheses of a frozen plan, one per line."""
    found: list[Text] = [(hole(_("contexte, revue des travaux et justification de l'étude")),)]
    if not pn.frozen(project):
        return found
    hypotheses = project.plan.hypotheses
    confirmatory = [h for h in hypotheses if h.kind == "confirmatory"]
    exploratory = [h for h in hypotheses if h.kind == "exploratory"]
    if confirmatory:
        found.append(rich(_("Les hypothèses suivantes ont été formulées :")))
        found += [rich(f"{h.id}. {h.statement}") for h in confirmatory]
    if exploratory:
        found.append(rich(_("Les questions suivantes ont été examinées de façon exploratoire :")))
        found += [rich(f"{h.id}. {h.statement}") for h in exploratory]
    return found


# --- The paragraph "Plan d'analyse" of the Method (§ 10). ---


def _ref_names(project: Project, refs: list) -> str:
    return ", ".join(_name(project, VariableRef.model_validate(r)) for r in refs)


def _changed(key: str, before: dict, after: dict, project: Project) -> list[str]:
    """What changed in one field of an hypothesis, in plain words."""
    old, new = before.get(key), after.get(key)
    if key == "statement":
        return [_("énoncé reformulé")]
    if key == "analysis":
        return [
            _("{new} au lieu de {old}").format(new=TITLES.get(new, new), old=TITLES.get(old, old))
        ]
    if key == "options":
        old, new = old or {}, new or {}
        found = []
        for option in sorted(set(old) | set(new)):
            if option != "alternative" and old.get(option) != new.get(option):
                found.append(
                    _("{option} : {new} au lieu de {old}").format(
                        option=OPTIONS.get(option, option).lower(),
                        new=CHOICES.get(new.get(option), new.get(option) or "—"),
                        old=CHOICES.get(old.get(option), old.get(option) or "—"),
                    )
                )
        return found
    if key == "roles":
        old, new = old or {}, new or {}
        found = []
        for role in sorted(set(old) | set(new)):
            if old.get(role) != new.get(role):
                found.append(
                    _("{role} : {new} au lieu de {old}").format(
                        role=ROLES.get(role, role).lower(),
                        new=_ref_names(project, new.get(role, [])) or "—",
                        old=_ref_names(project, old.get(role, [])) or "—",
                    )
                )
        return found
    if key == "effect":
        return [_("effet testé modifié")]
    if key == "direction":
        return [_("sens attendu modifié")]
    if key == "kind":
        return [
            _("{new} au lieu de {old}").format(new=KINDS.get(new, new), old=KINDS.get(old, old))
        ]
    if key == "family":
        return [
            _("famille : {new} au lieu de {old}").format(
                new=new or _("aucune"), old=old or _("aucune")
            )
        ]
    if key == "correction":
        return [
            _("correction : {new} au lieu de {old}").format(
                new=CORRECTIONS.get(new, new), old=CORRECTIONS.get(old, old)
            )
        ]
    if key == "alpha":
        return [
            _("seuil α : {new} au lieu de {old}").format(
                new=_alpha(new) if new is not None else "—",
                old=_alpha(old) if old is not None else "—",
            )
        ]
    if key == "sample_size":
        return [_("taille d'échantillon reformulée")]
    if key == "missing":
        return [_("traitement des valeurs manquantes modifié")]
    if key == "data_origin":
        return [_("origine des données modifiée")]
    if key == "data_status":
        return [_("état des données modifié")]
    return []


def amendment_summary(project: Project, amendment: Amendment) -> str:
    """ "méthode : Spearman au lieu de Pearson", "hypothèse ajoutée"..."""
    if amendment.change == "added":
        return _("hypothèse ajoutée")
    if amendment.change == "removed":
        return _("hypothèse retirée")
    keys = list(dict.fromkeys([*amendment.before, *amendment.after]))
    found = [t for key in keys for t in _changed(key, amendment.before, amendment.after, project)]
    return ", ".join(found) or _("hypothèse modifiée")


def _target(amendment: Amendment) -> str:
    return _("les règles générales") if amendment.target == "rules" else amendment.target


def amendment_line(project: Project, amendment: Amendment) -> str:
    """ "le 2 novembre 2026, pour H2 (méthode : Spearman au lieu de Pearson) : {reason}"."""
    return _("le {date}, pour {target} ({summary}) : {reason}").format(
        date=long_date(amendment.date),
        target=_target(amendment),
        summary=amendment_summary(project, amendment),
        reason=_lower(amendment.reason.rstrip(". ")),
    )


def _count(n: int, one: str, many: str) -> str:
    return (one if n == 1 else many).format(n=in_words(n))


def _uses_holm(project: Project) -> bool:
    return project.plan.correction == "holm" and bool(_families(project))


def plan_paragraph(project: Project, notebook: Notebook) -> Text:
    """PL1 to PL8; only with a frozen plan."""
    plan = project.plan
    frozen = plan.frozen
    parts: list[Text] = []
    origin = (
        rich(ORIGINS[plan.data_origin]) if plan.data_origin else (hole(_("origine des données")),)
    )
    written = (
        rich(WRITTEN[plan.data_status])
        if plan.data_status
        else (hole(_("état des données quand le plan a été écrit")),)
    )
    parts.append(
        marked(
            _(
                "Les données sont {origin}. Selon l'équipe, le plan d'analyse a été écrit "
                "{written}. Il a été arrêté dans l'outil le {date}. {registry}"
            ),
            origin=origin,
            written=written,
            date=long_date(frozen.date),
            registry=hole(_("lieu et identifiant du préenregistrement, s'il y en a un")),
        )
    )
    k = sum(h.kind == "confirmatory" for h in plan.hypotheses)
    e = len(plan.hypotheses) - k
    counted = []
    if k:
        counted.append(
            _count(k, _("{n} hypothèse confirmatoire"), _("{n} hypothèses confirmatoires"))
        )
    if e:
        counted.append(
            _count(e, _("{n} exploratoire"), _("{n} exploratoires"))
            if k
            else _count(e, _("{n} hypothèse exploratoire"), _("{n} hypothèses exploratoires"))
        )
    if counted:
        parts.append(rich(_("Il comptait {counted}.").format(counted=_and(counted))))
    if plan.alpha is not None:
        parts.append(rich(_("Le seuil α était fixé à {alpha}.").format(alpha=_alpha(plan.alpha))))
    families = _families(project)
    if families and plan.correction != "none":
        listed = semicolon().join(f"{key} ({', '.join(ids)})" for key, ids in families.items())
        template = (
            _(
                "Les valeurs de {p} ont été corrigées par la méthode de Holm (1979) au sein de "
                "chaque famille d'hypothèses : {families}."
            )
            if plan.correction == "holm"
            else _(
                "Les valeurs de {p} ont été corrigées par la méthode de Bonferroni au sein de "
                "chaque famille d'hypothèses : {families}."
            )
        )
        parts.append(marked(template, p=it("p"), families=listed))
    one_sided = [
        h.id for h in plan.hypotheses if h.options.get("alternative", "two_sided") != "two_sided"
    ]
    if len(one_sided) == 1:
        parts.append(
            rich(_("Le test de {id} était unilatéral, dans le sens attendu.").format(
                id=one_sided[0]
            ))
        )  # fmt: skip
    elif one_sided:
        parts.append(
            rich(_("Les tests de {ids} étaient unilatéraux, dans le sens attendu.").format(
                ids=_and(one_sided)
            ))
        )  # fmt: skip
    amendments = plan.amendments
    if amendments:
        times = _count(len(amendments), _("une fois"), _("{n} fois"))
        parts.append(
            rich(
                _("Le plan a été modifié {times} après avoir été arrêté : {changes}.").format(
                    times=times,
                    changes=semicolon().join(amendment_line(project, a) for a in amendments),
                )
            )
        )
    if frozen.prior:
        ids = [p.hypothesis for p in frozen.prior]
        template = (
            _(
                "Le jour où le plan a été arrêté, le carnet d'analyses contenait déjà l'analyse "
                "prévue pour {ids}."
            )
            if len(ids) == 1
            else _(
                "Le jour où le plan a été arrêté, le carnet d'analyses contenait déjà les "
                "analyses prévues pour {ids}."
            )
        )
        parts.append(rich(template.format(ids=_and(ids))))
    states = [pn.state(notebook, project, e) for e in notebook.entries if e.retained]
    if any(s is not None and s.kind in ("variant", "exploratory") for s in states):
        parts.append(rich(_("Les autres analyses sont présentées comme exploratoires.")))
    return _sentences(parts)


def closing(project: Project) -> list[str]:
    """The plan's lines at the end of the document: fingerprint, date, amendments."""
    frozen = project.plan.frozen
    if frozen is None:
        return []
    lines = [
        _("Plan arrêté dans l'outil le {date} ; empreinte du plan : {fingerprint}.").format(
            date=long_date(frozen.date), fingerprint=frozen.fingerprint[:12]
        )
    ]
    if project.plan.amendments:
        lines.append(_("Amendements du plan :"))
        lines += [amendment_line(project, a) for a in project.plan.amendments]
    return lines


# --- The References (§ 13). ---


def _sort_key(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def sources(project: Project, notebook: Notebook) -> list[str]:
    """The codebook's sources the article speaks of, once each, as the team wrote them:
    instruments, scorings, theoretical ranges and thresholds of the variables and the
    scored groups, and the documented questionnaire."""
    found: list[str] = []
    for group in project.groups:
        if group.scoring is None:
            continue
        if group.instrument_name is not None:
            found.append(group.instrument_name.source)
        found.append(group.scoring.source)
        if group.theoretical_range is not None:
            found.append(group.theoretical_range.source)
        found += [t.source for t in group.thresholds]
    used = set(_used(project, notebook))
    from ddict.export import wording as w

    for entry in project.variables:
        if w.final_name(entry) not in used:
            continue
        if entry.theoretical_range is not None:
            found.append(entry.theoretical_range.source)
        found += [t.source for t in entry.thresholds]
    if project.questionnaire is not None:
        found.append(project.questionnaire.file_name)
    unique = {s.strip(): None for s in found if s and s.strip()}
    return sorted(unique, key=_sort_key)


def _reference(parts: tuple[str, ...]) -> Text:
    """A fixed reference: the journal and the volume in italics."""
    return rich(parts[0], it(parts[1]), parts[2], it(parts[3]), parts[4])


def references(project: Project, notebook: Notebook, *, feldt: bool) -> list[Text]:
    """The warning, the codebook's sources, and the tool's fixed references for what its
    text cites (Holm when PL4 names it, Feldt when I6 gives an interval)."""
    found: list[Text] = [
        (
            Run(
                _(
                    "[à vérifier : les sources ci-dessous viennent du codebook, telles que "
                    "l'équipe les a écrites ; certaines ne sont peut-être pas des références "
                    "bibliographiques (une page du questionnaire, par exemple). Mettez-les au "
                    "format APA et ajoutez les autres références.]"
                ),
                hole=True,
            ),
        )
    ]
    fixed: list[tuple[str, Text]] = [(s, rich(s)) for s in sources(project, notebook)]
    if pn.frozen(project) and _uses_holm(project):
        fixed.append((HOLM[0], _reference(HOLM)))
    if feldt:
        fixed.append((FELDT[0], _reference(FELDT)))
    seen = set()
    for key, text in sorted(fixed, key=lambda f: _sort_key(f[0])):
        if key not in seen:
            seen.add(key)
            found.append(text)
    return found


# --- The Discussion (§ 12): without a frozen plan. ---


def discussion_frame(project: Project) -> tuple[list[Text], list[Text]]:
    """D1, and D7 and D8: what opens and what closes the Discussion."""
    return (
        [(hole(_("rappel du but de l'étude")),)],
        [(hole(_("limites")),), (hole(_("conclusion")),)],
    )


def discussion_without_plan() -> list[Text]:
    return [(hole(_("discussion des résultats")),)]
