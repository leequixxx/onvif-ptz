

const STRINGS = {
  en: {
    card_name: "ONVIF PTZ",
    card_description: "Joystick for controlling a pan-tilt camera",
    centered: "centered",
    speed: "Speed",
    ir: "IR",
    focus: "Focus",
    motion: "motion",
    expand: "Expand",
    collapse: "Collapse",
    loading: "loading…",
    connecting: "connecting…",
    reconnecting: "reconnecting…",
    no_link: "no link",
    joystick_hint:
      "Camera joystick. Use the arrow keys to pan and tilt.",
    video_title: "Camera video",
    err_no_stream: "Set stream — the source name from go2rtc.yaml.",
    err_mixed:
      "go2rtc is served over http while Home Assistant runs on https, so the browser blocks it. Use the add-on ingress path, or open Home Assistant over local http.",
    err_frame:
      "The player did not load — embedding is probably blocked.",
    err_frame_link: "Open in a new tab",
    err_stream_failed:
      "The stream did not start. Check go2rtc_url and the source name; details are in the browser console.",
    err_fallback_still:
      "Stream unavailable, showing a still frame. Details are in the browser console.",
    err_no_preview:
      "No preview: the camera returns no still image. Check still_image_url.",
    err_command: "The camera rejected the command",
    ed_title: "Title",
    ed_go2rtc_url: "go2rtc address",
    ed_stream: "Source name",
    ed_mode: "Mode",
    ed_camera_entity: "Camera (when not using go2rtc)",
    ed_live: "Live stream instead of a still",
    ed_speed: "Default speed",
    ed_axis_lock: "One axis at a time",
    ed_motion_entity: "Motion sensor",
    ed_night_entity: "Night mode",
    ed_autofocus_entity: "Autofocus",
    ed_presets: "Stored positions",
    ed_group_video: "Video",
    ed_group_control: "Control",
    ed_group_entities: "Camera entities",
    ed_mode_webrtc: "WebRTC — lowest latency",
    ed_mode_mse: "MSE — over the same HTTPS",
    ed_mode_mp4: "MP4 — most compatible",
    ed_help_url: "Path to go2rtc without /stream.html — the add-on ingress address, for example",
    ed_help_stream: "The name this source has in go2rtc.yaml",
    ed_help_axis:
      "Many cameras only pan when both axes are sent at once. Leave this on if tilting does not work",
    ed_help_presets: "A list like: - name: Gate, token: '1'",
    ed_layout: "Layout",
    ed_align: "Joystick alignment",
    ed_layout_auto: "Auto — by card width",
    ed_layout_stack: "Stacked — joystick below video",
    ed_layout_side: "Side by side — joystick next to video",
    ed_align_left: "Left",
    ed_align_center: "Center",
    ed_align_right: "Right",
    ed_help_align: "In the side-by-side layout this also picks which side the controls sit on.",
  },
  ru: {
    card_name: "ONVIF PTZ",
    card_description: "Джойстик для управления поворотной камерой",
    centered: "в центре",
    speed: "Скорость",
    ir: "ИК",
    focus: "Фокус",
    motion: "движение",
    expand: "Развернуть",
    collapse: "Свернуть",
    loading: "загрузка…",
    connecting: "подключение…",
    reconnecting: "переподключение…",
    no_link: "нет связи",
    joystick_hint:
      "Джойстик управления камерой. Стрелками — поворот и наклон.",
    video_title: "Видео с камеры",
    err_no_stream: "Укажите stream — имя потока из go2rtc.yaml.",
    err_mixed:
      "go2rtc доступен по http, а Home Assistant открыт по https — браузер заблокирует содержимое. Используйте ingress-путь аддона или откройте HA по локальному http-адресу.",
    err_frame:
      "Плеер не встроился — вероятно, запрещено встраивание в рамку.",
    err_frame_link: "Открыть в новой вкладке",
    err_stream_failed:
      "Поток не поднялся. Проверьте go2rtc_url и имя потока; подробности в консоли браузера.",
    err_fallback_still:
      "Поток не поднялся, показываю кадр. Подробности в консоли браузера.",
    err_no_preview:
      "Превью недоступно: камера не отдаёт кадр. Проверьте still_image_url.",
    err_command: "Камера не приняла команду",
    ed_title: "Заголовок",
    ed_go2rtc_url: "Адрес go2rtc",
    ed_stream: "Имя потока",
    ed_mode: "Режим",
    ed_camera_entity: "Камера (если без go2rtc)",
    ed_live: "Живой поток вместо кадра",
    ed_speed: "Скорость по умолчанию",
    ed_axis_lock: "Только одна ось за раз",
    ed_motion_entity: "Датчик движения",
    ed_night_entity: "Ночной режим",
    ed_autofocus_entity: "Автофокус",
    ed_presets: "Сохранённые позиции",
    ed_group_video: "Видео",
    ed_group_control: "Управление",
    ed_group_entities: "Сущности камеры",
    ed_mode_webrtc: "WebRTC — минимальная задержка",
    ed_mode_mse: "MSE — через тот же HTTPS",
    ed_mode_mp4: "MP4 — самый совместимый",
    ed_help_url: "Путь до go2rtc без /stream.html — например, ingress-адрес аддона",
    ed_help_stream: "Как поток назван в go2rtc.yaml",
    ed_help_axis:
      "Многие камеры при диагонали отрабатывают только поворот. Оставьте включённым, если наклон не работает",
    ed_help_presets: "Список вида: - name: Ворота, token: '1'",
    ed_layout: "Раскладка",
    ed_align: "Выравнивание джойстика",
    ed_layout_auto: "Авто — по ширине карточки",
    ed_layout_stack: "Столбиком — джойстик под видео",
    ed_layout_side: "Рядом — джойстик сбоку от видео",
    ed_align_left: "Слева",
    ed_align_center: "По центру",
    ed_align_right: "Справа",
    ed_help_align: "В раскладке «рядом» это же решает, с какой стороны будет панель управления.",
  },
};

