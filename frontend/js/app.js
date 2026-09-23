import { MapEngine } from "./windyLoader.js";
import { TemperatureLayer } from "./temperatureLayer.js";
import { fetchLatestTemperatures } from "./api.js";
import { TEMP_SCALES } from "./colorScale.js";

class AppController {
  constructor() {
    this.mapEngine = new MapEngine();
    this.tempLayer = null;
    this.stations = [];
    this.autoRefreshIntervalSec = 300; // 5 minutes
    this.remainingSec = this.autoRefreshIntervalSec;
    this.timerId = null;
    this.activeWindyOverlay = "wind";
  }

  async start() {
    this._bindDOMEvents();

    try {
      this._updateStatus("正在載入地圖引擎...", "loading");
      const { map, isWindy } = await this.mapEngine.init("map-container");

      this.tempLayer = new TemperatureLayer(map);
      this._updateMapEngineBadge(isWindy);

      await this.loadData();
      this._startAutoRefreshTimer();
    } catch (err) {
      console.error("Initialization error:", err);
      this._updateStatus("初始化地圖或連線失敗", "error");
    }
  }

  async loadData(forceRefresh = false) {
    const refreshBtn = document.getElementById("btn-refresh");
    if (refreshBtn) refreshBtn.classList.add("spinning");

    this._updateStatus("正在讀取 CWA 氣溫觀測資料...", "loading");

    try {
      const data = await fetchLatestTemperatures(forceRefresh);
      this.stations = data.stations || [];

      this.tempLayer.setStations(this.stations);
      this._populateCountySelect(this.stations);
      this._renderTopRankings(this.stations);
      this._renderLegendCounts(this.stations);

      // Update observation time
      const timeStr = data.updated_at ? data.updated_at.replace("T", " ").replace("+08:00", "") : "剛才";
      document.getElementById("cwa-update-time").textContent = timeStr;
      document.getElementById("station-count-badge").textContent = `${this.stations.length} 個觀測站`;

      const sourceBadge = document.getElementById("data-source-badge");
      if (sourceBadge) {
        sourceBadge.textContent = data.source || "CWA";
      }

      this._updateStatus("即時連線正常", "online");
      this.remainingSec = this.autoRefreshIntervalSec;
    } catch (err) {
      console.error("Failed to load CWA temperature data:", err);
      this._updateStatus("無法取得氣象資料，請檢查後端連線", "error");
    } finally {
      if (refreshBtn) {
        setTimeout(() => refreshBtn.classList.remove("spinning"), 600);
      }
    }
  }

