import { useState, useEffect } from 'react';
import { predictionApi } from '../services/api';
import { RiskBadge, PredictionBadge } from '../components/RiskBadge';
import { formatDate, formatPercent } from '../utils/helpers';
import { Search, Loader2, Download, AlertCircle } from 'lucide-react';

export default function PredictionHistory() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [total, setTotal] = useState(0);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const res = await predictionApi.getPredictions({ search, limit: 50 });
      setPredictions(res.data.predictions || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchHistory();
    }, 500);
    return () => clearTimeout(delayDebounceFn);
  }, [search]);

  const handleExport = () => {
    if (!predictions.length) return;
    
    // Convert to CSV
    const headers = ['Project ID', 'District', 'Stage', 'Prediction', 'Probability', 'Risk Level', 'Date', 'Model Version'];
    const rows = predictions.map(p => [
      p.project_id, 
      p.district, 
      p.current_stage, 
      p.prediction, 
      p.delay_probability, 
      p.risk_level,
      new Date(p.created_at).toISOString(),
      p.model_version
    ]);
    
    let csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(",") + "\n"
      + rows.map(e => e.join(",")).join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `bhoomiguard_predictions_${new Date().getTime()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6">
      
      <div className="flex flex-col md:flex-row gap-4 justify-between items-start md:items-center bg-card border border-border p-4 rounded-xl shadow-lg">
        <div className="relative w-full md:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
          <input
            type="text"
            placeholder="Search by Project ID or District..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-surface border border-border rounded-lg text-sm text-slate-200 focus:ring-1 focus:ring-primary-500 outline-none"
          />
        </div>
        
        <div className="flex items-center gap-4 text-sm w-full md:w-auto">
          <span className="text-slate-400">Total Records: <span className="text-slate-200 font-medium">{total}</span></span>
          <button 
            onClick={handleExport}
            className="ml-auto flex items-center gap-2 bg-surface border border-border hover:bg-slate-800 text-slate-200 px-4 py-2 rounded-lg transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-800/80 border-b border-border text-slate-400">
              <tr>
                <th className="px-6 py-4 font-semibold">Project ID</th>
                <th className="px-6 py-4 font-semibold">District & Stage</th>
                <th className="px-6 py-4 font-semibold">Prediction</th>
                <th className="px-6 py-4 font-semibold">Risk Level</th>
                <th className="px-6 py-4 font-semibold">Model</th>
                <th className="px-6 py-4 font-semibold">Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-primary-500 mx-auto" />
                  </td>
                </tr>
              ) : predictions.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-12 text-center text-slate-500">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    No predictions found
                  </td>
                </tr>
              ) : (
                predictions.map((p) => (
                  <tr key={p.id} className="border-b border-border hover:bg-slate-800/50 transition-colors">
                    <td className="px-6 py-4 font-mono font-medium text-slate-200">{p.project_id}</td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-200">{p.district}</div>
                      <div className="text-xs text-slate-500">{p.current_stage}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1 items-start">
                        <PredictionBadge prediction={p.prediction} />
                        <span className="text-xs font-mono text-slate-400 ml-1">Prob: {formatPercent(p.delay_probability * 100)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <RiskBadge level={p.risk_level} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-300">{p.model_name}</div>
                      <div className="text-xs font-mono text-slate-500">{p.model_version}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-slate-400">
                      {formatDate(p.created_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
    </div>
  );
}
