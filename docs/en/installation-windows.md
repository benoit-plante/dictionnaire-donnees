# Installing and using the tool on Windows

This guide is for people who do not program. It goes from the installation to a complete codebook, made from the fictional database and its questionnaire that come with the tool. Everything is done by double-clicking and in the tool's window; there are no commands to type. Allow an hour, plus the download of the AI model if you choose to use it.

En français : [`../installation-windows.md`](../installation-windows.md).

> **Trial version of the English.** The tool was written in French first; its English interface is new (version 0.5) and its translation has not yet been reviewed by a native English speaker. If a sentence is unclear or wrong, write it down and pass it on. The installer window speaks French only: this guide gives what it says.

## What you need

- Windows 10 or 11. No administrator rights needed.
- An Internet connection **during the installation only**. Afterwards, the tool no longer talks to the Internet: it reads your files and writes its results on your computer.
- For the AI, which is optional: about 5 GB of free space and 16 GB of memory (8 GB will do, more slowly). A graphics card speeds things up but is not needed; without one, a smaller model is advised (section 6).

## 1. Install

1. Download the tool's archive from the releases page of the project on GitHub: the **Source code (zip)** link, for example `dictionnaire-donnees-0.8.0.zip`.
2. In File Explorer, right-click the downloaded file, **Extract All**, then **Extract**. Open the extracted folder; if it holds only one folder of the same name, open that one: it is **the tool's folder**, with `installer.bat`, `docs` and `exemples`.
3. Double-click **`installer.bat`**.
   - If Windows shows "**Windows protected your PC**", click **More info**, then **Run anyway**. This message appears for any downloaded program that is not signed by a paying publisher; the installer is a plain script, readable in the `windows` folder.
4. A window opens and goes through four steps (in French): uv (the Python manager, installed in your user folder), the tool (a minute or two the first time), the icons ("Les icônes"), then the local AI ("IA locale"). A warning in English about the "PATH" may appear: that is normal, the installer takes care of it.
5. At the AI step, answer `y` (yes) or `n` (no) — the French `o`/`n` works too:
   - if Ollama is not installed, the installer offers to open its download page ("Ouvrir la page de téléchargement d'Ollama… ?"); install it, then run `installer.bat` again;
   - if Ollama is installed but not the recommended model, it offers to download it ("Le télécharger maintenant ?", about 4.7 GB, once).

   You can answer no and come back to it later: the tool works without AI.
6. "Installation terminée" (installation finished): press Enter to close the window. A **Dictionnaire de données** icon is on your desktop and in the Start menu.

## 2. Open the tool

Double-click the **Dictionnaire de données** icon. After a few seconds, the tool opens in its own window, on the **home page**. It is a local page (address `http://127.0.0.1`), reachable from your computer only.

**To stop the tool, close its window**, or click **Quit the tool** at the bottom of the sidebar. Your decisions are saved as you go: nothing is lost. Another double-click on the icon while the tool runs opens one more window.

If the window cannot open (on a computer without the Edge engine, for example), the tool opens in your browser and works the same way; then stop it with **Quit the tool**.

**Language**: at the top of the home page, **Français · English** chooses the language of the interface. The choice applies at once and is remembered on your computer. Choose **English**.

## 3. A first codebook, from the fictional database

The fictional database is a small invented study of sleep (200 fictional participants), with its questionnaire. It lets you try the tool without any real data. It exists in French and in English; this guide uses the English version.

1. On the home page, under **New project**, click **Choose a database…**. The Windows "Open" window appears (if you do not see it, look in the taskbar). Go to the tool's folder, then `exemples\bases-fictives`, and choose `sleep-study.sav`.
2. Click **Create the project**. The tool reads the database and creates next to it the **project file**, `sleep-study.dd.json`. It holds everything the tool computed (types, missing values, categories, labels) and, later, your decisions; it does not hold the participants' individual answers. The data file is never changed.
3. The **Database** page sums up what was read: number of variables and rows, sensitive variables, flags. It also shows the **language of the study** (that of its questionnaire and labels), guessed by the tool and which you can change: the model writes its proposals in this language. Here it is "English".
4. In the sidebar, choose **Export**, then **Write the codebook and the report**. Two files appear next to the project: `sleep-study.xlsx` (the codebook, to open with Excel) and `sleep-study.md` (the same content as text). The **Open the folder** button shows them in File Explorer.

