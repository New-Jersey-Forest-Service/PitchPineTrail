import { ACTIONS, Game } from "./game.js";
import { exportCSV, renderDataTable, showVariablePlot } from "./charts.js";
import { sounds, stopAllLoops } from "./sounds.js";

const root = document.getElementById("game-root");
const ASSET_BASE = "../src/assets/";

const game = new Game();
Object.assign(game, {
  current_bg_img: "Evenagestand.jpg",
  achievement_queue: [],
  achievement_final_bg: null,
  thin_lightly_event: false,
  prescribed_burn_event: false,
  pb_after_first_heavythin_shown: false,
  pb_after_heavythin_with_tl_shown: false,
  has_made_first_choice: false,
  hurricane_pending: false,
  wildfire_pending: false,
  wildfire_last_shown_year: null,
  hurricane_last_shown_year: null,
  hint_index: 0
});

window.pitchPineTrailGame = game;

const achievementScreens = {
  snake: { image: "Pinesnake.jpg", sound: sounds.playPineSnakeSound, title: "Pine snakes are utilizing this stand!" },
  gentian: { image: "gentian.jpg", sound: sounds.playGentianSound, title: "Gentian is now growing in this stand!" },
  short: { image: "shortleaf.jpg", sound: sounds.playPageTurnSound, title: "Shortleaf pine has established in this stand!" },
  turkey: { image: "turkeybeard.jpg", sound: sounds.playPageTurnSound, title: "Turkey Beard is now growing in this stand!" },
  tanager: { image: "Tanager.jpg", sound: sounds.playTanagerSound, title: "Summer tanager has colonized this stand!" },
  bunting: { image: "bunting.jpg", sound: sounds.playBuntingSound, title: "Indigo bunting has colonized this stand!" },
  frog: { image: "treefrog.jpg", sound: sounds.playTreeFrogSound, title: "Pine Barrens tree frog has colonized this stand!" }
};

function asset(name) {
  if (name.startsWith("../") || name.startsWith("http")) return name;
  return `${ASSET_BASE}${name.replace(/^assets\//, "")}`;
}

function setBg(name) {
  game.current_bg_img = name.replace(/^assets\//, "");
  root.style.backgroundImage = `url("${asset(name)}")`;
}

function clearScreen(bgName) {
  root.innerHTML = "";
  if (bgName) setBg(bgName);
}

function button(text, className, onClick) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = className;
  btn.textContent = text;
  btn.addEventListener("click", onClick);
  return btn;
}

function riskClass(risk) {
  return risk === "Low" ? "risk-low" : risk === "Moderate" ? "risk-moderate" : "risk-high";
}

function renderMetrics(parent = root) {
  const status = game.getStatusDict();
  const panel = document.createElement("section");
  panel.className = "metrics-panel";
  panel.innerHTML = `
    <div>Year: ${status.year}</div>
    <br>
    <div>Basal Area (BA): ${Number(status.BA).toFixed(1)} sqft/acre</div>
    <br>
    <div>Trees Per Acre (TPA): ${status.TPA}</div>
    <br>
    <div>Quadratic Mean Diameter (QMD): ${Number(status.QMD).toFixed(1)} inches</div>
    <br>
    <div>Carbon per Acre: ${Number(status.carbon).toFixed(1)} Metric Tons/acre</div>
    <br>
    <div>Crowning Index: ${Number(status.CI).toFixed(1)}</div>
    <span class="metric-risk ${riskClass(status.fire_risk)}">Fire Risk: ${status.fire_risk}</span>
    <span class="metric-risk ${riskClass(status.SPB_risk)}">Southern Pine Beetle Risk: ${status.SPB_risk}</span>
  `;
  parent.append(panel);
  return panel;
}

function renderCommonNav() {
  root.append(
    Object.assign(document.createElement("div"), { className: "field-guide-link" }),
    Object.assign(document.createElement("div"), { className: "definitions-link" }),
    Object.assign(document.createElement("div"), { className: "exit-link" }),
    Object.assign(document.createElement("div"), { className: "hint-link" })
  );
  root.querySelector(".field-guide-link").append(button("Click for Field Guide", "dark-button", showFieldGuideScreen));
  root.querySelector(".definitions-link").append(button("Click for Definitions", "dark-button", showDefinitionsScreen));
  root.querySelector(".exit-link").append(button("Exit", "red-button", () => showExitSurveyOverlay()));
  root.querySelector(".hint-link").append(button("Click for a Hint", "blue-button", () => showHintOverlay()));
}

