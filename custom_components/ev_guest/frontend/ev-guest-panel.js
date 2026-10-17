/* EV Guest – panel for Home Assistant. No build step, no dependencies. */

const TEXT = {
  da: {
    tab_charge: "Opladning",
    tab_history: "Historik",
    tab_settings: "Indstillinger",
    loading: "Henter EV Guest …",
    guest: "Gæstebil",
    plate_placeholder: "AB 12 345",
    lookup: "Slå op",
    looking_up: "Slår op …",
    lookup_needs_key: "Opslag på nummerplade kræver en gratis MotorAPI-nøgle.",
    add_key: "Tilføj nøgle",
    no_car: "Skriv nummerpladen og slå bilen op – eller sæt batteriet selv herunder.",
    battery: "Batteri",
    match: "Match",
    match_hint: "Hvor sikkert batteriet passer til bilen",
    model_year: "Årgang",
    charge: "Opladning",
    now_level: "Nu",
    target: "Mål",
    add_energy: "{kwh} i batteriet",
    charger: "Ladeeffekt",
    custom: "Andet",
    ready_by: "Klar kl.",
    no_deadline: "Ingen frist",
    mode: "Plan",
    continuous: "Én periode",
    split: "Billigste perioder",
    calculate: "Beregn plan",
    recalculate: "Beregn igen",
    calculating: "Beregner …",
    new_guest: "Ny gæst",
    preview: "Forslag",
    changed: "Inputtet er ændret. Beregn igen for at bruge det.",
    price_now: "pr. kWh nu",
    cheapest_at: "Billigst kl. {time}",
    no_prices: "Ingen priser",
    save: "Du sparer {amount}",
    save_vs: "i forhold til at lade med det samme",
    start: "Start",
    end: "Slut",
    duration: "Tid",
    energy: "Energi",
    cost: "Pris",
    savings: "Besparelse",
    speed: "Hastighed",
    measured: "Målt",
    measured_cost: "Målt pris",
    starts_in: "Starter om {time}",
    charging_until: "Lader – færdig kl. {time}",
    paused_until: "Pause – lader igen kl. {time}",
    completed_at: "Færdig kl. {time}",
    unplugged_at: "Bilen blev koblet fra kl. {time} – laderen er frigivet",
    status_ready: "Klar til en plan",
    status_planned: "Planlagt",
    status_charging: "Lader",
    status_completed: "Afsluttet",
    est_level: "ca. {pct} nu",
    est_level_measured: "ca. {pct} nu, målt",
    behind_plan: "Bilen lader langsommere end planlagt – den når måske ikke målet.",
    prices_title: "Elpris de næste døgn",
    today: "I dag",
    tomorrow: "I morgen",
    day_after: "Overmorgen",
    charging_window: "Opladning",
    deadline: "Frist",
    now: "Nu",
    per_kwh: "pr. kWh",
    history_empty: "Afsluttede opladninger kommer her, med energi og pris – klar til at afregne med gæsten.",
    sessions: "{n} opladninger",
    session: "1 opladning",
    total_energy: "Energi i alt",
    total_cost: "Pris i alt",
    total_saved: "Sparet i alt",
    bill: "Afregn",
    delete: "Slet",
    delete_all: "Slet hele historikken",
    confirm_delete_all: "Slet alle afsluttede opladninger?",
    unknown_car: "Ukendt bil",
    bill_title: "Afregning",
    bill_text_intro: "Opladning af {car}",
    bill_line_energy: "Energi: {kwh}",
    bill_line_price: "Pris: {amount}",
    bill_line_rate: "({rate} pr. kWh)",
    bill_line_date: "Dato: {date}",
    copy: "Kopiér",
    copied: "Kopieret",
    share: "Del",
    close: "Luk",
    by_actual: "Faktisk elpris",
    by_rate: "Fast pris pr. kWh",
    settings_billing: "Afregning med gæster",
    bill_rate: "Pris pr. kWh",
    bill_rate_hint: "Tom: brug den faktiske elpris fra planen eller elmåleren.",
    payment_text: "Betalingsoplysninger",
    payment_hint: "Kommer med i afregningen, fx MobilePay-nummer.",
    settings_charging: "Opladning",
    efficiency: "Ladeeffektivitet",
    efficiency_hint: "Andelen af strømmen, der ender i batteriet. 90 % passer til de fleste biler.",
    settings_sources: "Datakilder",
    price_sensor: "Prissensor",
    energy_meter: "Elmåler",
    not_set: "Ikke valgt",
    plate_lookup: "Nummerpladeopslag",
    on: "Til",
    off: "Fra",
    change_in_ha: "Skift under Indstillinger → Enheder og tjenester → EV Guest.",
    open_integration: "Åbn integrationen",
    app_title: "App på hjemmeskærmen",
    app_hint: "Åbn linket på telefonen og vælg Føj til hjemmeskærm.",
    open_app: "Åbn app",
    saved: "Gemt",
    err_invalid_input: "Batterikapacitet og ladeeffekt skal være over 0.",
    err_limit_not_above_soc: "Målet skal være højere end bilens ladeniveau nu.",
    err_no_price_data: "Prissensoren har ingen priser lige nu.",
    err_not_enough_prices: "Der er endnu ikke priser nok før fristen. EV Guest beregner selv, når priserne kommer (typisk efter kl. 13).",
    err_no_window: "Opladningen kan ikke nå at blive færdig før fristen. Hæv ladeeffekten, sænk målet eller flyt fristen.",
    err_license_plate_required: "Skriv en nummerplade først.",
    err_motorapi_key_missing: "Opslag kræver en MotorAPI-nøgle.",
    err_invalid_api_key: "MotorAPI afviste nøglen. Home Assistant beder dig om en ny.",
    err_vehicle_not_found: "Der findes ingen bil med den nummerplade.",
    err_lookup_failed: "Opslaget fejlede. Prøv igen om lidt.",
    err_entry_not_found: "EV Guest er ikke sat op.",
    err_unknown: "Noget gik galt: {detail}",
    hours_short: "t",
    minutes_short: "min",
  },
  en: {
    tab_charge: "Charging",
    tab_history: "History",
    tab_settings: "Settings",
    loading: "Loading EV Guest …",
    guest: "Guest car",
    plate_placeholder: "AB 12 345",
    lookup: "Look up",
    looking_up: "Looking up …",
    lookup_needs_key: "License plate lookup needs a free MotorAPI key.",
    add_key: "Add key",
    no_car: "Enter the license plate and look up the car – or set the battery yourself below.",
    battery: "Battery",
    match: "Match",
    match_hint: "How sure the battery match is",
    model_year: "Year",
    charge: "Charging",
    now_level: "Now",
    target: "Target",
    add_energy: "{kwh} into the battery",
    charger: "Charger power",
    custom: "Other",
    ready_by: "Ready by",
    no_deadline: "No deadline",
    mode: "Plan",
    continuous: "One period",
    split: "Cheapest periods",
    calculate: "Make plan",
    recalculate: "Plan again",
    calculating: "Planning …",
    new_guest: "New guest",
    preview: "Preview",
    changed: "The inputs changed. Plan again to use them.",
    price_now: "per kWh now",
    cheapest_at: "Cheapest at {time}",
    no_prices: "No prices",
    save: "You save {amount}",
    save_vs: "compared with charging right away",
    start: "Start",
    end: "End",
    duration: "Time",
    energy: "Energy",
    cost: "Cost",
    savings: "Savings",
    speed: "Speed",
    measured: "Measured",
    measured_cost: "Measured cost",
    starts_in: "Starts in {time}",
    charging_until: "Charging – done at {time}",
    paused_until: "Paused – charging again at {time}",
    completed_at: "Done at {time}",
    unplugged_at: "The car was unplugged at {time} – the charger is released",
    status_ready: "Ready for a plan",
    status_planned: "Planned",
    status_charging: "Charging",
    status_completed: "Completed",
    est_level: "about {pct} now",
    est_level_measured: "about {pct} now, measured",
    behind_plan: "The car charges slower than planned – it may not reach the target.",
    prices_title: "Electricity price, the next days",
    today: "Today",
    tomorrow: "Tomorrow",
    day_after: "Day after",
    charging_window: "Charging",
    deadline: "Deadline",
    now: "Now",
    per_kwh: "per kWh",
    history_empty: "Finished charges show up here, with energy and cost – ready to settle up with your guest.",
    sessions: "{n} charges",
    session: "1 charge",
    total_energy: "Total energy",
    total_cost: "Total cost",
    total_saved: "Total saved",
    bill: "Bill",
    delete: "Delete",
    delete_all: "Delete all history",
    confirm_delete_all: "Delete all finished charges?",
    unknown_car: "Unknown car",
    bill_title: "Bill",
    bill_text_intro: "Charging of {car}",
    bill_line_energy: "Energy: {kwh}",
    bill_line_price: "Price: {amount}",
    bill_line_rate: "({rate} per kWh)",
    bill_line_date: "Date: {date}",
    copy: "Copy",
    copied: "Copied",
    share: "Share",
    close: "Close",
    by_actual: "Actual electricity price",
    by_rate: "Fixed price per kWh",
    settings_billing: "Billing guests",
    bill_rate: "Price per kWh",
    bill_rate_hint: "Empty: use the actual price from the plan or the energy meter.",
    payment_text: "Payment details",
    payment_hint: "Added to the bill, e.g. a phone number for payment.",
    settings_charging: "Charging",
    efficiency: "Charging efficiency",
    efficiency_hint: "The share of the energy that ends up in the battery. 90 % suits most cars.",
    settings_sources: "Data sources",
    price_sensor: "Price sensor",
    energy_meter: "Energy meter",
    not_set: "Not set",
    plate_lookup: "License plate lookup",
    on: "On",
    off: "Off",
    change_in_ha: "Change under Settings → Devices & services → EV Guest.",
    open_integration: "Open the integration",
    app_title: "App on the home screen",
    app_hint: "Open the link on your phone and choose Add to Home Screen.",
    open_app: "Open app",
    saved: "Saved",
    err_invalid_input: "Battery capacity and charger power must be above 0.",
    err_limit_not_above_soc: "The target must be above the car's charge level now.",
    err_no_price_data: "The price sensor has no prices right now.",
    err_not_enough_prices: "Not enough prices before the deadline yet. EV Guest plans by itself when they arrive (usually after 13:00).",
    err_no_window: "Charging can't finish before the deadline. Raise the charger power, lower the target or move the deadline.",
    err_license_plate_required: "Enter a license plate first.",
    err_motorapi_key_missing: "Lookup needs a MotorAPI key.",
    err_invalid_api_key: "MotorAPI rejected the key. Home Assistant asks you for a new one.",
    err_vehicle_not_found: "No car has that license plate.",
    err_lookup_failed: "The lookup failed. Try again shortly.",
    err_entry_not_found: "EV Guest is not set up.",
    err_unknown: "Something went wrong: {detail}",
    hours_short: "h",
    minutes_short: "min",
  },
};

const CHARGER_PRESETS = [3.7, 7.4, 11, 22];
const DEADLINE_PRESETS = ["06:00", "07:00", "08:00"];
const ENTRY_KEY = "ev-guest-entry";
const PREVIEW_DELAY = 140;
const SVGNS = "http://www.w3.org/2000/svg";

const ICONS = {
  charge: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M13 2.5 6 13.2h5.2L10 21.5l7-10.7h-5.2z"/></svg>',
  history: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/></svg>',
  settings: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h9M17 7h3M4 17h3M11 17h9"/><circle cx="15" cy="7" r="2"/><circle cx="9" cy="17" r="2"/></svg>',
  search: '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/></svg>',
  plus: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
  trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h14M10 7V5h4v2M7 7l1 12h8l1-12"/></svg>',
  receipt: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6"/></svg>',
  copy: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="8" y="8" width="11" height="12" rx="2"/><path d="M5 15V5a1 1 0 0 1 1-1h9"/></svg>',
  share: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V4M8 8l4-4 4 4M5 13v6h14v-6"/></svg>',
  close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>',
};