Your first codebook is done, without AI: everything in it was computed exactly from the file. The next sections enrich it; you can stop at any of them and export.

At the top of the sidebar, the **to-do list** says what is waiting, in the recommended order ("Add the study questionnaire", "Acronyms to accept: 3"…). Each line is a button that leads to the right page. The **Home** button takes you back to the home page, where your **Recent projects** open again in one click.

## 4. Add the questionnaire

The study's questionnaire says what each variable means: the exact text of the questions, the meaning of acronyms, the answer options. The tool reads it without AI, as a PDF (export from SurveyMonkey, LimeSurvey, REDCap…) or as text (`.txt` copied from Word).

1. **Questionnaire** page (or "Add the study questionnaire" in the to-do list): **Choose the questionnaire…**, then `questionnaire-sleep.pdf` in `exemples\bases-fictives`, and **Read the questionnaire**.
2. The tool shows the number of questions found, the questions to check (for example a grid whose column headings run together), the **acronyms defined in the questionnaire** ("Cognitive behavioural therapy (CBT)") and the acronyms in variable names that have no definition. **Questions found** shows them all.
3. **Glossary** page: accept, correct or reject each acronym found, and add the missing ones (here, ANX: "anxiety"). **The AI never defines an acronym**: that is where it errs most, and the glossary comes only from the questionnaire and from you.

The text of the questionnaire stays in the project file; only the questions linked to variables go into the codebook, never the consent page.

## 5. Link the variables to the questions

Each variable comes from a question, a grid item or an option of a checkbox question; or from none (an identifier, a date of completion, a computed score).

- **Without AI**: **Variables** page, **Without a question** filter. On each variable's page, the **Question in the questionnaire** section offers a list with the candidate questions computed by the tool at the top; choose, then **Link**.
  - For an identifier, a date of completion or a score that is the exact sum of the items of a grid, "**No question in the questionnaire**" comes first: the tool deems it likely, but the decision is yours.
  - Some questions do not use the words of the variable's name ("How old are you?" for `age`). When the tool finds no candidate, it puts first the **neighbouring questions**, those at that place in the questionnaire, between the sure questions around it; a short text below the list says so.
- **With AI** (section 6): the model chooses among the candidates, then you accept, correct or reject each choice, in the same way. When the computation is sure of its choice and the model chooses another, the model's proposal is kept but flagged ("departs from the computation's sure choice"): compare with the first question of the list. These links are left out of the grouped decisions.

When the file has no value labels (a CSV, for example), the tool proposes "1 = Not at all … 5 = Extremely" from the options of the linked question, only in safe cases. The words "**assumed order, to check**" are meant seriously: check the order of the codes in your survey platform or recoding script before accepting. A recoded database may have 0 = "Other" where the questionnaire puts "Other" last.

## 6. Optional: the local AI

The AI proposes links to questions, then labels and descriptions easier to read than variable names. It runs on your computer, with the free software **Ollama**. The model never receives the participants' answers, only summary information (names, labels, proportions, questions). Every proposal waits for your decision.

**Which model?** (trials of 2026-10-14, in `docs/essais/`): with a graphics card of at least 6 GB, **qwen2.5 7B** (`ollama pull qwen2.5:7b-instruct-q4_K_M`, 4.7 GB). Without a graphics card, **qwen2.5 3B** (`ollama pull qwen2.5:3b-instruct`, 1.9 GB) is faster but makes more mistakes: review every proposal; its licence restricts commercial use. You can also do without a model: the computation alone already proposes the candidate questions.

1. **Local AI** page: the tool checks that Ollama answers and shows the chosen model. If something is missing, the page explains what to do; the tool never downloads a model itself.
2. **Links to questions**: **See exactly what would be sent (nothing is sent)** shows the messages, without sending anything. Then **Get proposals: links to questions**. A progress bar moves block by block.
3. **Review the links** (Variables page, "To review" filter; or the to-do list) before going further. The order matters: for the labels, the model receives the text of the questions whose link you accepted, and the meaning of the acronyms you accepted. A wrong link would give it a wrong question.
4. **Labels and descriptions**: **Get proposals: labels and descriptions**, then review them.

During a job, **Stop** (or a change of page) interrupts it after the block in progress. The finished blocks are saved; run it again to continue where it stopped. Allow about a minute for the fictional database with a graphics card, several minutes without.

