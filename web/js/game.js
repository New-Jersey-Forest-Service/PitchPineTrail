export const ACTIONS = {
  "1": "Do nothing",
  "2": "Thin lightly",
  "3": "Thin heavily",
  "4": "Prescribed burn",
  HURRICANE: "Hurricane",
  WILDFIRE: "Wildfire"
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function pyRound(value, digits = 0) {
  const factor = 10 ** digits;
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

function pyInt(value) {
  return Math.trunc(value);
}

function calculateBA(qmd, tpa) {
  return 0.005454 * tpa * (qmd ** 2);
}

function riskFromCI(ci) {
  return ci <= 20 ? "High" : ci < 25 ? "Moderate" : "Low";
}

function riskFromBA(ba) {
  return ba > 100 ? "High" : ba > 60 ? "Moderate" : "Low";
}

function eventMatches(event, name, year = null) {
  if (Array.isArray(event)) {
    return event.length > 1 && event[1] === name && (year === null || event[0] === year);
  }
  return event === name && year === null;
}

export class Game {
  constructor(randomFn = Math.random) {
    this.random = randomFn;
    this.resetGame();
  }

  randint(min, max) {
    return Math.floor(this.random() * (max - min + 1)) + min;
  }

  resetGame() {
    const qmd = 5.5;
    const tpa = 650;
    const ba = pyRound(calculateBA(qmd, tpa), 1);
    this.stand = {
      year: 0,
      QMD: qmd,
      TPA: tpa,
      carbon: 20.0,
      CI: 18.0,
      BA: ba,
      fire_risk: "High",
      SPB_risk: "Moderate",
      events: [],
      catastrophic_wildfire: false
    };
    this.initial_stand = clone(this.stand);
    this.low_tpa_count = 0;
    this.action_history = [];
    this.pine_snakes_colonized = false;
    this.gentian_colonized = false;
    this.suitable_tanager_ba_reached = false;
    this.summer_tanager_colonized = false;
    this.suitable_bunting_ba_reached = false;
    this.indigo_bunting_colonized = false;
    this.pine_barrens_tree_frog_colonized = false;
    this.short_colonized = false;
    this.pine_snake_achieved = false;
    this.gentian_achieved = false;
    this.summer_tanager_achieved = false;
    this.tree_frog_achieved = false;
    this.indigo_bunting_achieved = false;
    this.short_achieved = false;
    this.turkey_beard_achieved = false;
    this.achievements_history = [];
    this.recruitment_pending = [];
    this.recruitment_handled = new Set();
    this.summer_tanager_screen_shown = false;
    this.tree_frog_screen_shown = false;
    this.gentian_screen_shown = false;
    this.indigo_bunting_screen_shown = false;
    this.short_screen_shown = false;
    this.turkey_beard_screen_shown = false;
    this.hurricane_occurred = false;
    this.hurricane_screen_shown = false;
    this.hurricane_years = new Set();
    this.wildfire_screen_shown = false;
    this.history = [];
  }

  maxTpaReineke(qmd, a = 4.253, b = 1.6) {
    return 10 ** (a - b * Math.log10(qmd));
  }

  growQmd(qmd, management) {
    const annualGrowth = { "1": 0.009, "2": 0.015, "3": 0.022, "4": 0.013 };
    const rate = annualGrowth[management] ?? 0.009;
    return qmd * ((1 + rate) ** 10);
  }

  applyManagementTpa(tpa, management) {
    if (management === "2") return tpa * 0.75;
    if (management === "3") return tpa * 0.50;
    if (management === "4") return tpa * 0.65;
    return tpa * 0.97;
  }

  makeSnapshot(year = this.stand.year) {
    return {
      year: pyInt(year),
      QMD: Number(this.stand.QMD) || 0,
      TPA: Math.round(Number(this.stand.TPA) || 0),
      BA: Number(this.stand.BA) || 0,
      carbon: Number(this.stand.carbon) || 0,
      CI: Number(this.stand.CI) || 0,
      fire_risk: this.stand.fire_risk,
      SPB_risk: this.stand.SPB_risk,
      events: clone(this.stand.events || [])
    };
  }

  updateStand(action) {
    let tpaNext = this.applyManagementTpa(this.stand.TPA, action);
    let qmdNext = this.growQmd(this.stand.QMD, action);
    const prevFireRisk = this.stand.fire_risk ?? null;
    let recruitedCarbonIncrease = 0.0;

    if (this.recruitment_pending.length) {
      const currBa = this.stand.BA || 0.0;
      this.recruitment_pending = this.recruitment_pending.filter((entry) => {
        const threshold = entry.threshold;
        if (threshold != null && currBa > threshold + 5) {
          this.recruitment_handled.delete(threshold);
          return false;
        }
        return true;
      });

      const baseAdd = { 70: 5, 50: 30, 40: 50, 30: 70 };
      this.recruitment_pending.forEach((entry) => {
        entry.cycles_remaining = (entry.cycles_remaining ?? 2) - 1;
      });
      const toApply = this.recruitment_pending.filter((entry) => (entry.cycles_remaining ?? 0) <= 0);
      this.recruitment_pending = this.recruitment_pending.filter((entry) => (entry.cycles_remaining ?? 0) > 0);

      for (const entry of toApply) {
        const threshold = entry.threshold ?? 70;
        const baRef = Math.max(0.1, entry.ba_at_detection ?? this.stand.BA);
        const severity = Math.max(0.0, Math.log10(threshold / baRef));
        if (severity <= 0) continue;
        const addTpa = pyInt((baseAdd[threshold] ?? 80) * (1.0 + severity));
        const qmdDropFrac = Math.min(0.90, 0.12 * (1.0 + severity) + 0.0012 * addTpa);
        tpaNext = Math.max(1, pyInt(tpaNext + addTpa));
        qmdNext = Math.max(2.0, qmdNext * (1.0 - qmdDropFrac));
        recruitedCarbonIncrease += addTpa * 0.02 * (1.0 + severity);
      }
    }

    tpaNext = Math.min(tpaNext, this.maxTpaReineke(qmdNext));
    const baNext = calculateBA(qmdNext, tpaNext);
    let carbon = this.stand.carbon;
    if (action === "1") carbon += 0.5;
    else if (action === "2") carbon *= 0.96;
    else if (action === "3") carbon *= 0.88;
    else if (action === "4") carbon *= 0.90;
    carbon = Math.min(Math.max(carbon + recruitedCarbonIncrease, 0), 40);

    let ci = this.stand.CI;
    if (["2", "3", "4"].includes(action)) ci = Math.min(60, ci + 3);
    else ci = Math.max(15, ci - 2);

    this.stand.TPA = Math.round(tpaNext);
    this.stand.QMD = pyRound(qmdNext, 2);
    this.stand.BA = pyRound(baNext, 1);
    this.stand.carbon = pyRound(carbon, 1);
    this.stand.CI = ci;
    this.stand.fire_risk = riskFromCI(ci);
    this.stand.SPB_risk = riskFromBA(baNext);

    for (const threshold of [70, 50, 40, 30]) {
      if (baNext < threshold && !this.recruitment_handled.has(threshold)) {
        this.recruitment_pending.push({
          threshold,
          ba_at_detection: baNext,
          cycles_remaining: 2
        });
        this.recruitment_handled.add(threshold);
      } else if (baNext > threshold + 5 && this.recruitment_handled.has(threshold)) {
        this.recruitment_handled.delete(threshold);
        this.recruitment_pending = this.recruitment_pending.filter((entry) => entry.threshold !== threshold);
      }
    }

    if (30 <= baNext && baNext <= 50) {
      this.suitable_tanager_ba_reached = true;
      this.suitable_bunting_ba_reached = true;
    }

    if (tpaNext <= 20) this.low_tpa_count += 1;
    else this.low_tpa_count = 0;

    if (45 <= baNext && baNext <= 70 && !this.pine_snakes_colonized && this.random() < 0.3) {
      this.pine_snakes_colonized = true;
      this.addAchievement("Pine snake", this.stand.year);
    }

    if (action === "4" && !this.gentian_colonized && this.random() < 0.2) {
      this.gentian_colonized = true;
      this.addAchievement("Gentian", this.stand.year);
    }

    if (action === "4" && baNext < 60 && !this.turkey_beard_achieved && this.random() < 0.5) {
      this.turkey_beard_achieved = true;
      this.addAchievement("Turkey Beard", this.stand.year);
    }

    let actions = this.action_history.map(([, a]) => a).concat(action);
    if (!this.summer_tanager_colonized
      && this.suitable_tanager_ba_reached
      && actions.length >= 2
      && actions.at(-1) === "1"
      && actions.at(-2) === "1"
      && this.random() < 0.4) {
      this.summer_tanager_colonized = true;
      this.addAchievement("Summer Tanager", this.stand.year);
    }

    actions = this.action_history.map(([, a]) => a).concat(action);
    if (!this.indigo_bunting_colonized
      && this.suitable_bunting_ba_reached
      && actions.length >= 2
      && actions.at(-1) === "1"
      && actions.at(-2) === "1"
      && this.random() < 0.4) {
      this.indigo_bunting_colonized = true;
      this.addAchievement("Indigo Bunting", this.stand.year);
    }

    if (45 <= baNext && baNext <= 70 && !this.short_colonized && this.random() < 0.2) {
      this.short_colonized = true;
      this.short_achieved = true;
      this.addAchievement("Shortleaf pine", this.stand.year);
    }

    if (!this.pine_barrens_tree_frog_colonized) {
      actions = this.action_history.map(([, a]) => a).concat(action);
      if (actions.length >= 4) {
        let index = actions.length - 1;
        let trailingNoMgmt = 0;
        while (index >= 0 && actions[index] === "1") {
          trailingNoMgmt += 1;
          index -= 1;
        }
        if (trailingNoMgmt >= 2 && index >= 1 && actions[index] === "4" && actions[index - 1] === "3" && this.random() < 0.8) {
          this.pine_barrens_tree_frog_colonized = true;
          this.addAchievement("Pine Barrens tree frog", this.stand.year);
        }
      }
    }

    let hurricaneOccurred = false;
    const priorHurricaneExists = (this.stand.events || []).some((event) => eventMatches(event, "Hurricane passed through"));
    let currYear = this.stand.year;
    let hurricaneOffset = 1;
    if (!this.hurricane_occurred && !priorHurricaneExists && this.random() < 0.05) {
      const preSnapshot = this.makeSnapshot(currYear);
      hurricaneOffset = this.randint(2, 9);
      const postYear = pyInt(currYear) + hurricaneOffset;
      const newTpa = pyInt(Math.max(1, Math.round(this.stand.TPA * 0.8)));
      this.stand.TPA = newTpa;
      this.stand.carbon = pyRound(Math.max(0.0, this.stand.carbon * 0.9), 1);
      const baAfter = calculateBA(this.stand.QMD, newTpa);
      this.stand.BA = pyRound(baAfter, 1);
      this.stand.SPB_risk = riskFromBA(baAfter);
      const ciAfter = Math.min(60, Math.round(this.stand.CI) + 1);
      this.stand.CI = ciAfter;
      this.stand.fire_risk = riskFromCI(ciAfter);
      if (!this.stand.events.some((event) => eventMatches(event, "Hurricane passed through", postYear))) {
        this.stand.events.push([postYear, "Hurricane passed through"]);
      }
      this.hurricane_years.add(postYear);
      this.hurricane_occurred = true;
      this.history.push(preSnapshot, this.makeSnapshot(postYear));
      hurricaneOccurred = true;
    }

    let wildfireOccurred = false;
    currYear = this.stand.year;
    if (action === "4" && prevFireRisk === "High" && this.random() < 0.5) {
      const preSnapshot = this.makeSnapshot(currYear);
      const postYear = pyInt(currYear) + 1;
      const newTpa = pyInt(Math.max(1, Math.round(this.stand.TPA * 0.5)));
      this.stand.TPA = newTpa;
      this.stand.carbon = pyRound(Math.max(0.0, this.stand.carbon * 0.6), 1);
      const baAfter = calculateBA(this.stand.QMD, newTpa);
      this.stand.BA = pyRound(baAfter, 1);
      this.stand.SPB_risk = riskFromBA(baAfter);
      const ciAfter = Math.min(60, Math.round(this.stand.CI) + 3);
      this.stand.CI = ciAfter;
      this.stand.fire_risk = riskFromCI(ciAfter);
      if (!this.stand.events.some((event) => eventMatches(event, "WILDFIRE", postYear))) {
        this.stand.events.push([postYear, "WILDFIRE"]);
      }
      if (!this.stand.events.some((event) => eventMatches(event, "WILDFIRE", currYear))) {
        this.stand.events.push([currYear, "WILDFIRE"]);
      }
      preSnapshot.events = clone(this.stand.events);
      this.history.push(preSnapshot, this.makeSnapshot(postYear));
      wildfireOccurred = true;
    }

    this.action_history.push([this.stand.year, action]);

    if (hurricaneOccurred) {
      const postActionYear = pyInt(currYear) + hurricaneOffset;
      if (!this.action_history.some(([year, act]) => year === postActionYear && act === "HURRICANE")) {
        this.action_history.push([postActionYear, "HURRICANE"]);
      }
      return;
    }

    if (wildfireOccurred) {
      const postActionYear = pyInt(currYear) + 1;
      if (!this.action_history.some(([year, act]) => year === postActionYear && act === "WILDFIRE")) {
        this.action_history.push([postActionYear, "WILDFIRE"]);
      }
      return;
    }

    this.history.push(this.makeSnapshot(this.stand.year));
  }

  isLowTpaGameOver() {
    return (this.low_tpa_count ?? 0) >= 1;
  }

  simulateEvent() {
    let eventLog = null;
    if (this.random() < 0.15 && this.stand.fire_risk === "High") {
      this.stand.carbon *= 0.6;
      this.stand.TPA = pyInt(this.stand.TPA * 0.4);
      this.stand.CI += 15;
      eventLog = "Wildfire occurred!";
      this.stand.catastrophic_wildfire = true;
    } else {
      this.stand.catastrophic_wildfire = false;
    }

    if (!eventLog && this.random() < 0.10 && this.stand.SPB_risk === "High") {
      this.stand.TPA = pyInt(this.stand.TPA * 0.7);
      this.stand.BA *= 0.8;
      eventLog = "SPB outbreak!";
    }

    if (eventLog) {
      this.stand.events.push([this.stand.year, eventLog]);
      return eventLog;
    }
    return null;
  }

  getStatus() {
    return `Year: ${this.stand.year} | QMD: ${this.stand.QMD.toFixed(1)} | TPA: ${this.stand.TPA} | BA: ${this.stand.BA.toFixed(1)} | Carbon: ${this.stand.carbon.toFixed(1)} MT/ac | CI: ${Number(this.stand.CI).toFixed(1)} | Fire Risk: ${this.stand.fire_risk} | SPB Risk: ${this.stand.SPB_risk}`;
  }

  getStatusDict() {
    return {
      year: this.stand.year,
      QMD: this.stand.QMD,
      TPA: this.stand.TPA,
      BA: this.stand.BA,
      carbon: this.stand.carbon,
      CI: this.stand.CI,
      fire_risk: this.stand.fire_risk,
      SPB_risk: this.stand.SPB_risk
    };
  }

  getSummary() {
    let summary = `Final Stand: QMD: ${this.stand.QMD.toFixed(1)}, TPA: ${this.stand.TPA}, BA: ${this.stand.BA.toFixed(1)}, Carbon: ${this.stand.carbon.toFixed(1)} MT/ac, CI: ${this.stand.CI}, Fire Risk: ${this.stand.fire_risk}, SPB Risk: ${this.stand.SPB_risk}\n\n`;
    if (this.stand.events.length) {
      summary += "Events during your management:\n";
      for (const [year, event] of this.stand.events) summary += `  Year ${year}: ${event}\n`;
    } else {
      summary += "No major events occurred during your management.\n";
    }
    if (this.pine_snakes_colonized) summary += "\nPine snakes are utilizing this stand!\n";
    if (this.short_colonized) summary += "\nShortleaf pine has established in this stand!\n";
    if (this.gentian_colonized) summary += "\nGentian is now growing in this stand!\n";
    if (this.summer_tanager_colonized) summary += "\nSummer tanager has colonized this stand!\n";
    if (this.indigo_bunting_colonized) summary += "\nIndigo bunting has colonized this stand!\n";
    if (this.pine_barrens_tree_frog_colonized) summary += "\nPine Barrens tree frog has colonized this stand!\n";
    if (this.turkey_beard_achieved) summary += "\nTurkey Beard is now growing in this stand!\n";
    return summary;
  }

  addAchievement(name, year = null) {
    const yr = year == null ? pyInt(this.stand.year) : pyInt(year);
    if (this.achievements_history.some(([, n]) => n === name)) return;
    this.achievements_history.push([yr, name]);
  }

  getAchievementsList() {
    return [...this.achievements_history].sort((a, b) => a[0] - b[0]);
  }

  getActionSummary() {
    if (!this.action_history.length) return "No actions taken.";
    return this.action_history.map(([year, action]) => `Year ${year}: ${ACTIONS[String(action)] ?? String(action)}`).join("\n");
  }

  getDecadalData(interval = 10) {
    let snapshots;
    if (!this.history.length) {
      snapshots = [this.makeSnapshot(this.stand.year)];
    } else {
      snapshots = this.history.map((entry) => clone(entry));
      const currYear = pyInt(this.stand.year);
      if (!snapshots.some((entry) => entry.year === currYear)) {
        snapshots.push(this.makeSnapshot(currYear));
      }
    }

    if (this.initial_stand && !snapshots.some((entry) => entry.year === -1)) {
      snapshots.push({
        year: -1,
        QMD: Number(this.initial_stand.QMD) || 0,
        TPA: Math.round(Number(this.initial_stand.TPA) || 0),
        BA: Number(this.initial_stand.BA) || 0,
        carbon: Number(this.initial_stand.carbon) || 0,
        CI: Number(this.initial_stand.CI) || 0,
        fire_risk: this.initial_stand.fire_risk,
        SPB_risk: this.initial_stand.SPB_risk,
        events: clone(this.initial_stand.events || [])
      });
    }

    const yearMap = new Map();
    for (const snapshot of snapshots) yearMap.set(pyInt(snapshot.year), snapshot);
    const baseYears = new Set([...yearMap.keys()].filter((year) => year === -1 || interval === 1 || year % interval === 0));
    const decadalBases = [...yearMap.keys()].filter((year) => year !== -1 && interval !== 1 && year % interval === 0);
    const extraYears = new Set();
    for (const year of yearMap.keys()) {
      if (baseYears.has(year)) continue;
      if (decadalBases.some((base) => base < year && year <= base + interval - 1)) extraYears.add(year);
    }

    return [...new Set([...baseYears, ...extraYears])]
      .sort((a, b) => a - b)
      .map((year) => {
        const snapshot = yearMap.get(year) || {};
        return {
          year: year === -1 ? "Start" : year,
          QMD: snapshot.QMD,
          TPA: snapshot.TPA,
          BA: snapshot.BA,
          carbon: snapshot.carbon,
          CI: snapshot.CI,
          fireRisk: snapshot.fire_risk,
          spbRisk: snapshot.SPB_risk,
          events: snapshot.events || []
        };
      });
  }
}