const MARK = `<svg viewBox="19 19 218 218" aria-hidden="true">
  <defs><linearGradient id="evg-mark" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#00B894"/><stop offset="1" stop-color="#A3E635"/></linearGradient></defs>
  <circle cx="128" cy="128" r="96" fill="none" stroke="currentColor" stroke-opacity=".22" stroke-width="22"/>
  <path class="mark-arc" d="M224 128 A96 96 0 0 1 80 211.1" fill="none" stroke="url(#evg-mark)" stroke-width="22" stroke-linecap="round"/>
  <circle cx="80" cy="211.1" r="16" fill="#A3E635"/>
  <path d="M141 50 L84 140 H124 L111 206 L172 112 H132 Z" fill="url(#evg-mark)" stroke="url(#evg-mark)" stroke-width="8" stroke-linejoin="round"/>
</svg>`;

const esc = (value) =>
  String(value ?? "").replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch]);
const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

/* Price colour: cheap teal, middle sand, expensive coral – relative to the shown prices. */
function priceColor(t) {
  const stops = [
    [0, [0, 184, 148]],
    [0.5, [233, 185, 73]],
    [1, [228, 87, 46]],
  ];
  t = clamp(Number.isFinite(t) ? t : 0.5, 0, 1);
  const i = t <= 0.5 ? 0 : 1;
  const [t0, c0] = stops[i];
  const [t1, c1] = stops[i + 1];
  const k = (t - t0) / (t1 - t0);
  const c = c0.map((v, j) => Math.round(v + (c1[j] - v) * k));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

/* A point on a circle; 0 h is at the top, like a 24-hour clock. */
function polar(cx, cy, r, hours) {
  const a = ((hours / 24) * 360 - 90) * (Math.PI / 180);
  return [cx + r * Math.cos(a), cy + r * Math.sin(a)];
}

function arcPath(cx, cy, r, fromH, toH) {
  const span = clamp(toH - fromH, 0, 23.999);
  const [x1, y1] = polar(cx, cy, r, fromH);
  const [x2, y2] = polar(cx, cy, r, fromH + span);
  const large = span > 12 ? 1 : 0;
  return `M${x1.toFixed(2)} ${y1.toFixed(2)} A${r} ${r} 0 ${large} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}

class EvGuestPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._tab = "charge";
    this._state = null;
    this._draft = {};
    this._preview = null;
    this._busy = null;
    this._message = null;
    this._unsub = null;
    this._entryId = this._read(ENTRY_KEY);
    this._animatePlan = false;
    this._lastPlanKey = null;
    this._tick = null;
  }

  // ------------------------------------------------------------------ Home Assistant wiring

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (this._menu) this._menu.hass = hass;
    if (first) {
      this._renderShell();
      this._subscribe();
    }
  }

  set narrow(narrow) {
    this._narrow = narrow;
    if (this._menu) this._menu.narrow = narrow;
    this.toggleAttribute("narrow", Boolean(narrow));
  }

  set panel(panel) {
    this._panel = panel;
  }

  connectedCallback() {
    this._tick = setInterval(() => this._state && this._renderLive(), 30000);
    if (this._hass && !this._unsub) this._subscribe();
  }

  disconnectedCallback() {
    clearInterval(this._tick);
    this._unsubscribe();
  }

  get _lang() {
    const lang = (this._hass?.locale?.language || this._hass?.language || navigator.language || "en").slice(0, 2);
    return TEXT[lang] ? lang : "en";
  }

  _t(key, vars = {}) {
    const text = TEXT[this._lang][key] ?? TEXT.en[key] ?? key;
    return text.replace(/\{(\w+)\}/g, (_, name) => vars[name] ?? "");
  }

  _read(key) {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  _write(key, value) {
    try {
      localStorage.setItem(key, value);
    } catch {
      /* private mode */
    }
  }

  async _subscribe() {
    this._unsubscribe();
    const connection = this._hass?.connection;
    if (!connection) return;
    const message = { type: "ev_guest/subscribe" };
    if (this._entryId) message.entry_id = this._entryId;
    try {
      this._unsub = await connection.subscribeMessage((event) => this._onState(event), message);
    } catch (err) {
      if (this._entryId && err?.code === "entry_not_found") {
        this._entryId = null;
        this._subscribe();
        return;
      }
      this._showError(err);
    }
  }

  _unsubscribe() {
    if (this._unsub) {
      const unsub = this._unsub;
      this._unsub = null;
      Promise.resolve(unsub()).catch(() => {});
    }
  }

  _onState(state) {
    if (state.reload) {
      // The entry reloads after an options change; subscribe again.
      setTimeout(() => this._subscribe(), 800);
      return;
    }
    const firstState = !this._state || this._state.entry_id !== state.entry_id;
    this._state = state;
    const planKey = JSON.stringify(state.plan.segments);
    if (planKey !== this._lastPlanKey) {
      this._animatePlan = !firstState && state.plan.segments.length > 0;
      this._lastPlanKey = planKey;
    }
    if (firstState || this._tab !== "charge" || !this.shadowRoot.querySelector(".charging")) this._render();
    else this._update();
  }

  /* Update the charging page in place, so typing and animations are not interrupted. */
  _update() {
    this._renderTabs();
    this._renderGuest();
    this._renderInputs();
    this._renderLive();
  }

  _renderGuest() {
    const box = this.shadowRoot.querySelector(".guest-body");
    if (!box) return;
    const key = JSON.stringify([this._state.car, this._state.config.lookup, this._busy === "lookup"]);
    const plate = this.shadowRoot.querySelector("#plate");
    if (plate && this.shadowRoot.activeElement !== plate) plate.value = this._inputs.license_plate || "";
    this.shadowRoot.querySelector(".plate")?.classList.toggle("scanning", this._busy === "lookup");
    const lookup = this.shadowRoot.querySelector(".lookup");
    if (lookup) {
      lookup.disabled = !this._state.config.lookup || this._busy === "lookup";
      lookup.querySelector("span").textContent = this._busy === "lookup" ? this._t("looking_up") : this._t("lookup");
    }
    if (box.dataset.key === key) return;
    box.dataset.key = key;
    box.innerHTML = this._guestBodyHtml();
  }

  async _ws(type, data = {}) {
    const message = { type, ...data };
    if (this._state?.entry_id) message.entry_id = this._state.entry_id;
    return this._hass.callWS(message);
  }

  // ------------------------------------------------------------------ actions

  async _run(name, type, data) {
    this._busy = name;
    this._message = null;
    this._renderBusy();
    try {
      await this._ws(type, data);
      return true;
    } catch (err) {
      this._showError(err);
      return false;
    } finally {
      this._busy = null;
      this._renderBusy();
    }
  }

  _renderBusy() {
    this._renderToast();
    if (this._tab === "charge" && this.shadowRoot.querySelector(".charging")) {
      this._renderGuest();
      this._renderInputs();
    }
  }

  _showError(err) {
    const code = err?.code || err?.error?.code;
    const key = `err_${code}`;
    this._message = { kind: "error", text: TEXT.en[key] ? this._t(key) : this._t("err_unknown", { detail: err?.message || code || err }) };
    if (this._state) this._renderToast();
    else this.shadowRoot.querySelector(".loading p").textContent = this._message.text;
  }

  async _lookup() {
    const plate = this.shadowRoot.querySelector("#plate")?.value ?? "";
    await this._commit({ license_plate: plate });
    await this._run("lookup", "ev_guest/lookup");
  }

  async _calculate() {
    await this._commit(this._draft);
    if (await this._run("calculate", "ev_guest/calculate")) {
      this._preview = null;
      this._renderLive();
    }
  }

  async _newGuest() {
    this._draft = {};
    this._preview = null;
    await this._run("new_guest", "ev_guest/new_guest");
  }

  /* Store changed inputs. While a plan exists, the change is shown as a preview first. */
  async _commit(inputs) {
    const changes = Object.fromEntries(Object.entries(inputs).filter(([, v]) => v !== undefined));
    if (!Object.keys(changes).length) return;
    try {
      await this._ws("ev_guest/set_inputs", { inputs: changes });
      for (const key of Object.keys(changes)) delete this._draft[key];
    } catch (err) {
      this._showError(err);
    }
  }

  _change(inputs, { commit = true } = {}) {
    Object.assign(this._draft, inputs);
    this._renderInputs();
    clearTimeout(this._previewTimer);
    this._previewTimer = setTimeout(() => this._loadPreview(), PREVIEW_DELAY);
    if (commit) {
      clearTimeout(this._commitTimer);
      this._commitTimer = setTimeout(() => this._commit({ ...this._draft }), 600);
    }
  }

  async _loadPreview() {
    const inputs = { ...this._state.inputs, ...this._draft };
    delete inputs.license_plate;
    const ask = JSON.stringify(inputs);
    this._previewAsk = ask;
    try {
      const result = await this._ws("ev_guest/preview", { inputs: this._wsInputs(inputs) });
      if (this._previewAsk !== ask) return;
      this._preview = result;
    } catch {
      this._preview = null;
    }
    this._renderLive();
  }

  _wsInputs(inputs) {
    const keys = [
      "soc",
      "charge_limit",
      "battery_capacity",
      "charger_power",
      "charging_efficiency",
      "charge_completion_time",
      "use_completion_time",
      "continuous_charging_preferred",
    ];
    return Object.fromEntries(keys.filter((key) => inputs[key] !== undefined).map((key) => [key, inputs[key]]));
  }

  get _inputs() {
    return { ...(this._state?.inputs || {}), ...this._draft };
  }

  /* True when the stored plan was made with other inputs than shown now. */
  get _stale() {
    const info = this._state?.plan?.info;
    if (!info || !this._state.plan.segments.length || this._state.plan_locked) return false;
    const used = info.inputs || { soc: info.soc, charge_limit: info.limit };
    const inputs = this._inputs;
    return (
      Object.keys(this._draft).length > 0 ||
      Object.entries(used).some(([key, value]) => String(value) !== String(inputs[key]))
    );
  }

  // ------------------------------------------------------------------ formatting

  get _locale() {
    return this._lang === "da" ? "da-DK" : this._hass?.locale?.language || "en-GB";
  }

  _money(value, digits = 2) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "–";
    try {
      return new Intl.NumberFormat(this._locale, {
        style: "currency",
        currency: this._state?.currency || "DKK",
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      }).format(value);
    } catch {
      return `${Number(value).toFixed(digits)} ${this._state?.currency || ""}`;
    }
  }

  _num(value, digits = 1) {
    if (value === null || value === undefined) return "–";
    return new Intl.NumberFormat(this._locale, { maximumFractionDigits: digits, minimumFractionDigits: 0 }).format(value);
  }

  _kwh(value, digits = 1) {
    return `${this._num(value, digits)} kWh`;
  }

  _time(iso) {
    if (!iso) return "–";
    return new Intl.DateTimeFormat(this._locale, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }).format(new Date(iso));
  }

  _day(iso) {
    const date = new Date(iso);
    const today = new Date();
    const start = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
    const diff = Math.round((start(date) - start(today)) / 86400000);
    if (diff === 0) return this._t("today");
    if (diff === 1) return this._t("tomorrow");
    if (diff === 2) return this._t("day_after");
    return new Intl.DateTimeFormat(this._locale, { weekday: "long" }).format(date);
  }

  _date(iso) {
    return new Intl.DateTimeFormat(this._locale, { day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
  }

  _duration(minutes) {
    if (minutes === null || minutes === undefined) return "–";
    const h = Math.floor(minutes / 60);
    const m = Math.round(minutes % 60);
    if (!h) return `${m} ${this._t("minutes_short")}`;
    return m ? `${h} ${this._t("hours_short")} ${m} ${this._t("minutes_short")}` : `${h} ${this._t("hours_short")}`;
  }

  // ------------------------------------------------------------------ rendering

  _renderShell() {
    this.shadowRoot.innerHTML = `<style>${STYLE}</style>
      <div class="app">
        <header class="bar">
          <div class="menu"></div>
          <div class="brand">${MARK}<span>EV Guest</span></div>
          <div class="entry"></div>
          <nav class="tabs" role="tablist"></nav>
        </header>
        <main class="content"><div class="loading">${MARK}<p>${this._t("loading")}</p></div></main>
        <div class="toast" role="status" aria-live="polite"></div>
        <div class="sheet-root"></div>
      </div>`;
    if (customElements.get("ha-menu-button")) {
      this._menu = document.createElement("ha-menu-button");
      this._menu.hass = this._hass;
      this._menu.narrow = this._narrow;
      this.shadowRoot.querySelector(".menu").appendChild(this._menu);
    }
  }

  _render() {
    if (!this._state) return;
    const root = this.shadowRoot;
    this._renderTabs();
    this._renderEntries();
    const content = root.querySelector(".content");
    if (this._tab === "history") content.innerHTML = this._historyHtml();
    else if (this._tab === "settings") content.innerHTML = this._settingsHtml();
    else content.innerHTML = this._chargeHtml();
    this._bind();
    if (this._tab === "charge") {
      this._renderGuest();
      this._renderInputs();
      this._renderLive();
    }
    this._renderToast();
  }

  _renderTabs() {
    const nav = this.shadowRoot.querySelector(".tabs");
    nav.innerHTML = ["charge", "history", "settings"]
      .map(
        (tab) => `<button role="tab" data-tab="${tab}" aria-selected="${this._tab === tab}" class="${this._tab === tab ? "on" : ""}">
          ${ICONS[tab]}<span>${this._t(`tab_${tab}`)}</span>${tab === "history" && this._state.history.length ? `<em>${this._state.history.length}</em>` : ""}</button>`,
      )
      .join("");
    nav.querySelectorAll("button").forEach((button) =>
      button.addEventListener("click", () => {
        this._tab = button.dataset.tab;
        this._render();
        this.shadowRoot.querySelector(".content").scrollTop = 0;
      }),
    );
  }

  _renderEntries() {
    const box = this.shadowRoot.querySelector(".entry");
    const entries = this._state.entries || [];
    if (entries.length < 2) {
      box.innerHTML = "";
      return;
    }
    box.innerHTML = `<select aria-label="EV Guest">${entries
      .map((e) => `<option value="${esc(e.entry_id)}" ${e.entry_id === this._state.entry_id ? "selected" : ""}>${esc(e.title)}</option>`)
      .join("")}</select>`;
    box.querySelector("select").addEventListener("change", (ev) => {
      this._entryId = ev.target.value;
      this._write(ENTRY_KEY, this._entryId);
      this._state = null;
      this._draft = {};
      this._preview = null;
      this._subscribe();
    });
  }

  _renderToast() {
    const toast = this.shadowRoot.querySelector(".toast");
    if (!this._message) {
      toast.className = "toast";
      toast.textContent = "";
      return;
    }
    toast.className = `toast show ${this._message.kind}`;
    toast.innerHTML = `<span>${esc(this._message.text)}</span><button aria-label="${this._t("close")}">${ICONS.close}</button>`;
    toast.querySelector("button").addEventListener("click", () => {
      this._message = null;
      this._renderToast();
    });
    clearTimeout(this._toastTimer);
    if (this._message.kind !== "error") this._toastTimer = setTimeout(() => ((this._message = null), this._renderToast()), 2500);
  }

  // ------------------------------------------------------------------ charging tab

  _chargeHtml() {
    const s = this._state;
    const lookingUp = this._busy === "lookup";
    const plate = this._inputs.license_plate || "";
    return `
      <div class="col left">
      <section class="hero">
        <div class="dial-wrap">
          <svg class="dial" viewBox="0 0 400 400" role="img" aria-label="${this._t("prices_title")}"></svg>
          <div class="dial-center"></div>
        </div>
        <div class="status-line"></div>
      </section>
      <section class="panel facts"></section>
      </div>

      <div class="col right">
      <section class="panel guest">
        <h2>${this._t("guest")}</h2>
        <div class="plate-row">
          <label class="plate ${lookingUp ? "scanning" : ""}">
            <span class="eu" aria-hidden="true"><i></i>DK</span>
            <input id="plate" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="10"
              placeholder="${this._t("plate_placeholder")}" value="${esc(plate)}" aria-label="${this._t("guest")}">
            <span class="scan" aria-hidden="true"></span>
          </label>
          <button class="btn lookup" ${!s.config.lookup || lookingUp ? "disabled" : ""}>${ICONS.search}<span>${lookingUp ? this._t("looking_up") : this._t("lookup")}</span></button>
        </div>
        <div class="guest-body"></div>
        <div class="field battery-field">
          <span>${this._t("battery")}</span>
          <div class="stepper" data-key="battery_capacity" data-step="0.5" data-min="1" data-max="300">
            <button data-dir="-1" aria-label="−">−</button><output></output><button data-dir="1" aria-label="+">+</button>
          </div>
        </div>
      </section>

      <section class="panel charging">
        <h2>${this._t("charge")}</h2>
        <div class="battery" role="group" aria-label="${this._t("charge")}">
          <div class="cells">
            <div class="fill-target"></div>
            <div class="fill-now"></div>
            <div class="flow"></div>
            <div class="ticks">${[20, 40, 60, 80].map((v) => `<i style="left:${v}%"></i>`).join("")}</div>
            <button class="handle now" role="slider" aria-label="${this._t("now_level")}" aria-valuemin="0" aria-valuemax="100"></button>
            <button class="handle target" role="slider" aria-label="${this._t("target")}" aria-valuemin="0" aria-valuemax="100"></button>
          </div>
          <div class="nub"></div>
        </div>
        <div class="battery-legend">
          <span class="now-label"></span><span class="gain"></span><span class="target-label"></span>
        </div>

        <div class="field">
          <span>${this._t("charger")}</span>
          <div class="chips power">
            ${CHARGER_PRESETS.map((kw) => `<button data-kw="${kw}">${this._num(kw, 1)} kW</button>`).join("")}
            <label class="chip-input kw"><input type="number" min="0.1" max="350" step="0.1" inputmode="decimal" placeholder="${this._t("custom")}" aria-label="${this._t("charger")}"><span>kW</span></label>
          </div>
        </div>

        <div class="field">
          <span>${this._t("ready_by")}</span>
          <div class="chips deadline">
            ${DEADLINE_PRESETS.map((t) => `<button data-time="${t}">${t}</button>`).join("")}
            <button data-time="custom" class="custom-time">${this._t("custom")}</button>
            <label class="chip-input time" hidden><input type="time" step="900" aria-label="${this._t("ready_by")}"></label>
            <button data-time="none" class="none">${this._t("no_deadline")}</button>
          </div>
        </div>

        <div class="field">
          <span>${this._t("mode")}</span>
          <div class="segmented" role="radiogroup">
            <button role="radio" data-mode="continuous">${this._t("continuous")}</button>
            <button role="radio" data-mode="split">${this._t("split")}</button>
          </div>
        </div>

        <div class="actions">
          <button class="btn primary calc">${ICONS.charge}<span></span></button>
          <button class="btn ghost new-guest">${ICONS.plus}<span>${this._t("new_guest")}</span></button>
        </div>
        <p class="note"></p>
      </section>
      </div>

      <section class="panel prices">
        <h2>${this._t("prices_title")}</h2>
        <div class="timeline-wrap">
          <svg class="timeline" preserveAspectRatio="none"></svg>
          <div class="scrub" hidden></div>
        </div>
        <div class="legend">
          <span><i class="sw window"></i>${this._t("charging_window")}</span>
          <span><i class="sw scale"></i>${this._t("per_kwh")}</span>
        </div>
      </section>`;
  }

  _guestBodyHtml() {
    const s = this._state;
    const car = s.car;
    const hasCar = car.brand || car.model;
    const lookup = s.config.lookup
      ? ""
      : `<p class="hint">${this._t("lookup_needs_key")} <a href="/config/integrations/integration/ev_guest" target="_top">${this._t("add_key")}</a></p>`;
    if (!hasCar) return `${lookup}<p class="hint">${this._t("no_car")}</p>`;
    return `${lookup}<div class="car reveal">
        <div class="car-name"><strong>${esc([car.brand, car.model].filter(Boolean).join(" "))}</strong>
          <span>${esc([car.variant, car.model_year ? `${this._t("model_year")} ${car.model_year}` : ""].filter(Boolean).join(", "))}</span></div>
        ${car.match_score != null ? this._matchRing(car.match_score) : ""}
      </div>`;
  }

  _matchRing(score) {
    const pct = clamp(Number(score), 0, 100);
    const c = 2 * Math.PI * 16;
    return `<div class="match" title="${this._t("match_hint")}">
      <svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="16" class="track"/><circle cx="20" cy="20" r="16" class="val"
        style="stroke-dasharray:${((pct / 100) * c).toFixed(1)} ${c.toFixed(1)}"/></svg>
      <span><b>${Math.round(pct)}</b>${this._t("match")}</span></div>`;
  }

  /* The parts that change while dragging, without rebuilding the page. */
  _renderInputs() {
    const root = this.shadowRoot;
    const inputs = this._inputs;
    if (!root.querySelector(".charging")) return;
    const soc = Number(inputs.soc ?? 20);
    const limit = Number(inputs.charge_limit ?? 80);
    const capacity = Number(inputs.battery_capacity ?? 0);
    root.querySelector(".fill-now").style.width = `${soc}%`;
    const target = root.querySelector(".fill-target");
    target.style.left = `${soc}%`;
    target.style.width = `${Math.max(0, limit - soc)}%`;
    root.querySelector(".flow").style.cssText = `left:${soc}%;width:${Math.max(0, limit - soc)}%`;
    const now = root.querySelector(".handle.now");
    now.style.left = `${soc}%`;
    now.setAttribute("aria-valuenow", soc);
    now.dataset.label = `${Math.round(soc)} %`;
    const tgt = root.querySelector(".handle.target");
    tgt.style.left = `${limit}%`;
    tgt.setAttribute("aria-valuenow", limit);
    tgt.dataset.label = `${Math.round(limit)} %`;
    root.querySelector(".now-label").innerHTML = `${this._t("now_level")} <b>${Math.round(soc)} %</b>`;
    root.querySelector(".target-label").innerHTML = `${this._t("target")} <b>${Math.round(limit)} %</b>`;
    const gain = (capacity * Math.max(0, limit - soc)) / 100;
    root.querySelector(".gain").textContent = gain > 0 ? `+${this._t("add_energy", { kwh: this._kwh(gain) })}` : "";

    const stepper = root.querySelector('.stepper[data-key="battery_capacity"] output');
    if (stepper) stepper.textContent = this._kwh(capacity, 1);

    const kw = Number(inputs.charger_power);
    let preset = false;
    root.querySelectorAll(".power button").forEach((b) => {
      const on = Math.abs(Number(b.dataset.kw) - kw) < 0.01;
      preset ||= on;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on);
    });
    const custom = root.querySelector(".power input");
    if (custom && root.activeElement !== custom) custom.value = preset ? "" : kw;
    custom?.parentElement.classList.toggle("on", !preset);

    const useDeadline = inputs.use_completion_time !== false;
    const time = String(inputs.charge_completion_time || "07:00").slice(0, 5);
    const timePreset = DEADLINE_PRESETS.includes(time);
    const customTime = this._customTime || (useDeadline && !timePreset);
    root.querySelectorAll(".deadline button").forEach((b) => {
      const kind = b.dataset.time;
      const on = kind === "none" ? !useDeadline : kind === "custom" ? false : useDeadline && kind === time && !this._customTime;
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", on);
      if (kind === "custom") b.hidden = customTime;
    });
    const timeInput = root.querySelector(".deadline input");
    if (timeInput && root.activeElement !== timeInput) timeInput.value = time;
    timeInput.parentElement.hidden = !customTime;
    timeInput.parentElement.classList.toggle("on", customTime && useDeadline);

    const continuous = inputs.continuous_charging_preferred !== false;
    root.querySelectorAll(".segmented button").forEach((b) => {
      const on = (b.dataset.mode === "continuous") === continuous;
      b.classList.toggle("on", on);
      b.setAttribute("aria-checked", on);
    });

    const calc = root.querySelector(".calc span");
    const hasPlan = this._state.plan.segments.length > 0;
    calc.textContent = this._busy === "calculate" ? this._t("calculating") : hasPlan ? this._t("recalculate") : this._t("calculate");
    root.querySelector(".calc").disabled = this._busy === "calculate";
    root.querySelector(".calc").classList.toggle("pulse", this._stale);
    root.querySelector(".note").textContent = this._stale ? this._t("changed") : "";
  }

  /* Dial, status, facts and timeline: everything that depends on the plan or the clock. */
  _renderLive() {
    if (this._tab !== "charge" || !this.shadowRoot.querySelector(".dial")) return;
    this._renderDial();
    this._renderStatus();
    this._renderFacts();
    this._renderTimeline();
    this._renderBatteryLive();
    this._animatePlan = false;
  }

  _shownPlan() {
    const plan = this._state.plan;
    const usePreview = this._preview && (this._stale || !plan.segments.length) && !this._state.plan_locked;
    if (usePreview && !this._preview.error) return { ...this._preview, preview: true };
    if (plan.segments.length) return { ...plan, preview: false };
    return null;
  }

  _renderDial() {
    const svg = this.shadowRoot.querySelector(".dial");
    const s = this._state;
    const now = new Date();
    const nowH = now.getHours() + now.getMinutes() / 60;
    const end = now.getTime() + 24 * 3600 * 1000;
    const prices = s.prices.filter((p) => new Date(p.end).getTime() > now.getTime() && new Date(p.start).getTime() < end);
    const values = prices.map((p) => p.price);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const cx = 200;
    const cy = 200;
    let html = `<defs>
      <linearGradient id="win" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#00B894"/><stop offset="1" stop-color="#A3E635"/></linearGradient>
      <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="5"/></filter></defs>`;

    // Hour ticks and labels of a 24-hour clock.
    html += `<circle cx="${cx}" cy="${cy}" r="118" class="face"/>`;
    for (let h = 0; h < 24; h++) {
      const [x1, y1] = polar(cx, cy, 196, h);
      const [x2, y2] = polar(cx, cy, h % 6 === 0 ? 188 : 192, h);
      html += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="tick ${h % 6 === 0 ? "major" : ""}"/>`;
    }
    for (const h of [0, 6, 12, 18]) {
      const [x, y] = polar(cx, cy, 106, h);
      html += `<text x="${x}" y="${y}" class="hour" dominant-baseline="central" text-anchor="middle">${String(h).padStart(2, "0")}</text>`;
    }

    // Prices as bars around the clock, from now and one day ahead.
    const inner = 142;
    const outer = 184;
    prices.forEach((p, i) => {
      const from = Math.max(new Date(p.start).getTime(), now.getTime());
      const to = Math.min(new Date(p.end).getTime(), end);
      const fromH = nowH + (from - now.getTime()) / 3600000;
      const toH = nowH + (to - now.getTime()) / 3600000;
      const t = max > min ? (p.price - min) / (max - min) : 0.5;
      const r = inner + 8 + t * (outer - inner - 8);
      const gap = Math.min(0.04, (toH - fromH) * 0.12);
      const a1 = polar(cx, cy, inner, fromH + gap);
      const a2 = polar(cx, cy, r, fromH + gap);
      const b1 = polar(cx, cy, r, toH - gap);
      const b2 = polar(cx, cy, inner, toH - gap);
      const large = toH - fromH > 12 ? 1 : 0;
      html += `<path class="bar" style="fill:${priceColor(t)};--d:${(i * 8).toFixed(0)}ms" d="M${a1} L${a2} A${r} ${r} 0 ${large} 1 ${b1} L${b2} A${inner} ${inner} 0 ${large} 0 ${a1}Z"><title>${this._time(p.start)}: ${this._money(p.price)}</title></path>`;
    });

    // The charging window as the lit arc of the logo.
    const plan = this._shownPlan();
    if (plan) {
      plan.segments.forEach((seg, index) => {
        const startMs = new Date(seg.start).getTime();
        const endMs = Math.min(new Date(seg.end).getTime(), startMs + 23.9 * 3600000);
        const past = endMs <= now.getTime();
        const fromH = new Date(startMs).getHours() + new Date(startMs).getMinutes() / 60;
        const d = arcPath(cx, cy, 128, fromH, fromH + (endMs - startMs) / 3600000);
        const sweep = this._animatePlan && !reducedMotion() ? " sweep" : "";
        const cls = plan.preview ? "window preview" : `window${past ? " past" : ""}${sweep}`;
        if (!past) html += `<path d="${d}" class="window-glow ${plan.preview ? "preview" : ""}" filter="url(#glow)"/>`;
        html += `<path d="${d}" class="${cls}" pathLength="1" style="--i:${index}"/>`;
        if (s.charge_now && !plan.preview && startMs <= now.getTime() && now.getTime() < endMs) html += `<path d="${d}" class="window-flow"/>`;
      });
    }

    // Deadline flag.
    const inputs = this._inputs;
    if (inputs.use_completion_time !== false) {
      const [hh, mm] = String(inputs.charge_completion_time || "07:00").split(":").map(Number);
      const h = hh + mm / 60;
      const [x1, y1] = polar(cx, cy, 116, h);
      const [x2, y2] = polar(cx, cy, 198, h);
      const [fx, fy] = polar(cx, cy, 206, h);
      html += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="deadline-line"/><circle cx="${fx}" cy="${fy}" r="5" class="deadline-dot"><title>${this._t("deadline")} ${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}</title></circle>`;
    }

    // Now needle.
    const [nx1, ny1] = polar(cx, cy, 112, nowH);
    const [nx2, ny2] = polar(cx, cy, 196, nowH);
    html += `<line x1="${nx1}" y1="${ny1}" x2="${nx2}" y2="${ny2}" class="needle"/><circle cx="${nx2}" cy="${ny2}" r="4.5" class="needle-dot"/>`;

    svg.innerHTML = html;
    // The bars grow in once per page, not on every update.
    svg.classList.toggle("intro", !svg.dataset.shown);
    svg.dataset.shown = "1";
    this._renderDialCenter(plan, prices);
  }

  _renderDialCenter(plan, prices) {
    const box = this.shadowRoot.querySelector(".dial-center");
    const nowPrice = prices[0]?.price;
    if (plan) {
      const savings = plan.savings;
      box.innerHTML = `
        ${plan.preview ? `<span class="tag">${this._t("preview")}</span>` : ""}
        <strong class="big">${this._money(plan.cost)}</strong>
        <span class="range">${this._time(plan.segments[0].start)}–${this._time(plan.segments[plan.segments.length - 1].end)}</span>
        ${savings > 0.005 ? `<span class="save">${this._t("save", { amount: this._money(savings) })}</span>` : ""}`;
      if (this._animatePlan && !reducedMotion()) this._countUp(box.querySelector(".big"), plan.cost);
      return;
    }
    if (nowPrice === undefined) {
      box.innerHTML = `<strong class="big muted">${this._t("no_prices")}</strong>`;
      return;
    }
    const cheapest = prices.reduce((a, b) => (b.price < a.price ? b : a), prices[0]);
    box.innerHTML = `
      <strong class="big">${this._money(nowPrice)}</strong>
      <span class="range">${this._t("price_now")}</span>
      <span class="save">${this._t("cheapest_at", { time: this._time(cheapest.start) })}</span>`;
  }

  _countUp(el, value) {
    const startTime = performance.now();
    const duration = 900;
    const step = (now) => {
      const k = clamp((now - startTime) / duration, 0, 1);
      const eased = 1 - Math.pow(1 - k, 3);
      el.textContent = this._money(value * eased);
      if (k < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  _renderStatus() {
    const s = this._state;
    const box = this.shadowRoot.querySelector(".status-line");
    const now = Date.now();
    const segs = s.plan.segments.map((seg) => ({ start: new Date(seg.start).getTime(), end: new Date(seg.end).getTime() }));
    let text = "";
    let kind = s.status;
    if (s.error) {
      text = this._t(`err_${s.error}`);
      kind = "error";
    } else if (s.status === "charging") {
      text = this._t("charging_until", { time: this._time(s.plan.segments.at(-1).end) });
    } else if (s.status === "planned") {
      const next = segs.find((seg) => seg.start > now);
      const started = segs.some((seg) => seg.start <= now);
      if (started && next) text = this._t("paused_until", { time: this._time(new Date(next.start).toISOString()) });
      else if (next) text = this._t("starts_in", { time: this._duration((next.start - now) / 60000) });
    } else if (s.status === "completed") {
      text =
        s.release && s.release.reason === "unplugged"
          ? this._t("unplugged_at", { time: this._time(s.release.at) })
          : this._t("completed_at", { time: this._time(s.plan.segments.at(-1).end) });
    } else {
      text = this._t("status_ready");
    }
    if (!s.error && s.plan.progress && s.plan.progress.behind_plan) {
      text = `${text} ${this._t("behind_plan")}`.trim();
      kind = "behind";
    }
    box.className = `status-line ${kind}`;
    box.innerHTML = `<i></i><span>${esc(text)}</span>`;
  }

  _renderFacts() {
    const box = this.shadowRoot.querySelector(".facts");
    const plan = this._shownPlan();
    const s = this._state;
    if (!plan) {
      box.hidden = true;
      return;
    }
    box.hidden = false;
    const items = [
      [this._t("start"), `${this._day(plan.segments[0].start)} ${this._time(plan.segments[0].start)}`],
      [this._t("end"), `${this._day(plan.segments.at(-1).end)} ${this._time(plan.segments.at(-1).end)}`],
      [this._t("duration"), this._duration(plan.minutes)],
      [this._t("energy"), this._kwh(plan.energy)],
      [this._t("cost"), this._money(plan.cost)],
      [this._t("savings"), plan.savings == null ? "–" : this._money(plan.savings)],
      [this._t("speed"), `${this._num(plan.speed)} %/${this._t("hours_short")}`],
    ];
    if (!plan.preview && s.config.energy_entity && s.plan.measured_energy != null) {
      items.push([this._t("measured"), this._kwh(s.plan.measured_energy, 2)]);
      items.push([this._t("measured_cost"), this._money(s.plan.measured_cost)]);
    }
    box.innerHTML = `<dl class="${plan.preview ? "is-preview" : ""}">${items
      .map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`)
      .join("")}</dl>${
      plan.savings > 0.005 && !plan.preview ? `<p class="save-note">${this._t("save", { amount: this._money(plan.savings) })} ${this._t("save_vs")}</p>` : ""
    }`;
  }

  /* While charging: the battery fills as time passes, from the plan's start level. */
  _renderBatteryLive() {
    const root = this.shadowRoot;
    const s = this._state;
    const info = s.plan.info;
    const flow = root.querySelector(".flow");
    if (!flow) return;
    flow.classList.toggle("on", Boolean(s.charge_now));
    const est = root.querySelector(".battery-legend .gain");
    if (!s.charge_now || !info || !s.plan.speed) return;
    // With an energy meter the estimate follows the energy actually delivered.
    const progress = s.plan.progress;
    if (progress && progress.source === "meter") {
      const pct = clamp(Number(progress.soc), 0, 100);
      root.querySelector(".fill-now").style.width = `${pct}%`;
      if (est) est.textContent = this._t("est_level_measured", { pct: `${Math.round(pct)} %` });
      return;
    }
    const now = Date.now();
    let hours = 0;
    for (const seg of s.plan.segments) {
      const a = new Date(seg.start).getTime();
      const b = new Date(seg.end).getTime();
      hours += Math.max(0, Math.min(now, b) - a) / 3600000;
    }
    const pct = clamp(Number(info.soc) + hours * s.plan.speed, 0, Number(info.limit));
    root.querySelector(".fill-now").style.width = `${pct}%`;
    if (est) est.textContent = this._t("est_level", { pct: `${Math.round(pct)} %` });
  }

  _renderTimeline() {
    const svg = this.shadowRoot.querySelector(".timeline");
    const prices = this._state.prices;
    if (!prices.length) {
      svg.innerHTML = "";
      return;
    }
    const W = 1000;
    const H = 220;
    const top = 26;
    const bottom = 30;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    const t0 = new Date(prices[0].start).getTime();
    const t1 = new Date(prices.at(-1).end).getTime();
    const x = (ms) => ((ms - t0) / (t1 - t0)) * W;
    const values = prices.map((p) => p.price);
    const min = Math.min(0, ...values);
    const max = Math.max(...values);
    const y = (v) => H - bottom - ((v - min) / (max - min || 1)) * (H - top - bottom);
    const lo = Math.min(...values);
    const hi = Math.max(...values);
    let html = `<defs><linearGradient id="tw" x1="0" x2="1"><stop offset="0" stop-color="#00B894"/><stop offset="1" stop-color="#A3E635"/></linearGradient></defs>`;

    // Day bands.
    const days = new Map();
    for (const p of prices) {
      const d = new Date(p.start);
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      if (!days.has(key)) days.set(key, p.start);
    }
    [...days.values()].forEach((iso, i) => {
      const startMs = Math.max(new Date(new Date(iso).setHours(0, 0, 0, 0)).getTime(), t0);
      const xs = x(startMs);
      if (i % 2) html += `<rect x="${xs}" y="0" width="${Math.min(W - xs, x(startMs + 86400000) - xs)}" height="${H - bottom}" class="day-band"/>`;
      html += `<text x="${xs + 8}" y="16" class="day">${esc(this._day(iso))}</text>`;
    });

    // Charging window under the bars.
    const plan = this._shownPlan();
    if (plan) {
      for (const seg of plan.segments) {
        const a = x(new Date(seg.start).getTime());
        const b = x(new Date(seg.end).getTime());
        html += `<rect x="${a}" y="${top - 6}" width="${Math.max(2, b - a)}" height="${H - bottom - top + 6}" rx="6" class="tl-window ${plan.preview ? "preview" : ""}"/>`;
      }
    }

    // Bars.
    prices.forEach((p, i) => {
      const a = x(new Date(p.start).getTime());
      const b = x(new Date(p.end).getTime());
      const w = Math.max(1, b - a - (b - a > 6 ? 1.5 : 0.4));
      const t = hi > lo ? (p.price - lo) / (hi - lo) : 0.5;
      const yy = y(Math.max(p.price, min));
      html += `<rect x="${a}" y="${Math.min(yy, y(0))}" width="${w}" height="${Math.abs(y(0) - yy)}" rx="${Math.min(3, w / 3)}" class="tl-bar" style="fill:${priceColor(t)};--d:${i * 4}ms" data-i="${i}"/>`;
    });

    // Axis hours.
    for (let ms = Math.ceil(t0 / 21600000) * 21600000; ms <= t1; ms += 3600000) {
      const d = new Date(ms);
      if (d.getMinutes() !== 0 || d.getHours() % 6 || x(ms) < 14 || x(ms) > W - 14) continue;
      html += `<text x="${x(ms)}" y="${H - 9}" class="axis" text-anchor="middle">${String(d.getHours()).padStart(2, "0")}</text>`;
    }

    // Deadline and now.
    const inputs = this._inputs;
    if (inputs.use_completion_time !== false && plan) {
      const dl = new Date(plan.segments.at(-1).end);
      const [hh, mm] = String(inputs.charge_completion_time || "07:00").split(":").map(Number);
      const deadline = new Date(dl);
      deadline.setHours(hh, mm, 0, 0);
      if (deadline < dl) deadline.setDate(deadline.getDate() + 1);
      if (deadline.getTime() <= t1) html += `<line x1="${x(deadline.getTime())}" x2="${x(deadline.getTime())}" y1="${top - 8}" y2="${H - bottom}" class="tl-deadline"/>`;
    }
    const nowMs = Date.now();
    if (nowMs >= t0 && nowMs <= t1) {
      html += `<line x1="${x(nowMs)}" x2="${x(nowMs)}" y1="${top - 8}" y2="${H - bottom}" class="tl-now"/><text x="${x(nowMs) + 5}" y="${top - 1}" class="tl-now-label">${this._t("now")}</text>`;
    }
    svg.innerHTML = html;
    svg.classList.toggle("intro", !svg.dataset.shown);
    svg.dataset.shown = "1";
    this._bindScrub(svg, prices, t0, t1);
  }

  _bindScrub(svg, prices, t0, t1) {
    const scrub = this.shadowRoot.querySelector(".scrub");
    const show = (clientX) => {
      const rect = svg.getBoundingClientRect();
      const k = clamp((clientX - rect.left) / rect.width, 0, 1);
      const ms = t0 + k * (t1 - t0);
      const p = prices.find((item) => new Date(item.start).getTime() <= ms && ms < new Date(item.end).getTime());
      if (!p) return;
      scrub.hidden = false;
      scrub.style.left = `${clamp(k * 100, 8, 92)}%`;
      scrub.innerHTML = `<b>${this._money(p.price)}</b><span>${esc(this._day(p.start))} ${this._time(p.start)}–${this._time(p.end)}</span>`;
      svg.querySelectorAll(".tl-bar.hot").forEach((el) => el.classList.remove("hot"));
      svg.querySelector(`.tl-bar[data-i="${prices.indexOf(p)}"]`)?.classList.add("hot");
    };
    const hide = () => {
      scrub.hidden = true;
      svg.querySelectorAll(".tl-bar.hot").forEach((el) => el.classList.remove("hot"));
    };
    svg.onpointermove = (ev) => show(ev.clientX);
    svg.onpointerdown = (ev) => show(ev.clientX);
    svg.onpointerleave = hide;
  }

  // ------------------------------------------------------------------ history tab

  _historyHtml() {
    const history = this._state.history;
    if (!history.length) {
      return `<section class="empty">${MARK}<p>${this._t("history_empty")}</p></section>`;
    }
    const energyOf = (e) => (e.measured_energy ?? e.energy) || 0;
    const costOf = (e) => (e.measured_cost ?? e.cost) || 0;
    const totals = history.reduce(
      (acc, e) => ({ energy: acc.energy + energyOf(e), cost: acc.cost + costOf(e), saved: acc.saved + (e.savings || 0) }),
      { energy: 0, cost: 0, saved: 0 },
    );
    const recent = history.slice(0, 12).reverse();
    const peak = Math.max(...recent.map(energyOf), 1);
    return `
      <section class="panel totals">
        <p class="count">${history.length === 1 ? this._t("session") : this._t("sessions", { n: history.length })}</p>
        <dl>
          <div><dt>${this._t("total_energy")}</dt><dd>${this._kwh(totals.energy, 0)}</dd></div>
          <div><dt>${this._t("total_cost")}</dt><dd>${this._money(totals.cost)}</dd></div>
          <div><dt>${this._t("total_saved")}</dt><dd class="good">${this._money(totals.saved)}</dd></div>
        </dl>
        <div class="spark" aria-hidden="true">${recent
          .map((e, i) => `<i style="height:${((energyOf(e) / peak) * 100).toFixed(1)}%;--d:${i * 40}ms" title="${this._kwh(energyOf(e))}"></i>`)
          .join("")}</div>
      </section>
      <ul class="sessions">${history
        .map(
          (e) => `<li>
            <div class="when"><b>${new Date(e.start).getDate()}</b><span>${new Intl.DateTimeFormat(this._locale, { month: "short" }).format(new Date(e.start))}</span></div>
            <div class="what">
              <strong>${esc(e.car || this._t("unknown_car"))}</strong>
              <span>${e.plate ? `<em class="mini-plate">${esc(e.plate)}</em>` : ""}${this._time(e.start)}–${this._time(e.end)}</span>
            </div>
            <div class="nums"><b>${this._money(costOf(e))}</b><span>${this._kwh(energyOf(e))}</span></div>
            <div class="row-actions">
              <button class="icon bill" data-id="${esc(e.id)}" aria-label="${this._t("bill")}">${ICONS.receipt}</button>
              <button class="icon del" data-id="${esc(e.id)}" aria-label="${this._t("delete")}">${ICONS.trash}</button>
            </div>
          </li>`,
        )
        .join("")}</ul>
      <button class="btn ghost danger delete-all">${ICONS.trash}<span>${this._t("delete_all")}</span></button>`;
  }

  _billText(entry, byRate) {
    const settings = this._state.settings;
    const energy = (entry.measured_energy ?? entry.energy) || 0;
    const rate = Number(settings.bill_price);
    const amount = byRate && rate > 0 ? energy * rate : (entry.measured_cost ?? entry.cost) || 0;
    const car = [entry.car, entry.plate].filter(Boolean).join(" – ") || this._t("unknown_car");
    const lines = [
      this._t("bill_text_intro", { car }),
      this._t("bill_line_date", { date: this._date(entry.start) }),
      this._t("bill_line_energy", { kwh: this._kwh(energy, 2) }),
      `${this._t("bill_line_price", { amount: this._money(amount) })}${byRate && rate > 0 ? ` ${this._t("bill_line_rate", { rate: this._money(rate) })}` : ""}`,
    ];
    if (settings.payment_text) lines.push("", settings.payment_text);
    return { text: lines.join("\n"), amount, energy };
  }

  _openBill(entry) {
    const settings = this._state.settings;
    let byRate = Number(settings.bill_price) > 0;
    const root = this.shadowRoot.querySelector(".sheet-root");
    const render = () => {
      const bill = this._billText(entry, byRate);
      root.innerHTML = `<div class="scrim"></div>
        <div class="sheet" role="dialog" aria-modal="true" aria-label="${this._t("bill_title")}">
          <header><h2>${this._t("bill_title")}</h2><button class="icon close" aria-label="${this._t("close")}">${ICONS.close}</button></header>
          <div class="receipt">
            <p class="amount">${this._money(bill.amount)}</p>
            <p class="sub">${esc(entry.car || this._t("unknown_car"))}${entry.plate ? ` <em class="mini-plate">${esc(entry.plate)}</em>` : ""}</p>
            <pre>${esc(bill.text)}</pre>
          </div>
          ${
            Number(settings.bill_price) > 0
              ? `<div class="segmented"><button class="${byRate ? "" : "on"}" data-rate="0">${this._t("by_actual")}</button><button class="${byRate ? "on" : ""}" data-rate="1">${this._t("by_rate")}</button></div>`
              : ""
          }
          <div class="actions">
            <button class="btn primary copy">${ICONS.copy}<span>${this._t("copy")}</span></button>
            ${navigator.share ? `<button class="btn ghost share">${ICONS.share}<span>${this._t("share")}</span></button>` : ""}
          </div>
        </div>`;
      const close = () => (root.innerHTML = "");
      root.querySelector(".scrim").onclick = close;
      root.querySelector(".close").onclick = close;
      root.querySelectorAll("[data-rate]").forEach((b) => (b.onclick = () => ((byRate = b.dataset.rate === "1"), render())));
      root.querySelector(".copy").onclick = async () => {
        try {
          await navigator.clipboard.writeText(bill.text);
          this._message = { kind: "ok", text: this._t("copied") };
          this._renderToast();
        } catch {
          /* clipboard not allowed */
        }
      };
      const share = root.querySelector(".share");
      if (share) share.onclick = () => navigator.share({ text: bill.text }).catch(() => {});
      root.querySelector(".close").focus();
    };
    render();
  }

  // ------------------------------------------------------------------ settings tab

  _settingsHtml() {
    const s = this._state;
    const appUrl = `${location.origin}${this._panel?.config?.app_url || "/ev_guest_app"}/app.html`;
    return `
      <section class="panel">
        <h2>${this._t("settings_billing")}</h2>
        <label class="field col"><span>${this._t("bill_rate")}</span>
          <div class="unit-input"><input id="bill-rate" type="number" min="0" step="0.01" inputmode="decimal" value="${s.settings.bill_price ?? ""}"><span>${esc(s.currency)}/kWh</span></div>
          <small>${this._t("bill_rate_hint")}</small></label>
        <label class="field col"><span>${this._t("payment_text")}</span>
          <input id="payment-text" type="text" maxlength="200" value="${esc(s.settings.payment_text || "")}">
          <small>${this._t("payment_hint")}</small></label>
      </section>
      <section class="panel">
        <h2>${this._t("settings_charging")}</h2>
        <label class="field col"><span>${this._t("efficiency")} <b class="eff-value">${Math.round(this._inputs.charging_efficiency ?? 90)} %</b></span>
          <input id="efficiency" type="range" min="50" max="100" step="1" value="${this._inputs.charging_efficiency ?? 90}">
          <small>${this._t("efficiency_hint")}</small></label>
      </section>
      <section class="panel">
        <h2>${this._t("settings_sources")}</h2>
        <dl class="sources">
          <div><dt>${this._t("price_sensor")}</dt><dd>${esc(this._entityName(s.config.price_entity))}</dd></div>
          <div><dt>${this._t("energy_meter")}</dt><dd>${s.config.energy_entity ? esc(this._entityName(s.config.energy_entity)) : this._t("not_set")}</dd></div>
          <div><dt>${this._t("plate_lookup")}</dt><dd>${s.config.lookup ? this._t("on") : this._t("off")}</dd></div>
        </dl>
        <p class="hint">${this._t("change_in_ha")} <a href="/config/integrations/integration/ev_guest" target="_top">${this._t("open_integration")}</a></p>
      </section>
      <section class="panel">
        <h2>${this._t("app_title")}</h2>
        <p class="hint">${this._t("app_hint")}</p>
        <a class="btn ghost" href="${esc(appUrl)}" target="_blank" rel="noopener">${ICONS.share}<span>${this._t("open_app")}</span></a>
      </section>`;
  }

  _entityName(entityId) {
    const state = this._hass?.states?.[entityId];
    return state?.attributes?.friendly_name ? `${state.attributes.friendly_name} (${entityId})` : entityId;
  }

  // ------------------------------------------------------------------ events

  _bind() {
    const root = this.shadowRoot;
    if (this._tab === "charge") {
      const plate = root.querySelector("#plate");
      plate.addEventListener("input", () => {
        plate.value = plate.value.toUpperCase();
      });
      plate.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter") this._lookup();
      });
      plate.addEventListener("change", () => this._commit({ license_plate: plate.value }));
      root.querySelector(".lookup").addEventListener("click", () => this._lookup());
      root.querySelector(".calc").addEventListener("click", () => this._calculate());
      root.querySelector(".new-guest").addEventListener("click", () => this._newGuest());
      this._bindBattery();
      root.querySelectorAll(".stepper button").forEach((button) =>
        button.addEventListener("click", () => {
          const box = button.closest(".stepper");
          const key = box.dataset.key;
          const step = Number(box.dataset.step);
          const value = clamp(Number(this._inputs[key] || 0) + step * Number(button.dataset.dir), Number(box.dataset.min), Number(box.dataset.max));
          this._change({ [key]: Math.round(value * 10) / 10 });
        }),
      );
      root.querySelectorAll(".power button").forEach((b) => b.addEventListener("click", () => this._change({ charger_power: Number(b.dataset.kw) })));
      const kw = root.querySelector(".power input");
      kw.addEventListener("change", () => {
        const value = Number(kw.value);
        if (value > 0) this._change({ charger_power: value });
      });
      root.querySelectorAll(".deadline button").forEach((b) =>
        b.addEventListener("click", () => {
          if (b.dataset.time === "custom") {
            this._customTime = true;
            this._renderInputs();
            root.querySelector(".deadline input").focus();
            return;
          }
          this._customTime = false;
          this._change(b.dataset.time === "none" ? { use_completion_time: false } : { use_completion_time: true, charge_completion_time: b.dataset.time });
        }),
      );
      const time = root.querySelector(".deadline input");
      time.addEventListener("change", () => time.value && this._change({ use_completion_time: true, charge_completion_time: time.value }));
      root.querySelectorAll(".segmented button").forEach((b) =>
        b.addEventListener("click", () => this._change({ continuous_charging_preferred: b.dataset.mode === "continuous" })),
      );
      if (!this._preview && this._state.prices.length) this._loadPreview();
    }
    if (this._tab === "history") {
      root.querySelectorAll(".bill").forEach((b) =>
        b.addEventListener("click", () => this._openBill(this._state.history.find((e) => e.id === b.dataset.id))),
      );
      root.querySelectorAll(".del").forEach((b) =>
        b.addEventListener("click", () => this._run("delete", "ev_guest/delete_history", { history_id: b.dataset.id })),
      );
      root.querySelector(".delete-all")?.addEventListener("click", () => {
        if (confirm(this._t("confirm_delete_all"))) this._run("delete", "ev_guest/delete_history");
      });
    }
    if (this._tab === "settings") {
      const rate = root.querySelector("#bill-rate");
      rate.addEventListener("change", () =>
        this._saveSettings({ bill_price: rate.value === "" ? null : Number(rate.value) }),
      );
      const pay = root.querySelector("#payment-text");
      pay.addEventListener("change", () => this._saveSettings({ payment_text: pay.value }));
      const eff = root.querySelector("#efficiency");
      eff.addEventListener("input", () => (root.querySelector(".eff-value").textContent = `${eff.value} %`));
      eff.addEventListener("change", async () => {
        await this._commit({ charging_efficiency: Number(eff.value) });
        this._message = { kind: "ok", text: this._t("saved") };
        this._renderToast();
      });
    }
  }

  async _saveSettings(settings) {
    const ok = await this._run("settings", "ev_guest/settings", { settings });
    if (ok) {
      this._message = { kind: "ok", text: this._t("saved") };
      this._renderToast();
    }
  }

  _bindBattery() {
    const root = this.shadowRoot;
    const cells = root.querySelector(".cells");
    const valueAt = (clientX) => {
      const rect = cells.getBoundingClientRect();
      return Math.round(clamp(((clientX - rect.left) / rect.width) * 100, 0, 100));
    };
    const drag = (handle, key) => {
      handle.addEventListener("pointerdown", (ev) => {
        ev.preventDefault();
        handle.setPointerCapture(ev.pointerId);
        handle.classList.add("dragging");
        const move = (e) => {
          let v = valueAt(e.clientX);
          if (key === "soc") v = Math.min(v, Number(this._inputs.charge_limit) - 1);
          else v = Math.max(v, Number(this._inputs.soc) + 1);
          this._change({ [key]: clamp(v, 0, 100) }, { commit: false });
        };
        const up = () => {
          handle.classList.remove("dragging");
          handle.removeEventListener("pointermove", move);
          handle.removeEventListener("pointerup", up);
          handle.removeEventListener("pointercancel", up);
          this._commit({ [key]: this._inputs[key] });
        };
        handle.addEventListener("pointermove", move);
        handle.addEventListener("pointerup", up);
        handle.addEventListener("pointercancel", up);
      });
      handle.addEventListener("keydown", (ev) => {
        const delta = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 10, PageDown: -10 }[ev.key];
        if (!delta) return;
        ev.preventDefault();
        const current = Number(this._inputs[key]);
        let v = clamp(current + delta, 0, 100);
        if (key === "soc") v = Math.min(v, Number(this._inputs.charge_limit) - 1);
        else v = Math.max(v, Number(this._inputs.soc) + 1);
        this._change({ [key]: v });
      });
    };
    drag(root.querySelector(".handle.now"), "soc");
    drag(root.querySelector(".handle.target"), "charge_limit");
    // A tap on the battery moves the closest handle.
    cells.addEventListener("pointerdown", (ev) => {
      if (ev.target.classList.contains("handle")) return;
      const v = valueAt(ev.clientX);
      const soc = Number(this._inputs.soc);
      const limit = Number(this._inputs.charge_limit);
      if (Math.abs(v - soc) <= Math.abs(v - limit) && v < limit) this._change({ soc: v });
      else if (v > soc) this._change({ charge_limit: v });
    });
  }
}