  _bindDOMEvents() {
    // Refresh button
    const refreshBtn = document.getElementById("btn-refresh");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => this.loadData(true));
    }

    // Toggle Station Labels
    const toggleLabels = document.getElementById("toggle-labels");
    if (toggleLabels) {
      toggleLabels.addEventListener("change", (e) => {
        this.tempLayer.setShowLabels(e.target.checked);
      });
    }

    // County Filter
    const countySelect = document.getElementById("county-filter");
    if (countySelect) {
      countySelect.addEventListener("change", (e) => {
        this.tempLayer.setFilters({ county: e.target.value });
      });
    }

    // Search Station
    const searchInput = document.getElementById("station-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.tempLayer.setFilters({ searchQuery: e.target.value });
      });
    }

    // Windy Layer Switcher
    const layerButtons = document.querySelectorAll(".layer-btn");
    layerButtons.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const overlay = btn.dataset.overlay;
        layerButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        this.activeWindyOverlay = overlay;
        this.mapEngine.setWindyOverlay(overlay);
      });
    });

    // Toggle Wind Particles
    const toggleParticles = document.getElementById("toggle-particles");
    if (toggleParticles) {
      toggleParticles.addEventListener("change", (e) => {
        this.mapEngine.setParticleAnimation(e.target.checked);
      });
    }

    // Settings Modal
    const settingsBtn = document.getElementById("btn-settings");
    const settingsModal = document.getElementById("settings-modal");
    const closeSettingsBtn = document.getElementById("btn-close-settings");
    const saveSettingsBtn = document.getElementById("btn-save-settings");
    const windyKeyInput = document.getElementById("input-windy-key");

    if (windyKeyInput) {
      windyKeyInput.value = localStorage.getItem("windy_api_key") || "";
    }

    if (settingsBtn && settingsModal) {
      settingsBtn.addEventListener("click", () => settingsModal.classList.remove("hidden"));
    }
    if (closeSettingsBtn && settingsModal) {
      closeSettingsBtn.addEventListener("click", () => settingsModal.classList.add("hidden"));
    }
    if (saveSettingsBtn && windyKeyInput) {
      saveSettingsBtn.addEventListener("click", () => {
        const key = windyKeyInput.value.trim();
        localStorage.setItem("windy_api_key", key);
        settingsModal.classList.add("hidden");
        // Reload to apply Windy key
        window.location.reload();
      });
    }
  }

  _populateCountySelect(stations) {
    const countySelect = document.getElementById("county-filter");
    if (!countySelect || countySelect.options.length > 1) return;

    const counties = Array.from(new Set(stations.map((s) => s.county).filter(Boolean))).sort();
    counties.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      countySelect.appendChild(opt);
    });
  }

  _renderTopRankings(stations) {
    if (!stations.length) return;

    // Filter valid temperatures and sort
    const valid = [...stations].filter((s) => s.temperature_c !== null && !isNaN(s.temperature_c));
    valid.sort((a, b) => b.temperature_c - a.temperature_c);

    const hottest = valid.slice(0, 4);
    const coldest = [...valid].reverse().slice(0, 4);

    const renderList = (items, containerId) => {
      const el = document.getElementById(containerId);
      if (!el) return;
      el.innerHTML = items
        .map(
          (s) => `
        <div class="rank-card" data-station-id="${s.station_id}">
          <div class="rank-info">
            <span class="rank-name">${s.station_name}</span>
            <span class="rank-loc">${s.county || ""} ${s.town || ""}</span>
          </div>
          <span class="rank-temp">${s.temperature_c.toFixed(1)}°C</span>
        </div>
      `
        )
        .join("");

      el.querySelectorAll(".rank-card").forEach((card) => {
        card.addEventListener("click", () => {
          const id = card.dataset.stationId;
          this.tempLayer.flyToStation(id);
        });
      });
    };

    renderList(hottest, "hottest-list");
    renderList(coldest, "coldest-list");
  }

  _renderLegendCounts(stations) {
    const legendEl = document.getElementById("legend-items");
    if (!legendEl) return;

    legendEl.innerHTML = TEMP_SCALES.map((scale) => {
      const count = stations.filter((s) => {
        if (s.temperature_c === null || isNaN(s.temperature_c)) return false;
        return s.temperature_c >= scale.min && s.temperature_c < scale.max;
      }).length;

      return `
        <div class="legend-row">
          <div class="legend-swatch" style="background: ${scale.color}"></div>
          <span class="legend-range">${scale.label}</span>
          <span class="legend-name">${scale.name}</span>
          <span class="legend-badge">${count}</span>
        </div>
      `;
    }).join("");
  }

  _startAutoRefreshTimer() {
    if (this.timerId) clearInterval(this.timerId);

    const countdownEl = document.getElementById("refresh-countdown");

    this.timerId = setInterval(() => {
      this.remainingSec--;
      if (countdownEl) {
        const m = Math.floor(this.remainingSec / 60);
        const s = (this.remainingSec % 60).toString().padStart(2, "0");
        countdownEl.textContent = `${m}:${s}`;
      }

      if (this.remainingSec <= 0) {
        this.loadData();
      }
    }, 1000);
  }

  _updateStatus(text, state = "online") {
    const statusText = document.getElementById("connection-status-text");
    const statusDot = document.getElementById("status-indicator-dot");
    if (statusText) statusText.textContent = text;
    if (statusDot) {
      statusDot.className = `status-dot dot-${state}`;
    }
  }

  _updateMapEngineBadge(isWindy) {
    const badge = document.getElementById("map-engine-badge");
    if (badge) {
      if (isWindy) {
        badge.innerHTML = `<span class="engine-tag windy">Windy Forecast API</span>`;
      } else {
        badge.innerHTML = `<span class="engine-tag leaflet">Leaflet Weather Layer</span>`;
      }
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const app = new AppController();
  app.start();
});