**Model bench** (at the bottom of the same page): to choose a model, **Measure this model** tries it on the tool's fictional databases (three in French, one in English), whose right answers are known; the fourth, a fictional study of physical activity, served to check version 0.6 without any tuning. The report says how many links are right (and those of the computation alone, for comparison), how many labels or descriptions may contain an invention (citation, threshold, instrument name, meaning of an acronym, range, meaning of codes without a label) and the duration. Your data is not used. The report is written next to the project (`banc-essai-<model>-<date>.md`) and can be downloaded. About three minutes with a graphics card.

## 7. Review

- **Variables**: the filter ("To review", "With flags", "Sensitive", "Without a question", "Suspect codes", "All") and the list of variables. On each page: what the file says, what was computed, the linked question, and each proposal to **Accept**, **Reject**, or correct then **Save**. Each decision is saved at once in the project file.
- **Red box**: the proposal needs special attention: a guessed label for a variable without a label, the meaning of an acronym nobody gave the AI, or the observed range presented as the range of a scale.
- **Flags**: computed anomalies, among them **spelling variants** of the same answer ("French", "french", "FRENCH"), to correct in your data if you wish.
- **Grouped decisions**: at the top of the Variables page, **Accept the links where the model and the computation agree (N)…** opens the exact list of these links, each with its question. Read every line and uncheck what does not fit (in a trial, about one in five was wrong on a real database), then **Accept these N links**. On a group's page, **Accept the value labels of this group (N)…** does the same for the labels taken from the options.
- **Suspect codes** (filter of the same name, or the to-do list): a value such as 999 or −9, isolated far from the others, may be a missing code the file does not declare. Only your team knows: **It is a missing code** or **It is a real value**. The codebook will say so; **Undo this decision** cancels it.
- **Documented fields**: theoretical range, thresholds, references and notes. They are for people only, and the range and the thresholds require a source (manual, article).
- **Groups**: the scales found by the tool, their Cronbach's alpha and the items probably reversed. Confirming a reversal **documents** it in the codebook; the tool never recodes the data. For an **instrument protected by copyright** (CBCL, BDI…), check "Do not reproduce the text of this group's questions in the codebook": the codebook will give the reference of each question (`Q12.r3, p. 4`), without its text. Reproducing the items of a protected instrument is up to your team.
- **Scoring of a scale** (Groups page, "Scoring" section): the items of the score, sum or mean, the scale's minimum and maximum (pre-filled from the labels), the minimum of items answered and, for a sum that allows missing items, the rule (prorated sum or sum of the items answered), the score's name and **a required source**. The reversed items are those confirmed above; the range of the score is computed. A scoring that does not fit this frame is written as a note. The AI never proposes a scoring.
- **Measure levels** (Database page): when the file gives none (CSV, Excel), or when the file's is doubtful (a grid item declared "scale"), the tool proposes a level. Decide in the table, as for the names: **Accept**, **Reject**, or another level, then **Save**. For a few codes without labels (1, 2, 3, 9), it proposes nothing: only your team knows what they mean.
- **Description of the database** (Database page): what a row is (a participant, a repeated observation…), the structure (cross-sectional, one wave per file, wide or long format), the design variables and a short description. The tool only proposes the structure (one wave per file when a wave mark is set; wide format when suffixes `_t1`, `_t2` come back).
- **Completeness** (Database page, and at the head of the codebooks): for each element, what your team decided out of what applies, and the list of what remains to document.

## 8. Export

**Export** page:

- **Final version**: only what comes from the file, from computation, or from your decisions. **Working version**: with the pending proposals, marked as such.
- **Groups whose question text is not reproduced**: by default, those you checked in "Groups".
- **Codebook language**: French or English, by default that of the interface. It applies to the headings, the notes, the provenance, the report and the comments of the command files; what the team wrote (labels, descriptions, question text) is never translated.
- **Write the codebook and the report** (next to the project), or **Download** (to your downloads folder).

The codebook holds the labels, the text of the linked questions, the glossary ("Glossary" sheet), the accepted value labels and the provenance of every value. Counts below 5 are masked in it. The "Information" sheet and the head of the report give the **codebook fingerprint**, a 12-character code that changes as soon as a decision changes: note it with your results.

**The analysis context** (section of that name, at the bottom of the page): the codebook in a compact format, for a program or for an AI that helps write the analysis code. **Write the context next to the project** gives `sleep-study-contexte.md` (to paste into an assistant) and `sleep-study-datapackage.json` (Frictionless standard format, useful for a data deposit too). Only what is accepted; no participant data; the statistics only if you tick the box. See section 12.

