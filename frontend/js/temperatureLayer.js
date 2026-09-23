import { colorByTemperature, getTemperatureCategory, getMarkerRadius } from "./colorScale.js";

export class TemperatureLayer {
  constructor(map) {
    this.map = map;
    this.layerGroup = window.L.layerGroup().addTo(map);
    this.stations = [];
    this.showLabels = true;
    this.currentFilters = {
      county: "ALL",
      minTemp: -50,
      maxTemp: 60,
      searchQuery: ""
    };
    this.markers = new Map(); // station_id -> marker
  }

  setStations(stations) {
    this.stations = stations || [];
    this.render();
  }

  setShowLabels(visible) {
    this.showLabels = visible;
    this.render();
  }

  setFilters(filters) {
    this.currentFilters = { ...this.currentFilters, ...filters };
    this.render();
  }

  render() {
    this.layerGroup.clearLayers();
    this.markers.clear();

    const filtered = this.getFilteredStations();

    for (const station of filtered) {
      const color = colorByTemperature(station.temperature_c);
      const radius = getMarkerRadius(station.temperature_c);

      const marker = window.L.circleMarker([station.lat, station.lon], {
        radius: radius,
        fillColor: color,
        fillOpacity: 0.9,
        color: "#ffffff",
        weight: 1.5,
        className: "cwa-station-marker"
      });

      // Rich modern popup
      const popupContent = this._createPopupContent(station, color);
      marker.bindPopup(popupContent, {
        className: "cwa-custom-popup",
        closeButton: true,
        maxWidth: 280
      });

      // Optional temperature text label
      if (this.showLabels) {
        marker.bindTooltip(
          `<div class="station-temp-pill" style="border-left: 3px solid ${color};">
            <span class="station-temp-val">${station.temperature_c.toFixed(1)}°</span>
            <span class="station-temp-name">${station.station_name}</span>
          </div>`,
          {
            permanent: true,
            direction: "right",
            offset: [8, 0],
            className: "cwa-temp-tooltip"
          }
        );
      }

      marker.addTo(this.layerGroup);
      this.markers.set(station.station_id, marker);
    }
  }

  getFilteredStations() {
    return this.stations.filter(s => {
      // County match
      if (this.currentFilters.county !== "ALL" && s.county !== this.currentFilters.county) {
        return false;
      }
      // Temperature range
      if (s.temperature_c < this.currentFilters.minTemp || s.temperature_c > this.currentFilters.maxTemp) {
        return false;
      }
      // Search query (name, id, town)
      if (this.currentFilters.searchQuery) {
        const q = this.currentFilters.searchQuery.toLowerCase().trim();
        const name = (s.station_name || "").toLowerCase();
        const id = (s.station_id || "").toLowerCase();
        const county = (s.county || "").toLowerCase();
        const town = (s.town || "").toLowerCase();
        if (!name.includes(q) && !id.includes(q) && !county.includes(q) && !town.includes(q)) {
          return false;
        }
      }
      return true;
    });
  }

  flyToStation(stationId) {
    const marker = this.markers.get(stationId);
    if (marker) {
      const latLng = marker.getLatLng();
      this.map.flyTo(latLng, 11, { duration: 1.2 });
      setTimeout(() => {
        marker.openPopup();
      }, 1200);
      return true;
    }
    return false;
  }

  _createPopupContent(s, color) {
    const category = getTemperatureCategory(s.temperature_c);
    const location = [s.county, s.town].filter(Boolean).join(" · ") || "台灣觀測站";
    const obsTime = s.observed_at ? s.observed_at.replace("T", " ").replace("+08:00", "") : "-";

    return `
      <div class="cwa-popup-card">
        <div class="popup-header">
          <div>
            <h4 class="popup-station-title">${s.station_name}</h4>
            <span class="popup-location-sub">${location}</span>
          </div>
          <span class="popup-station-id">#${s.station_id}</span>
        </div>

        <div class="popup-temp-hero" style="color: ${color}">
          <span class="temp-big">${s.temperature_c.toFixed(1)}</span>
          <span class="temp-unit">°C</span>
          <span class="temp-badge" style="background: ${color}22; color: ${color}; border: 1px solid ${color}66;">${category}</span>
        </div>

        <div class="popup-grid">
          <div class="grid-item">
            <span class="item-label">相對濕度</span>
            <span class="item-val">${s.humidity_percent !== null ? `${Math.round(s.humidity_percent)}%` : "—"}</span>
          </div>
          <div class="grid-item">
            <span class="item-label">風速</span>
            <span class="item-val">${s.wind_speed_mps !== null ? `${s.wind_speed_mps} m/s` : "—"}</span>
          </div>
          <div class="grid-item">
            <span class="item-label">海平面氣壓</span>
            <span class="item-val">${s.pressure_hpa !== null ? `${Math.round(s.pressure_hpa)} hPa` : "—"}</span>
          </div>
          <div class="grid-item">
            <span class="item-label">天氣狀況</span>
            <span class="item-val">${s.weather || "正常"}</span>
          </div>
        </div>

        <div class="popup-footer">
          <span>觀測時間: ${obsTime}</span>
        </div>
      </div>
    `;
  }
}
