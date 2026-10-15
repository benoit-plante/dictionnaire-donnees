"""The study's questionnaire as a documented source (v0.2, D-012)."""

from ddict.project.model import Questionnaire
from ddict.questionnaire.header import read_header_questionnaire
from ddict.questionnaire.read import FORMATS, Line, QuestionnaireFile, read_questionnaire
from ddict.questionnaire.segment import join_lines, segment


def load_questionnaire(path, kinds: dict[int, str] | None = None) -> Questionnaire:
    """Read a questionnaire file and cut it into questions and paragraphs; the header of a
    survey platform's Excel export is read as its questionnaire (v0.7, D-045), with the
    kind of each question from the structure of the database (`kinds`), when known."""
    from pathlib import Path

    if Path(path).suffix.lower() == ".xlsx":
        return read_header_questionnaire(path, kinds)
    read = read_questionnaire(path)
    questions, texts = segment(read.lines, use_indent=read.format == "pdf")
    return Questionnaire(
        file_name=read.name,
        sha256=read.sha256,
        format=read.format,
        n_pages=read.n_pages,
        questions=questions,
        texts=texts,
    )


__all__ = [
    "FORMATS",
    "Line",
    "QuestionnaireFile",
    "join_lines",
    "load_questionnaire",
    "read_questionnaire",
    "segment",
]
