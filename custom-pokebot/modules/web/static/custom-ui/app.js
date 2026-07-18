/* PokéBot Dashboard — talks to the bot's own HTTP API (same origin).
   Endpoints and SSE topics documented in:
   40cakes repo/DOCUMENTATION/04-interfaces-gui-web-streaming.md */

"use strict";

const API = ""; // same origin

// ---------- tiny helpers ----------
const $ = (id) => document.getElementById(id);

async function getJson(path) {
  const response = await fetch(API + path);
  if (!response.ok) throw new Error(`${path} -> ${response.status}`);
  return response.json();
}

async function postJson(path, payload) {
  const response = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`${path} -> ${response.status}: ${await response.text()}`);
  return response.status === 204 ? null : response.json();
}

function logEvent(text, highlight = false) {
  const list = $("event-log");
  const item = document.createElement("li");
  const time = document.createElement("span");
  time.className = "event-time";
  time.textContent = new Date().toLocaleTimeString();
  const body = document.createElement("span");
  body.className = "event-text" + (highlight ? " highlight" : "");
  body.textContent = text;
  item.append(time, body);
  list.prepend(item);
  while (list.children.length > 100) list.removeChild(list.lastChild);
}

// ---------- state ----------
const state = {
  botMode: null,
  emulationSpeed: null,
  video: true,
  audio: true,
  heldButtons: new Set(),
};

// ---------- emulator status / controls ----------
function renderEmulator(info) {
  if (!info) return;
  state.botMode = info.bot_mode;
  state.emulationSpeed = info.emulation_speed;
  state.video = info.video_enabled;
  state.audio = info.audio_enabled;

  $("profile-line").textContent =
    `${info.profile?.name ?? "?"} · ${info.game?.name ?? info.game?.title ?? "?"}`;
  if (typeof info.current_fps === "number") {
    $("fps-label").textContent = `${info.current_fps} fps`;
  }
  $("bot-message").textContent = info.current_message ?? "";

  const select = $("mode-select");
  if (select.value !== info.bot_mode && !select.matches(":focus")) select.value = info.bot_mode;
  renderSpeed();
  renderToggles();
  renderPadEnabled();
}

function renderSpeed() {
  document.querySelectorAll("#speed-buttons .btn").forEach((btn) => {
    btn.classList.toggle("active", Number(btn.dataset.value) === state.emulationSpeed);
  });
}

function renderToggles() {
  $("toggle-video").classList.toggle("off", !state.video);
  $("toggle-audio").classList.toggle("off", !state.audio);
  $("video-overlay").classList.toggle("hidden", state.video);
}

function renderPadEnabled() {
  $("manual-pad").classList.toggle("enabled", state.botMode === "Manual");
}

async function setupControls() {
  // Speed buttons
  const speedBox = $("speed-buttons");
  for (const value of speedBox.dataset.values.split(",").map(Number)) {
    const btn = document.createElement("button");
    btn.className = "btn";
    btn.dataset.value = String(value);
    btn.textContent = value === 0 ? "MAX" : `${value}×`;
    btn.addEventListener("click", () =>
      postJson("/emulator", { emulation_speed: value }).then(renderEmulator).catch(reportError)
    );
    speedBox.append(btn);
  }

  $("toggle-video").addEventListener("click", () =>
    postJson("/emulator", { video_enabled: !state.video }).then(renderEmulator).catch(reportError)
  );
  $("toggle-audio").addEventListener("click", () =>
    postJson("/emulator", { audio_enabled: !state.audio }).then(renderEmulator).catch(reportError)
  );
  $("btn-enable-video").addEventListener("click", () =>
    postJson("/emulator", { video_enabled: true }).then(renderEmulator).catch(reportError)
  );

  // Bot mode dropdown
  try {
    const modes = await getJson("/bot_modes");
    const select = $("mode-select");
    select.innerHTML = "";
    for (const mode of modes) {
      const option = document.createElement("option");
      option.value = mode;
      option.textContent = mode;
      select.append(option);
    }
    select.addEventListener("change", () =>
      postJson("/emulator", { bot_mode: select.value })
        .then((info) => {
          renderEmulator(info);
          logEvent(`Bot mode set to ${select.value}`);
        })
        .catch(reportError)
    );
  } catch (error) {
    reportError(error);
  }

  // Manual controller pad: hold-to-press semantics via POST /input
  // (works only in Manual mode; the API silently ignores it otherwise).
  const sendHeld = () => postJson("/input", [...state.heldButtons]).catch(() => {});
  document.querySelectorAll(".pad-btn").forEach((btn) => {
    const name = btn.dataset.button;
    const press = (event) => {
      event.preventDefault();
      state.heldButtons.add(name);
      btn.classList.add("held");
      sendHeld();
    };
    const release = () => {
      if (!state.heldButtons.has(name)) return;
      state.heldButtons.delete(name);
      btn.classList.remove("held");
      sendHeld();
    };
    btn.addEventListener("pointerdown", press);
    btn.addEventListener("pointerup", release);
    btn.addEventListener("pointerleave", release);
    btn.addEventListener("pointercancel", release);
  });
}