function lastEventNamed(name) {
  const events = game.stand.events || [];
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index];
    const eventName = Array.isArray(event) ? event[1] : event;
    const eventYear = Array.isArray(event) ? event[0] : null;
    if (eventName === name) return { eventName, eventYear };
  }
  return null;
}

function consumeNewModalEvents() {
  const hurricane = lastEventNamed("Hurricane passed through");
  if (hurricane && game.hurricane_last_shown_year !== hurricane.eventYear && !game.hurricane_screen_shown) {
    game.hurricane_pending = true;
    game.hurricane_last_shown_year = hurricane.eventYear;
  }
  const wildfire = lastEventNamed("WILDFIRE");
  if (wildfire && game.wildfire_last_shown_year !== wildfire.eventYear && !game.wildfire_screen_shown) {
    game.wildfire_pending = true;
    game.wildfire_last_shown_year = wildfire.eventYear;
  }
}

function queueAchievements(before, finalBg) {
  const queue = [];
  if (!before.snake && game.pine_snakes_colonized) queue.push("snake");
  if (!before.gentian && game.gentian_colonized && !game.gentian_screen_shown) queue.push("gentian");
  if (!before.tanager && game.summer_tanager_colonized && !game.summer_tanager_screen_shown) queue.push("tanager");
  if (!before.bunting && game.indigo_bunting_colonized && !game.indigo_bunting_screen_shown) queue.push("bunting");
  if (!before.frog && game.pine_barrens_tree_frog_colonized && !game.tree_frog_screen_shown) queue.push("frog");
  if (!before.turkey && game.turkey_beard_achieved && !game.turkey_beard_screen_shown) queue.push("turkey");
  if (!before.short && game.short_colonized && !game.short_screen_shown) queue.push("short");
  consumeNewModalEvents();
  if (queue.length) {
    game.current_bg_img = finalBg.replace(/^assets\//, "");
    game.achievement_final_bg = game.current_bg_img;
    game.achievement_queue = queue;
    showNextQueuedAchievementOrGame();
    return true;
  }
  return false;
}

function applyTurn(action) {
  const before = {
    snake: game.pine_snakes_colonized,
    gentian: game.gentian_colonized,
    tanager: game.summer_tanager_colonized,
    bunting: game.indigo_bunting_colonized,
    frog: game.pine_barrens_tree_frog_colonized,
    turkey: game.turkey_beard_achieved,
    short: game.short_colonized
  };
  game.updateStand(action);
  const event = game.simulateEvent();
  game.stand.year += 10;
  return { before, event };
}

function finishTurn(before, event, finalBg, animate = null) {
  if (game.isLowTpaGameOver()) return showLowTpaScreen();
  if (game.stand.catastrophic_wildfire) return showFireLossScreen();
  if (event === "SPB outbreak!" && game.stand.SPB_risk === "High") return showSpbLossScreen();
  if (queueAchievements(before, finalBg)) return;
  consumeNewModalEvents();
  if (game.hurricane_pending) {
    game.hurricane_pending = false;
    return showHurricaneScreen();
  }
  if (game.wildfire_pending) {
    game.wildfire_pending = false;
    return showWildfireScreen();
  }
  if (game.stand.year >= 100) return showClosingScreen();
  if (animate) return startAnimation(animate.during, animate.ms, animate.final);
  showGameScreen(event || "");
}

function chooseAnimation(action) {
  const history = game.action_history;
  const burnIndices = history.map(([, a], i) => a === "4" ? i : -1).filter((i) => i >= 0);
  const heavyIndices = history.map(([, a], i) => a === "3" ? i : -1).filter((i) => i >= 0);
  const firstBurnIdx = burnIndices.length ? burnIndices[0] : null;
  const firstHeavyIdx = heavyIndices.length ? heavyIndices[0] : null;
  const pbBeforeHeavy = firstBurnIdx !== null && firstHeavyIdx !== null && burnIndices.some((i) => i < firstHeavyIdx);
  const pbAfterHeavy = firstBurnIdx !== null && firstHeavyIdx !== null && burnIndices.some((i) => i > firstHeavyIdx);
  const pbBothSides = pbBeforeHeavy && pbAfterHeavy;
  const heavyBeforeFirstBurn = firstBurnIdx !== null && heavyIndices.some((i) => i < firstBurnIdx);
  const heavyAfterFirstBurn = firstBurnIdx !== null && heavyIndices.some((i) => i > firstBurnIdx);
  const hasHeavy = history.some(([, a]) => a === "3");

  const pack = (during, ms, final) => ({ during, ms, final });
  if (action === "4" && !game.prescribed_burn_event && game.thin_lightly_event && !hasHeavy) {
    game.prescribed_burn_event = true;
    return pack("prescribedburn_treedown.jpg", 2000, "afterburn_treedown.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && game.prescribed_burn_event && !hasHeavy) {
    game.thin_lightly_event = true;
    return pack("chainsaw_afterburn.jpg", 1500, "afterburn_treedown.jpg");
  }
  if (action === "4" && !game.prescribed_burn_event && !history.some(([, a]) => ["2", "3"].includes(a))) {
    game.prescribed_burn_event = true;
    return pack("prescribedburn.jpg", 2000, "afterburn.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && !history.some(([, a]) => ["3", "4"].includes(a))) {
    game.thin_lightly_event = true;
    return pack("chainsaw.jpg", 1500, "treedown.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && hasHeavy && !game.prescribed_burn_event) {
    game.thin_lightly_event = true;
    return pack("chainsaw_heavythin.jpg", 1500, "heavythin_treedown.jpg");
  }
  if (action === "3" && !hasHeavy && game.prescribed_burn_event && !game.thin_lightly_event) {
    return pack("mower_afterburn.jpg", 2000, "heavythin_afterburn.jpg");
  }
  if (action === "3" && !hasHeavy && game.thin_lightly_event && !game.prescribed_burn_event) {
    return pack("mower_treedown.jpg", 2000, "heavythin_treedown.jpg");
  }
  if (action === "3" && !hasHeavy && !game.thin_lightly_event && !game.prescribed_burn_event) {
    return pack("mower.jpg", 2000, "heavythin.jpg");
  }
  if (action === "3" && !hasHeavy && game.prescribed_burn_event && game.thin_lightly_event) {
    return pack("mower_afterburn_treedown.jpg", 2000, "heavythin_afterburn_treedown.jpg");
  }
  if (action === "4" && !game.prescribed_burn_event && hasHeavy && !game.thin_lightly_event) {
    game.prescribed_burn_event = true;
    return pack("prescribedburn_heavythin.jpg", 2000, "afterburn_heavythin.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && game.prescribed_burn_event && hasHeavy && heavyAfterFirstBurn && !heavyBeforeFirstBurn) {
    game.thin_lightly_event = true;
    return pack("chainsaw_heavythin_afterburn.jpg", 1500, "heavythin_afterburn_treedown.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && game.prescribed_burn_event && hasHeavy && firstBurnIdx !== null && firstHeavyIdx !== null && firstHeavyIdx < firstBurnIdx) {
    game.thin_lightly_event = true;
    return pack("chainsaw_afterburn_heavythin.jpg", 1500, "afterburn_heavythin_treedown.jpg");
  }
  if (action === "4" && !game.prescribed_burn_event && game.thin_lightly_event && hasHeavy) {
    game.prescribed_burn_event = true;
    return pack("prescribedburn_treedown_heavythin.jpg", 2000, "afterburn_heavythin_treedown.jpg");
  }
  if (action === "4" && game.prescribed_burn_event && hasHeavy && !game.thin_lightly_event && pbBeforeHeavy && !game.pb_after_first_heavythin_shown) {
    game.pb_after_first_heavythin_shown = true;
    return pack("prescribedburn2_heavythin.jpg", 2000, "afterburn_heavythin.jpg");
  }
  if (action === "4" && game.prescribed_burn_event && hasHeavy && game.thin_lightly_event && pbBeforeHeavy && !game.pb_after_heavythin_with_tl_shown) {
    game.pb_after_heavythin_with_tl_shown = true;
    return pack("prescribedburn2_heavythin_treedown.jpg", 2000, "afterburn_heavythin_treedown.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && pbBothSides) {
    game.thin_lightly_event = true;
    return pack("chainsaw_afterburn_heavythin.jpg", 1500, "afterburn_heavythin_treedown.jpg");
  }
  if (action === "2" && !game.thin_lightly_event && !game.prescribed_burn_event && hasHeavy && firstHeavyIdx !== null && (firstBurnIdx === null || firstHeavyIdx < firstBurnIdx)) {
    game.thin_lightly_event = true;
    return pack("chainsaw_afterburn_heavythin.jpg", 1500, "afterburn_heavythin_treedown.jpg");
  }
  return null;
}

function nextTurn(action) {
  game.has_made_first_choice = true;
  const animation = game.stand.year >= 90 && game.stand.year < 100 ? null : chooseAnimation(action);
  const { before, event } = applyTurn(action);
  const finalBg = animation?.final ?? game.current_bg_img ?? "Evenagestand.jpg";
  finishTurn(before, event, finalBg, animation);
}

function startAnimation(during, durationMs, final) {
  clearScreen(during);
  setTimeout(() => {
    setBg(final);
    showGameScreen();
  }, durationMs);
}

function showIntroScreen() {
  clearScreen("introscreen.jpg");
  const buttons = document.createElement("div");
  buttons.className = "intro-buttons";
  buttons.append(
    button("Begin", "tan-button", () => {
      sounds.playForestSound();
      startZoomSequence();
    }),
    button("Exit", "tan-button", () => showExitSurveyOverlay())
  );
  root.append(buttons);
}

function startZoomSequence() {
  sounds.playZoomSound();
  clearScreen("zoom_1.jpg");
  let frame = 1;
  const timer = setInterval(() => {
    frame += 1;
    if (frame <= 10) setBg(`zoom_${frame}.jpg`);
    if (frame >= 10) {
      clearInterval(timer);
      const buttons = document.createElement("div");
      buttons.className = "intro-buttons";
      buttons.append(button("Let's Play!", "tan-button", () => {
        sounds.playLetsPlaySound();
        showGameScreen();
      }));
      root.append(buttons);
      const defs = document.createElement("div");
      defs.className = "definitions-link";
      defs.append(button("Click for Definitions", "dark-button", showDefinitionsScreen));
      root.append(defs);
    }
  }, 10);
}

function showGameScreen(narration = "") {
  clearScreen(game.current_bg_img || "Evenagestand.jpg");
  renderMetrics();
  const actions = document.createElement("section");
  actions.className = "action-panel";
  for (const [key, label] of Object.entries(ACTIONS).filter(([key]) => ["1", "2", "3", "4"].includes(key))) {
    actions.append(button(`${key}. ${label}`, "action-button", () => {
      if (key === "1") sounds.playDoNothingSound();
      if (key === "2") sounds.playThinLightlySound();
      if (key === "3") sounds.playThinHeavilySound();
      if (key === "4") sounds.playPrescribedBurnSound();
      nextTurn(key);
    }));
  }
  root.append(actions);
  if (narration) {
    const note = document.createElement("div");
    note.className = "event-message";
    note.textContent = narration;
    root.append(note);
  }
  renderCommonNav();
}

function showClosingScreen() {
  stopAllLoops();
  sounds.playTrumpetWinSound();
  clearScreen(getWinBgName());
  renderMetrics();
  const summary = document.createElement("section");
  summary.className = "summary-panel";
  summary.textContent = game.getActionSummary();
  root.append(summary);
  const actions = document.createElement("div");
  actions.className = "closing-actions";
  actions.append(
    button("Analyze My Management", "blue-button", () => {
      sounds.playComputerStartup();
      showAnalysisLab(getWinBgName(), true, "closing");
    }),
    button("Save your successful management certificate", "blue-button", showCertificateOverlay),
    button("Try Again", "green-button", restartGame),
    button("Exit", "red-button", () => showExitSurveyOverlay())
  );
  root.append(actions);
}

function getWinBgName() {
  const status = game.getStatusDict();
  const base = status.QMD < 13 || status.fire_risk === "High" || status.SPB_risk === "High"
    ? "bad"
    : status.QMD < 15
      ? "okay"
      : "good";
  const medals = [
    ["snake", game.pine_snake_achieved || game.pine_snakes_colonized],
    ["gentian", game.gentian_achieved || game.gentian_colonized],
    ["tanager", game.summer_tanager_achieved || game.summer_tanager_colonized],
    ["frog", game.tree_frog_achieved || game.pine_barrens_tree_frog_colonized],
    ["bunting", game.indigo_bunting_achieved || game.indigo_bunting_colonized],
    ["turkey", game.turkey_beard_achieved],
    ["short", game.short_achieved || game.short_colonized]
  ].filter(([, present]) => present).map(([name]) => name).join("-");
  return `${base}_${medals ? `${medals}medal` : "nomedal"}.jpg`;
}

function showLossScreen(bg, text, soundFn) {
  stopAllLoops();
  soundFn?.();
  clearScreen(bg);
  renderMetrics();
  const message = document.createElement("section");
  message.className = "loss-message";
  message.textContent = text;
  root.append(message);
  const actions = document.createElement("div");
  actions.className = "loss-actions";
  actions.append(
    button("Analyze My Management", "blue-button", () => showAnalysisLab(bg, true, bg)),
    button("Try Again", "green-button", restartGame),
    button("Exit", "red-button", () => showExitSurveyOverlay())
  );
  root.append(actions);
}

function showLowTpaScreen() {
  showLossScreen("LowStocking.jpg", "Your stand stocking is too low to continue growing a mature pitch pine forest.", sounds.playLosingTromboneSound);
}

function showFireLossScreen() {
  showLossScreen("LossByFire.jpg", "A catastrophic wildfire has occurred.\n\nA new pitch pine stand may begin, but the mature stand management goal was lost.", sounds.playLosingTromboneSound);
}

function showSpbLossScreen() {
  showLossScreen("LossBySPB.jpg", "Southern pine beetle caused a stand-level loss while SPB risk was High.", sounds.playSpbEatingSound);
}

function showAchievementScreen(code) {
  const info = achievementScreens[code];
  if (!info) return showNextQueuedAchievementOrGame();
  clearScreen(info.image);
  info.sound?.();
  renderMetrics();
  const message = document.createElement("section");
  message.className = "achievement-message";
  message.textContent = info.title;
  root.append(message);
  const actions = document.createElement("div");
  actions.className = "achievement-actions";
  actions.append(button("Continue", "green-button", () => {
    if (code === "frog") sounds.stopTreeFrogSound();
    showNextQueuedAchievementOrGame();
  }));
  root.append(actions);
}

function showNextQueuedAchievementOrGame() {
  const code = game.achievement_queue.shift();
  if (code) {
    if (code === "snake") game.pine_snake_achieved = true;
    if (code === "gentian") {
      game.gentian_screen_shown = true;
      game.gentian_achieved = true;
    }
    if (code === "tanager") {
      game.summer_tanager_screen_shown = true;
      game.summer_tanager_achieved = true;
    }
    if (code === "bunting") {
      game.indigo_bunting_screen_shown = true;
      game.indigo_bunting_achieved = true;
    }
    if (code === "frog") {
      game.tree_frog_screen_shown = true;
      game.tree_frog_achieved = true;
    }
    if (code === "turkey") {
      game.turkey_beard_screen_shown = true;
      game.turkey_beard_achieved = true;
    }
    if (code === "short") {
      game.short_screen_shown = true;
      game.short_achieved = true;
    }
    return showAchievementScreen(code);
  }
  if (game.hurricane_pending) {
    game.hurricane_pending = false;
    return showHurricaneScreen();
  }
  if (game.wildfire_pending) {
    game.wildfire_pending = false;
    return showWildfireScreen();
  }
  if (game.stand.year >= 100) return showClosingScreen();
  showGameScreen();
}

function showHurricaneScreen() {
  if (game.hurricane_screen_shown) return showGameScreen();
  game.hurricane_screen_shown = true;
  sounds.playHurricaneSound();
  clearScreen("hurricane_lightning.jpg");
  const sequence = [
    ["hurricane_lightning.jpg", 200],
    ["hurricane_rain.jpg", 2900],
    ["hurricane_lightning.jpg", 200],
    ["hurricane_rain.jpg", 5100],
    ["hurricane_after.jpg", null]
  ];
  let index = 0;
  const step = () => {
    const [image, delay] = sequence[index];
    setBg(image);
    if (delay == null) return finishHurricaneScreen();
    index += 1;
    setTimeout(step, delay);
  };
  step();
}

function finishHurricaneScreen() {
  root.innerHTML = "";
  renderMetrics();
  const message = document.createElement("section");
  message.className = "event-message";
  message.textContent = "A hurricane passed through your forest.\n\nYour forest is still living, but the storm changed your forest metrics.";
  root.append(message);
  const actions = document.createElement("div");
  actions.className = "event-actions";
  actions.append(button("Continue", "green-button", () => {
    sounds.stopHurricaneSound();
    if (game.stand.year >= 100) showClosingScreen();
    else showGameScreen();
  }));
  root.append(actions);
}

function showWildfireScreen() {
  if (game.wildfire_screen_shown) return showGameScreen();
  game.wildfire_screen_shown = true;
  sounds.playFireSound();
  clearScreen("nonlosing_fire.jpg");
  renderMetrics();
  const message = document.createElement("section");
  message.className = "event-message";
  message.textContent = "A wildfire burned through the stand.\n\nThe forest survived, but the event changed your stand metrics.";
  root.append(message);
  const actions = document.createElement("div");
  actions.className = "event-actions";
  actions.append(button("Continue", "green-button", () => {
    sounds.stopFireSound();
    if (game.stand.year >= 100) showClosingScreen();
    else showGameScreen();
  }));
  root.append(actions);
}

function showFieldGuideScreen() {
  sounds.playPageTurnSound();
  clearScreen("fieldguide.jpg");
  root.append(button("Return", "green-button exit-link", () => showGameScreen()));
}

function showDefinitionsScreen() {
  sounds.playPageTurnSound();
  clearScreen("definitions.jpg");
  root.append(button("Return", "green-button exit-link", () => showGameScreen()));
}

function showAnalysisDefinitions(prevBg, returnTarget) {
  sounds.playPageTurnSound();
  clearScreen("analyze_definitions.jpg");
  root.append(button("Return", "green-button exit-link", () => showAnalysisLab(prevBg, false, returnTarget)));
}

function showHintOverlay() {
  sounds.playHintOpenSound();
  const existing = root.querySelector(".hint-overlay");
  if (existing) existing.remove();
  const images = Array.from({ length: 12 }, (_, index) => `hint${index + 1}.jpg`);
  const overlay = document.createElement("div");
  overlay.className = "hint-overlay";
  overlay.innerHTML = `<img src="${asset(images[game.hint_index % images.length])}" alt="">`;
  game.hint_index = (game.hint_index + 1) % images.length;
  overlay.append(button("Close Hint", "red-button hint-close", () => {
    sounds.playHintCloseSound();
    overlay.remove();
  }));
  root.append(overlay);
}

function showExitSurveyOverlay() {
  sounds.playPageTurnSound();
  const existing = root.querySelector(".survey-overlay");
  if (existing) existing.remove();
  const overlay = document.createElement("div");
  overlay.className = "survey-overlay";
  overlay.innerHTML = `<img src="${asset("exitsurvey.jpg")}" alt="">`;
  const actions = document.createElement("div");
  actions.className = "survey-actions";
  actions.append(
    button("Open Feedback Survey", "tan-button", () => window.open("https://forms.office.com/g/N38DQhPe2V", "_blank", "noopener")),
    button("Exit", "red-button", () => {
      stopAllLoops();
      clearScreen(null);
      root.style.backgroundImage = "";
    }),
    button("Cancel", "green-button", () => overlay.remove())
  );
  overlay.append(actions);
  root.append(overlay);
}

function showCertificateOverlay() {
  const existing = root.querySelector(".certificate-overlay");
  if (existing) existing.remove();
  const overlay = document.createElement("div");
  overlay.className = "certificate-overlay";
  overlay.innerHTML = `<img src="${asset("nameplate.jpg")}" alt="">`;
  const input = document.createElement("input");
  input.className = "certificate-name";
  input.placeholder = "Your name";
  const save = button("Save", "green-button certificate-save", () => {
    sounds.playSaveSound();
    if (!window.html2canvas) return;
    save.classList.add("hidden");
    html2canvas(root).then((canvas) => {
      const link = document.createElement("a");
      link.download = `PitchPineTrail_certificate_${Date.now()}.jpg`;
      link.href = canvas.toDataURL("image/jpeg");
      link.click();
      save.classList.remove("hidden");
    }).catch(() => save.classList.remove("hidden"));
  });
  overlay.append(input, save);
  root.append(overlay);
}

function showAnalysisLab(prevBg = game.current_bg_img, loading = true, returnTarget = "game") {
  sounds.stopForestSound();
  sounds.stopFireSound();
  sounds.stopWindSound();
  sounds.stopSpbEatingSound();
  sounds.playAnalysisLabSound();
  clearScreen(loading ? "analyze_load.jpg" : "analyze.jpg");
  const build = () => {
    clearScreen("analyze.jpg");
    const rows = game.getDecadalData(10);
    const table = document.createElement("pre");
    table.className = "analysis-table";
    table.textContent = renderDataTable(rows);
    root.append(table);
    const summary = document.createElement("section");
    summary.className = "summary-panel";
    summary.textContent = game.getActionSummary();
    root.append(summary);
    const achievements = document.createElement("section");
    achievements.className = "achievement-list";
    const grouped = new Map();
    for (const [year, name] of game.getAchievementsList()) {
      if (!grouped.has(year)) grouped.set(year, []);
      grouped.get(year).push(name);
    }
    achievements.textContent = grouped.size
      ? [...grouped.entries()].map(([year, names]) => `Year ${year}:\n${names.map((name) => `   ${name}`).join("\n")}`).join("\n")
      : "No achievements.";
    root.append(achievements);
    root.append(button("Return to Game", "tan-button analysis-return", () => {
      sounds.playComputerShutdown();
      sounds.stopAnalysisLabSound();
      setBg(prevBg);
      if (returnTarget === "closing") showClosingScreen();
      else if (returnTarget === "LowStocking.jpg") showLowTpaScreen();
      else if (returnTarget === "LossByFire.jpg") showFireLossScreen();
      else if (returnTarget === "LossBySPB.jpg") showSpbLossScreen();
      else if (game.stand.year >= 100) showClosingScreen();
      else showGameScreen();
    }));
    root.append(button("Save Data", "red-button save-data-button", () => {
      sounds.playSaveSound();
      exportCSV(game);
    }));
    const plotButtons = document.createElement("div");
    plotButtons.className = "plot-buttons";
    const labels = {
      QMD: "QMD",
      TPA: "TPA",
      BA: "BA",
      carbon: "Carbon",
      CI: "CI",
      fireRisk: "Fire Risk",
      spbRisk: "SPB Risk"
    };
    for (const variable of Object.keys(labels)) {
      plotButtons.append(button(labels[variable], "green-button", () => showChartOverlay(variable, rows)));
    }
    root.append(plotButtons);
    const defs = document.createElement("div");
    defs.className = "analysis-definitions-link";
    defs.append(button("Click for Definitions", "dark-button", () => showAnalysisDefinitions(prevBg, returnTarget)));
    root.append(defs);
    startAnalysisBlink();
  };
  if (loading) setTimeout(build, 1000);
  else build();
}

function showChartOverlay(variable, rows) {
  const existing = root.querySelector(".chart-overlay");
  if (existing) existing.remove();
  const overlay = document.createElement("section");
  overlay.className = "chart-overlay";
  const chartBody = document.createElement("div");
  chartBody.className = "screen-fill";
  overlay.append(
    button("Close Graph", "blue-button chart-close", () => overlay.remove()),
    button("Why does my graph look like that?", "blue-button chart-faq", () => showFaqOverlay(overlay)),
    chartBody
  );
  root.append(overlay);
  showVariablePlot(chartBody, variable, rows);
}

function showFaqOverlay(parent) {
  if (parent.querySelector(".faq-overlay")) return;
  const overlay = document.createElement("div");
  overlay.className = "faq-overlay";
  overlay.innerHTML = `<img src="${asset("FAQs.jpg")}" alt="">`;
  overlay.append(button("Close FAQs", "green-button faq-close", () => overlay.remove()));
  parent.append(overlay);
}

let analysisBlinkTimer = null;
function startAnalysisBlink() {
  if (analysisBlinkTimer) clearInterval(analysisBlinkTimer);
  let blink = false;
  analysisBlinkTimer = setInterval(() => {
    if (!root.querySelector(".analysis-table")) {
      clearInterval(analysisBlinkTimer);
      analysisBlinkTimer = null;
      return;
    }
    setBg(blink ? "analyze.jpg" : "analyze_blink.jpg");
    blink = !blink;
  }, blink ? 500 : 1000);
}

function restartGame() {
  stopAllLoops();
  game.resetGame();
  Object.assign(game, {
    current_bg_img: "Evenagestand.jpg",
    achievement_queue: [],
    achievement_final_bg: null,
    thin_lightly_event: false,
    prescribed_burn_event: false,
    pb_after_first_heavythin_shown: false,
    pb_after_heavythin_with_tl_shown: false,
    has_made_first_choice: false,
    hurricane_pending: false,
    wildfire_pending: false,
    wildfire_last_shown_year: null,
    hurricane_last_shown_year: null
  });
  sounds.playForestSound();
  showGameScreen();
}

showIntroScreen();
