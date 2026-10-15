# Installing and using the tool on Windows

This guide is for people who do not program. It goes from the installation to a complete codebook, made from the fictional database and its questionnaire that come with the tool. Everything is done by double-clicking and in your browser; there are no commands to type. Allow an hour, plus the download of the AI model if you choose to use it.

On a Mac: [`installation-macos.md`](installation-macos.md). En français : [`../installation-windows.md`](../installation-windows.md).

> **Trial version of the English.** The tool was written in French first; its English interface is new (version 0.5) and its translation has not yet been reviewed by a native English speaker. If a sentence is unclear or wrong, write it down and pass it on. The installer window speaks French only: this guide gives what it says.

## What you need

- Windows 10 or 11. No administrator rights needed.
- An Internet connection **during the installation only**. Afterwards, the tool no longer talks to the Internet: it reads your files and writes its results on your computer.
- For the AI, which is optional: about 5 GB of free space and 16 GB of memory (8 GB will do, more slowly). A graphics card speeds things up but is not needed; without one, a smaller model is advised (section 6).

## 1. Install

1. Download the tool's archive from the releases page of the project on GitHub: the **Source code (zip)** link, for example `dictionnaire-donnees-0.6.0.zip`.
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

Double-click the **Dictionnaire de données** icon. Your browser opens on the tool's **home page**, at an address that starts with `http://127.0.0.1`: it can be reached from your computer only.

A small black window, minimized in the taskbar, runs the tool. **To stop the tool, close that window.** Closing the browser tab does not stop it: another double-click on the icon simply opens the tab again.

**Language**: at the top of the home page, **Français · English** chooses the language of the interface. The choice applies at once and is remembered on your computer. Choose **English**.

## 3. A first codebook, from the fictional database

The fictional database is a small invented study of sleep (200 fictional participants), with its questionnaire. It lets you try the tool without any real data. It exists in French and in English; this guide uses the English version.

1. On the home page, under **New project**, click **Choose a database…**. The Windows "Open" window appears (if you do not see it, look behind the browser). Go to the tool's folder, then `exemples\bases-fictives`, and choose `sleep-study.sav`.
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

## 8. Export

**Export** page:

- **Final version**: only what comes from the file, from computation, or from your decisions. **Working version**: with the pending proposals, marked as such.
- **Groups whose question text is not reproduced**: by default, those you checked in "Groups".
- **Codebook language**: French or English, by default that of the interface. It applies to the headings, the notes, the provenance, the report and the comments of the command files; what the team wrote (labels, descriptions, question text) is never translated.
- **Write the codebook and the report** (next to the project), or **Download** (to your downloads folder).

The codebook holds the labels, the text of the linked questions, the glossary ("Glossary" sheet), the accepted value labels and the provenance of every value. Counts below 5 are masked in it.

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

**The documented copy, if you want a ready-to-use file.** **Write the documented copy** writes next to the database `sleep-study-documente.sav`, in SPSS format, with your decisions. It also works from a CSV, Stata, SAS or Excel database. Before announcing it, the tool reads it back and compares it with the original cell by cell; at the slightest difference, it deletes it and tells you. Your original file is never changed, and an existing copy is replaced only if you tick the box. The database must be next to the project; otherwise, **Choose the database…**. The copy holds the participants' data: store it like the original.

## 10. With your own data

It works the same with your file: SPSS (`.sav`), CSV (including those of Excel in French, with semicolons and decimal commas), Stata (`.dta`), SAS (`.sas7bdat`) or Excel (`.xlsx`: the first sheet, with the names of the variables in the first row). And with your questionnaire, as PDF or text, in French or in English: check on the **Database** page that the language of the study is the right one.

**The format that gives the best results: `.sav`.** An SPSS file holds what other formats leave the tool to guess: the value labels ("1 = Never"), the declared missing-value codes and the level of measurement. If your survey platform (SurveyMonkey, Qualtrics, LimeSurvey…) or your software can export to `.sav`, choose that format, even if you do not use SPSS: the tool reads it without it. With another format everything works, but check the proposed missing codes and value labels more carefully. A platform's Excel export remains useful next to the `.sav`: choose it as the questionnaire, on the **Questionnaire** page, if you have no PDF.

- Work in a folder meant for this data, following the rules of your team and of your research ethics board. The project file, the codebooks and the `.dd-envois` folder (what was sent to the model) stay next to the data.
- The tool never changes your data file.
- Variables that look like identifiers, free text or dates of birth are found automatically: only their metadata is used, and counts below 5 are masked.
- On a large database, the links proposed by the AI are often right, but not always: questions repeated word for word ("How often does this person support you?", once per person) are the hardest case. Check them before the labels.
- The list of recent projects is kept on your computer (folder `%APPDATA%\ddict`) and holds only file paths; **Clear the list**, on the home page, empties it.

## Update or uninstall

- **Update**: download and extract the new archive, then double-click its `installer.bat`. If the tool is open, the installer offers to close it (answer `y`): it cannot replace it while it runs. Your project files are kept.
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
ddict document sleep-study.dd.json            # documented copy of the database (.sav)
ddict evaluate --model qwen2.5:7b-instruct-q4_K_M       # model bench
```

`--preview` (with `link` or `enrich`, without `--model`) writes the messages that would be sent into the `sleep-study.dd-envois\apercu` folder, without sending anything. `ddict export --no-text G2` leaves out the question text of a group for one export.

## If something goes wrong

| What happens | What to do |
|---|---|
| "Windows protected your PC" when double-clicking `installer.bat` | **More info**, then **Run anyway** (section 1). |
| `installer.bat` stops on a red message | Check the Internet connection, then run it again. If the message persists, write it down and pass it on. Some institutional computers forbid scripts: ask your IT support. |
| "Ce dossier ne contient pas l'outil" (this folder does not contain the tool) | `installer.bat` was copied out of the archive: run the one in the extracted tool's folder (section 1, step 2). |
| "L'outil est encore ouvert" (the tool is still open) | Close the tool's small black window, then run the installer again. |
| The "Open" window does not appear | It may be behind the browser: look in the taskbar. Otherwise, paste the file's path in the field under the button (right-click the file in File Explorer, **Copy as path**). |
| The browser does not open when double-clicking the icon | Open it yourself at `http://127.0.0.1:8501`. |
| "A project already exists for this database" | The tool does not overwrite your work: **Open the existing project**, or **Replace the project** if you really want to start over (its decisions will be lost). |
| Local AI page: "Is Ollama running?" | Start Ollama from the Start menu, wait for its icon next to the clock, then **Check again**. |
| Local AI page: no model installed | Run `installer.bat` again and answer `y` to download the model, or follow the page's instructions. |
| A grid of the questionnaire is "to check" | Its column headings run together in the PDF: the tool then proposes no value labels for its variables. A `.txt` copied from Word avoids the problem. |
| "Cannot write the files" when exporting | The codebook is probably open in Excel: close it, then try again. |
| Documented copy: "The database … cannot be found next to the project" | Put the database in the project's folder, or **Choose the database…**. |
| Documented copy: "… is no longer the file the project comes from" | The database changed since the project was created (new export, corrected data). Create a new project from the current database. |
| R: "there is no package called 'haven'" | In R, once: `install.packages("haven")`. |
| The tool seems frozen | Close the small black window in the taskbar, then double-click the icon again. The decisions already taken are saved. |

For any other difficulty, write down what you did and the message you got, and pass them on to the person who gave you the tool.
