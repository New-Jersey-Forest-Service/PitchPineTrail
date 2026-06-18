const ASSET_BASE = "../src/assets/";

const loops = new Map();

function src(name) {
  return `${ASSET_BASE}${name}`;
}

function playOne(name, volume = 1) {
  try {
    const audio = new Audio(src(name));
    audio.volume = volume;
    audio.play().catch(() => {});
    return audio;
  } catch {
    return null;
  }
}

function playLoop(key, name, volume = 1) {
  stopLoop(key);
  try {
    const audio = new Audio(src(name));
    audio.volume = volume;
    audio.loop = true;
    audio.play().catch(() => {});
    loops.set(key, audio);
    return audio;
  } catch {
    return null;
  }
}

function stopLoop(key) {
  const audio = loops.get(key);
  if (audio) {
    audio.pause();
    audio.currentTime = 0;
    loops.delete(key);
  }
}

export function stopAllLoops() {
  for (const key of [...loops.keys()]) stopLoop(key);
}

export const sounds = {
  playForestSound: () => playLoop("forest", "forest_sound.wav", 0.7),
  stopForestSound: () => stopLoop("forest"),
  playFireSound: () => playLoop("fire", "fire.wav", 0.85),
  stopFireSound: () => stopLoop("fire"),
  playSpbEatingSound: () => playLoop("spb", "SPB_eating.wav", 0.75),
  stopSpbEatingSound: () => stopLoop("spb"),
  playWindSound: () => playLoop("wind", "wind.wav", 0.75),
  stopWindSound: () => stopLoop("wind"),
  playTreeFrogSound: () => playLoop("treefrog", "treefrog.wav", 0.7),
  stopTreeFrogSound: () => stopLoop("treefrog"),
  playHurricaneSound: () => playLoop("hurricane", "hurricane.wav", 0.85),
  stopHurricaneSound: () => stopLoop("hurricane"),
  playAnalysisLabSound: () => playLoop("analysis", "analysis_lab.wav", 0.7),
  stopAnalysisLabSound: () => stopLoop("analysis"),
  playTrumpetWinSound: () => playOne("trumpet_win.wav"),
  playLosingTromboneSound: () => playOne("losing_trombone.wav"),
  playPineSnakeSound: () => playOne("pine_snake.wav"),
  playPageTurnSound: () => playOne("page_turn.wav"),
  playPageCloseSound: () => playOne("page_close.wav"),
  playZoomSound: () => playOne("zoom.wav"),
  playHintOpenSound: () => playOne("hintopen.wav"),
  playHintCloseSound: () => playOne("hintclose.wav"),
  playDoNothingSound: () => playOne("do_nothing.wav"),
  playThinLightlySound: () => playOne("thin_lightly.wav"),
  playThinHeavilySound: () => playOne("thin_heavily.wav"),
  playPrescribedBurnSound: () => playOne("prescribed_burn.wav"),
  playLetsPlaySound: () => playOne("lets_play.wav"),
  playGentianSound: () => playOne("gentian.wav"),
  playTanagerSound: () => playOne("tanager.wav"),
  playBuntingSound: () => playOne("bunting.wav"),
  playSaveSound: () => playOne("save.wav"),
  playComputerStartup: () => playOne("computer_startup.wav"),
  playComputerShutdown: () => playOne("computer_shutdown.wav")
};
