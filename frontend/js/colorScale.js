/**
 * Temperature color scale and classification
 * Compliant with CWA / Meteorological visualization guidelines
 */

export const TEMP_SCALES = [
  { min: -Infinity, max: 10, color: "#2b6cb0", label: "< 10°C", name: "寒冷 (Cold)" },
  { min: 10, max: 15, color: "#3182ce", label: "10–15°C", name: "涼冷 (Cool)" },
  { min: 15, max: 20, color: "#38a169", label: "15–20°C", name: "微涼 (Mild)" },
  { min: 20, max: 25, color: "#ecc94b", label: "20–25°C", name: "舒適 (Comfortable)" },
  { min: 25, max: 30, color: "#ed8936", label: "25–30°C", name: "溫暖 (Warm)" },
  { min: 30, max: 35, color: "#e53e3e", label: "30–35°C", name: "炎熱 (Hot)" },
  { min: 35, max: Infinity, color: "#9b2c2c", label: "> 35°C", name: "酷熱 (Very Hot)" }
];

export function colorByTemperature(temp) {
  if (temp === null || temp === undefined || isNaN(temp)) return "#718096";
  for (const scale of TEMP_SCALES) {
    if (temp < scale.max) {
      return scale.color;
    }
  }
  return "#9b2c2c";
}

export function getTemperatureCategory(temp) {
  if (temp === null || temp === undefined || isNaN(temp)) return "未知";
  for (const scale of TEMP_SCALES) {
    if (temp < scale.max) {
      return scale.name;
    }
  }
  return "酷熱 (Very Hot)";
}

export function getMarkerRadius(temp) {
  // Adaptive marker size based on temperature intensity
  if (temp === null || isNaN(temp)) return 7;
  if (temp < 15) return 7;
  if (temp < 25) return 8;
  if (temp < 32) return 9;
  return 10;
}
