# Installing and using the tool on Windows

This guide is for people who do not program. It goes from the installation to a complete codebook, made from the fictional database and its questionnaire that come with the tool. Everything is done by double-clicking and in the tool's window; there are no commands to type. Allow an hour.

En français : [`../installation-windows.md`](../installation-windows.md).

> **Trial version of the English.** The tool was written in French first; its English interface is new (version 0.5) and its translation has not yet been reviewed by a native English speaker. If a sentence is unclear or wrong, write it down and pass it on. The installer window speaks French only: this guide gives what it says.

## What you need

- Windows 10 or 11. No administrator rights needed.
- An Internet connection **during the installation**. Afterwards, the tool reads your files and writes its results on your computer, without the Internet; it uses it only for the AI, if you use it, and only for a project that allows it.
- For the AI, which is optional: an API key, paid by your team (section 6). Nothing to install, no graphics card.

## 1. Install

1. Download the tool's archive from the releases page of the project on GitHub: the **Source code (zip)** link, for example `dictionnaire-donnees-0.8.0.zip`.
2. In File Explorer, right-click the downloaded file, **Extract All**, then **Extract**. Open the extracted folder; if it holds only one folder of the same name, open that one: it is **the tool's folder**, with `installer.bat`, `docs` and `exemples`.
3. Double-click **`installer.bat`**.
   - If Windows shows "**Windows protected your PC**", click **More info**, then **Run anyway**. This message appears for any downloaded program that is not signed by a paying publisher; the installer is a plain script, readable in the `windows` folder.
4. A window opens and goes through three steps (in French): uv (the Python manager, installed in your user folder), the tool (a minute or two the first time), then the icons ("Les icônes"). A warning in English about the "PATH" may appear: that is normal, the installer takes care of it. The AI needs no installation: its key is typed later, in the tool (section 6).
5. "Installation terminée" (installation finished): press Enter to close the window. A **Dictionnaire de données** icon is on your desktop and in the Start menu.

## 2. Open the tool

Double-click the **Dictionnaire de données** icon. After a few seconds, the tool opens in its own window, on the **home page**. It is a local page (address `http://127.0.0.1`), reachable from your computer only.

**To stop the tool, close its window**, or click **Quit the tool** at the bottom of the sidebar. Your decisions are saved as you go: nothing is lost. Another double-click on the icon while the tool runs opens one more window.

If the window cannot open (on a computer without the Edge engine, for example), the tool opens in your browser and works the same way; then stop it with **Quit the tool**.

**Language**: at the top of the home page, **Français · English** chooses the language of the interface. The choice applies at once and is remembered on your computer. Choose **English**.

## 3. A first codebook, from the fictional database

The fictional database is a small invented study of sleep (200 fictional participants), with its questionnaire. It lets you try the tool without any real data. It exists in French and in English; this guide uses the English version.

**The shortest way** (since 0.16): on the home page, section **Try the tool**, click **Try with the fictional database**. The tool copies the French version (`etude-sommeil.sav` and `questionnaire-sommeil.pdf`) into your Documents folder, under `Dictionnaire de données - essai`, creates the project, reads the questionnaire and opens it. Afterwards the button becomes **Resume the trial**; **Start the trial again** makes the project anew after a tick box (its decisions are lost). The steps below use the English version, as with your own data:

1. On the home page, under **New project**, click **Choose a database…**. The Windows "Open" window appears (if you do not see it, look in the taskbar). Go to the tool's folder, then `exemples\bases-fictives`, and choose `sleep-study.sav`.
2. Click **Create the project**. The tool reads the database and creates next to it the **project file**, `sleep-study.dd.json`. It holds everything the tool computed (types, missing values, categories, labels) and, later, your decisions; it does not hold the participants' individual answers. The data file is never changed.
3. The **Database** page sums up what was read: number of variables and rows, sensitive variables, flags. It also shows the **language of the study** (that of its questionnaire and labels), guessed by the tool and which you can change: the model writes its proposals in this language. Here it is "English".
4. In the sidebar, choose **Export**, then **Write the codebook and the report**. Two files appear next to the project: `sleep-study.xlsx` (the codebook, to open with Excel) and `sleep-study.md` (the same content as text). The **Open the folder** button shows them in File Explorer.

Your first codebook is done, without AI: everything in it was computed exactly from the file. The next sections enrich it; you can stop at any of them and export.

**The menu of the sidebar** (since 0.16) arranges the pages in three jobs: **Document** (Database, Questionnaire, Glossary, Variables, Groups, Names, Export), **Analyse** (Plan, Analyses, Notebook) and **Write** (Method, Verify), then **Settings** (AI). Each page shows what waits there ("Glossary (2)"), or ✓ when nothing waits. The **Codebook N% documented** bar measures what your team has decided, part by part (the detail is in the Summary tab of the Database page). The long pages are in **tabs**: Database (Summary, Description, Measure levels, Sensitive), a group (Items, Scoring, Instrument, Recodings), the result of an analysis (Result, Tables and figures, Files).

Under the menu, the **to-do list** says what is waiting, in the recommended order ("Add the study questionnaire", "Acronyms to accept: 3"…), up to the article: the plan to freeze, the numbers to confirm in the notebook, the gaps of the Method, the draft to check. Each line is a button that leads to the right page. The **Home** button takes you back to the home page, where the table **My projects** comes first (section 19), then your **Recent projects**, with their folder and the date of their last change; each opens again in one click.

When a message points to another page ("The measure level is decided on the Database page", "acronyms… without a definition: anx"), a button comes with it and leads there, already filled in: **Define anx** opens the glossary with the acronym in its field.

## 4. Add the questionnaire

The study's questionnaire says what each variable means: the exact text of the questions, the meaning of acronyms, the answer options. The tool reads it without AI, as a PDF (export from SurveyMonkey, LimeSurvey, REDCap…) or as text (`.txt` copied from Word).

