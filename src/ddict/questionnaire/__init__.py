"""The study's questionnaire as a documented source (v0.2, D-012)."""

from ddict.project.model import Questionnaire
from ddict.questionnaire.read import FORMATS, Line, QuestionnaireFile, read_questionnaire
from ddict.questionnaire.segment import join_lines, segment


def load_questionnaire(path) -> Questionnaire:
    """Read a questionnaire file and cut it into questions and paragraphs."""
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
