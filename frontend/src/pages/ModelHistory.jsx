import { useState, useEffect } from 'react';
import { modelApi } from '../services/api';
import { formatDate, formatPercent } from '../utils/helpers';
import { GitBranch, Loader2 } from 'lucide-react';

export default function ModelHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    modelApi.getHistory()
      .then(res => setHistory(res.data || []))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <GitBranch className="w-6 h-6 text-primary-500" />
            Model Version History
          </h2>
          <p className="text-slate-400 mt-1">Audit log of all trained AI models. Prior versions are preserved but immutable.</p>
        </div>
      </div>

      <div className="bg-card border border-border rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs uppercase bg-slate-800/80 border-b border-border text-slate-400">
              <tr>
                <th className="px-6 py-4 font-semibold">Version</th>
                <th className="px-6 py-4 font-semibold">Algorithm</th>
                <th className="px-6 py-4 font-semibold text-center">F2 Score</th>
                <th className="px-6 py-4 font-semibold text-center">Accuracy</th>
                <th className="px-6 py-4 font-semibold text-center">Recall</th>
                <th className="px-6 py-4 font-semibold">Training Date</th>
                <th className="px-6 py-4 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-primary-500 mx-auto" />
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-slate-500">
                    No model history found.
                  </td>
                </tr>
              ) : (
                history.map((m, idx) => (
                  <tr key={m.id} className={`border-b border-border hover:bg-slate-800/50 transition-colors ${m.is_production ? 'bg-primary-900/5' : ''}`}>
                    <td className="px-6 py-4 font-mono font-bold text-slate-200">{m.version}</td>
                    <td className="px-6 py-4 font-medium text-slate-300">{m.model_name}</td>
                    <td className="px-6 py-4 text-center font-bold text-primary-400">{formatPercent(m.f2_score * 100)}</td>
                    <td className="px-6 py-4 text-center">{formatPercent(m.accuracy * 100)}</td>
                    <td className="px-6 py-4 text-center">{formatPercent(m.recall_score * 100)}</td>
                    <td className="px-6 py-4 text-slate-400 whitespace-nowrap">{formatDate(m.created_at)}</td>
                    <td className="px-6 py-4">
                      {m.is_production ? (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-green-500/10 border border-green-500/20 text-green-500 uppercase tracking-wider">
                          Production
                        </span>
                      ) : (
                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 border border-slate-600 text-slate-400 uppercase tracking-wider">
                          Archived
                        </span>
                      )}
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
