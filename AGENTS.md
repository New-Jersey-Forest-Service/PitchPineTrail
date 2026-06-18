# Agent Instructions

These instructions apply to agents working in this repository.

## Start Here

Before making changes, read:

- `README.md` for the project overview.
- `context/webplan.md` for the intended browser-port architecture.
- `context/LocalAnaconda.md` for this computer's Python/Anaconda guidance.
- `logs/processlog.md` for the latest handoff notes from prior agents.

Treat `src/game_logic.py` as the source of truth for simulation behavior. Treat `src/gui.py` as the source of truth for the desktop screen flow, animations, sound behavior, overlays, analysis lab, certificate workflow, and CSV export behavior.

## Python On This Machine

Do not assume `python`, `py`, or `conda` are available from the default shell.

Use the documented local Anaconda interpreter when Python is needed:

```powershell
& 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' --version
```

For scripts or local static servers, prefer the absolute interpreter path:

```powershell
& 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' script.py
```

The matching conda executable is:

```powershell
C:\Users\wzipse\AppData\Local\anaconda3\Scripts\conda.exe
```

## Web Port Rules

The web port lives under `web/`. The existing desktop app lives under `src/`.

Preserve the desktop Python version unless the user explicitly asks to change it. For the browser port:

- Use a static vanilla JavaScript app.
- Do not add a backend.
- Do not add a framework or build step unless the user approves the change in direction.
- Share existing assets from `src/assets/` when possible.
- Keep behavior aligned with the current Python source, not only with the summary in `context/webplan.md`.
- Preserve the retro fullscreen visual style, Courier typography, and original game aesthetic.

Important deployment caveat: paths such as `../src/assets/filename.jpg` work when serving the repository root and opening `/web/`. They do not work when serving `web/` as the HTTP document root. Resolve the GitHub Pages asset strategy intentionally before final deployment.

## Testing And Local Servers

When testing the web app locally, prefer serving the repository root and opening the app at:

```text
http://localhost:8001/web/
```

Example:

```powershell
Start-Process -FilePath 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' -ArgumentList @('-m','http.server','8001') -WindowStyle Hidden
```

If you start any local web server for testing, track:

- the command used,
- the port,
- the process ID if available,
- what URL the user should open.

At the end of a session, ask the user whether they want you to shut down any local testing servers you started. Do not close servers silently unless the user has explicitly asked you to shut them down.

If the user asks you to shut down local servers, stop only the server processes you started or can clearly identify as repo testing servers.

## Process Log

Always append a concise handoff note to `logs/processlog.md` when you make a meaningful change, run important verification, discover a caveat, or leave work for a downstream agent.

Each process-log entry should include:

- date,
- summary of work,
- files changed,
- commands or tests run,
- verification results,
- known caveats or next steps.

Do not overwrite prior process-log content. Append new notes.

## Git And File Safety

- Check existing work before editing.
- Do not revert user changes unless the user explicitly asks.
- Keep changes scoped to the user request.
- Avoid unrelated refactors.
- Use the current branch unless the user asks for branch work.
- Be clear in the final response about what changed and what was not verified.

## Useful Current Files

- `web/index.html`: browser app shell.
- `web/css/style.css`: web app styling.
- `web/js/game.js`: JavaScript game logic port.
- `web/js/screens.js`: web screen router and turn flow.
- `web/js/sounds.js`: browser audio wrappers.
- `web/js/charts.js`: analysis lab charts and CSV export.
- `logs/processlog.md`: running handoff log.
