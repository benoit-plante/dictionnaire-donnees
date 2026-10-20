"""The reproduction package (v0.15, step 6, D-119; docs/verification-depot.md, § 3): a zip ready
for a deposit (OSF, Borealis) with the codebook, the preregistration, the notebook, the
command files, the preparation scripts and the R master script, a README written by a
template where what the tool does not know stays a hole, and the fingerprints of its files.
Every file is made at the time of the package (D-089), never copied from an older one.

Never the database, nor the project file (its profile holds observed values), nor the
messages sent to a model, nor the draft of the article, nor a synthetic database (D-076).
"""

from __future__ import annotations

import hashlib
import io
import re
import zipfile
from datetime import date
from pathlib import Path

from ddict import __version__, i18n
from ddict.analysis import notebook as nb
from ddict.analysis import notebook_export as export
from ddict.i18n import _
from ddict.project import aside, fingerprint

SUFFIX = "-depot.zip"


class DepositError(Exception):
    """The package cannot be made; the message is for the person."""


def deposit_path(project_path: Path) -> Path:
    from ddict.workflow import project_stem

    return project_path.with_name(project_stem(project_path) + SUFFIX)


def _hole(what: str) -> str:
    return _("[à compléter : {what}]").format(what=what)


def readme(project, project_path: Path, notebook, files: list[str], today: str) -> str:
    """The README of the deposit: what it holds and how to run it again; no statistic."""
    from ddict.workflow import project_stem

    stem = project_stem(project_path)
    retained = sum(1 for e in notebook.entries if e.retained)
    plan = project.plan
    lines = [
        "# " + _hole(_("titre de l'étude")) + " — " + _("matériel de reproduction"),
        "",
        (
            _(
                "Ce dépôt contient le dictionnaire de données, le plan d'analyse et les scripts "
                "qui refont les analyses de l'article {article}. Il ne contient pas les "
                "données : {where}."
            )
            if plan.hypotheses
            else _(
                "Ce dépôt contient le dictionnaire de données et les scripts qui refont les "
                "analyses de l'article {article}. Il ne contient pas les données : {where}."
            )
        ).format(
            article=_hole(_("référence de l'article")),
            where=_hole(_("où et à quelles conditions les obtenir")),
        ),
        "",
        "## " + _("Contenu"),
        "",
        "- "
        + _("`codebook/` : le dictionnaire des {n} variables (Excel, Markdown, "
            "`datapackage.json`).").format(n=len(aside.kept(project))),
    ]  # fmt: skip
    if any(f.startswith("plan/") for f in files):
        if plan.frozen is not None:
            text = _(
                "`plan/` : le préenregistrement du plan d'analyse, arrêté dans l'outil le "
                "{date}, avec ses amendements ({n})."
            ).format(date=plan.frozen.date, n=len(plan.amendments))
        else:
            text = _("`plan/` : le préenregistrement du plan d'analyse, non arrêté.")
        lines.append("- " + text)
    lines += [
        "- "
        + _("`analyses/` : le carnet des {n} analyses retenues : leurs choix, leurs empreintes, "
            "leurs résultats agrégés ; aucune donnée individuelle.").format(n=retained),
        "- "
        + _("`scripts/` : les fichiers de commandes (SPSS et R), le script de préparation et le "
            "script R maître."),
        "",
        "## " + _("Refaire les analyses"),
        "",
        _(
            "Placez la base `{base}` dans le dossier `scripts/`. Dans R, avec le paquet haven, "
            "le dossier `scripts/` comme dossier de travail : "
            '`source("{script}", encoding = "UTF-8")`. Le script exécute le fichier de '
            "commandes, le script de préparation, puis les {n} analyses ; chaque résultat est "
            "rangé sous son identifiant (`resultats$A1`)."
        ).format(base=project.source.name, script=export.script_name(project_path), n=retained),
        "",
        _(
            "Dans SPSS ou PSPP : ouvrez la base, puis exécutez `{stem}.sps` et, s'il est "
            "présent, `{stem}-preparation.sps`."
        ).format(stem=stem),
        "",
        "## " + _("Versions"),
        "",
        _(
            "Produit par dictionnaire-donnees {version} le {date} ; empreinte du codebook "
            "`{fingerprint}` ; empreintes des fichiers dans `EMPREINTES.txt`."
        ).format(version=__version__, date=today, fingerprint=fingerprint.short(project)),
        "",
        "## " + _("Licence, auteurs, contact"),
        "",
        _("Licence : {licence}. Auteurs : {authors}. Contact : {contact}.").format(
            licence=_hole(_("licence")), authors=_hole(_("auteurs")),
            contact=_hole(_("contact")),
        ),
    ]  # fmt: skip
    return "\n".join(lines) + "\n"


