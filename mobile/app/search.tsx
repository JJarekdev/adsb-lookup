import { useState } from "react";
import {
  View,
  TextInput,
  Button,
  FlatList,
  Text,
  TouchableOpacity,
  ActivityIndicator,
} from "react-native";
import { useRouter } from "expo-router";
import { searchAircraft, type Aircraft } from "../lib/api";

export default function SearchScreen() {
  const [callsign, setCallsign] = useState("");
  const [tail, setTail] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Aircraft[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function onSearch() {
    setLoading(true);
    setError(null);
    try {
      const data = await searchAircraft({
        callsign: callsign.trim() || undefined,
        tail: tail.trim() || undefined,
      });
      setResults(data);
    } catch (e: any) {
      console.log("search error", e);
      setError(e?.message ?? "Search failed");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={{ flex: 1, padding: 16, gap: 12 }}>
      {/* Callsign input */}
      <View style={{ gap: 6 }}>
        <Text style={{ color: "#888" }}>Callsign</Text>
        <TextInput
          value={callsign}
          onChangeText={setCallsign}
          placeholder="e.g., DAL123"
          placeholderTextColor="#888"
          autoCapitalize="characters"
          style={{
            borderWidth: 1,
            borderColor: "#ccc",
            borderRadius: 8,
            padding: 12,
            backgroundColor: "#fff",
            color: "#000",
          }}
        />
      </View>

      {/* Tail/Registration input */}
      <View style={{ gap: 6 }}>
        <Text style={{ color: "#888" }}>Tail/Registration</Text>
        <TextInput
          value={tail}
          onChangeText={setTail}
          placeholder="e.g., N123AB"
          placeholderTextColor="#888"
          autoCapitalize="characters"
          style={{
            borderWidth: 1,
            borderColor: "#ccc",
            borderRadius: 8,
            padding: 12,
            backgroundColor: "#fff",
            color: "#000",
          }}
        />
      </View>

      <Button title="Search" onPress={onSearch} />
      {loading && <ActivityIndicator />}
      {error && <Text style={{ color: "red" }}>{error}</Text>}

      <FlatList
        data={results}
        keyExtractor={(item, idx) => `${item.callsign}-${item.tail ?? idx}`}
        ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        renderItem={({ item }) => (
            <TouchableOpacity
            onPress={() =>
                router.push({
                pathname: "/aircraft",
                params: { callsign: item.callsign, tail: item.tail ?? "" },
                })
            }
            style={{
                paddingVertical: 12,
                paddingHorizontal: 12,
                borderRadius: 10,
                // Light card so it pops on dark backgrounds:
                backgroundColor: "#fff",
                // subtle border for light mode too
                borderWidth: 1,
                borderColor: "#eee",
            }}
            >
            <Text style={{ fontWeight: "700", color: "#000" }}>
                {item.callsign || "(no callsign)"}
            </Text>
            <Text style={{ color: "#333" }}>
                {item.tail ?? ""}
                {item.icao24 ? ` • ${item.icao24}` : ""}
            </Text>
            {item.lat && item.lon ? (
                <Text style={{ color: "#555" }}>
                {item.lat.toFixed(3)}, {item.lon.toFixed(3)}
                </Text>
            ) : null}
            </TouchableOpacity>
        )}
        ListEmptyComponent={
            !loading ? <Text style={{ color: "#888" }}>Enter a callsign or tail and tap Search.</Text> : null
        }
      />
    </View>
  );
}