const STYLE = `
:host {
  --evg-a: #00B894;
  --evg-b: #A3E635;
  --evg-ink: var(--primary-text-color, #1c1c1c);
  --evg-soft: var(--secondary-text-color, #5e5e5e);
  --evg-card: var(--card-background-color, #fff);
  --evg-bg: var(--primary-background-color, #fafafa);
  --evg-line: var(--divider-color, rgba(0,0,0,.12));
  --evg-accent: var(--primary-color, #009ac7);
  --evg-radius: var(--ha-card-border-radius, 16px);
  --evg-good: #0E9F6E;
  --evg-bad: var(--error-color, #db4437);
  --evg-safe-top: var(--rema-safe-top, 0px);
  --evg-safe-bottom: var(--rema-safe-bottom, 0px);
  display: block;
  height: 100%;
  background: var(--evg-bg);
  color: var(--evg-ink);
  font-family: var(--ha-font-family-body, var(--paper-font-body1_-_font-family, Roboto, system-ui, sans-serif));
  -webkit-font-smoothing: antialiased;
}
* { box-sizing: border-box; }
button, input, select { font: inherit; color: inherit; }
svg { display: block; }
a { color: var(--evg-accent); }
.app { display: flex; flex-direction: column; height: 100%; }

/* ---------- header */
.bar {
  position: sticky; top: 0; z-index: 4;
  display: grid; grid-template-columns: auto auto 1fr auto; align-items: center; gap: 8px;
  padding: calc(6px + var(--evg-safe-top)) 16px 6px 4px;
  min-height: 56px;
  background: var(--app-header-background-color, var(--evg-card));
  color: var(--app-header-text-color, var(--evg-ink));
  border-bottom: 1px solid var(--app-header-border-bottom, var(--evg-line));
}
.menu:empty { width: 8px; }
.brand { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 600; letter-spacing: -.01em; }
.brand svg { width: 28px; height: 28px; }
.entry select { border: 1px solid var(--evg-line); background: transparent; border-radius: 10px; padding: 6px 10px; max-width: 200px; }
.tabs { display: flex; gap: 4px; justify-self: end; }
.tabs button {
  position: relative; display: flex; align-items: center; gap: 8px;
  border: 0; background: transparent; padding: 8px 14px; border-radius: 999px; cursor: pointer;
  color: var(--evg-soft); font-weight: 500;
}
.tabs button svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.tabs button svg path[d^="M13 2.5"] { fill: currentColor; stroke: none; }
.tabs button.on { color: var(--evg-ink); background: color-mix(in srgb, var(--evg-a) 14%, transparent); }
.tabs button em { font-style: normal; font-size: 11px; font-weight: 600; background: var(--evg-line); border-radius: 999px; padding: 1px 6px; }
.tabs button:focus-visible, .btn:focus-visible, .chips button:focus-visible, .segmented button:focus-visible, .handle:focus-visible, .icon:focus-visible {
  outline: 2px solid var(--evg-accent); outline-offset: 2px;
}

/* ---------- layout */
.content {
  flex: 1; overflow-y: auto; -webkit-overflow-scrolling: touch;
  padding: 20px 20px calc(32px + var(--evg-safe-bottom));
  display: grid; gap: 18px; align-content: start;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  max-width: 1180px; width: 100%; margin: 0 auto;
}
.col { display: grid; gap: 18px; align-content: start; min-width: 0; }
.col > *, .field > *, .plate-row > * { min-width: 0; }
.content > :not(.col) { grid-column: 1 / -1; }
.panel {
  background: var(--evg-card); border-radius: var(--evg-radius);
  box-shadow: var(--ha-card-box-shadow, none); border: 1px solid var(--ha-card-border-color, var(--evg-line));
  padding: 18px 20px 20px;
}
.panel h2 { margin: 0 0 14px; font-size: 16px; font-weight: 600; letter-spacing: -.005em; }
.hint, .note { color: var(--evg-soft); font-size: 14px; line-height: 1.45; margin: 10px 0 0; max-width: 60ch; }
.note:empty { display: none; }
.loading, .empty { grid-column: 1 / -1; display: grid; justify-items: center; gap: 14px; padding: 80px 20px; color: var(--evg-soft); text-align: center; }
.loading svg, .empty svg { width: 72px; height: 72px; }
.loading .mark-arc { stroke-dasharray: 0 1000; animation: draw 1.4s ease-in-out infinite alternate; }
.empty p { max-width: 42ch; line-height: 1.5; }
@keyframes draw { to { stroke-dasharray: 360 1000; } }

/* ---------- dial (the signature) */
.hero { position: relative; display: grid; justify-items: center; align-content: start; gap: 10px; padding-top: 4px; }
.dial-wrap { position: relative; width: min(100%, 460px); aspect-ratio: 1; }
.dial { width: 100%; height: 100%; overflow: visible; }
.dial .face { fill: color-mix(in srgb, var(--evg-ink) 3%, transparent); stroke: var(--evg-line); }
.dial .tick { stroke: var(--evg-soft); stroke-opacity: .35; stroke-width: 1.2; }
.dial .tick.major { stroke-opacity: .8; stroke-width: 2; }
.dial .hour { font-size: 13px; fill: var(--evg-soft); font-variant-numeric: tabular-nums; }
.dial .bar { opacity: .92; transform-origin: 200px 200px; }
.dial.intro .bar { animation: bar-in .7s cubic-bezier(.2,.8,.2,1) both; animation-delay: var(--d); }
.dial .bar:hover { opacity: 1; }
@keyframes bar-in { from { opacity: 0; transform: scale(.82); } }
.dial .window { fill: none; stroke: url(#win); stroke-width: 18; stroke-linecap: round; }
.dial .window.sweep { stroke-dasharray: 1; stroke-dashoffset: 1; animation: sweep 1.1s cubic-bezier(.6,0,.2,1) forwards; animation-delay: calc(var(--i) * 120ms); }
.dial .window.preview { stroke-dasharray: .018 .014; opacity: .85; }
.dial .window.past { opacity: .35; }
.dial .window-glow { fill: none; stroke: #A3E635; stroke-width: 18; stroke-linecap: round; opacity: .35; }
.dial .window-glow.preview { opacity: .12; }
.dial .window-flow { fill: none; stroke: #fff; stroke-width: 4; stroke-linecap: round; stroke-dasharray: 2 16; opacity: .85; animation: flow 1.2s linear infinite; }
@keyframes sweep { to { stroke-dashoffset: 0; } }
@keyframes flow { to { stroke-dashoffset: -18; } }
.dial .needle { stroke: var(--evg-ink); stroke-width: 2.5; stroke-linecap: round; }
.dial .needle-dot { fill: var(--evg-ink); }
.dial .deadline-line { stroke: var(--evg-ink); stroke-width: 1.5; stroke-dasharray: 3 4; opacity: .55; }
.dial .deadline-dot { fill: var(--evg-card); stroke: var(--evg-ink); stroke-width: 2.5; }
.dial-center {
  position: absolute; inset: 31%; display: grid; place-content: center; justify-items: center; text-align: center; gap: 4px;
  pointer-events: none;
}
.dial-center .big { font-size: clamp(26px, 6.2vw, 40px); font-weight: 650; letter-spacing: -.03em; font-variant-numeric: tabular-nums; line-height: 1.05; }
.dial-center .big.muted { font-size: 18px; color: var(--evg-soft); }
.dial-center .range { color: var(--evg-soft); font-variant-numeric: tabular-nums; font-size: 15px; }
.dial-center .save { color: var(--evg-good); font-weight: 600; font-size: 14px; }
.dial-center .tag { font-size: 12px; font-weight: 600; color: var(--evg-a); background: color-mix(in srgb, var(--evg-a) 14%, transparent); padding: 2px 8px; border-radius: 999px; }
.status-line { display: inline-flex; align-items: center; gap: 10px; padding: 8px 16px; border-radius: 999px; background: var(--evg-card); border: 1px solid var(--evg-line); font-weight: 500; }
.status-line i { width: 10px; height: 10px; border-radius: 50%; background: var(--evg-soft); }
.status-line.planned i { background: var(--evg-a); }
.status-line.charging i { background: var(--evg-b); box-shadow: 0 0 0 0 color-mix(in srgb, var(--evg-b) 70%, transparent); animation: ping 1.6s ease-out infinite; }
.status-line.completed i { background: var(--evg-good); }
.status-line.error { border-color: color-mix(in srgb, var(--evg-bad) 45%, transparent); }
.status-line.error i { background: var(--evg-bad); }
.status-line.behind { border-color: color-mix(in srgb, var(--evg-bad) 45%, transparent); }
.status-line.behind i { background: var(--evg-bad); }
.status-line span { line-height: 1.35; }
@keyframes ping { to { box-shadow: 0 0 0 10px transparent; } }

/* ---------- guest */
.plate-row { display: flex; gap: 10px; align-items: stretch; }
.plate {
  position: relative; flex: 1; display: flex; align-items: stretch; min-width: 0; overflow: hidden;
  background: #fff; border: 3px solid #C8102E; border-radius: 10px; height: 60px;
  box-shadow: inset 0 0 0 2px #fff, 0 1px 2px rgba(0,0,0,.15);
}
.plate .eu { display: grid; align-content: end; justify-items: center; width: 34px; padding: 0 0 6px; background: #003399; color: #fff; font-weight: 700; font-size: 13px; letter-spacing: .02em; }
.plate .eu i { width: 16px; height: 16px; margin-bottom: 8px; border-radius: 50%; border: 2px dotted #FFCC00; }
.plate input {
  flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; color: #111;
  font-family: "DIN Alternate", "DIN Condensed", "Barlow Condensed", "Roboto Condensed", "Arial Narrow", sans-serif;
  font-weight: 700; font-size: 32px; letter-spacing: .08em; text-transform: uppercase; padding: 0 12px; text-align: center;
}
.plate input::placeholder { color: #c4c4c4; }
.plate:focus-within { outline: 2px solid var(--evg-accent); outline-offset: 3px; }
.plate .scan { position: absolute; inset: 0 0 0 34px; pointer-events: none; opacity: 0; }
.plate.scanning .scan { opacity: 1; background: linear-gradient(90deg, transparent, rgba(0,184,148,.35), transparent); background-size: 40% 100%; background-repeat: no-repeat; animation: scan 1s linear infinite; }
@keyframes scan { from { background-position: -40% 0; } to { background-position: 140% 0; } }
.car { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin-top: 14px; padding: 12px 14px; border-radius: 12px; background: color-mix(in srgb, var(--evg-a) 7%, transparent); }
.car.reveal { animation: rise .5s cubic-bezier(.2,.8,.2,1); }
@keyframes rise { from { opacity: 0; transform: translateY(6px); } }
.car-name { display: grid; gap: 2px; min-width: 0; }
.car-name strong { font-size: 18px; font-weight: 600; }
.car-name span { color: var(--evg-soft); font-size: 14px; }
.match { position: relative; width: 52px; height: 52px; flex: none; }
.match svg { width: 52px; height: 52px; transform: rotate(-90deg); }
.match circle { fill: none; stroke-width: 4; }
.match .track { stroke: var(--evg-line); }
.match .val { stroke: var(--evg-a); stroke-linecap: round; transition: stroke-dasharray .8s ease; }
.match span { position: absolute; inset: 0; display: grid; place-content: center; text-align: center; font-size: 9px; color: var(--evg-soft); line-height: 1.1; }
.match b { font-size: 14px; color: var(--evg-ink); }

/* ---------- fields */
.field { display: grid; grid-template-columns: 120px 1fr; align-items: center; gap: 12px; margin-top: 16px; }
.field > span { color: var(--evg-soft); font-size: 14px; }
.field.col { grid-template-columns: 1fr; gap: 6px; }
.field small { color: var(--evg-soft); font-size: 13px; line-height: 1.4; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chips button, .chip-input {
  border: 1px solid var(--evg-line); background: transparent; border-radius: 999px; padding: 7px 13px; cursor: pointer;
  font-variant-numeric: tabular-nums; transition: background .15s, border-color .15s, color .15s;
}
.chips button.on, .chip-input.on { background: var(--evg-ink); color: var(--evg-card); border-color: var(--evg-ink); }
.chips .none { color: var(--evg-soft); }
.chip-input { display: inline-flex; align-items: center; gap: 4px; padding: 4px 10px; }
.chip-input input { width: 54px; border: 0; background: transparent; outline: 0; padding: 3px 0; text-align: right; }
.chip-input.time input { width: auto; text-align: left; }
.chip-input.kw input:placeholder-shown { width: 52px; text-align: center; }
.chip-input.kw input:placeholder-shown + span { display: none; }
.chip-input input::-webkit-outer-spin-button, .chip-input input::-webkit-inner-spin-button { -webkit-appearance: none; margin: 0; }
.chip-input input[type="number"] { -moz-appearance: textfield; }
.chip-input.on input { color: inherit; }
.chip-input.on input::-webkit-calendar-picker-indicator { filter: invert(1); }
.segmented { display: inline-grid; grid-auto-flow: column; grid-auto-columns: 1fr; max-width: 100%; justify-self: start; background: color-mix(in srgb, var(--evg-ink) 6%, transparent); border-radius: 12px; padding: 3px; }
.segmented button { border: 0; background: transparent; padding: 8px 14px; border-radius: 9px; cursor: pointer; color: var(--evg-soft); font-weight: 500; }
.segmented button.on { background: var(--evg-card); color: var(--evg-ink); box-shadow: 0 1px 3px rgba(0,0,0,.12); }
.stepper { display: inline-flex; align-items: center; border: 1px solid var(--evg-line); border-radius: 12px; overflow: hidden; justify-self: start; }
.stepper button { border: 0; background: transparent; width: 40px; height: 38px; cursor: pointer; font-size: 18px; }
.stepper button:hover { background: color-mix(in srgb, var(--evg-ink) 6%, transparent); }
.stepper output { min-width: 92px; text-align: center; font-variant-numeric: tabular-nums; font-weight: 600; }
input[type="text"], input[type="number"]:not(.chip-input input), .unit-input {
  border: 1px solid var(--evg-line); border-radius: 10px; padding: 10px 12px; background: transparent; width: 100%;
}
.unit-input { display: flex; align-items: center; gap: 8px; padding: 0 12px; }
.unit-input input { border: 0 !important; padding: 10px 0 !important; outline: 0; }
.unit-input span { color: var(--evg-soft); white-space: nowrap; }
input[type="range"] { width: 100%; accent-color: var(--evg-a); }

/* ---------- battery */
.battery { display: flex; align-items: center; gap: 4px; margin-top: 18px; touch-action: none; }
.cells {
  position: relative; flex: 1; height: 64px; border-radius: 14px; border: 2.5px solid var(--evg-ink);
  background: color-mix(in srgb, var(--evg-ink) 4%, transparent); cursor: pointer;
}
.nub { width: 7px; height: 24px; border-radius: 0 4px 4px 0; background: var(--evg-ink); }
.fill-now, .fill-target, .flow { position: absolute; top: 4px; bottom: 4px; border-radius: 9px; }
.fill-now { left: 4px; max-width: calc(100% - 8px); background: linear-gradient(90deg, #00B894, #3CCB7F); transition: width .25s ease; }
.fill-target {
  background: repeating-linear-gradient(-45deg, color-mix(in srgb, var(--evg-b) 45%, transparent) 0 6px, color-mix(in srgb, var(--evg-b) 18%, transparent) 6px 12px);
  margin-right: 4px;
}
.flow { opacity: 0; pointer-events: none; }
.flow.on { opacity: 1; background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent) no-repeat; background-size: 30% 100%; animation: charge 1.8s linear infinite; }
@keyframes charge { from { background-position: -30% 0; } to { background-position: 130% 0; } }
.ticks i { position: absolute; top: 18px; bottom: 18px; width: 1.5px; background: var(--evg-ink); opacity: .12; }
.handle {
  position: absolute; top: 50%; width: 30px; height: 46px; margin: -23px 0 0 -15px; border-radius: 10px; padding: 0;
  background: var(--evg-card); border: 2.5px solid var(--evg-ink); cursor: grab; touch-action: none; z-index: 2;
  box-shadow: 0 2px 6px rgba(0,0,0,.18); transition: transform .12s;
}
.handle::after { content: attr(data-label); position: absolute; left: 50%; bottom: calc(100% + 8px); transform: translateX(-50%); font-size: 13px; font-weight: 600; white-space: nowrap; font-variant-numeric: tabular-nums; opacity: 0; transition: opacity .15s; }
.handle.dragging { cursor: grabbing; transform: scale(1.08); }
.handle.dragging::after, .handle:focus-visible::after { opacity: 1; }
.handle.target { border-color: #5FA21B; }
.battery-legend { display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; font-size: 14px; color: var(--evg-soft); font-variant-numeric: tabular-nums; }
.battery-legend b { color: var(--evg-ink); }
.battery-legend .gain { color: var(--evg-ink); font-weight: 500; }

/* ---------- buttons */
.actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 22px; }
.btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 8px; border-radius: 12px; padding: 12px 18px;
  border: 1px solid var(--evg-line); background: transparent; cursor: pointer; font-weight: 600; text-decoration: none; color: var(--evg-ink);
}
.btn svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
.btn:disabled { opacity: .5; cursor: default; }
.btn.primary { flex: 1; min-width: 180px; border: 0; color: #08281F; background: linear-gradient(90deg, #00B894, #A3E635); box-shadow: 0 6px 18px -8px rgba(0,184,148,.8); }
.btn.primary svg path { fill: currentColor; stroke: none; }
.btn.primary.pulse { animation: nudge 1.8s ease-in-out infinite; }
@keyframes nudge { 50% { box-shadow: 0 0 0 6px rgba(163,230,53,.25); } }
.btn.lookup { white-space: nowrap; }
.btn.danger { color: var(--evg-bad); }
.icon { border: 0; background: transparent; width: 40px; height: 40px; border-radius: 10px; display: grid; place-content: center; cursor: pointer; color: var(--evg-soft); }
.icon:hover { background: color-mix(in srgb, var(--evg-ink) 6%, transparent); color: var(--evg-ink); }
.icon svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }

/* ---------- facts */
.facts dl { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 14px 18px; margin: 0; }
.facts dt { color: var(--evg-soft); font-size: 13px; }
.facts dd { margin: 2px 0 0; font-size: 18px; font-weight: 600; font-variant-numeric: tabular-nums; letter-spacing: -.01em; }
.facts dl.is-preview dd { color: var(--evg-soft); }
.save-note { margin: 14px 0 0; color: var(--evg-good); font-weight: 500; }

/* ---------- timeline */
.timeline-wrap { position: relative; }
.timeline { width: 100%; height: 220px; touch-action: pan-y; }
.timeline .day-band { fill: color-mix(in srgb, var(--evg-ink) 3.5%, transparent); }
.timeline .day { font-size: 13px; fill: var(--evg-soft); font-weight: 500; }
.timeline .axis { font-size: 12px; fill: var(--evg-soft); font-variant-numeric: tabular-nums; }
.timeline .tl-bar { opacity: .88; transform-box: fill-box; transform-origin: bottom; }
.timeline.intro .tl-bar { animation: grow .6s cubic-bezier(.2,.8,.2,1) both; animation-delay: var(--d); }
.timeline .tl-bar.hot { opacity: 1; stroke: var(--evg-ink); stroke-width: 1.5; }
@keyframes grow { from { transform: scaleY(0); } }
.timeline .tl-window { fill: color-mix(in srgb, var(--evg-b) 28%, transparent); stroke: url(#tw); stroke-width: 2; }
.timeline .tl-window.preview { stroke-dasharray: 5 5; fill: color-mix(in srgb, var(--evg-b) 14%, transparent); }
.timeline .tl-now { stroke: var(--evg-ink); stroke-width: 2; }
.timeline .tl-now-label { font-size: 12px; font-weight: 600; fill: var(--evg-ink); }
.timeline .tl-deadline { stroke: var(--evg-ink); stroke-width: 1.5; stroke-dasharray: 4 4; opacity: .55; }
.scrub { position: absolute; top: 2px; transform: translateX(-50%); background: var(--evg-ink); color: var(--evg-card); border-radius: 10px; padding: 6px 10px; display: grid; font-size: 12px; pointer-events: none; white-space: nowrap; }
.scrub b { font-size: 14px; }
.scrub[hidden], [hidden] { display: none !important; }
.legend { display: flex; gap: 18px; color: var(--evg-soft); font-size: 13px; margin-top: 6px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { width: 18px; height: 10px; border-radius: 3px; display: inline-block; }
.sw.window { background: color-mix(in srgb, var(--evg-b) 35%, transparent); border: 1.5px solid #6CC24A; }
.sw.scale { background: linear-gradient(90deg, rgb(0,184,148), rgb(233,185,73), rgb(228,87,46)); }

/* ---------- history */
.totals .count { margin: 0 0 10px; color: var(--evg-soft); }
.totals dl { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 0; }
.totals dt { color: var(--evg-soft); font-size: 13px; }
.totals dd { margin: 2px 0 0; font-size: 22px; font-weight: 650; font-variant-numeric: tabular-nums; letter-spacing: -.02em; }
.totals dd.good { color: var(--evg-good); }
.spark { display: flex; align-items: flex-end; gap: 6px; height: 56px; margin-top: 16px; }
.spark i { flex: 1; border-radius: 4px 4px 2px 2px; background: linear-gradient(0deg, #00B894, #A3E635); transform-origin: bottom; animation: grow .6s cubic-bezier(.2,.8,.2,1) both; animation-delay: var(--d); }
.sessions { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.sessions li { display: grid; grid-template-columns: 52px 1fr auto auto; align-items: center; gap: 14px; background: var(--evg-card); border: 1px solid var(--evg-line); border-radius: 14px; padding: 12px 10px 12px 14px; }
.when { display: grid; justify-items: center; line-height: 1.1; }
.when b { font-size: 22px; }
.when span { color: var(--evg-soft); font-size: 12px; }
.what { display: grid; gap: 4px; min-width: 0; }
.what strong { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.what span { color: var(--evg-soft); font-size: 13px; display: flex; align-items: center; gap: 8px; font-variant-numeric: tabular-nums; }
.mini-plate { font-style: normal; font-size: 12px; font-weight: 700; letter-spacing: .06em; color: #111; background: #fff; border: 1.5px solid #C8102E; border-left: 6px solid #003399; border-radius: 4px; padding: 0 5px; }
.nums { display: grid; justify-items: end; font-variant-numeric: tabular-nums; }
.nums span { color: var(--evg-soft); font-size: 13px; }
.row-actions { display: flex; }
.delete-all { justify-self: start; }

/* ---------- settings */
.sources { margin: 0; display: grid; gap: 10px; }
.sources div { display: grid; grid-template-columns: 160px 1fr; gap: 10px; }
.sources dt { color: var(--evg-soft); }
.sources dd { margin: 0; word-break: break-word; }

/* ---------- toast and sheet */
.toast { position: fixed; left: 50%; bottom: calc(20px + var(--evg-safe-bottom)); transform: translate(-50%, 140%); z-index: 10; display: flex; align-items: center; gap: 10px;
  background: var(--evg-ink); color: var(--evg-card); border-radius: 14px; padding: 10px 8px 10px 16px; max-width: min(92vw, 560px); transition: transform .3s cubic-bezier(.2,.8,.2,1); }
.toast:not(.show) { visibility: hidden; }
.toast.show { transform: translate(-50%, 0); }
.toast.error { background: var(--evg-bad); color: #fff; }
.toast button { border: 0; background: transparent; color: inherit; width: 32px; height: 32px; display: grid; place-content: center; cursor: pointer; }
.toast svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 2; }
.scrim { position: fixed; inset: 0; background: rgba(0,0,0,.45); z-index: 20; animation: fade .2s; }
.sheet { position: fixed; z-index: 21; left: 50%; bottom: 0; transform: translateX(-50%); width: min(520px, 100%); background: var(--evg-card); border-radius: 22px 22px 0 0;
  padding: 18px 20px calc(22px + var(--evg-safe-bottom)); animation: up .3s cubic-bezier(.2,.8,.2,1); max-height: 90vh; overflow: auto; }
.sheet header { display: flex; justify-content: space-between; align-items: center; }
.sheet h2 { margin: 0; font-size: 18px; }
.receipt { margin: 10px 0 16px; padding: 18px; border-radius: 16px; background: color-mix(in srgb, var(--evg-a) 7%, transparent); }
.receipt .amount { margin: 0; font-size: 36px; font-weight: 650; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }
.receipt .sub { margin: 4px 0 12px; color: var(--evg-soft); display: flex; gap: 8px; align-items: center; }
.receipt pre { margin: 0; white-space: pre-wrap; font: inherit; font-size: 14px; line-height: 1.55; }
.sheet .segmented { margin-bottom: 4px; }
@keyframes fade { from { opacity: 0; } }
@keyframes up { from { transform: translate(-50%, 100%); } }

/* ---------- narrow screens */
@media (max-width: 860px) {
  .content { grid-template-columns: 1fr; padding: 14px 12px calc(96px + var(--evg-safe-bottom)); gap: 14px; }
  .col { gap: 14px; }
  .tabs { position: fixed; left: 0; right: 0; bottom: 0; justify-self: stretch; justify-content: space-around; background: var(--evg-card); border-top: 1px solid var(--evg-line); padding: 6px 8px calc(6px + var(--evg-safe-bottom)); z-index: 5; }
  .tabs button { flex-direction: column; gap: 2px; font-size: 12px; padding: 6px 12px; border-radius: 12px; }
  .tabs button em { position: absolute; top: 2px; right: 6px; }
  .bar { grid-template-columns: auto 1fr auto; }
  .field { grid-template-columns: 1fr; gap: 8px; }
  .panel { padding: 16px; }
  .sessions li { grid-template-columns: 44px 1fr auto; }
  .row-actions { grid-column: 2 / -1; justify-content: flex-end; margin-top: -6px; }
  .totals dd { font-size: 18px; }
  .sources div { grid-template-columns: 1fr; gap: 2px; }
  .toast { bottom: calc(84px + var(--evg-safe-bottom)); }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .001ms !important; animation-iteration-count: 1 !important; transition-duration: .001ms !important; }
}
`;

if (!customElements.get("ev-guest-panel")) customElements.define("ev-guest-panel", EvGuestPanel);
