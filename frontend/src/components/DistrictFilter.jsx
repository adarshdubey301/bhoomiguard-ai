import { useState, useEffect } from 'react';
import { metadataApi } from '../services/api';

export default function DistrictFilter({ onFilterChange }) {
  const [districts, setDistricts] = useState([]);
  const [stages, setStages] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState('All Districts');
  const [selectedStage, setSelectedStage] = useState('All Stages');

  useEffect(() => {
    metadataApi.getMetadata().then(res => {
      setDistricts(res.data.districts || []);
      setStages(res.data.current_stages || []);
    }).catch(err => console.error("Failed to load metadata", err));
  }, []);

  const handleDistrictChange = (e) => {
    const v = e.target.value;
    setSelectedDistrict(v);
    onFilterChange(v, selectedStage);
  };

  const handleStageChange = (e) => {
    const v = e.target.value;
    setSelectedStage(v);
    onFilterChange(selectedDistrict, v);
  };

  return (
    <div className="flex flex-col sm:flex-row gap-4">
      <select 
        value={selectedDistrict} 
        onChange={handleDistrictChange}
        className="bg-surface border border-border text-slate-200 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5"
      >
        <option value="All Districts">All Districts</option>
        {districts.map(d => (
          <option key={d} value={d}>{d}</option>
        ))}
      </select>

      <select 
        value={selectedStage} 
        onChange={handleStageChange}
        className="bg-surface border border-border text-slate-200 text-sm rounded-lg focus:ring-primary-500 focus:border-primary-500 block w-full p-2.5"
      >
        <option value="All Stages">All Stages</option>
        {stages.map(s => (
          <option key={s} value={s}>{s}</option>
        ))}
      </select>
    </div>
  );
}