function reportError(error) {
  console.error(error);
  logEvent(`Error: ${error.message}`);
}

// ---------- party ----------
function hpClass(fraction) {
  if (fraction <= 0.2) return "low";
  if (fraction <= 0.5) return "mid";
  return "";
}

function renderParty(party) {
  const list = $("party-list");
  list.innerHTML = "";
  if (!Array.isArray(party) || party.length === 0) {
    list.innerHTML = '<li class="muted">Party is empty.</li>';
    return;
  }
  for (const pokemon of party) {
    const item = document.createElement("li");
    item.className = "party-member";

    if (pokemon.is_egg) {
      item.innerHTML = '<span class="pm-name pm-egg">Egg</span><span class="pm-level"></span>';
      list.append(item);
      continue;
    }

    const name = pokemon.name ?? pokemon.species?.name ?? "?";
    const level = pokemon.level ?? "?";
    const currentHp = pokemon.current_hp ?? 0;
    const totalHp = pokemon.total_hp ?? pokemon.stats?.hp ?? 0;
    const fraction = totalHp > 0 ? currentHp / totalHp : 0;
    const status = pokemon.status_condition && pokemon.status_condition !== "Healthy"
      ? pokemon.status_condition
      : null;

    const nameEl = document.createElement("span");
    nameEl.className = "pm-name";
    nameEl.textContent = name;
    if (pokemon.is_shiny) {
      const badge = document.createElement("span");
      badge.className = "shiny-badge";
      badge.textContent = "✨ shiny";
      nameEl.append(badge);
    }

    const levelEl = document.createElement("span");
    levelEl.className = "pm-level";
    levelEl.textContent = `Lv ${level}`;

    const hpRow = document.createElement("span");
    hpRow.className = "pm-hp-row";
    const bar = document.createElement("span");
    bar.className = "hp-bar";
    const fill = document.createElement("span");
    fill.className = `hp-fill ${hpClass(fraction)}`;
    fill.style.width = `${Math.max(0, Math.min(100, fraction * 100))}%`;
    bar.append(fill);
    const hpText = document.createElement("span");
    hpText.className = "pm-hp-text";
    hpText.textContent = `${currentHp}/${totalHp}`;
    hpRow.append(bar, hpText);
    if (status) {
      const statusEl = document.createElement("span");
      statusEl.className = "pm-status";
      statusEl.textContent = status;
      hpRow.append(statusEl);
    }

    item.append(nameEl, levelEl, hpRow);
    list.append(item);
  }
}

// ---------- opponent ----------
function renderOpponent(opponent) {
  const card = $("opponent-card");
  const body = $("opponent-body");
  if (!opponent) {
    card.hidden = true;
    body.innerHTML = "";
    return;
  }
  card.hidden = false;
  const name = opponent.name ?? opponent.species?.name ?? "?";
  const ivs = opponent.ivs
    ? Object.values(opponent.ivs).reduce((sum, iv) => sum + (Number(iv) || 0), 0)
    : null;
  body.innerHTML = "";
  const head = document.createElement("div");
  head.className = "opp-head";
  const nameEl = document.createElement("span");
  nameEl.className = "opp-name";
  nameEl.textContent = name;
  head.append(nameEl);
  if (opponent.is_shiny) {
    const shiny = document.createElement("span");
    shiny.className = "opp-shiny";
    shiny.textContent = "✨ SHINY";
    head.append(shiny);
  }
  const detail = document.createElement("div");
  detail.className = "opp-detail";
  const parts = [`Lv ${opponent.level ?? "?"}`];
  if (opponent.nature?.name ?? opponent.nature) parts.push(`${opponent.nature?.name ?? opponent.nature} nature`);
  if (ivs !== null) parts.push(`IV sum ${ivs}`);
  if (typeof opponent.shiny_value === "number") parts.push(`SV ${opponent.shiny_value}`);
  detail.textContent = parts.join(" · ");
  body.append(head, detail);
}

