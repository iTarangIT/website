export interface CityData {
  name: string;
  lat: number;
  lng: number;
  status: "active" | "planned";
  dealers?: number;
  batteries?: number;
}

export const cities: CityData[] = [
  { name: "Delhi NCR", lat: 28.6139, lng: 77.209, status: "active", dealers: 8, batteries: 45 },
  { name: "Lucknow", lat: 26.8467, lng: 80.9462, status: "active", dealers: 5, batteries: 38 },
  { name: "Kolkata", lat: 22.5726, lng: 88.3639, status: "active", dealers: 4, batteries: 32 },
  { name: "Patna", lat: 25.6093, lng: 85.1376, status: "planned", dealers: 2, batteries: 22 },
  { name: "Varanasi", lat: 25.3176, lng: 82.9739, status: "planned", dealers: 1, batteries: 15 },
  { name: "Jaipur", lat: 26.9124, lng: 75.7873, status: "planned" },
  { name: "Bhopal", lat: 23.2599, lng: 77.4126, status: "planned" },
  { name: "Ranchi", lat: 23.3441, lng: 85.3096, status: "planned" },
  { name: "Agra", lat: 27.1767, lng: 78.0081, status: "planned" },
  { name: "Kanpur", lat: 26.4499, lng: 80.3319, status: "planned" },
];
