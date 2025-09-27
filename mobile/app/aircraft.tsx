import { useLocalSearchParams } from "expo-router";
import MapView, { Marker } from "react-native-maps";
import { View, Text, Pressable, Linking, Platform } from "react-native";
import { useEffect, useState, useMemo } from "react";
import { searchAircraft, type Aircraft } from "../lib/api";

export default function AircraftDetail() {
  const { callsign = "", tail = "" } = useLocalSearchParams<{ callsign?: string; tail?: string }>();
  const [data, setData] = useState<Aircraft | null>(null);

  useEffect(() => {
    (async () => {
      const res = await searchAircraft({
        callsign: typeof callsign === "string" && callsign ? callsign : undefined,
        tail: typeof tail === "string" && tail ? tail : undefined,
      });
      setData(res[0] ?? null);
    })();
  }, [callsign, tail]);

  const region = useMemo(() => {
    if (!data?.lat || !data?.lon) return undefined;
    return {
      latitude: data.lat,
      longitude: data.lon,
      latitudeDelta: 2,
      longitudeDelta: 2,
    };
  }, [data?.lat, data?.lon]);

  function openInMaps() {
    if (!data?.lat || !data?.lon) return;
    const { lat, lon } = { lat: data.lat, lon: data.lon };
    // Apple Maps on iOS; Google Maps geo on Android
    const url =
      Platform.OS === "ios"
        ? `http://maps.apple.com/?ll=${lat},${lon}&q=${encodeURIComponent(data.callsign ?? "Aircraft")}`
        : `geo:${lat},${lon}?q=${lat},${lon}(${encodeURIComponent(data.callsign ?? "Aircraft")})`;
    Linking.openURL(url).catch(() => {});
  }

  if (!data) {
    return (
      <View style={{ flex: 1, alignItems: "center", justifyContent: "center", padding: 16 }}>
        <Text style={{ color: "#000" }}>Loading…</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      {/* Info card */}
      <View
        style={{
          margin: 16,
          padding: 16,
          backgroundColor: "#fff",
          borderRadius: 12,
          borderWidth: 1,
          borderColor: "#eee",
          gap: 6,
        }}
      >
        <Text style={{ fontSize: 18, fontWeight: "800", color: "#000" }}>
          {data.callsign || "(no callsign)"} {data.tail ? `• ${data.tail}` : ""}
        </Text>
        {data.icao24 ? <Text style={{ color: "#333" }}>ICAO24: {data.icao24}</Text> : null}
        {data.last_seen_utc ? <Text style={{ color: "#333" }}>Last seen: {data.last_seen_utc}</Text> : null}
        <Text style={{ color: "#333" }}>
          {data.altitude_m ? `Alt: ${Math.round(data.altitude_m)} m` : "Alt: —"}
          {data.velocity_ms ? ` • Speed: ${Math.round(data.velocity_ms)} m/s` : ""}
        </Text>

        <Pressable
          onPress={openInMaps}
          style={{
            marginTop: 8,
            alignSelf: "flex-start",
            paddingVertical: 8,
            paddingHorizontal: 12,
            backgroundColor: "#2563eb",
            borderRadius: 8,
          }}
        >
          <Text style={{ color: "#fff", fontWeight: "700" }}>Open in Maps</Text>
        </Pressable>
      </View>

      {/* Map */}
      {region ? (
        <MapView style={{ flex: 1 }} initialRegion={region}>
          <Marker
            coordinate={{ latitude: region.latitude, longitude: region.longitude }}
            title={data.callsign ?? "Aircraft"}
            description={data.tail ?? undefined}
          />
        </MapView>
      ) : (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <Text style={{ color: "#000" }}>No location available</Text>
        </View>
      )}
    </View>
  );
}
