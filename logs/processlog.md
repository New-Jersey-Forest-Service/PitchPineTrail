# Process Log

## Date

2026-06-18

## Repo Context

This repository is `PitchPineTrail`, a retro-style forest management game. The existing desktop version lives under `src/` and is implemented in Python with tkinter, pygame, Pillow, pandas, and matplotlib.

Important context files:

- `context/LocalAnaconda.md` documents this computer's preferred Python interpreter:
  `C:\Users\wzipse\AppData\Local\anaconda3\python.exe`
- `context/webplan.md` describes the intended static web port.
- `src/game_logic.py` is the source of truth for simulation behavior.
- `src/gui.py` is the source of truth for screen flow, animations, sounds, overlays, analysis lab behavior, and certificate/export behavior.

Current git note: at the time this log was written, both `context/` and `web/` appeared as untracked directories in `git status --short`.

## User Request

The user asked to execute the web port plan from `context/webplan.md`, after first becoming familiar with the repo and local Anaconda guidance.

## Work Completed

Created the first static web-port implementation under `web/`.

Added:

- `web/index.html`
  - Static app shell with `#game-root`.
  - Loads `css/style.css`.
  - Loads Chart.js and html2canvas from CDN.
  - Loads `js/screens.js` as an ES module.

- `web/css/style.css`
  - Fullscreen desktop-oriented layout.
  - Retro Courier styling.
  - Palette matching `context/webplan.md` and `src/gui.py`.
  - Styles for metrics, action buttons, overlays, analysis lab, chart overlays, certificate overlay, and survey overlay.

- `web/js/game.js`
  - ES module port of `src/game_logic.py`.
  - Exports `ACTIONS` and `Game`.
  - Preserves current Python source details that are more specific than `webplan.md`, including:
    - recruitment scheduling,
    - achievement flags/history,
    - hurricane random offset within the decade,
    - non-losing wildfire handling inside `updateStand`,
    - catastrophic wildfire and SPB random event logic,
    - decadal data generation with `Start` row and off-decade event snapshots.

- `web/js/sounds.js`
  - Browser `Audio` wrappers for existing WAV files.
  - Supports looping ambient sounds and one-shot effects.

- `web/js/charts.js`
  - Analysis data table rendering.
  - Chart.js plot rendering for numeric and risk variables.
  - CSV export including actions and achievements.

- `web/js/screens.js`
  - Main browser screen router.
  - Intro and zoom flow.
  - Main game action flow.
  - Management animations.
  - Loss screens.
  - Achievement queue/screens.
  - Hurricane and non-losing wildfire screens.
  - Win screen with dynamic medal background filename.
  - Field guide, definitions, hints, exit survey overlay.
  - Certificate overlay using html2canvas.
  - Analysis lab screen with table, plots, CSV export, definitions navigation, and return flow.

No desktop Python files under `src/` were intentionally edited.

## Local Verification Performed

The machine did not have `node` on PATH, and browser automation packages were not installed:

- `node --check ...` failed because `node` was not recognized.
- Python checks showed Playwright, Selenium, js2py, quickjs, and dukpy were not installed.

Used the documented Anaconda interpreter:

```powershell
& 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' --version
```

This returned Python 3.13.9.

Started a repo-root static server:

```powershell
Start-Process -FilePath 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' -ArgumentList @('-m','http.server','8001') -WindowStyle Hidden
```

Verified these returned HTTP 200:

- `http://localhost:8001/web/`
- `http://localhost:8001/web/js/charts.js`
- `http://localhost:8001/src/assets/analyze.jpg`
- `http://localhost:8001/src/assets/Evenagestand.jpg`

Also ran a Python asset-reference check over `web/`; it reported:

```text
missing asset refs: 0
```

## Important Caveat

The web plan says the web app should reference shared assets via paths like `../src/assets/filename.jpg`. This works only when the repository root is served and the app is opened at `/web/`.

It does not work if the HTTP document root is the `web/` folder itself. For example, `python -m http.server --directory web` cannot serve `../src/assets/...`.

This has deployment implications:

- GitHub Pages configured with source folder `/web` will likely break shared asset paths.
- Safer options:
  - configure Pages/source so the repo root is served and users open `/PitchPineTrail/web/`,
  - duplicate/copy assets into `web/assets/`,
  - add a build/copy step,
  - or revise paths/deployment layout intentionally.

Downstream agents should resolve this deployment-path decision before polishing the web port.

## Recommended Next Steps

