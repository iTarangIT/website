export const fleetMockData = {
  totalBatteriesMonitored: 152,
  fleetAvgSOH: 94.2,
  avgDailyKm: 47.3,
  avgChargeCycles: 312,
  fleetUptimePercent: 96.8,
  activeCities: [
    { name: "Delhi NCR", lat: 28.6139, lng: 77.209, count: 45 },
    { name: "Lucknow", lat: 26.8467, lng: 80.9462, count: 38 },
    { name: "Kolkata", lat: 22.5726, lng: 88.3639, count: 32 },
    { name: "Patna", lat: 25.6093, lng: 85.1376, count: 22 },
    { name: "Varanasi", lat: 25.3176, lng: 82.9739, count: 15 },
  ],
  sohDistribution: [
    { range: "95–100%", count: 42, color: "#00b090" },
    { range: "90–95%", count: 58, color: "#673de6" },
    { range: "85–90%", count: 35, color: "#8c85ff" },
    { range: "80–85%", count: 12, color: "#ffcd35" },
    { range: "<80%", count: 5, color: "#fc5185" },
  ],
};
