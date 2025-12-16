interface ZippopotamPlace {
  "place name": string; // city name
  state: string;
  "state abbreviation": string;
  longitude: string;
  latitude: string;
}

interface ZippopotamResponse {
  places?: ZippopotamPlace[];
}

export async function fetchLocationFromZip(
  zipCode: string,
): Promise<string | null> {
  try {
    const response = await fetch(`https://api.zippopotam.us/us/${zipCode}`);
    if (!response.ok) {
      return null;
    }
    const data = (await response.json()) as ZippopotamResponse;
    const place = data.places?.[0];
    if (place) {
      return `${place["place name"]}, ${place["state abbreviation"]}`;
    }
    return null;
  } catch (error) {
    console.error("Error fetching city/state from zip code:", error);
    return null;
  }
}
