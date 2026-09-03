import { indiaMap } from "@/data/india-map-paths";
import { mercator } from "./mercator";

/** Project a city's lat/lng onto the canvas the state outlines were drawn on. */
export function projectLatLng(lat: number, lng: number): [number, number] {
  return mercator(lng, lat, indiaMap);
}