// ---------- stats ----------
function renderStats(stats) {
  if (!stats) return;
  const totals = stats.totals ?? stats;
  const total = totals.total_encounters ?? totals.encounters;
  const shinies = totals.shiny_encounters;
  if (typeof total === "number") $("kpi-total").textContent = total.toLocaleString();
  if (typeof shinies === "number") $("kpi-shinies").textContent = shinies.toLocaleString();
  const phase = stats.current_phase?.encounters ?? stats.phase?.encounters;
  if (typeof phase === "number") $("kpi-phase").textContent = phase.toLocaleString();
}

async function refreshStats() {
  try {
    renderStats(await getJson("/stats"));
  } catch { /* stats may be unavailable early on */ }
  try {
    const { encounter_rate } = await getJson("/encounter_rate");
    if (typeof encounter_rate === "number") $("kpi-rate").textContent = encounter_rate.toLocaleString();
  } catch { /* ignore */ }
}

// ---------- map / location ----------
function renderLocation(mapData) {
  const map = mapData?.map ?? mapData;
  const name = map?.pretty_name ?? map?.name;
  const coords = mapData?.player_position ?? mapData?.local_position;
  let text = name ?? "";
  if (Array.isArray(coords)) text += ` (${coords[0]}, ${coords[1]})`;
  if (text) $("location-label").textContent = text;
}

// ---------- SSE ----------
const SSE_TOPICS = [
  "Party", "Opponent", "GameState", "BotMode", "Message",
  "WildEncounter", "Map", "EmulatorSettings", "PerformanceData",
];

function connectStream() {
  const query = SSE_TOPICS.map((topic) => `topic=${topic}`).join("&");
  const source = new EventSource(`${API}/stream_events?${query}`);
  const indicator = $("conn-indicator");

  source.onopen = () => {
    indicator.className = "conn ok";
    $("conn-label").textContent = "live";
  };
  source.onerror = () => {
    indicator.className = "conn err";
    $("conn-label").textContent = "reconnecting…";
  };

  const on = (type, handler) =>
    source.addEventListener(type, (event) => {
      let data = null;
      try { data = JSON.parse(event.data); } catch { data = event.data; }
      handler(data);
    });

  on("Party", renderParty);
  on("Opponent", renderOpponent);
  on("GameState", (gameState) => { $("game-state-label").textContent = gameState ?? "—"; });
  on("BotMode", (mode) => {
    state.botMode = mode;
    const select = $("mode-select");
    if (select.value !== mode && !select.matches(":focus")) select.value = mode;
    renderPadEnabled();
  });
  on("Message", (message) => { $("bot-message").textContent = message ?? ""; });
  on("WildEncounter", (encounter) => {
    const pokemon = encounter?.pokemon ?? encounter;
    const name = pokemon?.name ?? pokemon?.species?.name ?? "?";
    const shiny = Boolean(pokemon?.is_shiny);
    logEvent(`Encounter: ${name}${shiny ? " — ✨ SHINY! ✨" : ""}`, shiny);
    refreshStats();
  });
  on("MapChange", (map) => { renderLocation({ map }); logEvent(`Map: ${map?.pretty_name ?? map?.name ?? "?"}`); });
  on("MapTileChange", (coords) => renderLocation({ player_position: coords }));
  on("EmulationSpeed", (speed) => { state.emulationSpeed = speed; renderSpeed(); });
  on("VideoEnabled", (enabled) => { state.video = enabled; renderToggles(); });
  on("AudioEnabled", (enabled) => { state.audio = enabled; renderToggles(); });
  on("PerformanceData", (perf) => {
    if (perf && typeof perf.fps === "number") $("fps-label").textContent = `${perf.fps} fps`;
  });
}

// ---------- boot ----------
async function boot() {
  $("video-stream").src = `${API}/stream_video?fps=30`;
  await setupControls();
  try {
    renderEmulator(await getJson("/emulator"));
  } catch (error) {
    reportError(error);
  }
  try {
    renderParty(await getJson("/party"));
  } catch { /* no party yet */ }
  try {
    $("game-state-label").textContent = await getJson("/game_state");
  } catch { /* ignore */ }
  try {
    renderLocation(await getJson("/map"));
  } catch { /* not in overworld */ }
  refreshStats();
  setInterval(refreshStats, 30000);
  connectStream();
  logEvent("Dashboard connected.");
}

boot();