1. **Questionnaire** page (or "Add the study questionnaire" in the to-do list): **Choose the questionnaire…**, then `questionnaire-sleep.pdf` in `exemples\bases-fictives`, and **Read the questionnaire**.
2. The tool shows the number of questions found, the questions to check (for example a grid whose column headings run together), the **acronyms defined in the questionnaire** ("Cognitive behavioural therapy (CBT)") and the acronyms in variable names that have no definition. **Questions found** shows them all.
3. **Glossary** page: for each acronym found, **Accept** takes the meaning shown in its field, as it is or as you corrected it (the questionnaire's meaning is then kept as its origin); **Reject** is right next to it. **Accept all (N)…** shows the exact list, each acronym with its meaning, before accepting the ticked ones. Add the missing ones (here, ANX: "anxiety"; the **Define anx** button fills in the acronym). **The AI never defines an acronym**: that is where it errs most, and the glossary comes only from the questionnaire and from you.

The text of the questionnaire stays in the project file; only the questions linked to variables go into the codebook, never the consent page.

## 5. Link the variables to the questions

Each variable comes from a question, a grid item or an option of a checkbox question; or from none (an identifier, a date of completion, a computed score).

- **Without AI**: **Variables** page, **Without a question** filter. On each variable's page, the **Question in the questionnaire** section offers a list with the candidate questions computed by the tool at the top; choose, then **Link**.
  - For an identifier, a date of completion or a score that is the exact sum of the items of a grid, "**No question in the questionnaire**" comes first: the tool deems it likely, but the decision is yours.
  - Some questions do not use the words of the variable's name ("How old are you?" for `age`). When the tool finds no candidate, it puts first the **neighbouring questions**, those at that place in the questionnaire, between the sure questions around it; a short text below the list says so.
- **With AI** (section 6): the model chooses among the candidates, then you accept, correct or reject each choice, in the same way. When the computation is sure of its choice and the model chooses another, the model's proposal is kept but flagged ("departs from the computation's sure choice"): compare with the first question of the list. These links are left out of the grouped decisions.

When the file has no value labels (a CSV, for example), the tool proposes "1 = Not at all … 5 = Extremely" from the options of the linked question, only in safe cases. The words "**assumed order, to check**" are meant seriously: check the order of the codes in your survey platform or recoding script before accepting. A recoded database may have 0 = "Other" where the questionnaire puts "Other" last.

## 6. Optional: the AI, with an API key

The AI proposes links to questions, then labels and descriptions easier to read than variable names; on the Analyses page, it also proposes an analysis for an objective (section 13). Every proposal waits for your decision. The tool works fully without it: the computation alone already proposes the candidate questions.

**What is sent.** The AI is an external service (Anthropic by default, or your university's AI server). It receives **metadata only**, what the questionnaire and the codebook say: the names and labels of variables and values, the declared missing codes, the text of the questions whose link you accepted, the accepted acronyms of the glossary, the type and level of measurement. **Never** an answer of a participant, nor a statistic drawn from the answers (counts, proportions, missing values, minimum, maximum, mean, years), nor a value of a free text or of an identifier, nor the name of the database, nor your notes. And **only for a project that allows it**: a box, not ticked by default. At Anthropic, for the API, requests and answers are deleted within 30 days, with exceptions (a "zero data retention" agreement, content flagged under the usage policy, kept up to 2 years, a legal obligation; [their policy](https://privacy.claude.com/en/articles/7996866-how-long-does-anthropic-store-my-organizations-data), read on 2026-10-19). Submit these rules to your ethics board if your certificate requires it.

**Getting an API key (Anthropic)**, once, by the person who manages the team's budget:

1. Create an account on Anthropic's console, [console.anthropic.com](https://console.anthropic.com).
2. Add a payment method or credits: each request is billed on this account.
3. **Set a spending limit** in the console's billing settings: it protects the team from a mistake or a lost key.
4. Create an API key and copy it. It is shown only once; do not e-mail it to anyone, do not write it in any file.

(The names of the console's menus may change; what matters is the spending limit.) For a university's server, ask its IT service for its address (often ending with `/v1`), the model's name and a key.

**In the tool:**

1. **AI** page (Settings menu): the service (Anthropic by default), the address, the model (by default `claude-haiku-5-5`, with medium thinking: chosen after the model bench, `docs/essais/2026-10-19-anthropic.md`), then **Save the settings**. Paste the key in **New API key**, then **Record the key**: it is kept in Windows' Credential Manager, never in a project nor in a file, and will not be shown again; **Forget the key** erases it. **Test the connection** asks for the list of models: nothing of a project is sent, nothing is billed.
2. In the project's sidebar, tick **Allow the metadata of this project to be sent to the AI**. The box is saved in the project, with its date: your colleagues see it. Without it, no AI button sends anything.
3. **Links to questions**: **See exactly what would be sent (nothing is sent)** shows the messages, without sending anything (always possible, even without the box). Then **Get proposals: links to questions**. A progress bar moves block by block (20 variables per message).
4. **Review the links** (Variables page, "To review" filter; or the to-do list) before going further. The order matters: for the labels, the model receives the text of the questions whose link you accepted, and the meaning of the acronyms you accepted. A wrong link would give it a wrong question.
5. **Labels and descriptions**: **Get proposals: labels and descriptions** (25 variables per message), then review them.

During a job, **Stop** (or a change of page) interrupts it after the block in progress. The finished blocks are saved; run it again to continue where it stopped. Each exchange is kept next to the project, in the `<project>.dd-envois` folder.

**What it costs**: a few cents for the labels of a database of a few hundred variables with `claude-haiku-5-5`, more with a larger model; the model bench gives the real figures.

**Model bench** (at the bottom of the same page, or `ddict evaluate`): to choose a model, **Measure this model** tries it on the tool's fictional databases (three in French, one in English), whose right answers are known; the fourth, a fictional study of physical activity, served to check version 0.6 without any tuning. The report says how many links are right (and those of the computation alone, for comparison), how many labels or descriptions may contain an invention (citation, threshold, instrument name, meaning of an acronym, range, meaning of codes without a label) and the duration. Your data is not used. The bench sends several dozen messages: it asks before spending. The report is written next to the project (`banc-essai-<model>-<date>.md`) and can be downloaded.

## 7. Review

- **Variables**: the filter ("To review", "With flags", "Sensitive", "Without a question", "Suspect codes", "All") and the list of variables; **Previous** and **Next**, at the top of the page, go from one variable to the next in the filter's order. An empty filter says so in the middle of the page and offers the filters that hold variables. On each page: what the file says, what was computed, the linked question, and each proposal on the same **decision card** (since 0.16): the value, its origin and status, the field to correct it, then **Accept**, which takes the value shown in the field, corrected or not, and **Reject**, right next to it. A decided value is then changed with **Save**. The proposed measure level and new name are decided there too, as in the tables of the Database and Names pages. Each decision is saved at once in the project file.
- **Red box**: the proposal needs special attention: a guessed label for a variable without a label, the meaning of an acronym nobody gave the AI, or the observed range presented as the range of a scale.
- **Flags**: computed anomalies, among them **spelling variants** of the same answer ("French", "french", "FRENCH"), to correct in your data if you wish.
- **Grouped decisions**: at the top of the Variables page, **Accept the links where the model and the computation agree (N)…** opens the exact list of these links, each with its question. Read every line and uncheck what does not fit (in a trial, about one in five was wrong on a real database), then **Accept these N links**. On a group's page, **Accept the value labels of this group (N)…** does the same for the labels taken from the options.
- **Suspect codes** (filter of the same name, or the to-do list): a value such as 999 or −9, isolated far from the others, may be a missing code the file does not declare. Only your team knows: **It is a missing code** or **It is a real value**. The codebook will say so; **Undo this decision** cancels it.
- **Documented fields**: theoretical range, thresholds, references and notes. They are for people only, and the range and the thresholds require a source (manual, article). They start empty.
- **One "Save" per section** (since 0.16): the texts of a variable, each tab of a group, the description of the database. Until the section is saved, "Changes not saved" shows next to the button. If you leave the page or the variable without saving, nothing is lost: the page you arrive on says "Typed and not saved: …", with **Back to …** (what you typed goes back into its fields) and **Discard**. **Quit the tool** asks first in that case. Closing the window, however, gives no warning.
- **Nothing proposed is already filled in** (since 0.16): a field that holds a decision of the team never starts from a computed value. A **Take up…** button names what the tool proposes and puts it in the field, without saving anything; so for the question to link ("Take up the computed proposal: Q3"), the reversed items and the scoring.
- **Groups**: the scales found by the tool (named by what they are: "G1 — 8 items, codes 1 to 5"), their Cronbach's alpha and the items probably reversed. "Confirmed reversed items" stays empty until you confirm any; **Take up the likely items (…)** puts them there, then save. Confirming a reversal **documents** it in the codebook; the tool never recodes the data. For an **instrument protected by copyright** (CBCL, BDI…), check "Do not reproduce the text of this group's questions in the codebook": the codebook will give the reference of each question (`Q12.r3, p. 4`), without its text. Reproducing the items of a protected instrument is up to your team.
- **Scoring of a scale** (Groups page, "Scoring" section): the items of the score (**Take the N items of the group**), sum or mean, the scale's minimum and maximum (**Take up the bounds of the labels**), the minimum of items answered (0: all) and, for a sum that allows missing items, the rule (prorated sum or sum of the items answered), the score's name and **a required source**. The reversed items are those confirmed above; the range of the score is computed. A scoring that does not fit this frame is written as a note. The AI never proposes a scoring.
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
- The lists of recent and followed projects are kept on your computer (folder `%APPDATA%\ddict`) and hold only file paths; **Clear the list**, on the home page, empties the recent ones, and **Stop following** takes a followed project off its list.

**A raw SurveyMonkey export** (variables named `q0003_0004`, as `.sav`, `.xlsx` or `.csv`) is recognized: the **Database** page shows "SurveyMonkey export recognized.". The tool then reads the structure of the survey in the names: `q0003_0004` is the 4th item of the 3rd question. Each grid becomes a group, each check-all-that-apply question a "multiple response" group with its "other" variable, and a variable is linked to its question in the questionnaire when their texts agree. In an `.xlsx` or `.csv`, the second header row is never read as a participant. Codes whose label says "Don't know" or "Prefer not to answer" are proposed as missing codes, for the team to confirm.

## 11. Rename the variables

A platform export gives names like `q0003_0004`, and a longitudinal study wants the same names from one wave to the next. The **Names** page (Document section of the menu) proposes new names; you decide them. The original name stays that of your file, which is never changed.

1. **Give the prefix of the grids.** **Groups** page, on each grid: **Prefix of its items' names** (for example `k6`), then **Save**, at the bottom of the Items tab. Its items will be named `k6_1`, `k6_2`… The tool never proposes a prefix itself: the acronym of an instrument is your decision.
2. **Naming settings** (**Names** page): the **wave mark** (`_t2`, or empty for a study with a single time point), its place (at the end or at the start) and the maximum length of the names (32, Stata's limit, suits SPSS, R and Stata). **Propose the names** saves these settings, then proposes (a single action since 0.16).
3. **The proposals**, by rules, without AI: the platform's variables get a fixed name (`respondent_id`, `start_date`…); the items of a grid, `<prefix>_<rank>`; the options of a check-all-that-apply question, `<base name>_<rank>` and `<base name>_other_txt`; a single question, a base name taken from the words of its question. The **base name** of a question is corrected once, in **Base names of the questions** at the bottom of the page, and all its variables follow. A variable with no possible proposal stays "to name" and keeps its original name in the export. Optional: under the table of base names, **Get proposals: base names** asks the AI for those the rules leave open (the project must allow it, section 6); on the fictional database, it finds more often the name a team would choose. Each name stays to decide; an acronym that is not in the question is flagged.
4. **Decide in the table.** It shows, for each variable, the proposed name, its origin, its status and any problem; filters "To name", "Proposed", "In conflict", "Decided". On each row, choose **Accept** or **Reject** in the **Decision** column, or write another name in the **New name** column (it then counts as decided), then click **Save**. Each name is checked (lower case, digits and `_`, a letter first, no SPSS reserved word, no name twice). To go faster, **Choose "Accept" for the N proposed names** fills in the **Decision** column: read the table, change what does not fit, then **Save**. Nothing is saved before that click.

**Take the names of an earlier wave.** Open **Take the names of an earlier wave** and choose the file of wave 1: its project file (`.dd.json`, the most complete), its documented copy (`.sav`) or its table of names (`-correspondance.csv`, written by the tool at export, or your own, with the header `original_name,new_name`). **Take the names** matches each variable by its label, its value labels and its question, never by its number alone: SurveyMonkey renumbers the questions as soon as a question is added. The wave 1 name is proposed with the mark of the current wave (`k6_1_t1` → `k6_1_t2`), and the prefixes of the grids are taken again. A reworded question is never matched on that alone: it is shown to you as a candidate. A **report of the differences** is written next to the project (`<project>-ecarts-vagues.md`): variables added, removed, value labels changed. A table of names only matches by identical original name; if the numbering changed, the report says so.

**At export**, the accepted names apply everywhere: the codebook has an "Original name" column and a "Correspondence" sheet; the SPSS file starts with `RENAME VARIABLES`, the R script with the renaming; the documented copy is written with the new names. The table `<project>-correspondance.csv` is written next to the codebook: it, or the project file, is what the next wave will use. The final version holds only the accepted names.

On the command line: `ddict rename project.dd.json --suffix _t2 --reference wave1.dd.json` (and `--ai` for base names proposed by the AI).

## 12. Using the analysis context with an AI

The analysis context (section 8) is made to be given as it is to an assistant that writes the code of your analysis. **The model never sees your data**: it receives the description of the database, writes code, and your computer runs that code on the real data.

- **What you send is for your team and your ethics approval to decide**, not the tool. The context without statistics holds metadata only, but the text of the questions, the variable names or the description of the study may be sensitive. The tool itself sends nothing: you copy the file.
- **Choose an assistant that can write code.** In the trial (fictional database, `docs/essais/2026-10-15-contexte-analyse-modele.md`), three online assistants wrote a correct analysis from the context alone; a small model of 7 billion parameters, installed on the computer, failed, not knowing how to program in R.
- **Give it the scores already computed** when you can: the preparation script (section 9) does without AI what an AI most often gets wrong (reversed items, missing items, missing codes).
- **Always read and check the code before running it** on your data: in the trial, one assistant kept an empty "Prefer not to answer" group in its results. Note the codebook fingerprint with the code and the results.

## 13. Analyse the database

The **Analyses** page (Analyse section of the menu) computes, on your database and with your accepted decisions, six analyses written and checked in advance: **Table 1** (describe the sample), **t test** (compare two groups), **ANOVA** (several groups), **chi-square** (two categorical variables), **correlation** and **linear regression**. Each one is described in detail (conditions, options, formulas, examples, in French) in [`../catalogue-analyses.md`](../catalogue-analyses.md). Nothing is sent outside your computer, and your file is never changed.

**Before you start**, your decisions count: the confirmed missing codes (999, −9) are removed, the new names applied, the reversed items and the scores computed from your scoring (section 7). The **measure level** of each variable (**Database** page) decides which analyses it may enter: a variable without a decided level is offered nowhere. On the command line, `ddict levels list` shows the proposed levels, `ddict levels accept` (names, or `--all`), `reject` and `set age scale` decide them; `ddict codes list` shows the suspect missing codes, `ddict codes missing -9 nb_reveils`, `value` and `undo` decide them, as the **Database** and **Variables** pages do. Identifiers, free texts and dates are always left out. Since 0.13, a category written out in a CSV ("yes", "no") enters the analyses once its level is "nominal"; an empty cell counts there as a missing value.

1. **Find the database.** The page looks for the database next to the project and checks that it is the one the project comes from. Otherwise, **Choose the database…**. It is read once, in memory, for the session.
2. **Choose the analysis**, then its variables, role by role (for example **Dependent variable** and **Grouping variable**): each list puts first the variables that fit, then the others, each with its reason in brackets ("3 categories: choose the two compared", "ordinal level", "scale level"); a variable that does not fit is still refused before the computation (since 0.16). With the fictional database: **t test**, dependent variable your sleep score (the name you gave it in the scoring, for example `sleep_total`), grouping variable `gender`. As `gender` has three categories, choose the two to compare in **Levels compared**: Woman and Man.
3. **The options** have the recommended value by default (for example Welch, which does not assume equal variances); change them only if you know why.
4. **The conditions show before the computation.** In red, a **refusal**, with its reason (fewer than 2 people in a group, too few observations per predictor…): the button stays greyed out. In yellow, a **warning** (a group of fewer than 5 people, an ordinal variable in a Pearson correlation): the analysis stays allowed, you judge.
5. **Run the analysis.** The result gives an APA-style sentence that describes without judging (no "significant"): the means and standard deviations of the two groups, t with its degrees of freedom, p, and Cohen's d with its 95% confidence interval. Then the people used and excluded, the warnings and the tables.

**The files of the analysis.** **Write next to the project** gives `sleep-study-analyse-1.md` (the report: variables, options, results, codebook fingerprint, date and library versions), `sleep-study-analyse-1.xlsx` (the tables) and `sleep-study-analyse-1.R` (the equivalent R script), with the command file and the preparation script it runs; the next analysis takes number 2. Right under **Run the analysis**, before the result, a bar gives what comes next: **Add to the notebook**, **Word** (the APA tables and figures), **Excel** (the result's tables) and **R script** (a `.zip` with its two files). Only the last analysis stays on screen: keep the reports you need, or add the analysis to the notebook (section 14).

**Redo the analysis in R.** Put the script and its two files in the database's folder, then, in R: `source("sleep-study-analyse-1.R", encoding = "UTF-8")`. It uses only base R and haven, and gives the same results as the tool (checked by tests, within 10⁻⁶).

**The APA tables and figures.** Under the result, the **APA tables and figures** section presents the analysis in APA 7 style: a table ("**Table 1**" in bold, the title in *italics*, horizontal rules only, symbols in italics, a "*Note.*") and, except for Table 1, a figure (means and their 95% confidence interval, grouped bars of a chi-square, scatter plot of a correlation, standardized coefficients of a regression). Each table and figure is described in detail (in French) in [`../tableaux-figures-apa.md`](../tableaux-figures-apa.md).

- **Number, title and note** are changed in the box of each table and figure (for example "Table 3" to follow your article); the preview follows. The numbers cannot be changed: they come from the computation.
- **Word** (in the bar, under **Run the analysis**): a `.docx` file. Each table is a real Word table, to edit like any other; each figure a sharp image, with its number, title and note as text. At the end, in small print, the result's sentence and the codebook fingerprint, for the record.
- **Excel (editable charts)**: a workbook, one sheet per figure, with its data and the **native Excel chart**. Change the colours, axes or labels there, then copy the chart into Word: it stays editable. For a regression chart, the coefficients are horizontal bars with their interval.
- **Write next to the project** also writes these two files (`sleep-study-analyse-1.docx` and `sleep-study-analyse-1-graphiques.xlsx`), with your numbers, titles and notes. On the command line: `ddict analyse … --format docx xlsx` (both by default; `--format aucun` for none).
- The figures show the study's data (a scatter plot shows each person): as for the tables, the team decides what may be published.

**These results come from your data**: store the reports as you store the data, and decide before publishing what small counts (flagged below 5) may show.

**Ask the AI for a proposal (optional).** At the top of the page, the **Ask the AI for a proposal** box: write your objective in one sentence ("Do women and men have the same sleep quality?"), then **Ask for a proposal** (the project must allow it, section 6). The model chosen on the **AI** page receives this objective as is, the list of the analyses and that of the variables (name, label, level, group): **no data, no statistic**; **See what would be sent** shows the exact message. Do not write any participant data in the objective. It answers within seconds with one to three proposals, each with its reason; **Take up this proposal** fills the page's choices, and nothing is computed before **Run the analysis**.

What to expect (trials `docs/essais/2026-10-16-ia-conseillere.md` and `2026-10-16-essai-analyses.md`, in French): on the fictional database, the right analysis and the right variables 9 times out of 13; on a real database of 250 variables, the right kind of analysis two times out of three, but less reliable variables. The model proposes an analysis even when none fits, and sometimes picks a less fitting method (Student rather than Welch). **It helps to find the kind of analysis; the choice stays yours.** For a very large database, the tool may refuse to send the message, too long for the model: then choose the analysis yourself.

## 14. The analysis notebook and the article draft

An article often brings together ten or twenty results, numbered one after the other, that must stay right when the codebook changes. The **notebook** keeps the study's analyses, in your article's order, and brings them together in an article draft. It uses no AI. The details are in [`../carnet-analyses.md`](../carnet-analyses.md) (in French).

1. **Add an analysis.** On the **Analyses** page, right under **Run the analysis**, the **Add to the notebook** button. The analysis goes at the end of the notebook, retained, with the titles and notes you changed in the APA tables and figures (not their numbers: the notebook numbers in its order). The button becomes "Already in the notebook: A1", with **Open the notebook**; an identical analysis (same variables, options and subgroup) says so on the following days too: it never goes in twice.
2. **The Notebook page** (after **Analyses**) lists the analyses in their order: number (A1, A2…), title, variables, result sentence and state. **Move up** and **Move down** change the order; **Retained for the document** leaves an analysis out of the document without removing it; **Remove** deletes it (its number does not come back).
3. **When a decision changes** (a missing code confirmed, a measure level corrected), each analysis is recomputed when the page opens:
   - **up to date** or **recomputed, unchanged**: nothing to do;
   - **changed, to confirm**: the page shows what changed (for example "n_used : 200 → 196", "r : ,05 → ,01") and the new sentence. **Confirm the new computation** adopts it. As long as a retained analysis waits for its confirmation, the article draft is not produced;
   - **cannot be computed**: the reason shows (a variable removed, a measure level that no longer fits). The analysis stays in the notebook, but it is left out of the document, and the end of the document says so.
4. **The article draft.** Set the **First table** and the **First figure** if needed (for example 3, if two tables come before in your article), then **Produce the article draft**. Three files are written next to the project, and replaced each time:
   - `sleep-study-article.docx`: since 0.13, an APA article draft, from the title page to the References (section 16): the Method (section 15), then a heading per analysis ("A2 — t test: compare two groups"), or per hypothesis when the study has a plan, with its result sentence and its APA tables and figures, numbered one after the other across the whole document; at the end, the codebook fingerprint, the date, the versions and the list of the analyses;
   - `sleep-study-article-graphiques.xlsx`: the native Excel chart of each figure;
   - `sleep-study-article-R.zip`: the **R master script**, which redoes all the retained analyses, in order, with the command file and the preparation script. Unzip it in the database's folder, then, in R: `source("sleep-study-article.R", encoding = "UTF-8")`. It gives the same values as the tool (checked by tests, within 10⁻⁶), stored in `resultats$A1`, `resultats$A2`…

Each analysis is **recomputed** on the database when the document is produced: nothing is copied from the notebook. The notebook, `sleep-study-carnet.json`, is next to the project; it keeps aggregates only (counts, means, statistics, sentences), never a row of the database. Without the database, the page shows the notebook as it is, without recomputing it, and **Choose the database…** finds it.

On the command line: `ddict notebook add` (same options as `ddict analyse`), `list`, `move A3 1`, `retain A2`, `leave-out A2`, `remove A2`, `confirm A1` (or `--all`), `numbers --table 3 --figure 2`; then `ddict paper` (or `ddict article`) writes the three files (`ddict results`, its former name, still works in this version). The page and the commands read and write the same notebook.

## 15. The Method: exclusions, flow diagram and paragraphs

The Method section of an article says who was excluded and why, describes the sample and the measures, and names the analyses. The **Method** page (after **Notebook**) prepares all of this from your decisions, without any AI. It decides nothing for you: each exclusion rule is yours, written with its reason. The details of the sentences are in [`../methode-gabarits.md`](../methode-gabarits.md) (in French).

1. **The exclusion rules.** Open **Add a rule** and choose the **Kind of rule**:
   - **Condition on a variable**: for example `age` "< less than" 18; or "missing";
   - **Condition on a score**: on the score of a scored group (Groups page, "Scoring" section, see section 7);
   - **Completeness of a group**: exclude whoever answered fewer than … items;
   - **Duration of administration**: between a start date and an end date, under a threshold in seconds. The tool proposes no threshold: it is the team's choice, and the **Source** is required (minutes of a meeting, an article);
   - **Grid in a straight line**: every item of a grid answered with the same value;
   - **Duplicates**: an answer that repeats an earlier one on the chosen variables (the first is kept).

   Write the **Reason, as published** ("Under 18"), then **Add the rule**. The rules apply in their order: a person is counted by the first rule that excludes them. **Move up** and **Move down** change the order (and so the count of each rule, never the analysed sample); **Remove** deletes a rule. The tool refuses a condition that would name a person (a value of an identifier, an e-mail address, a free text): a rule describes whom to exclude, never a list of people.
2. **The flow diagram** shows the **Answers received**, the **Excluded** (rule by rule) and the **Analysed sample**, with the picture that will be Figure 1 of the document.
3. **The quality signals of the administration** show how many people a rule would touch, without ever applying it: the durations (with the threshold you type), the grids in a straight line and the duplicates. **Make it a rule** fills the **Add a rule** form, above; you still write the reason and add the rule.
4. **The description of the sample**: choose the variables that describe the participants (for example age and gender).
5. **The preview of the paragraphs** shows the three paragraphs of the Method, **Participants**, **Measures** and **Analyses**, as they will be in the document. What the codebook does not say becomes a hole highlighted in yellow, "[to complete: name and source of the instrument of group G1]": the tool never guesses an instrument's name or a source. Fill them in Word, or in the project (**Groups** page, name of the instrument with its source) so that they are filled in every document.

**The Method's figures are kept by the notebook**, like those of an analysis. When a rule changes, the **Notebook** page shows "M. Method — changed, to confirm" and what changed; a new rule also changes the analyses, recomputed on the new sample. **Confirm everything** adopts all the new computations at once; until then, the document is not produced.

**Everywhere the same way.** The rules apply before each analysis of the tool, in the SPSS and R preparation script (a variable `ddict_exclusion`: 0 for a person kept, otherwise the rank of the rule that excludes them) and in the R master script. The documented copy of the database (section 9) keeps no trace of them: it stays identical to the original. The reliability of the scores (Cronbach's alpha and its 95 % confidence interval) is computed again on the analysed sample.

On the command line: `ddict exclusions list`, `add` (`--condition age lt 18`, `--score G1 lt 10`, `--completeness G1 5`, `--duration start end 180 --source "…"`, `--straightlining G2`, `--duplicates email`, always with `--reason "…"`), `remove E2`, `move E3 1` and `signals` (`--start`, `--end`, `--min-duration`, `--duplicates`); `ddict notebook sample sleep-study.dd.json age gender` chooses the sample's variables. The page and the commands write the same rules.

## 16. The analysis plan, the preregistration and the article

A confirmatory study writes its hypotheses before analysing, and its article then says what was planned and what changed. The **Plan** page (before **Analyses**) keeps this plan: the team's hypotheses, each tied to an analysis of the catalogue, the general rules, the freezing and the amendments. It uses no AI, and nothing is sent outside your computer. The details are in [`../plan-analyse-article.md`](../plan-analyse-article.md) (in French).

1. **The general rules**, saved at once:
   - the **α level**, typed by the team: the page never offers one by default;
   - the **Correction for multiple comparisons** (Holm by default, Bonferroni or none), applied within each family of hypotheses;
   - the **Sample size rationale**, as text;
   - the **Origin of the data** (primary or secondary) and their **State when the plan was written** (before their creation, before any observation, before access, before analysis, after an analysis). This is the team's declaration: the article writes it "according to the team".
2. **Add a hypothesis**: its statement, as the team writes it, the analysis and its variables role by role, as on the **Analyses** page (section 13), then:
   - the **Tested effect**: for a regression, the whole model or a predictor; for a correlation of more than two variables, the pair;
   - the **Expected direction** (the first or the second group higher, in the order of the codes; positive or negative). For a t test, it makes the test one-sided;
   - the **Kind**: confirmatory (by default) or exploratory;
   - the **Family (correction)**, for example F1: the hypotheses of the same family have their *p* values adjusted together.

   The conditions of the analysis are checked on the database, as on the **Analyses** page. **Move up** and **Move down** set the article's order; **Remove** deletes a hypothesis (its number does not come back).
3. **Freeze the plan.** The plan receives its date and fingerprint, and each hypothesis becomes an analysis of the notebook (section 14). The list **To freeze the plan** ticks what is ready: at least one hypothesis, the α level, the origin and state of the data, the database open, each hypothesis computable; the button stays greyed out while a box is missing. A plan just begun is not a fault: nothing there is in red. Afterwards, **every change needs a reason**, typed at the top of the page, and becomes an **amendment**, kept forever: the article cites it with its date and reason. The original analysis stays in the notebook, left out, and the new one takes its place. The **Notebook** page gives the state of each analysis against the plan: "planned (H1)", "replaced by the amendment of …", "variant of H1", "exploratory".
4. **The preregistration.** **Write the preregistration next to the project** gives `sleep-study-preenregistrement.docx` and `.md`. The template follows the origin of the data: OSF Prereg for primary data, van den Akker et al. (2021) for secondary data. It is written from the plan and the codebook only, **never from the database**: no count, no result. What the tool cannot know (what the team already knew of the data, where it is registered) stays a highlighted hole, to complete in Word. The tool registers nothing and never says the study was preregistered.
5. **The article draft** (**Notebook** page, section 14) follows the plan once it is frozen:
   - the Introduction states the hypotheses, and the Method gains an **Analysis plan** paragraph (declared origin and state, date of the freezing, α, correction and families, one-sided tests, amendments);
   - the Results follow the hypotheses, with, for a hypothesis of a family, the adjusted *p* next to the raw *p*; then the "Exploratory analysis";
   - the Discussion recalls each hypothesis, the expected and the observed direction, then leaves a hole for its interpretation.

   **The tool never writes that a hypothesis is "supported" or "rejected"**, nor "significant": it describes what was observed, and the judgement belongs to the authors. The title, authors, abstract, background, limitations and conclusion stay holes.

On the command line: `ddict plan list`, `add` (the variables as for `ddict notebook add`, and `--pair A B`, `--predictor X` or `--model`, `--direction positive`, `--family F1`, `--exploratory`), `modify H2 --method spearman --reason "…"` (or `amend`), `remove H2`, `move H3 1`, `rules --alpha 0.05 --correction holm --origin primary --status before-analysis --sample-size "…"`, `freeze`, `clear --confirm` and `preregistration`; then `ddict paper`. The page and the commands write the same plan, the same preregistration and the same article.

A trial on an open database and its published article is described (in French) in [`../essais/2026-10-18-essai-plan-article-amatus.md`](../essais/2026-10-18-essai-plan-article-amatus.md): the tool's figures there are those of the article and of R.

## 17. The widened catalogue and the subgroup

Since 0.14, the **Analyses** page, the **Plan** page and the notebook offer five more analyses, written and checked in advance like the first six (details: [`catalogue-elargi.md`](../catalogue-elargi.md), in French):

- **Paired t test**: compare two measures of the same person (before and after a programme). Method: paired t test or Wilcoxon signed-rank test. The expected direction names the two measures.
- **Repeated-measures ANOVA**: three or more measures of the same person, with the Greenhouse-Geisser correction when sphericity is doubtful; pairwise comparisons corrected by Holm, if wanted.
- **Logistic regression**: predict an outcome with two categories (dropped out: yes or no); the table gives the odds ratios, the figure shows them on a logarithmic scale around 1. **Predicted category** says which of the two is the outcome studied.
- **Partial correlation**: the link between two variables when one or more covariates are held constant; the table also gives the simple correlation.
- **Moderation**: a link that depends on a third variable; the interaction, with its simple slopes at −1 SD, the mean and +1 SD. Continuous variables are centred by default.

**The subgroup.** Each analysis, notebook entry and hypothesis can be about part of the people only: open **Subgroup (optional)**, choose the variable, the condition (=, ≠, among; for a numeric variable also <, ≤, >, ≥) and the value, by its label (“Female”). The subgroup applies after the exclusion rules; the result sentence starts with “Subgroup (sex = Female).”, the note of each table and figure says it, so do the Method and the preregistration, and the R script makes the same selection. People outside the subgroup count among those left out. A subgroup is described by a coded variable, never by an identifier, free text or a date.

On the command line, the same analyses are called `paired`, `rm_anova`, `logistic`, `partial` and `moderation`, and the subgroup is written `--subgroup sex eq 1` (or `sex in 1 2`, `age ge 40`) with `ddict analyse`, `ddict notebook add` and `ddict plan add`; `ddict plan modify H1 --subgroup aucun` removes it. For example:

```
ddict analyse etude-suivi.dd.json paired --first anxiete_t1 --second anxiete_t2 --subgroup sexe eq 1
ddict analyse etude-suivi.dd.json rm_anova --measures anxiete_t1 anxiete_t2 anxiete_t3
ddict analyse etude-suivi.dd.json logistic --outcome abandon --predictors motivation
ddict analyse etude-suivi.dd.json partial --variables stress sommeil --covariates charge
ddict analyse etude-suivi.dd.json moderation --outcome epuisement --focal charge --moderator soutien
```

The fictional database `etude-suivi.sav` (folder `exemples\bases-fictives`) is there to try them. The advising AI knows these analyses too: on six objectives written for this database, a small model installed on the computer (trial of version 0.14) proposed the right analysis first four times, and among its proposals five times; it sometimes added covariates the objective does not ask for. The subgroup is not part of its proposals: it is yours to choose.

A second trial on the open AMATUS database is described in [`essais/2026-10-18-essai-v014-amatus.md`](../essais/2026-10-18-essai-v014-amatus.md) (in French): the subgroups of the published article, chosen in the tool on the whole database, give its figures again, and R gives the tool's.

## 18. Recode, verify the figures, prepare the deposit

Since 0.15, three tools for the end of the work, without AI; nothing is sent outside your computer. The details are in [`../verification-depot.md`](../verification-depot.md) (in French).

**Recode a variable.** A new variable, derived from a single other one, to regroup categories (“Female”; “Male or other identity”) or cut a number into classes (“under 30”, “30 to under 45”, “45 and over”). The project keeps the rule and its reason, never the column: it is computed in memory after the scores and before the exclusion rules, so an exclusion, a subgroup, an analysis or a hypothesis can use it.

1. Page **Variables**, the source variable, box **Recode this variable** (regroup for a nominal or ordinal variable, cut for a scale or a score). An identifier, a free text or a date is not recoded.
2. To regroup: beside each value, the name of its new group, or **missing**. To cut: the cuts, increasing; a class goes from its cut included to the next one excluded; labels are proposed.
3. The name, the label and the **reason**; the **Preview** shows the count of each new category before saving. A value without a group refuses the recoding; an empty class or a category under 5 people gives a warning.
4. **Save the recoding.** The page **Groups** lists the recodings, with their rule and reason. A recoding used by an exclusion rule or a hypothesis cannot be removed; used by a hypothesis of a frozen plan, it no longer changes.

The recoding goes into the SPSS (`RECODE … INTO`) and R preparation scripts, the R master script, the codebook (sheet “Recodages”) and the Method (“The variable age_classe was derived from age: …”). On the command line: `ddict recode list`, `group` (`--group "2,3" "Male or other"`, `--missing`), `cut` (`--cuts 30 45`) and `remove`.

**Verify the figures of a manuscript.** Once the draft is edited in Word, or for an article written without the tool: page **Verify** (after **Notebook**), choose the `.docx` manuscript, **Verify**. The tool finds the statistics written in the APA style, in French or in English, and compares each with what it writes itself, recomputed on the database, section by section. Each value is classed:

- **agrees**: within half a unit of its last decimal; “*p* < .001” agrees with a *p* under .001;
- **differs**, with the value the tool writes;
- **sign reversed** (for *t*, *z* and *d*, whose sign depends on the order of the groups);
- **no origin**: no analysis of the notebook nor the Method gives this figure;
- **not recognised**: a writing the tool cannot read without guessing.

It gives a report (Markdown and Excel) and a copy `-verifie.docx` with a Word comment on each value that does not agree; your manuscript is never changed. It reads neither figures, footnotes nor percentages: the report says so at the top. Without the database, it compares with the values kept in the notebook. On the command line: `ddict verify study.dd.json manuscript.docx`.

**Prepare the reproduction package.** Page **Notebook**, **Prepare the reproduction package**: `<project>-depot.zip`, ready for OSF or Borealis, with the codebook, the preregistration, the notebook, the command files, the preparation script, the R master script, a `README.md` to complete (title, reference, data access, licence, authors) and the fingerprints of the files. **The database is never in it**: you deposit it, or not, according to your ethics approval. Put in the package's `scripts/` folder, it lets the R master script run all the analyses again. On the command line: `ddict deposit study.dd.json`.

A trial on the open AMATUS database and its published article is described (in French) in [`../essais/2026-10-18-essai-v015-amatus.md`](../essais/2026-10-18-essai-v015-amatus.md).

## 19. Follow several projects

Since 0.17, the home page begins with the table **My projects**: one row per followed project, the latest changed at the top. Nothing is sent outside your computer; the table reads the project files and the notebooks, never the databases.

| Column | What it says |
|---|---|
| Project | The project file's name, and its folder in small print |
| Phase | **Document** while nothing is analysed; **Analyse** as soon as the plan has a hypothesis or the notebook an analysis; **Write** as soon as the article's draft exists |
| Codebook | The same percentage as the open project's bar |
| Waiting | The number of tasks, and the first one ("4 · Acronyms to accept: 3"); "—" when nothing waits |
| Plan | "in progress (2 hypotheses)", "frozen on 2026-10-18", "frozen, 1 amendment" |
| Notebook | The analyses retained, those **to confirm** (a new calculation waits for your agreement) and those **to recompute** (a decision changed since they were computed: open the notebook to find out whether their figures change) |
| Database | "found" when a file of that name is next to the project; the tool checks it is the right one when the project is opened |
| Changed | The last change of the project or of its notebook |

**Open a project**: a click on its name opens it where something waits ("Acronyms to accept" opens the glossary), otherwise on the first page of its phase.

**Which projects are followed.** A project created from the home page, or by `ddict profile`, is followed at once; the trial project on the fictional database is not. To follow another one: **Follow this project** next to a recent project, or in the sidebar of the open project. To find several at once: **Look for projects in a folder…**, under the table, then choose the folder. The tool looks in that folder and its subfolders, 4 levels down, without opening any file (a OneDrive file "available online only" is not downloaded); it passes over hidden and system folders. Nothing is checked at first: check those you want to follow, then **Follow these N projects**.

**The ⋮ menu** at the end of a row: **Stop following** takes the project off the table; its file is never touched, nor its notebook. A project moved or renamed stays in the table, greyed, "Not found": **Find it again…** opens the "Open" window, where you show where it is now. The old file being gone, the tool cannot check it is the same project: it says which database the chosen project was made from, for you to judge.

**The same project open twice**: in two tabs, by two people on a shared folder, or by the interface and the command line. The tool never overwrites a decision taken elsewhere. If the project changed since you opened it, a banner says so, and your last decision is not saved; it is recalled (the page, the button, what you had typed). **Reload the project** reads the project as it is now; your decision stays shown, "Decision to make again", for you to make again if it still holds. Nothing is merged for you. The notebook is protected the same way.

On the command line: `ddict projects list` prints the table; `ddict projects follow study.dd.json` and `ddict projects remove study.dd.json`; `ddict projects search "C:\Users\you\Documents\Studies"` lists the projects found, and `--follow` adds them all.

## 20. Design a questionnaire, before the collection

For a study without data yet: the questionnaire is built in the tool, and the data dictionary exists **before the collection**. The Word for the ethics committee and the file for LimeSurvey are drawn from it **by computation**, never by the AI; when the responses arrive, each variable finds again what the team decided.

**Create the project.** On the home page, **Design a questionnaire**: the folder, the questionnaire's name and the study's language. The project opens on the phase **Design**, at the top of the menu: Questionnaire, Review, Publish.

**Questionnaire.** The sections and their questions, one row each, with Move up, Move down, Change and Remove. A question opens in a form: its kind (single choice, checkbox, grid, open, displayed text), its text, its instruction, "required", its choices or items and their **codes**, where its text comes from (typed by the team, or taken from a source, with the page), and the **question's code**, which names its variables (`sommeil_SQ001`). One **Save** per question; what is typed and not saved is kept as a draft.

**Review.** The points to look at, all computed: choices without a code, a duplicate code, a question's code not decided, categories that overlap ("18-25", "25 to 35"), a required question without "Prefer not to answer", a grid without instruction, a grid taken from a source without an instrument name, names in conflict. Each one leads to where it is settled; **Keep as it is** closes it while the question does not change.

**Publish.**

- **The Word**, in two versions: **for the ethics committee** (what a person answering will read, without names, codes or provenance) and **working** (with each question's codes, kind and LimeSurvey type, its variables, the provenance, the groups and the review points). The footer gives the version, the date of the last change and the questionnaire's fingerprint: the same questionnaire gives the same file.
- **The file for LimeSurvey** (`… - LimeSurvey.txt`, the tab-separated structure), checked on LimeSurvey Cloud 7.6. Before giving it, the tool says what it holds and what stays in the tool (provenance, reversed items, scoring, instruments). What LimeSurvey would refuse (a code not starting with a letter, a brace, a duplicate code) blocks the file and leads to the review.
- **Import into LimeSurvey**, step by step (folded in the page): in the list of surveys, the **+** menu, then **Import**; choose the file; **Import survey**; the import report should announce the number of groups, questions, subquestions and answers the page gives, without warning. Then read LimeSurvey's preview: only LimeSurvey shows what the people answering will see. No branching, random order or quota: they are set in LimeSurvey.
- **Mark as sent** (to the ethics committee, or published in LimeSurvey, with the date and an optional note): the project keeps a copy. Changing it afterwards stays allowed; the page says at the top that LimeSurvey or the committee is to be updated, and each version sent shows what changed since.
- **Compare LimeSurvey's re-export**: export the structure again from LimeSurvey (`.lss` or `.txt`) and give it: the tool compares it with the project by the codes of the questions (question added, removed, same text under another code, text changed word by word, choice recoded…). Nothing changes without you: **Take into the project** or **Keep the project** (LimeSurvey is then to be corrected).
- **The preview**: the questionnaire roughly as a person answering will see it; **Show the names** adds the codes.

**The database has arrived.** On the page **Database**, which was waiting: choose the export of the responses (LimeSurvey's `.sav` preferably), then **Read the database**. Each variable finds its planned variable by its name and takes again your decisions (question, new name, label, description, unit, measure level, labels, privacy class). The **conformity report** says what differs from the questionnaire: planned variables absent, variables not planned, codes observed outside the planned codes (the codes only, never their counts), different labels, a different type; it is on the page "Database" and written next to the project (`… -conformite.md`). The project is then documented like any other.

On the command line: `ddict questionnaire create "C:\Users\you\Documents\Studies" --name "Sleep study"` creates the project; `ddict questionnaire word <project>` writes both Words next to the project; `ddict questionnaire limesurvey <project>` writes the file for LimeSurvey and prints the import steps; `ddict profile <database> --project <project>` reads the database that arrives.

## Update or uninstall

- **Update**: download and extract the new archive, then double-click its `installer.bat`. If the tool is open, the installer offers to close it (answer `y`): it cannot replace it while it runs. Your project files are kept. A project opened with version 0.8 no longer opens with an older version (its format changed); the reverse works. Likewise, a project saved by version 0.18 (which notes in it whether it may be sent to the AI) no longer opens with 0.17.
- **Uninstall**: double-click `desinstaller.bat`, in the tool's folder. It removes the tool and its icons, without touching your projects, codebooks or data; it asks before clearing the lists of recent and followed projects with the AI settings, then, separately, the API key of Windows' Credential Manager. uv stays installed.

## For those who prefer the command line

Every step also exists as a command, in PowerShell (`ddict --help` lists them). The commands have English names next to their French ones:

```
ddict                                         # open the interface on the home page
ddict profile sleep-study.sav                 # read the database, create the project file
ddict questionnaire sleep-study.dd.json questionnaire-sleep.pdf
ddict ai key                                  # type the API key (nothing shows), once
ddict ai test --model claude-haiku-5-5        # the key and the connection, nothing of a project sent
ddict ai allow sleep-study.dd.json            # this project allows its metadata to be sent
ddict link sleep-study.dd.json --ai
ddict enrich sleep-study.dd.json --model claude-haiku-5-5
ddict review sleep-study.dd.json              # open a project directly
ddict export sleep-study.dd.json --language en          # Excel codebook and report
ddict export sleep-study.dd.json --syntax     # and the SPSS and R command files
ddict export sleep-study.dd.json --context    # and the analysis context (--with-statistics)
ddict document sleep-study.dd.json            # documented copy of the database (.sav)
ddict rename study-t2.dd.json --suffix _t2 --reference study-t1.dd.json   # names
ddict analyse sleep-study.dd.json t_test --outcome sleep_total --group gender --levels 1,2
ddict notebook add sleep-study.dd.json correlation --variables sleep_hours n_awakenings
ddict notebook list sleep-study.dd.json      # the notebook, recomputed
ddict exclusions add sleep-study.dd.json --condition age lt 18 --reason "Under 18"
ddict exclusions list sleep-study.dd.json    # the rules and the flow diagram
ddict notebook sample sleep-study.dd.json age gender   # the sample's variables
ddict plan add sleep-study.dd.json t_test --statement "Women sleep better." --outcome sleep_total --group gender --levels 1,2 --direction first
ddict plan rules sleep-study.dd.json --alpha 0.05 --origin primary --status before-analysis
ddict plan freeze sleep-study.dd.json        # the plan finalised; afterwards, --reason for each change
ddict plan preregistration sleep-study.dd.json   # the preregistration (Word and Markdown)
ddict paper sleep-study.dd.json              # the article draft and the R master script
ddict recode cut sleep-study.dd.json age --name age_class --cuts 30 45 --reason "…"
ddict verify sleep-study.dd.json manuscript.docx   # the figures of a Word manuscript
ddict deposit sleep-study.dd.json            # the reproduction package, without the database
ddict projects list                          # the followed projects, as the home page's table
ddict projects search "C:\Users\you\Documents\Studies" --follow   # follow those of a folder
ddict advise sleep-study.dd.json "Compare the sleep of women and men."
ddict evaluate --model claude-haiku-5-5       # model bench (billed)
```

The service, the address and the model come from the settings of the **AI** page, unless `--protocol`, `--address` or `--model` give them; the key is never given as an argument (PowerShell keeps the history of commands), only through `ddict ai key`. `ddict ai forget` erases it; `ddict ai deny` withdraws a project's permission. `--preview` (with `link`, `enrich`, `rename` or `advise`) writes the messages that would be sent into the `sleep-study.dd-envois\apercu` folder, without sending anything, even for a project that does not allow it. `ddict export --no-text G2` leaves out the question text of a group for one export. `ddict analyse` writes the report, the tables and the R script next to the project (analyses: `table1`, `t_test`, `paired`, `rm_anova`, `anova`, `chi_square`, `correlation`, `partial`, `regression`, `logistic`, `moderation`; `--subgroup` for part of the people); `ddict advise` shows the model's proposals without computing anything (`--preview` to see the message only).

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
| AI buttons greyed out: "Sending to the AI is not allowed for this project" | Tick **Allow the metadata of this project to be sent to the AI** in the sidebar (section 6), if your team allows it. |
| "The key is refused (or missing)" | Record the key again on the **AI** page; check in Anthropic's console that it was not disabled and that the credit or the spending limit is not used up. |
| "Cannot reach …" when testing the connection | Check the Internet connection; on an institution's network, a firewall may block the service: ask your IT support. |
| "Too many requests" or "service overloaded" | Wait a few minutes, then run it again: the finished blocks are kept. |
| A grid of the questionnaire is "to check" | Its column headings run together in the PDF: the tool then proposes no value labels for its variables. A `.txt` copied from Word avoids the problem. |
| "Cannot write the files" when exporting | The codebook is probably open in Excel: close it, then try again. |
| Documented copy: "The database … cannot be found next to the project" | Put the database in the project's folder, or **Choose the database…**. |
| Documented copy: "… is no longer the file the project comes from" | The database changed since the project was created (new export, corrected data). Create a new project from the current database. |
| "The plan is finalised: give the reason for this change." | After the freezing, each change is an amendment: type its reason at the top of the **Plan** page (or `--reason "…"`), then try again. |
| R: "there is no package called 'haven'" | In R, once: `install.packages("haven")`. |
| "This project was changed elsewhere since you opened it" | Another tab, another person or a command saved the project meanwhile. **Reload the project**, then make your decision again if it still holds (section 19). On the command line: run the command again. |
| "The file is busy, perhaps being synced by OneDrive" | Nothing is saved and the project is intact: wait a moment, then click again. |
| "A save was interrupted… the file ….tmp was left" | The open project is the last one saved in full; the `.tmp` file can be deleted. The tool never deletes it itself. |
| A project of the table is "Not found" | It was moved or renamed: **⋮** menu of its row, **Find it again…** (section 19). |
| The tool seems frozen | Close its window, then double-click the icon again. The decisions already taken are saved. |

For any other difficulty, write down what you did and the message you got, and pass them on to the person who gave you the tool.
