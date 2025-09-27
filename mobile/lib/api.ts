// mobile/lib/api.ts
import Constants from "expo-constants";

export type Aircraft = {
  callsign: string;
  tail?: string;
  icao24?: string;
  lat?: number;
  lon?: number;
  altitude_m?: number;
  velocity_ms?: number;
  last_seen_utc?: string;
};

function resolveApiBase(): string {
  // Try all the usual Expo places for `extra`
  const fromExpo =
    (Constants.expoConfig as any)?.extra?.EXPO_PUBLIC_API_BASE ??
    (Constants.manifest as any)?.extra?.EXPO_PUBLIC_API_BASE ?? // older Expo path (Expo Go)
    process.env.EXPO_PUBLIC_API_BASE;

  // Fallback to your LAN IP so the phone can reach your PC
  const apiBase = (fromExpo as string) || "http://192.168.50.191:8000";
  console.log("[config] API_BASE =", apiBase);
  return apiBase;
}

const API_BASE = resolveApiBase();

export async function searchAircraft(q: { callsign?: string; tail?: string }): Promise<Aircraft[]> {
  const params = new URLSearchParams();
  if (q.callsign) params.set("callsign", q.callsign);
  if (q.tail) params.set("tail", q.tail);

  const url = `${API_BASE}/aircraft?${params.toString()}`;
  const t0 = performance.now();
  const res = await fetch(url, { headers: { Accept: "application/json" } });
  const duration = Math.round(performance.now() - t0);

  console.log(
    "[trace]",
    JSON.stringify({ event: "api_call", endpoint: "/aircraft", status: res.status, duration_ms: duration, url })
  );

  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}
