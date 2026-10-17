"""The preregistration (v0.13, step 4, D-109): a document written from the plan and the
codebook, never from the data, as the validated sheet `docs/plan-analyse-article.md` (§ 8)
gives it. Two templates, chosen by the origin of the data the team declares: OSF Prereg
(Bowman et al., 2020, CC0 1.0) for primary data, the template for secondary data analysis
(van den Akker et al., 2021, CC BY 4.0) for secondary data; their questions translated into
French by us, with the same statement of origin at the head of the document.

No count and no result enters it: no N, no count per exclusion rule, no observed alpha, no
statistic. What the tool cannot know stays a hole, "[à compléter : …]", highlighted in Word;
the prior knowledge of the data always does. The tool never writes that the study was
preregistered: the team registers it, or not.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ddict import i18n
from ddict.analysis.apa import ApaDocument, Section, Text, apa, hole, it, marked, rich
from ddict.analysis.catalogue import CHOICES, OPTIONS, ROLES, TITLES
from ddict.analysis.method import _missing
from ddict.analysis.method_text import scale_description
from ddict.analysis.notebook import NotebookError, resolve
from ddict.analysis.planning import EFFECT_NAMES, plan_fingerprint
from ddict.analysis.report import versions
from ddict.export import wording as w
from ddict.export.preparation import plan as preparation_plan
from ddict.i18n import N_, Texts, _, semicolon
from ddict.project import exclusions, fingerprint
from ddict.project.model import Hypothesis, Project, VariableRef
from ddict.questionnaire.labels import accepted_labels

SUFFIX = "-preenregistrement"
MONTHS = (
    N_("janvier"), N_("février"), N_("mars"), N_("avril"), N_("mai"), N_("juin"),
    N_("juillet"), N_("août"), N_("septembre"), N_("octobre"), N_("novembre"), N_("décembre"),
)  # fmt: skip
STATUSES = Texts(
    {
        "before_creation": N_(
            "Avant la création des données : elles n'avaient pas encore été recueillies."
        ),
        "before_observation": N_(
            "Avant toute observation : les données existaient, mais personne ne les avait "
            "encore observées."
        ),
        "before_access": N_(
            "Avant l'accès : les données existaient, mais ni l'équipe ni ses collaborateurs n'y "
            "avaient accédé."
        ),
        "before_analysis": N_(
            "Avant l'analyse : l'équipe avait accédé aux données, sans faire d'analyse liée au "
            "plan."
        ),
        "after_analysis": N_(
            "Après une analyse : l'équipe avait déjà analysé une partie des données "
            "(statistiques descriptives, analyses préliminaires…)."
        ),
    }
)
KINDS = Texts({"confirmatory": N_("confirmatoire"), "exploratory": N_("exploratoire")})
# A variable's role in an hypothesis, in the singular.
ROLE_OF = Texts(
    {
        "outcome": N_("variable dépendante"),
        "group": N_("variable de groupe"),
        "rows": N_("variable en lignes"),
        "columns": N_("variable en colonnes"),
        "predictors": N_("prédicteur"),
        "variables": N_("variable de la corrélation"),
    }
)
TESTS = Texts(
    {
        "two_sided": N_("test bilatéral"),
        "greater": N_("test unilatéral, le premier groupe plus élevé"),
        "less": N_("test unilatéral, le premier groupe moins élevé"),
    }
)


def long_date(iso: str) -> str:
    """ "2026-10-18" -> "18 octobre 2026" (in the language in use)."""
    found = date.fromisoformat(iso)
    month = i18n._translated(MONTHS[found.month - 1])
    return _("{day} {month} {year}").format(day=found.day, month=month, year=found.year)


def _alpha(value: float) -> str:
    """The alpha level, APA style: no leading zero, two decimals or three when needed."""
    decimals = 2 if round(value, 2) == value else 3
    return apa(value, decimals, zero=False)


# --- What a variable, an effect and a direction are called. ---


def _entry(project: Project, name: str):
    return next((e for e in project.variables if w.final_name(e) == name), None)


def _name(project: Project, ref: VariableRef) -> str:
    try:
        return resolve(project, ref)
    except NotebookError:
        return ref.variable or ref.score or ref.reversed or ""


def _named(project: Project, ref: VariableRef) -> str:
    """ "heures_travail (Heures de travail par semaine)"; a score says its group."""
    name = _name(project, ref)
    if ref.score is not None:
        return _("{name} (score de {group})").format(name=name, group=ref.score)
    entry = _entry(project, name)
    label = w.label_text(entry, "final") if entry is not None else ""
    return f"{name} ({label})" if label and label != name else name


def _effect(project: Project, hypothesis: Hypothesis) -> str:
    effect = hypothesis.effect
    if effect.kind == "pair":
        a, b = (_name(project, r) for r in effect.variables)
        return _("la corrélation entre {a} et {b}").format(a=a, b=b)
    if effect.kind == "predictor":
        return _("le coefficient de {x}").format(x=_name(project, effect.variable))
    return EFFECT_NAMES[effect.kind]


def _groups(project: Project, hypothesis: Hypothesis) -> tuple[str, str] | None:
    """The two groups a t test compares, by their labels: the modalities chosen, or the two
    value labels of the group variable."""
    refs = hypothesis.roles.get("group", [])
    entry = _entry(project, _name(project, refs[0])) if refs else None
    if entry is None:
        return None
    labels = {lab.code: lab.label for lab in accepted_labels(entry)}
    chosen = hypothesis.options.get("levels")
    if chosen:
        codes = [float(c) for c in chosen.split(",")]
        found = [labels.get(c, labels.get(int(c))) for c in codes]
        return tuple(found) if all(found) and len(found) == 2 else None
    if len(labels) == 2:
        first, second = sorted(labels, key=lambda c: (isinstance(c, str), c))
        return labels[first], labels[second]
    return None


def _direction(project: Project, hypothesis: Hypothesis) -> str:
    direction = hypothesis.direction
    if direction in ("first_higher", "second_higher"):
        groups = _groups(project, hypothesis)
        if groups is None:
            return (
                _("le premier groupe, dans l'ordre des codes, plus élevé")
                if direction == "first_higher"
                else _("le second groupe, dans l'ordre des codes, plus élevé")
            )
        high, low = groups if direction == "first_higher" else groups[::-1]
        return _("{high} plus élevé que {low}").format(high=high, low=low)
    if hypothesis.effect.kind == "pair":
        return (
            _("une corrélation positive")
            if direction == "positive"
            else _("une corrélation négative")
        )
    return _("un coefficient positif") if direction == "positive" else _("un coefficient négatif")


# --- The answers the tool fills, shared by the two templates (§ 8.3). ---


def _hypotheses(project: Project) -> list[Text]:
    found = []
    for h in project.plan.hypotheses:
        kind = KINDS[h.kind]
        if h.family:
            kind = _("{kind}, famille {family}").format(kind=kind, family=h.family)
        parts = [
            _("{id} ({kind}).").format(id=h.id, kind=kind),
            h.statement,
            _("Effet testé : {effect}.").format(effect=_effect(project, h)),
        ]
        if h.direction:
            parts.append(_("Sens attendu : {direction}.").format(direction=_direction(project, h)))
        found.append(rich(" ".join(parts)))
    return found or [(hole(_("hypothèses")),)]


def _roles(project: Project) -> dict[str, list[str]]:
    """Each variable of the hypotheses (not the scores), with its roles and hypotheses."""
    found: dict[str, list[str]] = {}
    for h in project.plan.hypotheses:
        for role, refs in h.roles.items():
            for ref in refs:
                if ref.score is None:
                    key = _named(project, ref)
                    found.setdefault(key, []).append(f"{ROLE_OF.get(role, role)} ({h.id})")
    return found


def _measured(project: Project) -> list[Text]:
    found = [
        rich(f"{name} : {semicolon().join(dict.fromkeys(roles))}.")
        for name, roles in _roles(project).items()
    ]
    return found or [(hole(_("variables mesurées")),)]


def _scored_groups(project: Project) -> list:
    wanted = [r.score for h in project.plan.hypotheses for refs in h.roles.values() for r in refs]
    return [g for g in project.groups if g.group_id in wanted and g.scoring is not None]


def _scores(project: Project) -> list[Text]:
    return [scale_description(project, g) for g in _scored_groups(project)]


def _exclusions(project: Project) -> list[Text]:
    rules = project.exclusions.rules
    if not rules:
        return [rich(_("Aucune règle d'exclusion n'est prévue."))]
    found = []
    for rule in rules:
        text = _("{id}. {reason} ({rule}).").format(
            id=rule.id, reason=rule.reason, rule=exclusions.rule_text(rule)
        )
        if rule.source:
            text += " " + _("Source : {source}.").format(source=rule.source)
        found.append(rich(text))
    found.insert(0, rich(_("Les règles s'appliquent dans cet ordre :")))
    return found


def _used(project: Project) -> list[str]:
    names = [_name(project, r) for h in project.plan.hypotheses for refs in h.roles.values()
             for r in refs]  # fmt: skip
    for score in preparation_plan(project)[1]:  # a score's items carry its missing codes
        if score.name in names:
            group = next(g for g in project.groups if g.group_id == score.group)
            names += [w.names_of(project)[n] for n in exclusions.members(group)]
    return list(dict.fromkeys(names))


def _missing_data(project: Project) -> list[Text]:
    found = []
    codes = [
        f"{', '.join(c if isinstance(c, str) else w.code_text(c) for c in listed)} ({name})"
        for name, listed in _missing(project, _used(project))
    ]
    if codes:
        found.append(
            rich(
                _("Les codes {codes} seront traités comme des valeurs manquantes.").format(
                    codes=semicolon().join(codes)
                )
            )
        )
    found.append(
        rich(
            _(
                "Les valeurs manquantes seront retirées analyse par analyse : chaque analyse "
                "portera sur les personnes qui ont répondu à toutes ses variables."
            )
        )
    )
    found.append((hole(_("ce que l'équipe sait des taux de valeurs manquantes")),))
    return found


def _models(project: Project) -> list[Text]:
    found = []
    for h in project.plan.hypotheses:
        parts = [TITLES.get(h.analysis, h.analysis)]
        for key, value in h.options.items():
            if key != "alternative":
                parts.append(f"{OPTIONS.get(key, key).lower()} : {CHOICES.get(value, value)}")
        for role, refs in h.roles.items():
            names = ", ".join(_name(project, r) for r in refs)
            parts.append(f"{ROLES.get(role, role).lower()} : {names}")
        parts.append(_("effet testé : {effect}").format(effect=_effect(project, h)))
        parts.append(TESTS[h.options.get("alternative", "two_sided")])
        found.append(rich(f"{h.id}. {semicolon().join(parts)}."))
    return found or [(hole(_("modèles statistiques")),)]


def _families(project: Project) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for h in project.plan.hypotheses:
        if h.kind == "confirmatory" and h.family:
            found.setdefault(h.family, []).append(h.id)
    return {k: v for k, v in found.items() if len(v) > 1}


def _inference(project: Project) -> list[Text]:
    plan = project.plan
    found = []
    if plan.alpha is None:
        found.append((hole(_("seuil α")),))
    else:
        found.append(rich(_("Le seuil α est fixé à {alpha}.").format(alpha=_alpha(plan.alpha))))
    families = _families(project)
    if families and plan.correction != "none":
        listed = semicolon().join(f"{k} ({', '.join(v)})" for k, v in families.items())
        template = (
            _(
                "Les valeurs de {p} seront corrigées par la méthode de Holm dans chaque "
                "famille : {families}."
            )
            if plan.correction == "holm"
            else _(
                "Les valeurs de {p} seront corrigées par la méthode de Bonferroni dans chaque "
                "famille : {families}."
            )
        )
        found.append(marked(template, p=it("p"), families=listed))
    else:
        found.append(
            marked(
                _("Les valeurs de {p} ne seront pas corrigées pour comparaisons multiples."),
                p=it("p"),
            )
        )
    found.append(
        rich(_("Les tailles d'effet seront données avec leur intervalle de confiance à 95 %."))
    )
    return found


def _exploratory(project: Project) -> list[Text]:
    found = [
        rich(f"{h.id}. {h.statement}") for h in project.plan.hypotheses if h.kind == "exploratory"
    ]
    found.append(rich(_("Toute autre analyse sera présentée comme exploratoire.")))
    return found


def _prior(project: Project) -> list[Text]:
    frozen = project.plan.frozen
    found = []
    if frozen is not None and frozen.prior:
        listed = ", ".join(
            _("{id} ({entry}, ajoutée le {date})").format(
                id=p.hypothesis, entry=p.entry, date=long_date(p.added)
            )
            for p in frozen.prior
        )
        found.append(
            rich(
                _(
                    "Le carnet de l'outil contenait déjà, le jour où le plan a été arrêté, les "
                    "analyses prévues pour {listed}."
                ).format(listed=listed)
            )
        )
    found.append((hole(_("ce que l'équipe a vu des données par ailleurs")),))
    return found


def _status(project: Project) -> list[Text]:
    status = project.plan.data_status
    if status is None:
        return [(hole(_("état des données quand le plan a été écrit")),)]
    return [rich(STATUSES[status] + " " + _("(Déclaré par l'équipe.)"))]


def _status_and_prior(project: Project) -> list[Text]:
    found = _status(project) + _prior(project)
    found.append((hole(_("connaissance préalable des données")),))
    return found


def _structure(project: Project, count: bool) -> list[Text]:
    found = [rich(f"{label} : {value}.") for label, value in w.dataset_facts(project)]
    if count:
        found.append(rich(_("La base compte {n} variables.").format(n=len(project.variables))))
    found.append((hole(_("description des données")),))
    return found


def _collection(project: Project) -> list[Text]:
    found = []
    if project.questionnaire is not None:
        found.append(
            rich(
                _("Le questionnaire de l'étude est joint ({file}).").format(
                    file=project.questionnaire.file_name
                )
            )
        )
    found.append((hole(_("procédure de collecte")),))
    return found


def _sample_size(project: Project) -> list[Text]:
    text = project.plan.sample_size.strip()
    return [rich(text)] if text else [(hole(_("taille d'échantillon")),)]


def _gap(what: str):
    return lambda project: [(hole(what),)]


def _outliers(project: Project) -> list[Text]:
    return [rich(_("Le plan ne prévoit aucun retrait de valeurs extrêmes."))]


# --- The two templates (§ 8.4 and 8.5). ---


def _primary(stem: str) -> list[tuple[str, list[tuple[str, object]]]]:
    return [
        (
            _("Informations sur l'étude"),
            [
                (_("Titre"), _gap(_("titre"))),
                (_("Auteurs"), _gap(_("auteurs"))),
                (_("Description"), _gap(_("description de l'étude"))),
                (_("Hypothèses"), _hypotheses),
            ],
        ),
        (
            _("Plan de l'étude"),
            [
                (
                    _("Type d'étude"),
                    _gap(_("type d'étude : expérience, observation, méta-analyse ou autre")),
                ),
                (_("Insu"), _gap(_("insu"))),
                (_("Devis"), lambda p: _structure(p, count=False)),
                (_("Répartition aléatoire"), _gap(_("répartition aléatoire"))),
            ],
        ),
        (
            _("Échantillonnage"),
            [
                (_("Données existantes"), _status),
                (_("Explication sur les données existantes"), _prior),
                (_("Procédure de collecte"), _collection),
                (_("Taille d'échantillon"), _sample_size),
                (
                    _("Justification de la taille d'échantillon"),
                    _gap(_("justification de la taille d'échantillon")),
                ),
                (_("Règle d'arrêt"), _gap(_("règle d'arrêt"))),
            ],
        ),
        (
            _("Variables"),
            [
                (_("Variables manipulées"), _gap(_("variables manipulées"))),
                (_("Variables mesurées"), _measured),
                (_("Indices"), lambda p: _scores(p) or [rich(_("Aucun score."))]),
            ],
        ),
        (
            _("Plan d'analyse"),
            [
                (_("Modèles statistiques"), _models),
                (
                    _("Transformations"),
                    lambda p: [
                        rich(_("Les scores sont calculés comme décrit sous « Indices »."))
                        if _scored_groups(p)
                        else rich(_("Aucun score.")),
                        (hole(_("autres transformations")),),
                    ],
                ),
                (_("Critères d'inférence"), _inference),
                (_("Exclusion de données"), lambda p: _exclusions(p) + _outliers(p)),
                (_("Données manquantes"), _missing_data),
                (_("Analyses exploratoires"), _exploratory),
            ],
        ),
        (_("Autre"), [(_("Autre"), _gap(_("autres renseignements")))]),
    ]


def _secondary(stem: str) -> list[tuple[str, list[tuple[str, object]]]]:
    codebook = rich(
        _("Le dictionnaire de données joint ({file}) décrit chaque variable.").format(
            file=f"{stem}.xlsx"
        )
    )
    questions = [
        (
            _("Informations sur l'étude"),
            [
                (_("Titre de l'étude"), _gap(_("titre"))),
                (_("Auteurs"), _gap(_("auteurs"))),
                (_("Questions de recherche"), _gap(_("questions de recherche"))),
                (_("Hypothèses"), _hypotheses),
            ],
        ),
        (
            _("Description des données"),
            [
                (_("Description des données"), lambda p: _structure(p, count=True)),
                (_("Accès public aux données"), _gap(_("accès public aux données"))),
                (_("Comment obtenir les données"), _gap(_("comment obtenir les données"))),
                (
                    _("Date de téléchargement ou d'accès"),
                    _gap(_("date de téléchargement ou d'accès")),
                ),
                (_("Procédure de collecte"), _collection),
                (_("Codebook"), lambda p: [codebook]),
            ],
        ),
        (
            _("Variables"),
            [
                (_("Variables manipulées"), _gap(_("variables manipulées"))),
                (_("Variables mesurées"), lambda p: _measured(p) + _scores(p)),
                (
                    _("Unités et critères d'inclusion et d'exclusion"),
                    lambda p: _exclusions(p) + _sample_size(p),
                ),
                (_("Données manquantes"), _missing_data),
                (_("Valeurs extrêmes"), _outliers),
                (_("Pondérations"), lambda p: [rich(_("Aucune pondération n'est utilisée."))]),
            ],
        ),
        (
            _("Connaissance des données"),
            [
                (
                    _("Travaux antérieurs sur ces données"),
                    _gap(_("travaux antérieurs sur ces données")),
                ),
                (_("Connaissance préalable des données"), _status_and_prior),
            ],
        ),
        (
            _("Analyses"),
            [
                (_("Modèle statistique par hypothèse"), _models),
                (_("Taille d'effet prévue"), _gap(_("taille d'effet prévue"))),
                (_("Puissance statistique"), _gap(_("puissance statistique"))),
                (_("Critères d'inférence"), _inference),
                (
                    _("Violation des conditions"),
                    _gap(_("ce qui sera fait si les conditions ne sont pas remplies")),
                ),
                (_("Robustesse"), _gap(_("robustesse"))),
                (_("Analyses exploratoires"), _exploratory),
            ],
        ),
    ]
    number = 0
    numbered = []
    for part, items in questions:
        listed = []
        for title, build in items:
            number += 1
            listed.append((f"Q{number}. {title}", build))
        numbered.append((part, listed))
    integrity = rich(
        _(
            "Les auteurs de ce préenregistrement déclarent l'avoir rempli au mieux de leurs "
            "connaissances, et qu'aucun autre préenregistrement ne porte sur les mêmes hypothèses "
            "et les mêmes données."
        )
    )
    numbered.append((_("Déclaration d'intégrité"), [("", lambda p: [integrity])]))
    return numbered


def _head(project: Project, version: str) -> tuple[str, list[Text]]:
    origin = project.plan.data_origin
    if origin == "secondary":
        title = _("Préenregistrement d'une analyse de données secondaires")
        source = (
            "van den Akker et al. (2021), Meta-Psychology, 5, https://doi.org/10.15626/MP.2020.2625"
        )
        licence = "CC BY 4.0"
    else:
        title = _("Préenregistrement selon le gabarit OSF Prereg")
        source = "Bowman et al. (2020), OSF Prereg Template, https://doi.org/10.31222/osf.io/epgjd"
        licence = "CC0 1.0"
    paragraphs = [
        rich(
            _(
                "Questions adaptées de {source}, sous licence {licence} ; traduction et réponses "
                "préremplies par dictionnaire-donnees {version}."
            ).format(source=source, licence=licence, version=version)
        )
    ]
    if origin is None:
        paragraphs.append((hole(_("origine des données")),))
    if project.plan.frozen is None:
        paragraphs.append((hole(_("ce plan n'est pas encore arrêté dans l'outil")),))
    return title, paragraphs


def preregistration(
    project: Project, project_path: Path, *, language: str | None = None, today: str | None = None
) -> ApaDocument:
    """The preregistration of the project's plan, in the codebook's language or this one."""
    from ddict.workflow import project_stem

    with i18n.using(language):
        language = i18n.language()
        version = versions()["dictionnaire-donnees"]
        stem = project_stem(project_path)
        title, head = _head(project, version)
        sections = [Section("title", title, "", paragraphs=tuple(head), level=1)]
        template = _secondary if project.plan.data_origin == "secondary" else _primary
        for index, (part, questions) in enumerate(template(stem)):
            sections.append(Section(f"part-{index}", part, "", level=2))
            for heading, build in questions:
                paragraphs = tuple(build(project))
                if heading:
                    sections.append(
                        Section("question", heading, "", paragraphs=paragraphs, level=3)
                    )
                else:
                    sections[-1] = Section(
                        f"part-{index}", part, "", paragraphs=paragraphs, level=2
                    )
        frozen = project.plan.frozen
        closing = [
            _("Plan arrêté dans l'outil le {date} ; empreinte du plan : {fingerprint}.").format(
                date=long_date(frozen.date), fingerprint=frozen.fingerprint[:12]
            )
            if frozen is not None
            else _("Plan non arrêté ; empreinte du plan : {fingerprint}.").format(
                fingerprint=plan_fingerprint(project.plan)[:12]
            ),
            _("Empreinte du codebook : {fingerprint}.").format(
                fingerprint=fingerprint.short(project)
            ),
            _("Préparé par dictionnaire-donnees {version} le {date}.").format(
                version=version, date=long_date(today or date.today().isoformat())
            ),
        ]
    return ApaDocument(
        "preregistration", language, sections=tuple(sections), closing=tuple(closing)
    )


# --- Markdown, and the files. ---


def _markdown_text(text: Text) -> str:
    return "".join(f"*{r.text}*" if r.italic and not r.hole else r.text for r in text)


def markdown(document: ApaDocument) -> str:
    """The document in Markdown: headings by level, paragraphs, the record at the end."""
    lines: list[str] = []
    for section in document.sections:
        lines += ["#" * section.level + " " + section.heading, ""]
        for paragraph in section.paragraphs:
            lines += [_markdown_text(paragraph), ""]
    if document.closing:
        lines += ["---", ""]
        for line in document.closing:
            lines += [line, ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def preregistration_paths(project_path: Path) -> dict[str, Path]:
    from ddict.workflow import project_stem

    stem = project_stem(project_path) + SUFFIX
    return {
        "docx": project_path.with_name(stem + ".docx"),
        "md": project_path.with_name(stem + ".md"),
    }


def write_preregistration(
    project: Project, project_path: Path, *, language: str | None = None, today: str | None = None
) -> list[Path]:
    """`<projet>-preenregistrement.docx` and `.md`, next to the project, replaced each time."""
    from ddict.analysis.formats import FORMATS

    document = preregistration(project, project_path, language=language, today=today)
    paths = preregistration_paths(project_path)
    paths["docx"].write_bytes(FORMATS["docx"].render(document))
    with paths["md"].open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(markdown(document))
    return [paths["docx"], paths["md"]]