CORE_DATES = re.compile(r"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:)")


def steady_xlsx(data: bytes, today: str) -> bytes:
    """The same workbook, the same bytes: openpyxl writes the time of the saving into the
    workbook's properties and into the dates of its zip entries; both take `today`."""
    stamp = f"{today}T00:00:00Z"
    year, month, day = (int(part) for part in today.split("-"))
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as source, zipfile.ZipFile(out, "w") as archive:
        for entry in source.infolist():
            content = source.read(entry.filename)
            if entry.filename == "docProps/core.xml":
                text = CORE_DATES.sub(rf"\g<1>{stamp}\g<2>", content.decode("utf-8"))
                content = text.encode("utf-8")
            info = zipfile.ZipInfo(entry.filename, date_time=(year, month, day, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    return out.getvalue()


def _fingerprints(project, files: dict[str, bytes]) -> str:
    lines = [
        _("# Empreintes SHA-256 des fichiers du paquet."),
        *[f"{hashlib.sha256(data).hexdigest()}  {name}" for name, data in sorted(files.items())],
        "",
        _("# Empreinte du codebook : {fingerprint}").format(
            fingerprint=fingerprint.fingerprint(project)
        ),
        _(
            "# Empreinte de la base d'origine, non incluse (elle ne permet pas de la "
            "retrouver) : {sha256}"
        ).format(sha256=project.source.sha256),
    ]
    return "\n".join(lines) + "\n"


def package(project, prepared, notebook, project_path: Path, *, language=None, today=None):
    """The files of the package, by their path in the zip. Raises DepositError (no database)
    or ExportBlocked (an analysis waits for a confirmation, as for the draft)."""
    from ddict.analysis import prereg
    from ddict.analysis.formats import FORMATS
    from ddict.export.context import context_package, package_text
    from ddict.export.markdown import render_markdown
    from ddict.export.preparation import needed, render_preparation
    from ddict.export.syntax import render_syntax
    from ddict.export.xlsx import write_xlsx
    from ddict.workflow import project_stem

    if prepared is None:
        raise DepositError(
            _("La base est nécessaire pour préparer le paquet (elle n'y entre pas).")
        )
    today = today or date.today().isoformat()
    stem = project_stem(project_path)
    with i18n.using(language):
        language = i18n.language()
        _document, analyses = export._results(project, prepared, notebook, language=language,
                                              today=today)  # fmt: skip
        files: dict[str, bytes] = {}
        book = io.BytesIO()
        write_xlsx(project, book)
        files[f"codebook/{stem}.xlsx"] = steady_xlsx(book.getvalue(), today)
        files[f"codebook/{stem}.md"] = render_markdown(project).encode("utf-8")
        files[f"codebook/{stem}-datapackage.json"] = package_text(context_package(project)).encode(
            "utf-8"
        )
        if project.plan.hypotheses:
            document = prereg.preregistration(project, project_path, today=today)
            files[f"plan/{stem}-preenregistrement.docx"] = FORMATS["docx"].render(document)
            files[f"plan/{stem}-preenregistrement.md"] = prereg.markdown(document).encode("utf-8")
        files[f"analyses/{stem}-carnet.json"] = nb.dumps(notebook).encode("utf-8")
        files[f"scripts/{stem}.sps"] = render_syntax(project, "spss", today).encode("utf-8")
        if needed(project):
            files[f"scripts/{stem}-preparation.sps"] = render_preparation(
                project, "spss", today
            ).encode("utf-8")
        bundle = export.r_bundle(project, project_path, analyses, today=today)
        with zipfile.ZipFile(io.BytesIO(bundle)) as archive:
            for name in archive.namelist():
                files[f"scripts/{name}"] = archive.read(name)
        files["README.md"] = readme(project, project_path, notebook, list(files), today).encode(
            "utf-8"
        )
        files["EMPREINTES.txt"] = _fingerprints(project, files).encode("utf-8")
    return files


def zipped(files: dict[str, bytes]) -> bytes:
    """The zip, the same bytes for the same files (a fixed date, a fixed order)."""
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        first = ["README.md", "EMPREINTES.txt"]
        for name in [*first, *sorted(set(files) - set(first))]:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name])
    return out.getvalue()


def write_deposit(project, prepared, notebook, project_path: Path, *, language=None,
                  today=None) -> tuple[Path, list[str]]:  # fmt: skip
    """`<projet>-depot.zip` next to the project; its path and the files it holds."""
    files = package(project, prepared, notebook, project_path, language=language, today=today)
    target = deposit_path(project_path)
    target.write_bytes(zipped(files))
    return target, list(files)
