import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { analyticsApi } from '../services/api';

const DISTRICT_COORDS = {
  "Ahmedabad": [23.0225, 72.5714],
  "Amreli": [21.6032, 71.2189],
  "Anand": [22.5645, 72.9289],
  "Banaskantha": [24.1724, 71.7451],
  "Bharuch": [21.7051, 72.9959],
  "Bhavnagar": [21.7645, 72.1519],
  "Gandhinagar": [23.2156, 72.6369],
  "Jamnagar": [22.4707, 70.0577],
  "Junagadh": [21.5222, 70.4579],
  "Kheda": [22.7506, 72.6828],
  "Mehsana": [23.5880, 72.3693],
  "Morbi": [22.8120, 70.8320],
  "Navsari": [20.9467, 72.9520],
  "Panchmahal": [22.7562, 73.5791],
  "Patan": [23.8493, 72.1266],
  "Rajkot": [22.3039, 70.8022],
  "Sabarkantha": [23.8312, 72.9739],
  "Surat": [21.1702, 72.8311],
  "Vadodara": [22.3072, 73.1812],
  "Valsad": [20.5992, 72.9342],
};

export default function RiskMap() {
  const [districtData, setDistrictData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await analyticsApi.getDistricts();
        if (res.data && res.data.districts) {
          setDistrictData(res.data.districts);
        }
      } catch (err) {
        console.error("Failed to load map data", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div className="h-96 flex items-center justify-center text-slate-400">Loading Map...</div>;
  }

  const getColor = (delayRate) => {
    if (delayRate > 0.6) return '#ef4444'; // Red (High Risk)
    if (delayRate > 0.4) return '#f59e0b'; // Amber (Medium Risk)
    return '#10b981'; // Green (Low Risk)
  };

  return (
    <div className="bg-card border border-border rounded-xl p-6">
      <h3 className="text-lg font-bold text-slate-100 mb-4">Geospatial Risk Map</h3>
      <div className="h-[400px] w-full rounded-lg overflow-hidden border border-border">
        <MapContainer center={[22.2587, 71.1924]} zoom={6.5} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {districtData.map((d) => {
            const coords = DISTRICT_COORDS[d.district];
            if (!coords) return null;
            
            return (
              <CircleMarker
                key={d.district}
                center={coords}
                radius={6}
                pathOptions={{
                  fillColor: getColor(d.delay_rate),
                  color: getColor(d.delay_rate),
                  weight: 1,
                  opacity: 0.9,
                  fillOpacity: 0.8,
                }}
              >
                <Tooltip direction="top" offset={[0, -10]} opacity={1}>
                  <div className="text-sm p-1">
                    <strong className="text-slate-900 block mb-1 text-base">{d.district}</strong>
                    <div className="text-slate-600">Total Projects: {d.total_projects}</div>
                    <div className="text-slate-600">Delayed: {d.delayed_projects}</div>
                    <div className="text-slate-600 font-semibold mt-1">Delay Rate: {(d.delay_rate * 100).toFixed(1)}%</div>
                  </div>
                </Tooltip>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