## 9. Apply your decisions to your data

The codebook documents; your data itself has not changed. To bring into it what you accepted (labels, value labels, missing codes, including those confirmed by the team, measurement levels), there are two ways, on the **Export** page.

**The command files, the recommended way.** **Write the command files next to the project** (or download them) gives two files: `sleep-study-metadonnees.sps` (SPSS) and `.R` (R). There is no file for Stata, which could not be tried: with Stata, use the documented copy below. They hold only your accepted decisions and change no value: you open them in your own software, you can read them before running them, and they remain as a record of what was done. The reversed items you indicated are only suggested in them, as comments.

- **R** (with the haven package, installed once with `install.packages("haven")`), in RStudio or the R console, in the project's folder:

  ```r
  donnees <- haven::read_sav("sleep-study.sav", user_na = TRUE)   # or read.csv(...), haven::read_dta(...)
  source("sleep-study-metadonnees.R", encoding = "UTF-8")
  haven::write_sav(donnees, "sleep-study-with-metadata.sav")      # optional: a copy
  ```

  `user_na = TRUE` matters for an SPSS file: without it, haven turns the missing codes already declared into empty cells (a 9 "Prefer not to answer" becomes an empty cell, and the copy loses that information). Measurement levels are not applied by R: haven does not write them.
- **SPSS**: open the database, then **File > Open > Syntax…**, choose the `.sps` file, and **Run > All**. Then save the database under a new name.

**The preparation script, for your scores.** When you have confirmed reversed items or written a scoring, the same button also writes `sleep-study-preparation.sps` and `.R`. To run **after** the command file: they create **new variables**, the reversed items (`sleep_q3_inv`) and the scores, from your scoring; no original variable is changed, and the missing codes are left out of the computations. If the database already holds a score of the same group, the script counts the differences with the one it computes. In R: `source("sleep-study-preparation.R", encoding = "UTF-8")` right after the command file.

**The documented copy, if you want a ready-to-use file.** **Write the documented copy** writes next to the database `sleep-study-documente.sav`, in SPSS format, with your decisions. It also works from a CSV, Stata, SAS or Excel database. Before announcing it, the tool reads it back and compares it with the original cell by cell; at the slightest difference, it deletes it and tells you. Your original file is never changed, and an existing copy is replaced only if you tick the box. The database must be next to the project; otherwise, **Choose the database…**. The copy holds the participants' data: store it like the original.

## 10. With your own data

It works the same with your file: SPSS (`.sav`), CSV (including those of Excel in French, with semicolons and decimal commas), Stata (`.dta`), SAS (`.sas7bdat`) or Excel (`.xlsx`: the first sheet, with the names of the variables in the first row). And with your questionnaire, as PDF or text, in French or in English: check on the **Database** page that the language of the study is the right one.

**The format that gives the best results: `.sav`.** An SPSS file holds what other formats leave the tool to guess: the value labels ("1 = Never"), the declared missing-value codes and the level of measurement. If your survey platform (SurveyMonkey, Qualtrics, LimeSurvey…) or your software can export to `.sav`, choose that format, even if you do not use SPSS: the tool reads it without it. With another format everything works, but check the proposed missing codes and value labels more carefully. A platform's Excel export remains useful next to the `.sav`: choose it as the questionnaire, on the **Questionnaire** page, if you have no PDF.

- Work in a folder meant for this data, following the rules of your team and of your research ethics board. The project file, the codebooks and the `.dd-envois` folder (what was sent to the model) stay next to the data.
- The tool never changes your data file.
- Variables that look like identifiers, free text or dates of birth are found automatically: only their metadata is used, and counts below 5 are masked.
- On a large database, the links proposed by the AI are often right, but not always: questions repeated word for word ("How often does this person support you?", once per person) are the hardest case. Check them before the labels.
- The list of recent projects is kept on your computer (folder `%APPDATA%\ddict`) and holds only file paths; **Clear the list**, on the home page, empties it.

