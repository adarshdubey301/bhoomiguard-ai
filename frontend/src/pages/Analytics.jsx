import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { analyticsApi } from '../services/api';
import DistrictFilter from '../components/DistrictFilter';
import RiskMap from '../components/RiskMap';
import { formatPercent } from '../utils/helpers';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts';
import { Loader2 } from 'lucide-react';

export default function Analytics() {
  const [district, setDistrict] = useState('All Districts');
  const [stage, setStage] = useState('All Stages');
  
  const [districtsData, setDistrictsData] = useState([]);
  const [stagesData, setStagesData] = useState([]);
  const [riskData, setRiskData] = useState([]);
  const [featureData, setFeatureData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      setLoading(true);
      try {
        const d = district === 'All Districts' ? null : district;
        
        const [distRes, stageRes, riskRes, featRes] = await Promise.all([
          analyticsApi.getDistricts(),
          analyticsApi.getStages({ district: d }),
          analyticsApi.getRiskDistribution({ district: d }),
          analyticsApi.getFeatureImportance().catch(() => ({ data: { feature_importance: [] } }))
        ]);
        
        setDistrictsData(distRes.data.districts || []);
        setStagesData(stageRes.data.stages || []);
        setRiskData(riskRes.data.risk_distribution || []);
        setFeatureData(featRes.data.feature_importance || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadAnalytics();
  }, [district]); // Only re-fetch if district changes

  const handleFilterChange = (newDistrict, newStage) => {
    setDistrict(newDistrict);
    setStage(newStage);
  };

  const portalEl = document.getElementById('header-filters-portal');

  if (loading && districtsData.length === 0) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>;
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border p-3 rounded-lg shadow-xl">
          <p className="font-semibold text-slate-100 mb-2">{label}</p>
          {payload.map(p => (
            <p key={p.name} style={{ color: p.color || p.fill }} className="text-sm">
              {p.name}: {p.value}{p.dataKey.includes('rate') || p.dataKey.includes('pct') || p.dataKey === 'importance' ? '%' : ''}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const riskColors = {
    'Low': '#22c55e',
    'Medium': '#eab308',
    'High': '#f97316',
    'Critical': '#ef4444'
  };

  return (
    <div className="space-y-6">
      {portalEl && createPortal(
        <DistrictFilter onFilterChange={handleFilterChange} />,
        portalEl
      )}

      <RiskMap />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* District Leaderboard Chart */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-lg lg:col-span-2">
          <h3 className="text-lg font-semibold text-slate-100 mb-6">District Delay Risk Comparison</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={districtsData.slice(0, 15)} margin={{ top: 5, right: 30, left: 0, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="district" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} angle={-45} textAnchor="end" />
                <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} tickFormatter={(val) => `${val}%`} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="delay_rate_pct" name="Historical Delay Rate" fill="#ef4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Stage Distribution */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-slate-100 mb-6">Delays by Project Stage</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stagesData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
                <YAxis dataKey="stage" type="category" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="delayed" name="Delayed Projects" stackId="a" fill="#ef4444" />
                <Bar dataKey="non_delayed" name="On Track" stackId="a" fill="#22c55e" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Prediction Risk Distribution */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold text-slate-100 mb-6">System Risk Prediction Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="count"
                  nameKey="risk_level"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={riskColors[entry.risk_level] || '#94a3b8'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Feature Importance (Global) */}
        {featureData.length > 0 && (
          <div className="bg-card border border-border rounded-xl p-6 shadow-lg lg:col-span-2">
            <h3 className="text-lg font-semibold text-slate-100 mb-6">Global Model Feature Importance (SHAP Aggregate)</h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={featureData.slice(0, 10)} layout="vertical" margin={{ top: 5, right: 30, left: 120, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                  <XAxis type="number" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
                  <YAxis dataKey="feature" type="category" stroke="#94a3b8" tick={{ fill: '#e2e8f0', fontSize: 11 }} width={110} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="importance" name="Relative Importance" fill="#3b82f6" radius={[0, 4, 4, 0]}>
                    {featureData.slice(0, 10).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={`rgba(59, 130, 246, ${1 - index * 0.08})`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
