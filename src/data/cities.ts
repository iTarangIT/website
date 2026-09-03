export interface CityData {
  name: string;
  /** State or union territory, spelled exactly as in `src/data/india-map-paths.ts`. */
  state: string;
  lat: number;
  lng: number;
  status: "active" | "planned";
  dealers?: number;
  batteries?: number;
}

export const cities: CityData[] = [
  { name: "Delhi NCR", state: "Delhi", lat: 28.6139, lng: 77.209, status: "active", dealers: 8, batteries: 45 },
  { name: "Lucknow", state: "Uttar Pradesh", lat: 26.8467, lng: 80.9462, status: "active", dealers: 5, batteries: 38 },
  { name: "Kolkata", state: "West Bengal", lat: 22.5726, lng: 88.3639, status: "active", dealers: 4, batteries: 32 },
  { name: "Patna", state: "Bihar", lat: 25.6093, lng: 85.1376, status: "planned", dealers: 2, batteries: 22 },
  { name: "Varanasi", state: "Uttar Pradesh", lat: 25.3176, lng: 82.9739, status: "planned", dealers: 1, batteries: 15 },
  { name: "Jaipur", state: "Rajasthan", lat: 26.9124, lng: 75.7873, status: "planned" },
  { name: "Bhopal", state: "Madhya Pradesh", lat: 23.2599, lng: 77.4126, status: "planned" },
  { name: "Ranchi", state: "Jharkhand", lat: 23.3441, lng: 85.3096, status: "planned" },
  { name: "Agra", state: "Uttar Pradesh", lat: 27.1767, lng: 78.0081, status: "planned" },
  { name: "Kanpur", state: "Uttar Pradesh", lat: 26.4499, lng: 80.3319, status: "planned" },
];
