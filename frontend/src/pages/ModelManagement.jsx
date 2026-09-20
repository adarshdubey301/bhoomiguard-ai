import { useState, useEffect } from 'react';
import { modelApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import ConfusionMatrix from '../components/ConfusionMatrix';
import ModelComparisonChart from '../components/ModelComparisonChart';
import { formatPercent, formatDate } from '../utils/helpers';
import { Brain, Play, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ModelManagement() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const [retrainNotes, setRetrainNotes] = useState('');
  const [retrainStatus, setRetrainStatus] = useState(null);
  const [isRetraining, setIsRetraining] = useState(false);

  const fetchModelData = async () => {
    try {
      const [metRes, compRes, statusRes] = await Promise.all([
        modelApi.getMetrics().catch(() => ({ data: null })),
        modelApi.getComparison().catch(() => ({ data: null })),
        modelApi.getRetrainStatus().catch(() => ({ data: null }))
      ]);
      if (metRes.data) setMetrics(metRes.data);
      if (compRes.data) setComparison(compRes.data);
      if (statusRes.data) {
        setRetrainStatus(statusRes.data);
        setIsRetraining(statusRes.data.status === 'running');
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModelData();
    let interval;
    if (isRetraining) {
      interval = setInterval(async () => {
        const res = await modelApi.getRetrainStatus();
        setRetrainStatus(res.data);
        if (res.data.status !== 'running') {
          setIsRetraining(false);
          fetchModelData(); // refresh data
        }
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [isRetraining]);

  const handleRetrain = async () => {
    if (user?.role !== 'admin') {
      alert('Only administrators can trigger model retraining.');
      return;
    }
    try {
      setIsRetraining(true);
      await modelApi.retrainModel({ notes: retrainNotes });
      setRetrainNotes('');
    } catch (err) {
      setIsRetraining(false);
      alert(err.response?.data?.detail || 'Failed to trigger retraining');
    }
  };

  if (loading) {
    return <div className="flex h-full items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-primary-500" /></div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      
      {retrainStatus && retrainStatus.status !== 'idle' && (
        <div className={`p-4 rounded-xl border flex items-start gap-4 shadow-lg ${
          retrainStatus.status === 'running' ? 'bg-primary-900/20 border-primary-500/30' :
          retrainStatus.status === 'failed' ? 'bg-red-500/10 border-red-500/20' :
          'bg-green-500/10 border-green-500/20'
        }`}>
          {retrainStatus.status === 'running' ? <Loader2 className="w-6 h-6 text-primary-500 animate-spin shrink-0" /> :
           retrainStatus.status === 'failed' ? <AlertCircle className="w-6 h-6 text-red-500 shrink-0" /> :
           <CheckCircle2 className="w-6 h-6 text-green-500 shrink-0" />}
          
          <div className="flex-1">
            <h4 className={`font-semibold ${
              retrainStatus.status === 'running' ? 'text-primary-400' :
              retrainStatus.status === 'failed' ? 'text-red-400' : 'text-green-400'
            }`}>
              {retrainStatus.status === 'running' ? 'Model Retraining in Progress' :
               retrainStatus.status === 'failed' ? 'Retraining Failed' : 'Retraining Complete'}
            </h4>
            <p className="text-sm text-slate-300 mt-1">{retrainStatus.message}</p>
            {retrainStatus.status === 'running' && (
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-3 overflow-hidden">
                <div className="bg-primary-500 h-1.5 rounded-full transition-all duration-500 ease-out" style={{ width: `${retrainStatus.progress || 10}%` }}></div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Production Model Details */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
            <div className="flex items-center gap-3 mb-6 border-b border-border pb-4">
              <div className="p-3 rounded-lg bg-primary-500/10">
                <Brain className="w-6 h-6 text-primary-500" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-100">Production Model</h2>
                <span className="text-xs text-green-500 font-semibold uppercase tracking-wider bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">Active</span>
              </div>
            </div>
            
            {metrics ? (
              <div className="space-y-4">
                <DetailRow label="Algorithm" value={metrics.model_name} />
                <DetailRow label="Version" value={metrics.model_version} />
                <DetailRow label="Training Date" value={formatDate(metrics.training_date)} />
                <DetailRow label="Features Used" value={metrics.feature_count} />
                <DetailRow label="Dataset Size" value={metrics.dataset_size?.toLocaleString()} />
                <DetailRow label="Train Split" value={metrics.training_size?.toLocaleString()} />
                <DetailRow label="Test Split" value={metrics.testing_size?.toLocaleString()} />
                
                <div className="pt-4 mt-4 border-t border-border">
                  <h3 className="text-sm font-semibold text-slate-300 mb-3">Model Action</h3>
                  {user?.role === 'admin' ? (
                    <div className="space-y-3">
                      <input 
                        type="text" 
                        value={retrainNotes}
                        onChange={(e) => setRetrainNotes(e.target.value)}
                        placeholder="Retraining notes (optional)"
                        className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-primary-500"
                        disabled={isRetraining}
                      />
                      <button
                        onClick={handleRetrain}
                        disabled={isRetraining}
                        className="w-full bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg px-4 py-2 flex items-center justify-center gap-2 transition-colors"
                      >
                        {isRetraining ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                        Trigger Retraining
                      </button>
                    </div>
                  ) : (
                    <div className="text-sm text-slate-500 bg-surface p-3 rounded-lg border border-border">
                      Only administrators can trigger model retraining.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-slate-500 text-sm py-4">No model deployed.</div>
            )}
          </div>
        </div>

        {/* Metrics & Comparison */}
        <div className="lg:col-span-2 space-y-6">
          
          <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-slate-100 mb-6">Test Set Performance</h3>
            {metrics ? (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <MetricBox label="Accuracy" value={metrics.accuracy} />
                <MetricBox label="Precision" value={metrics.precision} />
                <MetricBox label="Recall" value={metrics.recall} />
                <MetricBox label="F2 Score" value={metrics.f2_score} highlight />
                <MetricBox label="ROC-AUC" value={metrics.roc_auc} />
              </div>
            ) : (
              <div className="text-slate-500">No metrics available.</div>
            )}
          </div>

          <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
            <h3 className="text-lg font-semibold text-slate-100 mb-6">Confusion Matrix</h3>
            {metrics ? (
              <div className="max-w-md mx-auto">
                <ConfusionMatrix confusionMatrix={metrics.confusion_matrix} />
              </div>
            ) : (
              <div className="text-slate-500">No confusion matrix available.</div>
            )}
          </div>

          <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-slate-100">Algorithm Comparison</h3>
              <div className="text-xs text-slate-400 bg-surface px-3 py-1 rounded border border-border max-w-xs text-right">
                {comparison?.selection_rule || 'Selection Rule: Primary=F1 Score; Tiebreaker=F2 Score'}
              </div>
            </div>
            {comparison?.comparison ? (
              <ModelComparisonChart data={comparison.comparison} />
            ) : (
              <div className="text-slate-500">No comparison data available.</div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

function DetailRow({ label, value }) {
  return (
    <div className="flex justify-between items-center text-sm">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-slate-200">{value}</span>
    </div>
  );
}

function MetricBox({ label, value, highlight = false }) {
  return (
    <div className={`p-4 rounded-xl border flex flex-col items-center justify-center text-center ${
      highlight ? 'bg-primary-900/20 border-primary-500/30' : 'bg-surface border-border'
    }`}>
      <span className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-2">{label}</span>
      <span className={`text-2xl font-bold ${highlight ? 'text-primary-400' : 'text-slate-200'}`}>
        {formatPercent(value * 100)}
      </span>
    </div>
  );
}
