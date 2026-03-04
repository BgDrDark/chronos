// Координати на офиса (Пример: София, НДК)
// В бъдеще може да идват от API
const OFFICE_COORDS = {
  lat: 42.6853,
  lon: 23.3199
};

const MAX_DISTANCE_METERS = 300; // Разрешен радиус в метри

function deg2rad(deg: number) {
  return deg * (Math.PI / 180);
}

export const getDistanceFromLatLonInMeters = (lat1: number, lon1: number, lat2: number, lon2: number) => {
  const R = 6371e3; // Radius of the earth in meters
  const dLat = deg2rad(lat2 - lat1);
  const dLon = deg2rad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const d = R * c; // Distance in meters
  return d;
};

export const checkIsAtOffice = (currentLat: number, currentLon: number): boolean => {
    const distance = getDistanceFromLatLonInMeters(currentLat, currentLon, OFFICE_COORDS.lat, OFFICE_COORDS.lon);
    console.log(`Разстояние до офиса: ${distance.toFixed(2)} метра`);
    return distance <= MAX_DISTANCE_METERS;
};