**A raw SurveyMonkey export** (variables named `q0003_0004`, as `.sav`, `.xlsx` or `.csv`) is recognized: the **Database** page shows "SurveyMonkey export recognized.". The tool then reads the structure of the survey in the names: `q0003_0004` is the 4th item of the 3rd question. Each grid becomes a group, each check-all-that-apply question a "multiple response" group with its "other" variable, and a variable is linked to its question in the questionnaire when their texts agree. In an `.xlsx` or `.csv`, the second header row is never read as a participant. Codes whose label says "Don't know" or "Prefer not to answer" are proposed as missing codes, for the team to confirm.

## 11. Rename the variables

A platform export gives names like `q0003_0004`, and a longitudinal study wants the same names from one wave to the next. The **Names** page (after **Groups** in the sidebar) proposes new names; you decide them. The original name stays that of your file, which is never changed.

1. **Give the prefix of the grids.** **Groups** page, on each grid: **Prefix of its items' names** (for example `k6`), then **Save the prefix**. Its items will be named `k6_1`, `k6_2`… The tool never proposes a prefix itself: the acronym of an instrument is your decision.
2. **Naming settings** (**Names** page): the **wave mark** (`_t2`, or empty for a study with a single time point), its place (at the end or at the start) and the maximum length of the names (32, Stata's limit, suits SPSS, R and Stata). **Save and propose the names**.
3. **The proposals**, by rules, without AI: the platform's variables get a fixed name (`respondent_id`, `start_date`…); the items of a grid, `<prefix>_<rank>`; the options of a check-all-that-apply question, `<base name>_<rank>` and `<base name>_other_txt`; a single question, a base name taken from the words of its question. The **base name** of a question is corrected once, in **Base names of the questions** at the bottom of the page, and all its variables follow. A variable with no possible proposal stays "to name" and keeps its original name in the export.
4. **Decide in the table.** It shows, for each variable, the proposed name, its origin, its status and any problem; filters "To name", "Proposed", "In conflict", "Decided". On each row, choose **Accept** or **Reject** in the **Decision** column, or write another name in the **New name** column (it then counts as decided), then click **Save**. Each name is checked (lower case, digits and `_`, a letter first, no SPSS reserved word, no name twice). To go faster, **Choose "Accept" for the N proposed names** fills in the **Decision** column: read the table, change what does not fit, then **Save**. Nothing is saved before that click.

**Take the names of an earlier wave.** Open **Take the names of an earlier wave** and choose the file of wave 1: its project file (`.dd.json`, the most complete), its documented copy (`.sav`) or its table of names (`-correspondance.csv`, written by the tool at export, or your own, with the header `original_name,new_name`). **Take the names** matches each variable by its label, its value labels and its question, never by its number alone: SurveyMonkey renumbers the questions as soon as a question is added. The wave 1 name is proposed with the mark of the current wave (`k6_1_t1` → `k6_1_t2`), and the prefixes of the grids are taken again. A reworded question is never matched on that alone: it is shown to you as a candidate. A **report of the differences** is written next to the project (`<project>-ecarts-vagues.md`): variables added, removed, value labels changed. A table of names only matches by identical original name; if the numbering changed, the report says so.

**At export**, the accepted names apply everywhere: the codebook has an "Original name" column and a "Correspondence" sheet; the SPSS file starts with `RENAME VARIABLES`, the R script with the renaming; the documented copy is written with the new names. The table `<project>-correspondance.csv` is written next to the codebook: it, or the project file, is what the next wave will use. The final version holds only the accepted names.

On the command line: `ddict rename project.dd.json --suffix _t2 --reference wave1.dd.json`.

## 12. Using the analysis context with an AI

The analysis context (section 8) is made to be given as it is to an assistant that writes the code of your analysis. **The model never sees your data**: it receives the description of the database, writes code, and your computer runs that code on the real data.

- **What you send is for your team and your ethics approval to decide**, not the tool. The context without statistics holds metadata only, but the text of the questions, the variable names or the description of the study may be sensitive. The tool itself sends nothing: you copy the file.
- **Choose an assistant that can write code.** In the trial (fictional database, `docs/essais/2026-10-15-contexte-analyse-modele.md`), three online assistants wrote a correct analysis from the context alone; the tool's small local model (qwen2.5 7B) failed, not knowing how to program in R. The local model remains useful for labels and links, not for writing an analysis.
- **Give it the scores already computed** when you can: the preparation script (section 9) does without AI what an AI most often gets wrong (reversed items, missing items, missing codes).
- **Always read and check the code before running it** on your data: in the trial, one assistant kept an empty "Prefer not to answer" group in its results. Note the codebook fingerprint with the code and the results.

## 13. Analyse the database

The **Analyses** page (after **Names** in the sidebar) computes, on your database and with your accepted decisions, six analyses written and checked in advance: **Table 1** (describe the sample), **t test** (compare two groups), **ANOVA** (several groups), **chi-square** (two categorical variables), **correlation** and **linear regression**. Each one is described in detail (conditions, options, formulas, examples, in French) in [`../catalogue-analyses.md`](../catalogue-analyses.md). Nothing is sent outside your computer, and your file is never changed.

**Before you start**, your decisions count: the confirmed missing codes (999, −9) are removed, the new names applied, the reversed items and the scores computed from your scoring (section 7). The **measure level** of each variable (**Database** page) decides which analyses it may enter: a variable without a decided level is offered nowhere. Identifiers, free texts and dates are always left out.

1. **Find the database.** The page looks for the database next to the project and checks that it is the one the project comes from. Otherwise, **Choose the database…**. It is read once, in memory, for the session.
2. **Choose the analysis**, then its variables, role by role (for example **Dependent variable** and **Grouping variable**): each list offers only the variables whose level fits. With the fictional database: **t test**, dependent variable your sleep score (the name you gave it in the scoring, for example `sleep_total`), grouping variable `gender`. As `gender` has three categories, choose the two to compare in **Levels compared**: Woman and Man.
3. **The options** have the recommended value by default (for example Welch, which does not assume equal variances); change them only if you know why.
4. **The conditions show before the computation.** In red, a **refusal**, with its reason (fewer than 2 people in a group, too few observations per predictor…): the button stays greyed out. In yellow, a **warning** (a group of fewer than 5 people, an ordinal variable in a Pearson correlation): the analysis stays allowed, you judge.
5. **Run the analysis.** The result gives an APA-style sentence that describes without judging (no "significant"): the means and standard deviations of the two groups, t with its degrees of freedom, p, and Cohen's d with its 95% confidence interval. Then the people used and excluded, the warnings and the tables.

**The files of the analysis.** **Write next to the project** gives `sleep-study-analyse-1.md` (the report: variables, options, results, codebook fingerprint, date and library versions), `sleep-study-analyse-1.xlsx` (the tables) and `sleep-study-analyse-1.R` (the equivalent R script), with the command file and the preparation script it runs; the next analysis takes number 2. They can also be **downloaded**; the R script comes as a `.zip` with its two files. Only the last analysis stays on screen: keep the reports you need, or add the analysis to the notebook (section 14).

**Redo the analysis in R.** Put the script and its two files in the database's folder, then, in R: `source("sleep-study-analyse-1.R", encoding = "UTF-8")`. It uses only base R and haven, and gives the same results as the tool (checked by tests, within 10⁻⁶).

**The APA tables and figures.** Under the result, the **APA tables and figures** section presents the analysis in APA 7 style: a table ("**Table 1**" in bold, the title in *italics*, horizontal rules only, symbols in italics, a "*Note.*") and, except for Table 1, a figure (means and their 95% confidence interval, grouped bars of a chi-square, scatter plot of a correlation, standardized coefficients of a regression). Each table and figure is described in detail (in French) in [`../tableaux-figures-apa.md`](../tableaux-figures-apa.md).

- **Number, title and note** are changed in the box of each table and figure (for example "Table 3" to follow your article); the preview follows. The numbers cannot be changed: they come from the computation.
- **Word (APA tables and figures)**: a `.docx` file. Each table is a real Word table, to edit like any other; each figure a sharp image, with its number, title and note as text. At the end, in small print, the result's sentence and the codebook fingerprint, for the record.
- **Excel (editable charts)**: a workbook, one sheet per figure, with its data and the **native Excel chart**. Change the colours, axes or labels there, then copy the chart into Word: it stays editable. For a regression chart, the coefficients are horizontal bars with their interval.
- **Write next to the project** also writes these two files (`sleep-study-analyse-1.docx` and `sleep-study-analyse-1-graphiques.xlsx`), with your numbers, titles and notes. On the command line: `ddict analyse … --format docx xlsx` (both by default; `--format aucun` for none).
- The figures show the study's data (a scatter plot shows each person): as for the tables, the team decides what may be published.

**These results come from your data**: store the reports as you store the data, and decide before publishing what small counts (flagged below 5) may show.

**Ask the local AI for a proposal (optional).** At the top of the page, the **Ask the local AI for a proposal** box: write your objective in one sentence ("Do women and men have the same sleep quality?"), then **Ask for a proposal**. The model chosen on the **Local AI** page receives this objective as is, the list of the analyses and that of the variables (name, label, level, group): **no data, no statistic**; **See what would be sent** shows the exact message. Do not write any participant data in the objective. It answers within seconds with one to three proposals, each with its reason; **Take up this proposal** fills the page's choices, and nothing is computed before **Run the analysis**.

What to expect (trials `docs/essais/2026-10-16-ia-conseillere.md` and `2026-10-16-essai-analyses.md`, in French): on the fictional database, the right analysis and the right variables 9 times out of 13; on a real database of 250 variables, the right kind of analysis two times out of three, but less reliable variables. The model proposes an analysis even when none fits, and sometimes picks a less fitting method (Student rather than Welch). **It helps to find the kind of analysis; the choice stays yours.** For a very large database, the tool may refuse to send the message, too long for the model: then choose the analysis yourself.

## 14. The analysis notebook and the results document

An article often brings together ten or twenty results, numbered one after the other, that must stay right when the codebook changes. The **notebook** keeps the study's analyses, in your article's order, and brings them together in a single "Results" document. It uses no AI. The details are in [`../carnet-analyses.md`](../carnet-analyses.md) (in French).

1. **Add an analysis.** On the **Analyses** page, after **Run the analysis**, the **Analysis notebook** section has an **Add to the notebook** button. The analysis goes at the end of the notebook, retained, with the titles and notes you changed in the APA tables and figures (not their numbers: the notebook numbers in its order). The button becomes "Already in the notebook (A1)".
2. **The Notebook page** (after **Analyses**) lists the analyses in their order: number (A1, A2…), title, variables, result sentence and state. **Move up** and **Move down** change the order; **Retained for the document** leaves an analysis out of the document without removing it; **Remove** deletes it (its number does not come back).
3. **When a decision changes** (a missing code confirmed, a measure level corrected), each analysis is recomputed when the page opens:
   - **up to date** or **recomputed, unchanged**: nothing to do;
   - **changed, to confirm**: the page shows what changed (for example "n_used : 200 → 196", "r : ,05 → ,01") and the new sentence. **Confirm the new computation** adopts it. As long as a retained analysis waits for its confirmation, the results document is not produced;
   - **cannot be computed**: the reason shows (a variable removed, a measure level that no longer fits). The analysis stays in the notebook, but it is left out of the document, and the end of the document says so.
4. **The results document.** Set the **First table** and the **First figure** if needed (for example 3, if two tables come before in your article), then **Produce the results**. Three files are written next to the project, and replaced each time:
   - `sleep-study-resultats.docx`: a heading per analysis ("A2 — t test: compare two groups"), its result sentence, its APA tables and figures numbered one after the other; at the end, the codebook fingerprint, the date, the versions and the list of the analyses;
   - `sleep-study-resultats-graphiques.xlsx`: the native Excel chart of each figure;
   - `sleep-study-resultats-R.zip`: the **R master script**, which redoes all the retained analyses, in order, with the command file and the preparation script. Unzip it in the database's folder, then, in R: `source("sleep-study-resultats.R", encoding = "UTF-8")`. It gives the same values as the tool (checked by tests, within 10⁻⁶), stored in `resultats$A1`, `resultats$A2`…

Each analysis is **recomputed** on the database when the document is produced: nothing is copied from the notebook. The notebook, `sleep-study-carnet.json`, is next to the project; it keeps aggregates only (counts, means, statistics, sentences), never a row of the database. Without the database, the page shows the notebook as it is, without recomputing it, and **Choose the database…** finds it.

On the command line: `ddict notebook add` (same options as `ddict analyse`), `list`, `move A3 1`, `retain A2`, `leave-out A2`, `remove A2`, `confirm A1` (or `--all`), `numbers --table 3 --figure 2`; then `ddict results` writes the three files. The page and the commands read and write the same notebook.

## Update or uninstall

- **Update**: download and extract the new archive, then double-click its `installer.bat`. If the tool is open, the installer offers to close it (answer `y`): it cannot replace it while it runs. Your project files are kept. A project opened with version 0.8 no longer opens with an older version (its format changed); the reverse works.
- **Uninstall**: double-click `desinstaller.bat`, in the tool's folder. It removes the tool and its icons, without touching your projects, codebooks or data; it asks before clearing the list of recent projects. uv and Ollama stay installed.

## For those who prefer the command line

Every step also exists as a command, in PowerShell (`ddict --help` lists them). The commands have English names next to their French ones:

```
ddict                                         # open the interface on the home page
ddict profile sleep-study.sav                 # read the database, create the project file
ddict questionnaire sleep-study.dd.json questionnaire-sleep.pdf
ddict link sleep-study.dd.json --model qwen2.5:7b-instruct-q4_K_M
ddict enrich sleep-study.dd.json --model qwen2.5:7b-instruct-q4_K_M
ddict review sleep-study.dd.json              # open a project directly
ddict export sleep-study.dd.json --language en          # Excel codebook and report
ddict export sleep-study.dd.json --syntax     # and the SPSS and R command files
ddict export sleep-study.dd.json --context    # and the analysis context (--with-statistics)
ddict document sleep-study.dd.json            # documented copy of the database (.sav)
ddict rename study-t2.dd.json --suffix _t2 --reference study-t1.dd.json   # names
ddict analyse sleep-study.dd.json t_test --outcome sleep_total --group gender --levels 1,2
ddict notebook add sleep-study.dd.json correlation --variables sleep_hours n_awakenings
ddict notebook list sleep-study.dd.json      # the notebook, recomputed
ddict results sleep-study.dd.json            # the results document and the R master script
ddict advise sleep-study.dd.json "Compare the sleep of women and men." --model qwen2.5:7b-instruct-q4_K_M
ddict evaluate --model qwen2.5:7b-instruct-q4_K_M       # model bench
```

`--preview` (with `link` or `enrich`, without `--model`) writes the messages that would be sent into the `sleep-study.dd-envois\apercu` folder, without sending anything. `ddict export --no-text G2` leaves out the question text of a group for one export. `ddict analyse` writes the report, the tables and the R script next to the project (analyses: `table1`, `t_test`, `anova`, `chi_square`, `correlation`, `regression`); `ddict advise` shows the model's proposals without computing anything (`--preview` to see the message only).

## If something goes wrong

| What happens | What to do |
|---|---|
| "Windows protected your PC" when double-clicking `installer.bat` | **More info**, then **Run anyway** (section 1). |
| `installer.bat` stops on a red message | Check the Internet connection, then run it again. If the message persists, write it down and pass it on. Some institutional computers forbid scripts: ask your IT support. |
| "Ce dossier ne contient pas l'outil" (this folder does not contain the tool) | `installer.bat` was copied out of the archive: run the one in the extracted tool's folder (section 1, step 2). |
| "L'outil est encore ouvert" (the tool is still open) | Close the tool's window (or click **Quit the tool**), then run the installer again. |
| The "Open" window does not appear | It may be behind the tool's window: look in the taskbar. Otherwise, paste the file's path in the field under the button (right-click the file in File Explorer, **Copy as path**). |
| Nothing opens when double-clicking the icon | Wait ten seconds or so. Otherwise, open the tool's journal: paste `%APPDATA%\ddict\journal.txt` in the address bar of File Explorer, then Enter. It holds its start-up messages (no data): pass it on. |
| "A project already exists for this database" | The tool does not overwrite your work: **Open the existing project**, or **Replace the project** if you really want to start over (its decisions will be lost). |
| Local AI page: "Is Ollama running?" | Start Ollama from the Start menu, wait for its icon next to the clock, then **Check again**. |
| Local AI page: no model installed | Run `installer.bat` again and answer `y` to download the model, or follow the page's instructions. |
| A grid of the questionnaire is "to check" | Its column headings run together in the PDF: the tool then proposes no value labels for its variables. A `.txt` copied from Word avoids the problem. |
| "Cannot write the files" when exporting | The codebook is probably open in Excel: close it, then try again. |
| Documented copy: "The database … cannot be found next to the project" | Put the database in the project's folder, or **Choose the database…**. |
| Documented copy: "… is no longer the file the project comes from" | The database changed since the project was created (new export, corrected data). Create a new project from the current database. |
| R: "there is no package called 'haven'" | In R, once: `install.packages("haven")`. |
| The tool seems frozen | Close its window, then double-click the icon again. The decisions already taken are saved. |

For any other difficulty, write down what you did and the message you got, and pass them on to the person who gave you the tool.
