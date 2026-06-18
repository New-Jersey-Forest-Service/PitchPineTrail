# Pitch Pine Trail — Web Port Plan
**Repository:** [New-Jersey-Forest-Service/PitchPineTrail](https://github.com/New-Jersey-Forest-Service/PitchPineTrail)  
**Authors:** William Zipse, Andrea Brown, Cara Escalona, Justin Gimmillaro  
**Target:** A browser-playable version of the game deployable via GitHub Pages, preserving the full aesthetic and gameplay of the desktop Python version.

---

## 1. Overview

Pitch Pine Trail is a retro-style, turn-based forest management simulation. The player makes decadal management decisions over 100 years for a pitch pine stand in the New Jersey Pinelands, earning wildlife achievements and avoiding loss conditions (catastrophic wildfire, SPB outbreak, low stocking).

The desktop version is written in Python using **tkinter** (UI), **pygame** (audio), **Pillow** (images), **pandas** (data table), and **matplotlib** (charts). The core game logic (`game_logic.py`) has no display dependencies and is a pure Python state machine — it ports directly to JavaScript.

The web version will be a **vanilla JS single-page app** served as a static site from GitHub Pages. No build step, no framework, no backend.

---

## 2. Repository Structure

Keep both versions in the same repository. Do **not** create a separate repo.

```
PitchPineTrail/
├── src/                          ← Desktop Python app (do not modify)
│   ├── main.py
│   ├── gui.py
│   ├── game_logic.py
│   └── assets/                   ← Single shared copy of all JPGs and WAVs
├── web/                          ← New: GitHub Pages source root
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── game.js               ← Port of game_logic.py (no DOM)
│       ├── screens.js            ← Screen router and all show_X_screen() equivalents
│       ├── sounds.js             ← Audio API wrappers
│       └── charts.js             ← Analysis lab charts (Chart.js)
├── requirements.txt
├── README.md
└── webplan.md                    ← This file
```

**Assets are shared.** The web app references all images and audio using relative paths: `../src/assets/filename.jpg`. Do not duplicate the assets folder.

**GitHub Pages configuration:** In repository Settings → Pages, set source to branch `main`, folder `/web`. The game will be live at `new-jersey-forest-service.github.io/PitchPineTrail`.

**Branch strategy:**
- `main` — canonical desktop version (stable)
- `dev` — desktop development branch (existing)
- `web-dev` — new branch for web port development; merge to `main` when stable

---

## 3. Visual Design & Aesthetic

The web version must preserve the desktop game's look and feel exactly.

**Color palette** (from `gui.py`):
- Background panels: `#1b2336` (dark navy)
- Accent / button text: `#05dd4c` (bright green)
- Secondary text: `#b5c3d8` (light blue-grey)
- White panels: `#FFFFFF`
- Action buttons: `#404d6d` background, `#05dd4c` text
- Risk colors: Low = `#228B22`, Moderate = `#FFA600`, High = `#B22222`
- Loss screen panels: `#05dd4c` buttons, `#1b2336` background

**Typography:** `Courier New`, bold, throughout. Font sizes scale with viewport — use `clamp()` in CSS or viewport-relative units. The desktop baseline is 1920×1080.

**Layout:** Every screen is fullscreen. A background JPG fills 100% of the viewport. UI elements are overlaid using `position: absolute`. The metrics panel is always anchored to the right side (approximately `right: 8%, top: 57%`). Action buttons are center-right (approximately `right: 12%, top: 26%`).

**No mobile layout required** at this time. Target desktop browsers only (min-width ~1024px).

---

## 4. Screen Inventory

Every screen follows the same pattern: fullscreen background JPG + right-side metrics panel (white box) + contextual buttons. The table below lists all screens, their background assets, and what triggers them.

| Screen | Background Asset(s) | Trigger |
|---|---|---|
| Intro | `introscreen.jpg` | App load |
| Zoom sequence | `zoom_1.jpg` → `zoom_10.jpg` (10 frames, 10ms each) | "Begin" button |
| Main game | `Evenagestand.jpg` + animation variants (see §6) | Every turn |
| Definitions | `definitions.jpg` | Button on main/intro screens |
| Field Guide | `fieldguide.jpg` | Button on main screen |
| Hints | `hint1.jpg` – `hint12.jpg` (cycles on each click) | Button on main screen |
| Pine snake | `pinesnake.jpg` | Achievement unlock |
| Gentian | `gentian.jpg` | Achievement unlock |
| Turkey Beard | `turkeybeard.jpg` | Achievement unlock |
| Summer Tanager | `Tanager.jpg` | Achievement unlock |
| Indigo Bunting | `bunting.jpg` | Achievement unlock |
| Tree Frog | `treefrog.jpg` ↔ `treefrog_1.jpg` (random blink) | Achievement unlock |
| Hurricane event | `hurricane_lightning.jpg` → `hurricane_rain.jpg` → `hurricane_lightning.jpg` → `hurricane_rain.jpg` → `hurricane_after.jpg` | Random event (5% chance, once per game) |
| Non-losing wildfire | `nonlosing_fire.jpg` | Prescribed burn while fire risk is High |
| Low TPA loss | `LowStocking.jpg` | TPA ≤ 20 |
| Fire loss | `LossByFire.jpg` | Catastrophic wildfire event |
| SPB loss | `LossBySPB.jpg` | SPB outbreak while SPB risk is High |
| Win / Closing | Dynamic filename (see §7) | Year reaches 100 |
| Analysis Lab | `analyze_load.jpg` → `analyze.jpg` ↔ `analyze_blink.jpg` (cycling) | "Analyze My Management" button |
| Analysis Definitions | `analyze_definitions.jpg` | Button within Analysis Lab |
| Certificate overlay | `nameplate.jpg` (overlaid on win screen) | Button on win screen |
| Exit survey overlay | `exitsurvey.jpg` (overlaid on current screen) | "Exit" button |

---

## 5. JavaScript Module Breakdown

### 5.1 `game.js` — Game Logic Port

A direct translation of `game_logic.py` into an ES6 class. No DOM access. Fully testable in the browser console.

**Key translation mappings:**

| Python | JavaScript |
|---|---|
| `class Game` | `class Game` (ES6, exported) |
| `random.random()` | `Math.random()` |
| `math.log10(x)` | `Math.log10(x)` |
| `math.log(x)` | `Math.log(x)` |
| `round(x, n)` | `Math.round(x * 10**n) / 10**n` |
| `deepcopy(obj)` | `JSON.parse(JSON.stringify(obj))` |
| `int(x)` | `Math.round(x)` or `Math.trunc(x)` |
| `pd.DataFrame` | Plain array of objects (no pandas needed) |
| `self.X` | `this.X` |

**Methods to port (1:1):**
- `constructor()` ← `__init__`
- `resetGame()` ← `reset_game`
- `updateStand(action)` ← `update_stand`
- `isLowTpaGameOver()` ← `is_low_tpa_game_over`
- `simulateEvent()` ← `simulate_event`
- `getStatus()` ← `get_status`
- `getStatusDict()` ← `get_status_dict`
- `getSummary()` ← `get_summary`
- `addAchievement(name, year)` ← `add_achievement`
- `getAchievementsList()` ← `get_achievements_list`
- `getActionSummary()` ← `get_action_summary`
- `getDecadalData()` ← `get_decadal_dataframe` (returns array of objects instead of DataFrame)

**`ACTIONS` constant:**
```javascript
const ACTIONS = {
  '1': 'Do nothing',
  '2': 'Thin lightly',
  '3': 'Thin heavily',
  '4': 'Prescribed burn'
};
```

**`getDecadalData()` return format** (replaces pandas DataFrame):
```javascript
// Returns an array of plain objects, one per decadal year
[
  { year: 'Start', QMD: 5.5, TPA: 650, BA: 107.5, carbon: 20.0, CI: 18.0, fireRisk: 'High', spbRisk: 'Moderate' },
  { year: 10,      QMD: 6.1, TPA: 590, ... },
  ...
]
```

### 5.2 `screens.js` — Screen Router

Manages which screen is currently visible. Each `showXScreen()` function:
1. Hides all existing screen elements (`innerHTML = ''` on a root container, or hide/show named divs)
2. Sets the background image on a fullscreen `<div>`
3. Renders the metrics panel
4. Renders contextual buttons and text

**Screen router pattern:**
```javascript
function showScreen(bgImagePath, builderFn) {
  const root = document.getElementById('game-root');
  root.innerHTML = '';
  root.style.backgroundImage = `url('${bgImagePath}')`;
  builderFn(root);
}
```

**Animation helper** (replaces `root.after(ms, fn)` + `start_animation()`):
```javascript
function startAnimation(startImg, durationMs, finalImg, onComplete) {
  setBg(startImg);
  setTimeout(() => {
    setBg(finalImg);
    if (onComplete) onComplete();
  }, durationMs);
}
```

**Achievement queue** — implement identically to the Python version: maintain a `game.achievementQueue` array, pop and show one screen at a time, then call `showNextQueuedAchievementOrGame()` from each achievement screen's Continue button.

**Turn sequencing** — the `nextTurn(action)` function in `screens.js` mirrors the Python `next_turn()` exactly, including:
- All animation branch conditions (prescribed burn after thin lightly, heavy thin after burn, etc.)
- Loss checks (low TPA, catastrophic wildfire, SPB)
- Achievement queue population
- Win check at year ≥ 100

### 5.3 `sounds.js` — Audio Wrappers

Use the Web Audio API (`new Audio(src)`) for all sounds. Match the pygame function names for clarity.

```javascript
let forestAudio = null;

export function playForestSound() {
  forestAudio = new Audio('../src/assets/forest_sound.wav');
  forestAudio.loop = true;
  forestAudio.play();
}

export function stopForestSound() {
  if (forestAudio) { forestAudio.pause(); forestAudio = null; }
}
```

Implement wrappers for all ~25 audio files. Looping sounds (forest, fire, SPB eating, tree frog, hurricane, analysis lab, wind) need a stored reference to allow stopping. One-shot sounds (page turn, pine snake, trumpet win, etc.) can fire and forget.

**Sound files to wrap:**
`forest_sound.wav`, `fire.wav`, `trumpet_win.wav`, `losing_trombone.wav`, `pine_snake.wav`, `SPB_eating.wav`, `page_turn.wav`, `page_close.wav`, `zoom.wav`, `wind.wav`, `hintopen.wav`, `hintclose.wav`, `do_nothing.wav`, `thin_lightly.wav`, `thin_heavily.wav`, `prescribed_burn.wav`, `lets_play.wav`, `gentian.wav`, `tanager.wav`, `bunting.wav`, `treefrog.wav`, `hurricane.wav`, `save.wav`, `computer_startup.wav`, `computer_shutdown.wav`, `analysis_lab.wav`

### 5.4 `charts.js` — Analysis Lab Charts

Use **Chart.js** (load from CDN, no install required):
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
```

Implement `showVariablePlot(variable, decadalData)` which renders a Chart.js chart into a canvas element overlaid on the analysis lab screen.

**Variables to plot:** `QMD`, `TPA`, `BA`, `carbon`, `CI`, `fire_risk`, `SPB_risk`

**Categorical variables** (`fire_risk`, `SPB_risk`): render as bar charts with color-coded bars (Low = `#228B22`, Moderate = `#FFA600`, High = `#B22222`). Map to numeric values 1/2/3 for the y-axis, with custom tick labels.

**Numeric variables**: line chart with markers, color `#05dd4c`, dark background `#1f3339`.

**Chart styling** to match desktop:
```javascript
Chart.defaults.color = '#b5c3d8';
Chart.defaults.borderColor = '#2c404b';
// backgroundColor on datasets: '#1f3339'
// gridColor: '#2c404b'
```

**X-axis:** always span -10 to 100 (Year "Start" = -1, shown as blank label). Ticks every 10 years.

**CSV export** (replaces `filedialog.asksaveasfilename` + pandas `to_csv`):
```javascript
function exportCSV(decadalData, actionHistory, achievementsHistory) {
  const rows = decadalData.map(row => ({ ...row,
    actions: actionHistory.filter(([y]) => y === row.year).map(([,a]) => ACTIONS[a]).join('; '),
    achievements: achievementsHistory.filter(([y]) => y === row.year).map(([,n]) => n).join(' - ')
  }));
  const csv = [Object.keys(rows[0]).join(','), ...rows.map(r => Object.values(r).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `PitchPineTrail_data_${Date.now()}.csv`;
  a.click();
}
```

---

## 6. Animation Sequences

All animations use `setTimeout` chains. The background image is set by updating `style.backgroundImage` on the root element.

### Zoom sequence (intro → game)
Show `zoom_1.jpg` through `zoom_9.jpg` at 10ms each, then show `zoom_10.jpg` and overlay the "Let's Play!" button.

### Management animations (main game)
Each animation shows a "during" image for a set duration, then swaps to a "final" image that persists as the background for subsequent turns.

| Action context | During image | Duration | Final image |
|---|---|---|---|
| First prescribed burn (no prior TL or HT) | `prescribedburn.jpg` | 2000ms | `afterburn.jpg` |
| First thin lightly (no prior PB or HT) | `chainsaw.jpg` | 1500ms | `treedown.jpg` |
| First heavy thin (no prior TL or PB) | `mower.jpg` | 2000ms | `heavythin.jpg` |
| PB after TL (no HT) | `prescribedburn_treedown.jpg` | 2000ms | `afterburn_treedown.jpg` |
| TL after PB (no HT) | `chainsaw_afterburn.jpg` | 1500ms | `afterburn_treedown.jpg` |
| HT after PB (no TL) | `mower_afterburn.jpg` | 2000ms | `heavythin_afterburn.jpg` |
| HT after TL (no PB) | `mower_treedown.jpg` | 2000ms | `heavythin_treedown.jpg` |
| HT after both TL and PB | `mower_afterburn_treedown.jpg` | 2000ms | `heavythin_afterburn_treedown.jpg` |
| PB after HT (no TL) | `prescribedburn_heavythin.jpg` | 2000ms | `afterburn_heavythin.jpg` |
| TL after HT (no PB) | `chainsaw_heavythin.jpg` | 1500ms | `heavythin_treedown.jpg` |
| PB after TL+HT | `prescribedburn_treedown_heavythin.jpg` | 2000ms | `afterburn_heavythin_treedown.jpg` |
| TL after HT+PB (HT after PB) | `chainsaw_heavythin_afterburn.jpg` | 1500ms | `heavythin_afterburn_treedown.jpg` |
| TL after HT+PB (HT before PB) | `chainsaw_afterburn_heavythin.jpg` | 1500ms | `afterburn_heavythin_treedown.jpg` |
| Second PB after HT (no TL) | `prescribedburn2_heavythin.jpg` | 2000ms | `afterburn_heavythin.jpg` |
| Second PB after HT (with TL) | `prescribedburn2_heavythin_treedown.jpg` | 2000ms | `afterburn_heavythin_treedown.jpg` |

### Hurricane sequence
`hurricane_lightning.jpg` (200ms) → `hurricane_rain.jpg` (2900ms) → `hurricane_lightning.jpg` (200ms) → `hurricane_rain.jpg` (5100ms) → `hurricane_after.jpg` (static, wait for Continue)

### Tree frog blink
Alternate between `treefrog.jpg` and `treefrog_1.jpg` at random intervals between 200ms and 800ms using `setInterval` with random re-scheduling. Stop on Continue.

### Analysis lab
`analyze_load.jpg` for 1000ms, then begin cycling: `analyze.jpg` (1000ms) ↔ `analyze_blink.jpg` (500ms) continuously until the screen is left.

---

## 7. Win Screen — Dynamic Background Filename

The win screen background is assembled from game outcome and achievements earned:

```javascript
function getWinBgPath(statusDict, achievements) {
  const qmd = statusDict.QMD;
  const fireHigh = statusDict.fireRisk === 'High';
  const spbHigh = statusDict.spbRisk === 'High';

  const base = (qmd < 13 || fireHigh || spbHigh) ? 'bad'
             : (qmd < 15) ? 'okay'
             : 'good';

  const medalOrder = ['snake','gentian','tanager','frog','bunting','turkey','short'];
  const achievementMap = {
    snake:   game.pine_snake_achieved || game.pine_snakes_colonized,
    gentian: game.gentian_achieved || game.gentian_colonized,
    tanager: game.summer_tanager_achieved || game.summer_tanager_colonized,
    frog:    game.tree_frog_achieved || game.pine_barrens_tree_frog_colonized,
    bunting: game.indigo_bunting_achieved || game.indigo_bunting_colonized,
    turkey:  game.turkey_beard_achieved,
    short:   game.short_achieved || game.short_colonized
  };

  const medals = medalOrder.filter(m => achievementMap[m]).join('-');
  const suffix = medals ? `${medals}medal` : 'nomedal';
  return `../src/assets/${base}_${suffix}.jpg`;
}
```

---

## 8. Certificate & Screenshot

The desktop version uses `PIL.ImageGrab` to capture a screenshot. In the browser, use **html2canvas**:

```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
```

```javascript
function saveCertificate() {
  html2canvas(document.getElementById('game-root')).then(canvas => {
    const a = document.createElement('a');
    a.download = `PitchPineTrail_certificate_${Date.now()}.jpg`;
    a.href = canvas.toDataURL('image/jpeg');
    a.click();
  });
}
```

The nameplate overlay (`nameplate.jpg`) with a text input for the player's name is built as an absolutely positioned `<div>` over the win screen, matching the desktop layout.

---

## 9. Exit Survey

The exit survey overlay displays `exitsurvey.jpg` and links to:
```
https://forms.office.com/g/N38DQhPe2V
```
Open in a new tab (`window.open(url, '_blank')`). The "Exit" button on the web version should navigate to a neutral end state (blank screen or close tab attempt) rather than `root.destroy()`.

---

## 10. Metrics Panel

The metrics panel is rendered on every screen (game, achievement, event, loss, win screens). It is a white `<div>` positioned `right: 8%, top: 57%` in absolute coordinates.

**Content:**
```
Year: {year}

Basal Area (BA): {BA} sqft/acre

Trees Per Acre (TPA): {TPA}

Quadratic Mean Diameter (QMD): {QMD} inches

Carbon per Acre: {carbon} Metric Tons/acre

Crowning Index: {CI}

Fire Risk: {fireRisk}          ← colored per risk level
Southern Pine Beetle Risk: {spbRisk}   ← colored per risk level
```

Font: `Courier New`, bold. Risk label colors: `#228B22` / `#FFA600` / `#B22222`.

---

## 11. Build Order for Coding Agent

Implement in this order. Each step is independently testable before proceeding.

1. **`game.js`** — Complete port of `game_logic.py`. Test in browser console: instantiate `new Game()`, call `updateStand('1')` ten times, verify `getStatusDict()` returns expected values. No DOM access in this file.

2. **`index.html` + `style.css`** — HTML shell with a single `#game-root` fullscreen div, CDN script imports (Chart.js, html2canvas), and CSS establishing the color palette, Courier New font, and fullscreen background image layout.

3. **`sounds.js`** — All audio wrappers. Test by calling `playForestSound()` and `stopForestSound()` from the console.

4. **`screens.js` (intro + main game only)** — Implement `showIntroScreen()`, zoom sequence, and `showGameScreen()` with the four action buttons and metrics panel. Verify a full 100-year game can be played to the win screen.

5. **`screens.js` (loss screens)** — Add `showLowTpaScreen()`, `showFireLossScreen()`, `showSpbLossScreen()`.

6. **`screens.js` (achievement screens)** — Add all seven achievement screens and the queue system (`showNextQueuedAchievementOrGame()`).

7. **`screens.js` (event screens)** — Add `showHurricaneScreen()` and `showWildfireScreen()`.

8. **`screens.js` (win screen)** — Add `showClosingScreen()` with dynamic background filename logic and certificate overlay.

9. **`screens.js` (auxiliary screens)** — Add Definitions, Field Guide, Hints, and exit survey overlay.

10. **`charts.js` + Analysis Lab** — Add `showAnalysisLab()` with all 7 chart buttons, data table, CSV export, and return-to-game navigation.

11. **Polish and GitHub Pages deployment** — Verify all asset paths resolve correctly from the `web/` folder using `../src/assets/`. Enable GitHub Pages from `main` branch `/web` folder.

---

## 12. Known Constraints and Notes

- **No Python, no server.** Everything must run as static files. No Flask, no FastAPI, no Node backend.
- **Audio autoplay policy.** Browsers block audio until the user interacts with the page. Ensure all sounds are triggered from user click events, not from page load. The intro screen's forest sound should start on the "Begin" button click, not on page load.
- **WAV compatibility.** All existing audio files are `.wav`. These are broadly supported in modern browsers but file size may be large. Consider converting to `.mp3` or `.ogg` as an optional optimization step after the port is working.
- **Asset path depth.** All asset references from `web/js/*.js` files go up two levels: `../../src/assets/filename.jpg`. From `web/index.html` they go up one level: `../src/assets/filename.jpg`. Be consistent.
- **`simulate_event()` is separate from `update_stand()`.** In the Python version, `next_turn()` calls `update_stand(action)` then `simulate_event()` then increments `game.stand['year'] += 10`. Preserve this exact call order in `nextTurn()`.
- **Achievement deduplication.** The Python version uses both `achieved` flags (persistent) and `colonized` flags. The win screen checks both with `||`. Preserve this logic exactly.
- **Hurricane is once-per-game.** Guarded by `game.hurricaneOccurred` flag. The wildfire screen is also once-per-game, guarded by `game.wildfireScreenShown`.
- **Year counter.** Year starts at 0 and is incremented by 10 *after* `update_stand()` and `simulate_event()` are called, inside `next_turn()`. The initial stand state is stored as `initial_stand` and displayed as year "Start" (internally year -1) in the analysis table.
