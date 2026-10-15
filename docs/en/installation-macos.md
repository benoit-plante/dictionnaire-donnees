# Installing and using the tool on a Mac

This guide is for people who do not program. It covers what is specific to the Mac: the installation, opening and stopping the tool, updating and common problems. Once the tool is open, everything happens in your browser, exactly as on Windows: the rest is in the [Windows guide](installation-windows.md), from its section 3.

En français : [`../installation-macos.md`](../installation-macos.md).

> **Trial version on the Mac.** Installing on a Mac is new (version 0.5). It was checked on a GitHub Mac (macOS 26, Apple silicon), not yet by a person on their own Mac; the English translation has not yet been reviewed by a native speaker either. If something does not happen as described here, write it down and pass it on. The installer window speaks French only: this guide gives what it says.

## What you need

- macOS 13 (Ventura) or later, on an Apple silicon (M1 and later) or Intel Mac. No administrator rights needed.
- An Internet connection **during the installation only**. Afterwards, the tool no longer talks to the Internet.
- For the AI, which is optional: about 5 GB of free space and 16 GB of memory (8 GB will do with a smaller model). On an Apple silicon Mac, the model runs on the chip, without a separate graphics card.

## 1. Install

1. Download the tool's archive from the releases page of the project on GitHub: the **Source code (zip)** link, for example `dictionnaire-donnees-0.6.0.zip`.
2. In the Finder, double-click the downloaded file: macOS extracts it next to it. Open the folder you get: it is **the tool's folder**, with `installer.command`, `docs` and `exemples`.
3. Double-click **`installer.command`**. The first time, macOS refuses to open it, with a message such as "Apple could not verify “installer.command” is free of malware" or "from an unidentified developer". That is normal: the message appears for any downloaded script that is not signed by a paying publisher; the installer is a plain text file, readable in any editor.
   - Click **Done** (or **OK**), then open **System Settings > Privacy & Security**. Further down, a message mentions `installer.command`: click **Open Anyway**, confirm with your password or Touch ID, then **Open**.
   - On an older macOS (before 15), you can also **Control-click** `installer.command`, then **Open**, and **Open** again.
4. A **Terminal** window opens and goes through four steps (in French): uv (the Python manager, installed in your user folder), the tool (a minute or two the first time), the icons ("Les icônes"), then the local AI ("IA locale").
5. At the AI step, answer `y` (yes) or `n` (no), then Return — the French `o`/`n` works too:
   - if Ollama is not installed, the installer offers to open its download page; install Ollama for macOS, open it once, then run `installer.command` again;
   - if Ollama is installed but not the recommended model, it offers to download it ("Le télécharger maintenant ?", about 4.7 GB, once).

   You can answer no and come back to it later: the tool works without AI.
6. "Installation terminée" (installation finished): press Return, then close the Terminal window. A **Dictionnaire de données** icon is on your desktop and in the **Applications** folder of your user folder.

## 2. Open and stop the tool

Double-click the **Dictionnaire de données** icon. A Terminal window opens and runs the tool, then your browser opens on the **home page**, at an address that starts with `http://127.0.0.1`: it can be reached from your computer only.

- **To stop the tool, close that Terminal window** (or press Control-C in it). If the Terminal asks whether to terminate the process, answer **Terminate**. Closing the browser tab does not stop it: another double-click on the icon simply opens the tab again.
- At the first start, macOS may ask whether the Terminal may access the **Documents** folder: the tool starts there, so that the "Open" window begins there. You can allow or refuse; the tool works either way.
- **Language**: at the top of the home page, **Français · English** chooses the language of the interface.

## 3. What comes next

Everything else happens in the browser, as on Windows: follow the [Windows guide](installation-windows.md) from section 3 (a first codebook with the fictional database, questionnaire, links, local AI, review, export, command files, your own data). A few differences:

- The "Open" window is the Mac's; the example files are in the tool's folder, then `exemples/bases-fictives`. If the window does not appear, it may be behind the browser.
- To paste a path in the field under the button: in the Finder, select the file, then **Option-Command-C** ("Copy as Pathname").
- **Open the folder** (Export page) opens the Finder.
- Ollama runs in the menu bar, at the top of the screen: if it does not answer, open it from the Applications folder.
- The list of recent projects and the chosen language are kept in `~/Library/Application Support/ddict`; **Clear the list**, on the home page, empties the list.

## Update or uninstall

- **Update**: download and extract the new archive, then double-click its `installer.command` (with, the first time, the visit to **Privacy & Security** of section 1). If the tool is open, the installer offers to close it (answer `y`): it cannot replace it while it runs. Your project files are kept.
- **Uninstall**: double-click `desinstaller.command`, in the tool's folder. It removes the tool and its icons, without touching your projects, codebooks or data; it asks before clearing the list of recent projects. uv and Ollama stay installed.

## For those who prefer the command line

After the installation, open a new Terminal window: the `ddict` command is available there, with the same commands as on Windows (`ddict --help` lists them; see the section of the same name in the Windows guide).

## If something goes wrong

| What happens | What to do |
|---|---|
| "Apple could not verify…" or "unidentified developer" when double-clicking `installer.command` | **System Settings > Privacy & Security > Open Anyway** (section 1). |
| "You do not have permission" or nothing happens on double-click | The archive lost the script's permission to run. In the Terminal, type `chmod +x ` (with the space), drag `installer.command` into the window, then Return; run it again. |
| The installer stops on a red message | Check the Internet connection, then run it again. If the message persists, write it down and pass it on. |
| "L'outil est encore ouvert" (the tool is still open) | Close the Terminal window where the tool runs, then run the installer again. |
| The browser does not open when double-clicking the icon | Open it yourself at `http://127.0.0.1:8501`. |
| Local AI page: "Is Ollama running?" | Open Ollama from the Applications folder, wait for its icon in the menu bar, then **Check again**. |
| The tool seems frozen | Close the tool's Terminal window, then double-click the icon again. The decisions already taken are saved. |

For the other messages (export, documented copy, R), see the table of the [Windows guide](installation-windows.md#if-something-goes-wrong). For any other difficulty, write down what you did and the message you got, and pass them on to the person who gave you the tool.
