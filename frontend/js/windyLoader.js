/**
 * Windy Map Forecast API Loader with Smart Leaflet Fallback
 */

export class MapEngine {
  constructor() {
    this.map = null;
    this.windyAPI = null;
    this.isWindy = false;
    this.currentOverlay = "wind";
  }

  async init(containerId, options = {}) {
    const {
      apiKey = localStorage.getItem("windy_api_key") || "",
      lat = 23.75,
      lon = 120.95,
      zoom = 7.5,
      overlay = "wind"
    } = options;

    const container = document.getElementById(containerId);
    if (!container) {
      throw new Error(`Map container #${containerId} not found`);
    }

    // Check if Windy API Key is available
    if (apiKey && apiKey.trim().length > 10) {
      try {
        await this._initWindy(containerId, apiKey.trim(), { lat, lon, zoom, overlay });
        return { map: this.map, isWindy: true, windyAPI: this.windyAPI };
      } catch (err) {
        console.warn("Windy initialization failed, falling back to Leaflet:", err);
      }
    }

    // Fallback to high-definition Leaflet Dark Mode
    this._initLeafletFallback(containerId, { lat, lon, zoom });
    return { map: this.map, isWindy: false, windyAPI: null };
  }

  async _initWindy(containerId, key, { lat, lon, zoom, overlay }) {
    if (typeof window.windyInit !== "function") {
      throw new Error("Windy libBoot.js not loaded");
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Windy initialization timeout (8s)"));
      }, 8000);

      const windyOptions = {
        key: key,
        lat: lat,
        lon: lon,
        zoom: Math.round(zoom),
        overlay: overlay,
        verbose: false
      };

      try {
        window.windyInit(windyOptions, (windyAPI) => {
          clearTimeout(timeout);
          this.windyAPI = windyAPI;
          this.map = windyAPI.map;
          this.isWindy = true;

          // Configure default store parameters
          try {
            windyAPI.store.set("overlay", overlay);
            windyAPI.store.set("particlesAnim", "on");
          } catch (e) {
            console.warn("Error setting Windy store options:", e);
          }

          resolve();
        });
      } catch (err) {
        clearTimeout(timeout);
        reject(err);
      }
    });
  }

  _initLeafletFallback(containerId, { lat, lon, zoom }) {
    if (typeof window.L === "undefined") {
      throw new Error("Leaflet is not loaded on window");
    }

    // Initialize standalone Leaflet
    const map = window.L.map(containerId, {
      center: [lat, lon],
      zoom: zoom,
      zoomControl: false,
      attributionControl: false
    });

    // Dark Matter CartoDB Basemap
    const darkTile = window.L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
      {
        subdomains: "abcd",
        maxZoom: 19
      }
    );
    darkTile.addTo(map);

    // Zoom control at bottom right
    window.L.control.zoom({ position: "bottomright" }).addTo(map);

    this.map = map;
    this.isWindy = false;
  }

  setWindyOverlay(overlayName) {
    this.currentOverlay = overlayName;
    if (this.isWindy && this.windyAPI && this.windyAPI.store) {
      try {
        this.windyAPI.store.set("overlay", overlayName);
      } catch (e) {
        console.error("Failed to set Windy overlay:", e);
      }
    }
  }

  setParticleAnimation(enabled) {
    if (this.isWindy && this.windyAPI && this.windyAPI.store) {
      try {
        this.windyAPI.store.set("particlesAnim", enabled ? "on" : "off");
      } catch (e) {
        console.error("Failed to toggle particles animation:", e);
      }
    }
  }
}