1. Open `http://localhost:8001/web/` in a browser and click through the app manually.
2. Check browser console for ES module/runtime errors.
3. Verify a complete 100-year game can be played.
4. Test high-risk flows:
   - low TPA loss,
   - catastrophic wildfire loss,
   - SPB loss,
   - hurricane screen,
   - non-losing wildfire screen,
   - all achievement popups,
   - win screen medal background selection,
   - analysis lab charts and CSV export,
   - certificate save.
5. Decide on GitHub Pages asset strategy.
6. Once browser-tested, consider adding a lightweight automated test harness for `web/js/game.js` parity against expected deterministic simulations.

## Known Limits Of Current Implementation

- Pixel-perfect tkinter parity has not been browser-verified yet.
- Runtime JavaScript has not been checked with Node or browser automation because the local tools were unavailable.
- CDN dependencies require network access in the browser:
  - Chart.js
  - html2canvas
- Browser audio autoplay behavior means sounds should begin only after user interaction; this was considered in the screen flow, but still needs manual browser testing.

## 2026-06-18 Update: Agent Instructions

Created root-level `AGENTS.md` with repo-specific operating instructions for downstream agents.

The instructions cover:

- required context files to read before editing,
- local Anaconda interpreter usage,
- web-port constraints,
- shared-asset/GitHub Pages caveat,
- local testing server workflow,
- requirement to ask the user before shutting down test servers at session end,
- requirement to append meaningful updates to `logs/processlog.md`,
- git/file safety guidance.

Files changed:

- `AGENTS.md`
- `logs/processlog.md`

## 2026-06-18 Update: GitHub Pages Site Instructions

Created `context/siteinstructions.md` with instructions for publishing the web port on GitHub Pages.

The instructions note a corrected deployment constraint from GitHub's current Pages documentation: branch-based publishing supports a selected branch root or `/docs`, not an arbitrary `/web` folder. Because the current web app references shared assets via `../src/assets/...`, the recommended current deployment is to publish from the repository root and open the game at `/PitchPineTrail/web/`.

Files changed:

- `context/siteinstructions.md`
- `logs/processlog.md`

Verification/context used:

- Official GitHub Pages docs for creating a Pages site.
- Official GitHub Pages docs for configuring a publishing source.

## 2026-06-18 Update: Local Test Server Started

Started a local repo-root HTTP server for testing the web game.

Command used:

```powershell
Start-Process -FilePath 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' -ArgumentList @('-m','http.server','8001') -WindowStyle Hidden
```

Working directory:

```text
C:\Users\wzipse\Documents\dev\projects\PitchPineTrail
```

Open the game at:

```text
http://localhost:8001/web/
```

Verification:

- `http://localhost:8001/web/` returned HTTP 200.

Server process:

- PID `29984`
- Command line: `"C:\Users\wzipse\AppData\Local\anaconda3\python.exe" -m http.server 8001`

Reminder: ask the user before shutting this server down at session end.

## 2026-06-18 Update: Local Test Server Stopped

Stopped the local repo-root HTTP server after the user asked to shut it down.

Stopped process:

- PID `29984`
- Port `8001`

Verification:

- `netstat -ano | Select-String ':8001'` returned no listeners.

## 2026-06-18 Update: User-Started 8001 Server Stopped

The user reported that their attempt to run the local server on port `8001` failed and asked to shut it down.

Stopped process:

- PID `24044`
- Command line observed before shutdown: `"C:\Users\wzipse\AppData\Local\anaconda3\python.exe" -m http.server 8001`

Verification:

- After stopping the process, `netstat -ano | Select-String ':8001'` showed no active listener.
- A temporary `TIME_WAIT` entry remained, which is expected after closing a TCP server.

## 2026-06-18 Update: Local Test Server Restarted

Started the repo-root HTTP server for web game testing after the user asked to start it again.

Command used:

```powershell
Start-Process -FilePath 'C:\Users\wzipse\AppData\Local\anaconda3\python.exe' -ArgumentList @('-m','http.server','8001') -WindowStyle Hidden
```

Working directory:

```text
C:\Users\wzipse\Documents\dev\projects\PitchPineTrail
```

Open the game at:

```text
http://localhost:8001/web/
```

Verification:

- `http://localhost:8001/web/` returned HTTP 200.

Server process:

- PID `24672`
- Command line: `"C:\Users\wzipse\AppData\Local\anaconda3\python.exe" -m http.server 8001`

Reminder: ask the user before shutting this server down at session end.
