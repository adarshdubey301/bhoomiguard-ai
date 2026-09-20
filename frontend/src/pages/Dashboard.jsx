import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { analyticsApi, modelApi } from '../services/api';
import DistrictFilter from '../components/DistrictFilter';
import RiskMap from '../components/RiskMap';
import ConfusionMatrix from '../components/ConfusionMatrix';
import { formatPercent } from '../utils/helpers';
import { AlertCircle, CheckCircle2, TrendingUp, FolderKanban, Loader2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Filter states
  const [district, setDistrict] = useState('All Districts');
  const [stage, setStage] = useState('All Stages');

  const loadData = useCallback(async (dist, stg) => {
    setLoading(true);
    try {
      const d = dist === 'All Districts' ? null : dist;
      const s = stg === 'All Stages' ? null : stg;
      
      const [ovRes, metRes] = await Promise.all([
        analyticsApi.getOverview({ district: d, stage: s }),
        modelApi.getMetrics().catch(() => ({ data: null }))
      ]);
      setOverview(ovRes.data);
      if (metRes.data) setMetrics(metRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData(district, stage);
  }, [loadData, district, stage]);

  const handleFilterChange = (newDistrict, newStage) => {
    setDistrict(newDistrict);
    setStage(newStage);
  };

  const portalEl = document.getElementById('header-filters-portal');

  if (loading && !overview) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>;
  }

  const pieData = overview ? [
    { name: 'Delayed', value: overview.delayed_projects, color: '#ef4444' },
    { name: 'On Track', value: overview.non_delayed_projects, color: '#22c55e' }
  ] : [];

  return (
    <div className="space-y-6">
      {portalEl && createPortal(
        <DistrictFilter onFilterChange={handleFilterChange} />,
        portalEl
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Projects" 
          value={overview?.total_projects?.toLocaleString() || 0}
          icon={FolderKanban}
          color="text-primary-500"
          bg="bg-primary-500/10"
        />
        <StatCard 
          title="Delay Rate" 
          value={formatPercent(overview?.delay_rate * 100)}
          icon={TrendingUp}
          color="text-orange-500"
          bg="bg-orange-500/10"
        />
        <StatCard 
          title="Delayed Projects" 
          value={overview?.delayed_projects?.toLocaleString() || 0}
          icon={AlertCircle}
          color="text-red-500"
          bg="bg-red-500/10"
        />
        <StatCard 
          title="On Track" 
          value={overview?.non_delayed_projects?.toLocaleString() || 0}
          icon={CheckCircle2}
          color="text-green-500"
          bg="bg-green-500/10"
        />
      </div>
      
      {/* Risk Map Section */}
      <RiskMap />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Dataset Distribution */}
        <div className="bg-card border border-border rounded-xl p-6 lg:col-span-1 shadow-lg">
          <h3 className="text-lg font-semibold text-slate-100 mb-4">Historical Delay Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                  itemStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p className="text-center text-sm text-slate-400 mt-2">
            Based on {overview?.total_projects?.toLocaleString()} projects
          </p>
        </div>

        {/* AI Model Performance */}
        <div className="bg-card border border-border rounded-xl p-6 lg:col-span-2 shadow-lg">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold text-slate-100">AI Model Performance (Test Set)</h3>
            <div className="px-3 py-1 bg-primary-500/10 text-primary-400 border border-primary-500/20 rounded-full text-xs font-semibold">
              {metrics?.model_name || 'Loading...'} {metrics?.model_version || ''}
            </div>
          </div>
          
          {metrics ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <MetricBox label="Accuracy" value={metrics.accuracy} />
                  <MetricBox label="F2 Score" value={metrics.f2_score} highlight />
                  <MetricBox label="Precision" value={metrics.precision} />
                  <MetricBox label="Recall" value={metrics.recall} />
                  <MetricBox label="ROC-AUC" value={metrics.roc_auc} className="col-span-2" />
                </div>
                <p className="text-xs text-slate-400 bg-surface p-3 rounded border border-border">
                  <span className="font-semibold text-primary-400">Note:</span> Model selection prioritizes F1 Score, with F2 Score as a tiebreaker to emphasize recall (minimizing dangerous False Negatives).
                </p>
              </div>
              
              <div className="bg-surface rounded-lg p-4 border border-border">
                <h4 className="text-sm font-semibold text-slate-300 mb-4 text-center">Confusion Matrix</h4>
                <ConfusionMatrix confusionMatrix={metrics.confusion_matrix} />
              </div>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-slate-500 border border-dashed border-border rounded-lg">
              Model metrics not available. Run training pipeline first.
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color, bg }) {
  return (
    <div className="bg-card border border-border p-6 rounded-xl shadow-lg flex items-center gap-4">
      <div className={`p-4 rounded-xl ${bg}`}>
        <Icon className={`w-8 h-8 ${color}`} />
      </div>
      <div>
        <p className="text-sm font-medium text-slate-400">{title}</p>
        <p className="text-2xl font-bold text-slate-100">{value}</p>
      </div>
    </div>
  );
}

function MetricBox({ label, value, highlight = false, className = "" }) {
  return (
    <div className={`p-3 rounded-lg border ${highlight ? 'bg-primary-900/20 border-primary-500/30' : 'bg-surface border-border'} ${className}`}>
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      <div className={`text-xl font-bold ${highlight ? 'text-primary-400' : 'text-slate-200'}`}>
        {formatPercent(value * 100)}
      </div>
    </div>
  );
}