function pickLang(hass) {
  const raw =
    (hass && (hass.language || (hass.locale && hass.locale.language))) ||
    (navigator.language || "en");
  const code = String(raw).slice(0, 2).toLowerCase();
  return STRINGS[code] ? code : "en";
}

function t(key, hass) {
  const lang = pickLang(hass);
  return STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
}

window.customCards = window.customCards || [];
if (!window.customCards.some((card) => card.type === "onvif-ptz-card")) {
  window.customCards.push({
    type: "onvif-ptz-card",
    name: t("card_name"),
    description: t("card_description"),
    preview: true,
  });
}

console.info("%c ONVIF-PTZ-CARD %c 2.4.0 ", "background:#03a9f4;color:#fff", "");

const MIN_DELTA = 0.08;
const KEEPALIVE_MS = 2000;
const DEADZONE = 0.12;
const MAX_SNAPSHOT_RETRIES = 3;
const WEBRTC_TIMEOUT_MS = 8000;
const WEBRTC_MAX_RETRIES = 5;

class OnvifPtzCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._vector = { x: 0, y: 0 };
    this._sent = { x: 0, y: 0 };
    this._active = false;
    this._keepalive = null;
    this._pending = false;
    this._rendered = false;
    this._pressedKeys = new Set();
  }

  static getConfigElement() {
    return document.createElement("onvif-ptz-card-editor");
  }

  static getStubConfig() {
    return { speed: 0.6, mode: "webrtc", axis_lock: true, layout: "auto", align: "center" };
  }

  _applyLayoutClasses() {
    const cfg = this._config;
    for (const name of ["auto", "stack", "side"]) {
      this.classList.toggle(`layout-${name}`, cfg.layout === name);
    }
    for (const name of ["left", "center", "right"]) {
      this.classList.toggle(`align-${name}`, cfg.align === name);
    }
  }

  setConfig(config) {
    this._config = {
      speed: 0.6,
      live: true,
      axis_lock: true,
      layout: "auto",
      align: "center",
      presets: [],
      ...config,
    };
    if (this._config.speed <= 0 || this._config.speed > 1) {
      throw new Error("speed must be between 0.1 and 1.0");
    }
    if (!["auto", "stack", "side"].includes(this._config.layout)) {
      throw new Error("layout must be auto, stack or side");
    }
    if (!["left", "center", "right"].includes(this._config.align)) {
      throw new Error("align must be left, center or right");
    }
    this._applyLayoutClasses();
    this._rendered = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._rendered) {
      this._render();
      this._rendered = true;
    }
    this._updatePreview();
    this._updateToggles();
    this._updateMotion();
  }

  getCardSize() {
    if (!this._config) return 5;
    const cfg = this._config;
    return cfg.go2rtc_url || cfg.camera_entity || cfg.stream_card ? 8 : 5;
  }

  _render() {
    const cfg = this._config;
    const presets = Array.isArray(cfg.presets) ? cfg.presets : [];

    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; }

        ha-card {
          container-type: inline-size;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .preview {
          position: relative;
          width: 100%;
          border-radius: var(--ha-card-border-radius, 12px);
          overflow: hidden;
          background: #000;
        }
        .frame { width: 100%; display: block; }
        .frame img,
        .frame video,
        .frame iframe {
          width: 100%;
          display: block;
          border: 0;
          background: #000;
          aspect-ratio: 16 / 9;
        }
        .frame video { object-fit: contain; }

        .tap { position: absolute; inset: 0; cursor: zoom-in; }

        .expand {
          position: absolute;
          top: 8px; right: 8px;
          width: 32px; height: 32px;
          display: grid; place-items: center;
          border: 0;
          border-radius: 8px;
          background: rgba(0,0,0,0.5);
          color: #fff;
          cursor: pointer;
          padding: 0;
        }
        .expand svg { width: 18px; height: 18px; fill: currentColor; }
        .expand:focus-visible {
          outline: 2px solid var(--primary-color);
          outline-offset: 2px;
        }

        .badge {
          position: absolute;
          top: 8px; left: 8px;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 11px;
          letter-spacing: 0.06em;
          background: rgba(0,0,0,0.55);
          color: #fff;
          pointer-events: none;
        }

        .controls {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .stage { display: flex; align-items: center; justify-content: center; }

        .pad {
          position: relative;
          width: clamp(150px, 55cqw, 210px);
          aspect-ratio: 1;
          flex: none;
          border-radius: 50%;
          background:
            radial-gradient(circle at 50% 50%,
              var(--card-background-color) 55%,
              var(--secondary-background-color) 100%);
          border: 2px solid var(--divider-color);
          touch-action: none;
          cursor: grab;
          display: grid;
          place-items: center;
          transition: border-color 120ms ease;
        }
        .pad:focus-visible {
          outline: 2px solid var(--primary-color);
          outline-offset: 3px;
        }
        .pad.live { cursor: grabbing; border-color: var(--primary-color); }

        .crosshair { position: absolute; inset: 0; pointer-events: none; opacity: 0.35; }
        .crosshair::before,
        .crosshair::after { content: ""; position: absolute; background: var(--divider-color); }
        .crosshair::before { left: 12%; right: 12%; top: 50%; height: 1px; }
        .crosshair::after { top: 12%; bottom: 12%; left: 50%; width: 1px; }

        .knob {
          position: absolute;
          width: 32%; aspect-ratio: 1;
          border-radius: 50%;
          background: var(--primary-color);
          box-shadow: 0 2px 8px rgba(0,0,0,0.28);
          display: grid; place-items: center;
          color: var(--text-primary-color, #fff);
          will-change: transform;
        }
        .knob svg { width: 42%; height: 42%; fill: currentColor; }

        .readout {
          font-family: var(--code-font-family, monospace);
          font-size: 12px;
          color: var(--secondary-text-color);
          text-align: center;
          min-height: 16px;
          letter-spacing: 0.04em;
        }

        .row { display: flex; align-items: center; gap: 12px; }
        .row label { font-size: 13px; color: var(--secondary-text-color); white-space: nowrap; }
        input[type="range"] { flex: 1; min-width: 0; accent-color: var(--primary-color); }

        .toggles { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
        button.toggle {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          border: 1px solid var(--divider-color);
          background: transparent;
          color: var(--secondary-text-color);
          border-radius: 16px;
          padding: 6px 12px;
          font-size: 13px;
          font-family: inherit;
          cursor: pointer;
        }
        button.toggle svg { width: 16px; height: 16px; fill: currentColor; }
        button.toggle[aria-pressed="true"] {
          border-color: var(--primary-color);
          color: var(--primary-color);
          background: color-mix(in srgb, var(--primary-color) 12%, transparent);
        }
        button.toggle:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }

        .motion {
          position: absolute;
          top: 8px; left: 8px;
          display: none;
          align-items: center;
          gap: 6px;
          padding: 3px 9px;
          border-radius: 10px;
          font-size: 11px;
          letter-spacing: 0.05em;
          background: rgba(219, 68, 55, 0.85);
          color: #fff;
          pointer-events: none;
        }
        .motion.active { display: inline-flex; }
        .motion::before {
          content: "";
          width: 6px; height: 6px;
          border-radius: 50%;
          background: #fff;
          animation: pulse 1.2s ease-in-out infinite;
        }
        @keyframes pulse { 50% { opacity: 0.25; } }
        @media (prefers-reduced-motion: reduce) {
          .motion::before { animation: none; }
        }

        .presets { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
        button.preset {
          border: 1px solid var(--divider-color);
          background: transparent;
          color: var(--primary-text-color);
          border-radius: 16px;
          padding: 6px 14px;
          font-size: 13px;
          font-family: inherit;
          cursor: pointer;
        }
        button.preset:hover { background: var(--secondary-background-color); }
        button.preset:focus-visible { outline: 2px solid var(--primary-color); outline-offset: 2px; }

        .error { color: var(--error-color, #db4437); font-size: 13px; min-height: 18px; }
        .error a { color: var(--primary-color); }

        @container (max-width: 320px) {
          ha-card { padding: 12px; gap: 12px; }
          .row label { font-size: 12px; }
          button.preset { padding: 5px 11px; font-size: 12px; }
        }

        .stage,
        .presets,
        .toggles { justify-content: center; }
        :host(.align-left) .stage,
        :host(.align-left) .presets,
        :host(.align-left) .toggles { justify-content: flex-start; }
        :host(.align-right) .stage,
        :host(.align-right) .presets,
        :host(.align-right) .toggles { justify-content: flex-end; }

        :host(.layout-side) ha-card,
        :host(.layout-auto) ha-card {
          display: flex;
          flex-direction: column;
        }

        :host(.layout-side) ha-card {
          display: grid;
          grid-template-columns: 1fr auto;
          align-items: start;
        }
        :host(.layout-side) .preview { grid-row: span 2; }
        :host(.layout-side) .controls { width: 220px; }
        :host(.layout-side) .pad { width: 190px; }
        :host(.layout-side) .error { grid-column: 1 / -1; }

        :host(.layout-side.align-left) ha-card {
          grid-template-columns: auto 1fr;
        }
        :host(.layout-side.align-left) .preview { grid-column: 2; grid-row: span 2; }
        :host(.layout-side.align-left) .controls { grid-column: 1; grid-row: 1; }
        :host(.layout-side) .stage,
        :host(.layout-side) .presets,
        :host(.layout-side) .toggles { justify-content: center; }

        @container (min-width: 620px) {
          :host(.layout-auto) ha-card {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: start;
          }
          :host(.layout-auto) .preview { grid-row: span 2; }
          :host(.layout-auto) .controls { width: 220px; }
          :host(.layout-auto) .pad { width: 190px; }
          :host(.layout-auto) .error { grid-column: 1 / -1; }
          :host(.layout-auto.align-left) ha-card {
            grid-template-columns: auto 1fr;
          }
          :host(.layout-auto.align-left) .preview { grid-column: 2; grid-row: span 2; }
          :host(.layout-auto.align-left) .controls { grid-column: 1; grid-row: 1; }
          :host(.layout-auto) .stage,
          :host(.layout-auto) .presets,
          :host(.layout-auto) .toggles { justify-content: center; }
        }

        :host(.expanded) .preview {
          position: fixed;
          inset: 0;
          z-index: 100;
          border-radius: 0;
          display: grid;
          place-items: center;
        }
        :host(.expanded) .frame,
        :host(.expanded) .frame iframe,
        :host(.expanded) .frame video {
          width: 100vw;
          height: 100vh;
          aspect-ratio: auto;
          object-fit: contain;
        }
        :host(.expanded) .tap { cursor: default; }
        :host(.expanded) .expand {
          top: max(12px, env(safe-area-inset-top));
          right: max(12px, env(safe-area-inset-right));
          z-index: 102;
        }
        :host(.expanded) .controls {
          position: fixed;
          z-index: 101;
          width: auto;
          gap: 8px;
          padding: 12px;
          border-radius: 16px;
          background: rgba(0, 0, 0, 0.45);
          backdrop-filter: blur(8px);
          right: max(16px, env(safe-area-inset-right));
          bottom: max(16px, env(safe-area-inset-bottom));
        }
        :host(.expanded) .pad {
          width: 128px;
          background: rgba(255,255,255,0.08);
          border-color: rgba(255,255,255,0.35);
        }
        :host(.expanded) .readout { color: rgba(255,255,255,0.75); }

        :host(.expanded) .row {
          width: 128px;
          gap: 8px;
        }
        :host(.expanded) .row label {
          color: rgba(255,255,255,0.75);
          font-size: 11px;
        }
        :host(.expanded) .row label[for="speed"] { display: none; }

        :host(.expanded) .presets { display: none; }
        :host(.expanded) .toggles { width: 128px; }
        :host(.expanded) button.toggle {
          flex: 1;
          justify-content: center;
          padding: 5px 8px;
          font-size: 11px;
          color: rgba(255,255,255,0.8);
          border-color: rgba(255,255,255,0.3);
        }
        :host(.expanded) button.toggle[aria-pressed="true"] {
          color: #fff;
          border-color: var(--primary-color);
          background: var(--primary-color);
        }
        :host(.expanded) .error { display: none; }

        @media (max-width: 640px) {
          :host(.expanded) .pad { width: 112px; }
          :host(.expanded) .row,
          :host(.expanded) .toggles { width: 112px; }
        }

        @media (prefers-reduced-motion: reduce) {
          .pad, .knob { transition: none; }
        }
      </style>

      <ha-card${cfg.title ? ` header="${this._escape(cfg.title)}"` : ""}>
        ${
          cfg.go2rtc_url || cfg.camera_entity || cfg.stream_card
            ? `<div class="preview">
                 <div class="frame" id="preview"></div>
                 <div class="tap" id="tap"></div>
                 <span class="motion" id="motion">${this._t("motion")}</span>
                 <button class="expand" id="expand" aria-label="${this._t("expand")}"
                         aria-pressed="false">
                   <svg viewBox="0 0 24 24" aria-hidden="true"><path id="expand-icon"
                     d="M4 4h6v2H6v4H4V4zm10 0h6v6h-2V6h-4V4zM4 14h2v4h4v2H4v-6zm14 0h2v6h-6v-2h4v-4z"/></svg>
                 </button>
               </div>`
            : ""
        }

        <div class="controls">
        <div class="stage">
          <div class="pad" id="pad" tabindex="0" role="application"
               aria-label="${this._t('joystick_hint')}">
            <div class="crosshair"></div>
            <div class="knob" id="knob">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 4l3 3h-2v3h3V8l3 3-3 3v-2h-3v3h2l-3 3-3-3h2v-3H8v2l-3-3 3-3v2h3V7H9l3-3z"/>
              </svg>
            </div>
          </div>
        </div>

        <div class="readout" id="readout">${this._t("centered")}</div>

        <div class="row">
          <label for="speed">${this._t("speed")}</label>
          <input type="range" id="speed" min="0.1" max="1" step="0.05"
                 value="${cfg.speed}">
          <label id="speedval">${Math.round(cfg.speed * 100)}%</label>
        </div>

        <div class="toggles" id="toggles">
          <button class="toggle" id="toggle-night" aria-pressed="false" hidden>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3a9 9 0 108.9 10.5A7 7 0 0112 3z"/></svg>
            <span>${this._t("ir")}</span>
          </button>
          <button class="toggle" id="toggle-focus" aria-pressed="false" hidden>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 8a4 4 0 100 8 4 4 0 000-8zm0-6v3m0 14v3m10-10h-3M5 12H2"/><circle cx="12" cy="12" r="3"/></svg>
            <span>${this._t("focus")}</span>
          </button>
        </div>

        ${
          presets.length
            ? `<div class="presets">${presets
                .map(
                  (p, i) =>
                    `<button class="preset" data-index="${i}">${this._escape(
                      p.name || p.token
                    )}</button>`
                )
                .join("")}</div>`
            : ""
        }

        </div>

        <div class="error" id="error"></div>
      </ha-card>
    `;

    this._pad = this.shadowRoot.getElementById("pad");
    this._knob = this.shadowRoot.getElementById("knob");
    this._readout = this.shadowRoot.getElementById("readout");
    this._errorBox = this.shadowRoot.getElementById("error");

    if (cfg.go2rtc_url || cfg.camera_entity || cfg.stream_card) this._mountStream();

    this._bindPointer();
    this._bindKeyboard();
    this._bindExpand();
    this._bindToggles();
    this._observeResize();
    this._bindSpeed();
    this._bindPresets(presets);
  }

  _t(key) {
    return t(key, this._hass);
  }

  _escape(text) {
    return String(text).replace(
      /[&<>"']/g,
      (c) =>
        ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );
  }

  _bindPointer() {
    const pad = this._pad;

    const positionFrom = (event) => {
      const rect = pad.getBoundingClientRect();
      const radius = rect.width / 2;
      let dx = (event.clientX - rect.left - radius) / radius;
      let dy = (event.clientY - rect.top - radius) / radius;

      const length = Math.hypot(dx, dy);
      if (length > 1) {
        dx /= length;
        dy /= length;
      }
      return { x: dx, y: dy };
    };

    pad.addEventListener("pointerdown", (event) => {
      pad.setPointerCapture(event.pointerId);
      pad.classList.add("live");
      this._active = true;
      this._onVector(positionFrom(event));
      this._startKeepalive();
    });

    pad.addEventListener("pointermove", (event) => {
      if (!this._active) return;
      this._onVector(positionFrom(event));
    });

    const release = (event) => {
      if (!this._active) return;
      this._active = false;
      pad.classList.remove("live");
      if (event.pointerId !== undefined && pad.hasPointerCapture(event.pointerId)) {
        pad.releasePointerCapture(event.pointerId);
      }
      this._center();
    };

    pad.addEventListener("pointerup", release);
    pad.addEventListener("pointercancel", release);
    pad.addEventListener("lostpointercapture", release);
  }

  _bindKeyboard() {
    const map = {
      ArrowLeft: { x: -1, y: 0 },
      ArrowRight: { x: 1, y: 0 },
      ArrowUp: { x: 0, y: -1 },
      ArrowDown: { x: 0, y: 1 },
    };

    this._pad.addEventListener("keydown", (event) => {
      const dir = map[event.key];
      if (!dir) return;
      event.preventDefault();
      if (this._pressedKeys.has(event.key)) return;
      this._pressedKeys.add(event.key);
      this._applyKeys(map);
      this._startKeepalive();
    });

    this._pad.addEventListener("keyup", (event) => {
      if (!map[event.key]) return;
      event.preventDefault();
      this._pressedKeys.delete(event.key);
      if (this._pressedKeys.size === 0) {
        this._center();
      } else {
        this._applyKeys(map);
      }
    });

    this._pad.addEventListener("blur", () => {
      if (this._pressedKeys.size) {
        this._pressedKeys.clear();
        this._center();
      }
    });
  }

  _applyKeys(map) {
    let x = 0;
    let y = 0;
    this._pressedKeys.forEach((key) => {
      x += map[key].x;
      y += map[key].y;
    });
    const length = Math.hypot(x, y) || 1;
    this._onVector({ x: x / length, y: y / length });
  }

  _bindExpand() {
    const tap = this.shadowRoot.getElementById("tap");
    const button = this.shadowRoot.getElementById("expand");
    if (!tap || !button) return;

    tap.addEventListener("click", () => {
      if (!this._expanded) this._setExpanded(true);
    });

    button.addEventListener("click", (event) => {
      event.stopPropagation();
      this._setExpanded(!this._expanded);
    });

    this._onKeyDown = (event) => {
      if (event.key === "Escape" && this._expanded) this._setExpanded(false);
    };
    document.addEventListener("keydown", this._onKeyDown);
  }

  _setExpanded(expanded) {
    this._expanded = expanded;
    this.classList.toggle("expanded", expanded);

    const button = this.shadowRoot.getElementById("expand");
    if (button) {
      button.setAttribute("aria-pressed", String(expanded));
      button.setAttribute(
        "aria-label",
        this._t(expanded ? "collapse" : "expand")
      );
      const icon = this.shadowRoot.getElementById("expand-icon");
      if (icon) {
        icon.setAttribute(
          "d",
          expanded
            ? "M10 4v6H4V8h4V4h2zm4 0h2v4h4v2h-6V4zM4 14h6v6H8v-4H4v-2zm10 0h6v2h-4v4h-2v-6z"
            : "M4 4h6v2H6v4H4V4zm10 0h6v6h-2V6h-4V4zM4 14h2v4h4v2H4v-6zm14 0h2v6h-6v-2h4v-4z"
        );
      }
    }

    requestAnimationFrame(() => this._paint(this._vector));
  }

  _observeResize() {
    if (!window.ResizeObserver || !this._pad) return;
    this._resizeObserver = new ResizeObserver(() => this._paint(this._vector));
    this._resizeObserver.observe(this._pad);
  }

  _bindSpeed() {
    const slider = this.shadowRoot.getElementById("speed");
    const label = this.shadowRoot.getElementById("speedval");
    slider.addEventListener("input", () => {
      this._config.speed = parseFloat(slider.value);
      label.textContent = `${Math.round(this._config.speed * 100)}%`;
    });
  }

  _bindToggles() {
    const pairs = [
      ["toggle-night", "night_entity"],
      ["toggle-focus", "autofocus_entity"],
    ];

    for (const [id, key] of pairs) {
      const button = this.shadowRoot.getElementById(id);
      const entity = this._config[key];
      if (!button || !entity) continue;

      button.hidden = false;
      button.addEventListener("click", () => {
        this._hass.callService("switch", "toggle", { entity_id: entity });
      });
    }
  }

  _updateToggles() {
    if (!this._hass) return;

    const pairs = [
      ["toggle-night", this._config.night_entity],
      ["toggle-focus", this._config.autofocus_entity],
    ];

    for (const [id, entity] of pairs) {
      const button = this.shadowRoot.getElementById(id);
      if (!button || !entity) continue;
      const state = this._hass.states[entity];
      const on = state && state.state === "on";
      button.setAttribute("aria-pressed", String(Boolean(on)));
      button.disabled = !state || state.state === "unavailable";
    }
  }

  _updateMotion() {
    const badge = this.shadowRoot.getElementById("motion");
    const entity = this._config.motion_entity;
    if (!badge || !entity || !this._hass) return;
    const state = this._hass.states[entity];
    badge.classList.toggle("active", Boolean(state && state.state === "on"));
  }

  _bindPresets(presets) {
    this.shadowRoot.querySelectorAll("button.preset").forEach((button) => {
      button.addEventListener("click", () => {
        const preset = presets[parseInt(button.dataset.index, 10)];
        if (!preset || !preset.token) return;
        this._callService("goto_preset", { preset: String(preset.token) });
      });
    });
  }

  _lockAxis(vector) {
    if (this._config.axis_lock === false) return vector;
    return Math.abs(vector.x) >= Math.abs(vector.y)
      ? { x: vector.x, y: 0 }
      : { x: 0, y: vector.y };
  }

  _onVector(rawVector) {
    const vector = this._lockAxis(rawVector);
    this._vector = vector;
    this._paint(rawVector, vector);

    const length = Math.hypot(vector.x, vector.y);
    if (length < DEADZONE) {
      if (Math.hypot(this._sent.x, this._sent.y) > 0) this._center();
      return;
    }

    const moved =
      Math.abs(vector.x - this._sent.x) > MIN_DELTA ||
      Math.abs(vector.y - this._sent.y) > MIN_DELTA;

    if (moved) this._send(vector);
  }

  _paint(knobVector, sentVector = knobVector) {
    const radius = (this._pad.clientWidth - this._knob.offsetWidth) / 2;
    this._knob.style.transform =
      `translate(${knobVector.x * radius}px, ${knobVector.y * radius}px)`;

    const length = Math.hypot(sentVector.x, sentVector.y);
    if (length < DEADZONE) {
      this._readout.textContent = this._t("centered");
    } else {
      const pan = (sentVector.x * this._config.speed).toFixed(2);
      const tilt = (-sentVector.y * this._config.speed).toFixed(2);
      this._readout.textContent = `pan ${pan}  tilt ${tilt}`;
    }
  }

  _send(vector) {
    this._sent = { ...vector };
    this._callService("move", {
      pan: +(vector.x * this._config.speed).toFixed(3),
      tilt: +(-vector.y * this._config.speed).toFixed(3),
    });
  }

  _center() {
    this._stopKeepalive();
    this._vector = { x: 0, y: 0 };
    this._sent = { x: 0, y: 0 };
    this._paint(this._vector);
    this._callService("stop", {});
  }

  _startKeepalive() {
    this._stopKeepalive();
    this._keepalive = setInterval(() => {
      const length = Math.hypot(this._vector.x, this._vector.y);
      if (length >= DEADZONE) this._send(this._vector);
    }, KEEPALIVE_MS);
  }

  _stopKeepalive() {
    if (this._keepalive) {
      clearInterval(this._keepalive);
      this._keepalive = null;
    }
  }

  async _callService(service, data) {
    if (!this._hass) return;
    if (this._config.entry_id) data.entry_id = this._config.entry_id;

    try {
      await this._hass.callService("onvif_ptz", service, data);
      this._errorBox.textContent = "";
    } catch (err) {
      this._errorBox.textContent =
        (err && err.message) || this._t("err_command");
    }
  }

  _mountWebRTC(host) {
    const base = String(this._config.go2rtc_url).replace(/\/+$/, "");
    const src = this._config.stream || this._config.camera_entity;

    if (!src) {
      this._errorBox.textContent =
        this._t("err_no_stream");
      return;
    }

    if (window.location.protocol === "https:" && base.startsWith("http://")) {
      this._errorBox.textContent = this._t("err_mixed");
      return;
    }

    const mode = this._config.mode || "webrtc";

    if (this._config.native_webrtc !== true) {
      const url =
        `${base}/stream.html?src=${encodeURIComponent(src)}` +
        `&mode=${encodeURIComponent(mode)}`;
      console.info("onvif-ptz-card: embedding go2rtc player", url);

      const frame = document.createElement("iframe");
      frame.src = url;
      frame.setAttribute("allow", "autoplay; fullscreen");
      frame.setAttribute("scrolling", "no");
      frame.setAttribute("title", this._t("video_title"));

      host.innerHTML =
        `<span class="badge" id="badge">${this._t("loading")}</span>`;
      host.appendChild(frame);
      this._frame = frame;
      this._badge = host.querySelector("#badge");

      let loaded = false;
      frame.addEventListener("load", () => {
        loaded = true;
        if (this._badge) this._badge.remove();
      });

      setTimeout(() => {
        if (loaded || !this._frame) return;
        this._errorBox.innerHTML =
          this._escape(this._t("err_frame")) +
          ' <a href="' + this._escape(url) + '" target="_blank" rel="noopener">' +
          this._escape(this._t("err_frame_link")) + "</a>";
        console.error(
          "onvif-ptz-card: iframe did not load. Check the X-Frame-Options " +
            "and Content-Security-Policy headers for " + url
        );
      }, 6000);

      return;
    }

    host.innerHTML =
      '<video id="webrtc" autoplay playsinline muted></video>' +
      `<span class="badge" id="badge">${this._t("connecting")}</span>`;

    this._video = host.querySelector("#webrtc");
    this._badge = host.querySelector("#badge");
    this._webrtcRetries = 0;
    this._connectWebRTC(base, src);
  }

  _connectWebRTC(base, src) {
    this._teardownWebRTC();

    const wsUrl =
      base.replace(/^http/, "ws") + "/api/ws?src=" + encodeURIComponent(src);

    let ws;
    try {
      ws = new WebSocket(wsUrl);
    } catch (err) {
      this._webrtcFailed(base, src, err);
      return;
    }
    this._ws = ws;

    const pc = new RTCPeerConnection({
      iceServers: [],
      bundlePolicy: "max-bundle",
    });
    this._pc = pc;

    this._webrtcTimer = setTimeout(() => {
      if (!this._video || this._video.readyState < 2) {
        this._webrtcFailed(base, src, new Error("no video within the timeout"));
      }
    }, WEBRTC_TIMEOUT_MS);

    pc.addTransceiver("video", { direction: "recvonly" });
    if (this._config.audio) {
      pc.addTransceiver("audio", { direction: "recvonly" });
    }

    pc.ontrack = (event) => {
      if (this._video && event.streams && event.streams[0]) {
        this._video.srcObject = event.streams[0];
      }
    };

    pc.onicecandidate = (event) => {
      if (!event.candidate || ws.readyState !== WebSocket.OPEN) return;
      ws.send(
        JSON.stringify({
          type: "webrtc/candidate",
          value: event.candidate.candidate,
        })
      );
    };

    pc.onconnectionstatechange = () => {
      if (!this._badge) return;
      const state = pc.connectionState;
      if (state === "connected") {
        this._badge.textContent = "WebRTC";
        this._errorBox.textContent = "";
        this._webrtcRetries = 0;
        clearTimeout(this._webrtcTimer);
      } else if (state === "failed" || state === "disconnected") {
        this._webrtcFailed(base, src, new Error(`connection ${state}`));
      }
    };

    ws.addEventListener("open", async () => {
      try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        ws.send(JSON.stringify({ type: "webrtc/offer", value: offer.sdp }));
      } catch (err) {
        this._webrtcFailed(base, src, err);
      }
    });

    ws.addEventListener("message", async (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch {
        return;
      }

      try {
        if (message.type === "webrtc/answer") {
          await pc.setRemoteDescription({ type: "answer", sdp: message.value });
        } else if (message.type === "webrtc/candidate" && message.value) {
          await pc.addIceCandidate({ candidate: message.value, sdpMid: "0" });
        } else if (message.type === "error") {
          this._webrtcFailed(base, src, new Error(message.value));
        }
      } catch (err) {
        console.warn("onvif-ptz-card: signalling", err);
      }
    });

    ws.addEventListener("error", () => {
      this._webrtcFailed(base, src, new Error("WebSocket did not open"));
    });

    ws.addEventListener("close", () => {
      if (pc.connectionState !== "connected") {
        this._webrtcFailed(base, src, new Error("signalling closed"));
      }
    });
  }

  _webrtcFailed(base, src, err) {
    if (this._webrtcRetrying) return;
    this._webrtcRetries += 1;

    if (this._webrtcRetries > WEBRTC_MAX_RETRIES) {
      this._teardownWebRTC();
      if (this._badge) this._badge.textContent = this._t("no_link");
      this._errorBox.textContent = this._t("err_stream_failed");
      console.error("onvif-ptz-card: WebRTC failed to start", err);
      return;
    }

    if (this._badge) this._badge.textContent = this._t("reconnecting");
    this._webrtcRetrying = true;
    setTimeout(() => {
      this._webrtcRetrying = false;
      this._connectWebRTC(base, src);
    }, 1000 * this._webrtcRetries);
  }

  _teardownWebRTC() {
    if (this._frame) {
      this._frame.remove();
      this._frame = null;
    }
    clearTimeout(this._webrtcTimer);
    if (this._ws) {
      try {
        this._ws.close();
      } catch {}
      this._ws = null;
    }
    if (this._pc) {
      try {
        this._pc.close();
      } catch {}
      this._pc = null;
    }
  }

  async _mountStream() {
    const host = this.shadowRoot.getElementById("preview");
    if (!host) return;

    if (this._config.go2rtc_url) {
      this._mountWebRTC(host);
      return;
    }

    const config = this._config.stream_card || {
      type: "picture-entity",
      entity: this._config.camera_entity,
      camera_view: this._config.live === false ? "auto" : "live",
      show_name: false,
      show_state: false,
    };

    try {
      const helpers = await window.loadCardHelpers();
      const card = await helpers.createCardElement(config);
      card.hass = this._hass;
      host.innerHTML = "";
      host.appendChild(card);
      this._streamCard = card;
    } catch (err) {
      console.error("onvif-ptz-card: live stream failed", err);
      this._errorBox.textContent = this._t("err_fallback_still");
      host.innerHTML = '<img id="preview-img" alt="">';
      const image = host.querySelector("#preview-img");
      this._snapshotFails = 0;
      image.addEventListener("error", () => {
        if (this._snapshotRetry) return;
        this._snapshotFails += 1;
        if (this._snapshotFails > MAX_SNAPSHOT_RETRIES) {
          this._errorBox.textContent = this._t("err_no_preview");
          return;
        }
        this._snapshotRetry = setTimeout(() => {
          this._snapshotRetry = null;
          this._updateSnapshot(true);
        }, 5000 * this._snapshotFails);
      });
      this._updateSnapshot(true);
    }
  }

  _updatePreview() {
    if (this._frame || this._pc) return;
    if (this._streamCard) {
      this._streamCard.hass = this._hass;
      return;
    }
    this._updateSnapshot();
  }

  _updateSnapshot(force = false) {
    const entity = this._config.camera_entity;
    if (!entity || !this._hass) return;
    const image = this.shadowRoot.getElementById("preview-img");
    if (!image) return;

    const state = this._hass.states[entity];
    if (!state || !state.attributes.entity_picture) return;

    const url = state.attributes.entity_picture;
    if (force || url !== this._lastPictureUrl) {
      this._lastPictureUrl = url;
      image.src = url;
    }
  }

  disconnectedCallback() {
    if (this._onKeyDown) {
      document.removeEventListener("keydown", this._onKeyDown);
      this._onKeyDown = null;
    }
    if (this._resizeObserver) {
      this._resizeObserver.disconnect();
      this._resizeObserver = null;
    }
    this.classList.remove("expanded");
    this._teardownWebRTC();
    if (this._snapshotRetry) {
      clearTimeout(this._snapshotRetry);
      this._snapshotRetry = null;
    }
    this._stopKeepalive();
    if (Math.hypot(this._sent.x, this._sent.y) > 0) {
      this._callService("stop", {});
    }
  }
}

function editorSchema(hass) {
  const s = (key) => t(key, hass);
  return [
    { name: "title", selector: { text: {} } },
    {
      name: "",
      type: "expandable",
      title: s("ed_group_video"),
      schema: [
        { name: "go2rtc_url", selector: { text: {} } },
        { name: "stream", selector: { text: {} } },
        {
          name: "mode",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "webrtc", label: s("ed_mode_webrtc") },
                { value: "mse", label: s("ed_mode_mse") },
                { value: "mp4", label: s("ed_mode_mp4") },
              ],
            },
          },
        },
        { name: "camera_entity", selector: { entity: { domain: "camera" } } },
        { name: "live", selector: { boolean: {} } },
      ],
    },
    {
      name: "",
      type: "expandable",
      title: s("ed_group_control"),
      schema: [
        {
          name: "speed",
          selector: { number: { min: 0.1, max: 1, step: 0.05, mode: "slider" } },
        },
        { name: "axis_lock", selector: { boolean: {} } },
        {
          name: "layout",
          selector: {
            select: {
              mode: "dropdown",
              options: [
                { value: "auto", label: s("ed_layout_auto") },
                { value: "stack", label: s("ed_layout_stack") },
                { value: "side", label: s("ed_layout_side") },
              ],
            },
          },
        },
        {
          name: "align",
          selector: {
            select: {
              mode: "box",
              options: [
                { value: "left", label: s("ed_align_left") },
                { value: "center", label: s("ed_align_center") },
                { value: "right", label: s("ed_align_right") },
              ],
            },
          },
        },
      ],
    },
    {
      name: "",
      type: "expandable",
      title: s("ed_group_entities"),
      schema: [
        { name: "motion_entity", selector: { entity: { domain: "binary_sensor" } } },
        { name: "night_entity", selector: { entity: { domain: "switch" } } },
        { name: "autofocus_entity", selector: { entity: { domain: "switch" } } },
      ],
    },
    { name: "presets", selector: { object: {} } },
  ];
}

const LABEL_KEYS = {
  title: "ed_title",
  go2rtc_url: "ed_go2rtc_url",
  stream: "ed_stream",
  mode: "ed_mode",
  camera_entity: "ed_camera_entity",
  live: "ed_live",
  speed: "ed_speed",
  axis_lock: "ed_axis_lock",
  layout: "ed_layout",
  align: "ed_align",
  motion_entity: "ed_motion_entity",
  night_entity: "ed_night_entity",
  autofocus_entity: "ed_autofocus_entity",
  presets: "ed_presets",
};

const HELPER_KEYS = {
  go2rtc_url: "ed_help_url",
  stream: "ed_help_stream",
  axis_lock: "ed_help_axis",
  align: "ed_help_align",
  presets: "ed_help_presets",
};

class OnvifPtzCardEditor extends HTMLElement {
  _applyLayoutClasses() {
    const cfg = this._config;
    for (const name of ["auto", "stack", "side"]) {
      this.classList.toggle(`layout-${name}`, cfg.layout === name);
    }
    for (const name of ["left", "center", "right"]) {
      this.classList.toggle(`align-${name}`, cfg.align === name);
    }
  }

  setConfig(config) {
    this._config = { ...config };
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
  }

  _render() {
    if (this._form) {
      this._form.data = this._config;
      return;
    }

    const form = document.createElement("ha-form");
    form.schema = editorSchema(this._hass);
    form.data = this._config;
    form.hass = this._hass;
    form.computeLabel = (item) =>
      LABEL_KEYS[item.name] ? t(LABEL_KEYS[item.name], this._hass) : item.name;
    form.computeHelper = (item) =>
      HELPER_KEYS[item.name] ? t(HELPER_KEYS[item.name], this._hass) : "";

    form.addEventListener("value-changed", (event) => {
      event.stopPropagation();

      const next = {};
      for (const [key, value] of Object.entries(event.detail.value)) {
        if (value === "" || value === undefined || value === null) continue;
        next[key] = value;
      }
      next.type = this._config.type || "custom:onvif-ptz-card";

      this._config = next;
      this.dispatchEvent(
        new CustomEvent("config-changed", {
          detail: { config: next },
          bubbles: true,
          composed: true,
        })
      );
    });

    this._form = form;
    this.appendChild(form);
  }
}

customElements.define("onvif-ptz-card-editor", OnvifPtzCardEditor);

customElements.define("onvif-ptz-card", OnvifPtzCard);

