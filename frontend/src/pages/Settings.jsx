import { useState, useEffect } from 'react';
import { metadataApi } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { User, Settings as SettingsIcon, Shield, Database } from 'lucide-react';

export default function Settings() {
  const { user } = useAuth();
  const [thresholds, setThresholds] = useState(null);

  useEffect(() => {
    metadataApi.getMetadata().then(res => {
      setThresholds(res.data.risk_thresholds);
    });
  }, []);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Profile Section */}
      <div className="bg-card border border-border rounded-xl shadow-lg p-6 flex items-start gap-6">
        <div className="w-20 h-20 rounded-full bg-primary-900 border-2 border-primary-500 flex items-center justify-center text-3xl font-bold text-primary-100">
          {user?.username?.[0]?.toUpperCase()}
        </div>
        <div>
          <h2 className="text-2xl font-bold text-slate-100">{user?.username}</h2>
          <p className="text-primary-400 font-medium capitalize flex items-center gap-2 mt-1">
            <Shield className="w-4 h-4" /> {user?.role} Access
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Config */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-6">
            <SettingsIcon className="w-6 h-6 text-slate-400" />
            <h3 className="text-lg font-semibold text-slate-100">System Configuration</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">Risk Thresholds (Managed Server-Side)</label>
              {thresholds ? (
                <div className="bg-surface border border-border rounded-lg p-4 font-mono text-sm space-y-2">
                  <div className="flex justify-between"><span className="text-green-500">Low Risk</span> <span className="text-slate-300">&lt; {thresholds.Low.max * 100}% prob</span></div>
                  <div className="flex justify-between"><span className="text-yellow-500">Medium Risk</span> <span className="text-slate-300">{thresholds.Medium.min * 100}% - {thresholds.Medium.max * 100}% prob</span></div>
                  <div className="flex justify-between"><span className="text-orange-500">High Risk</span> <span className="text-slate-300">{thresholds.High.min * 100}% - {thresholds.High.max * 100}% prob</span></div>
                  <div className="flex justify-between"><span className="text-red-500">Critical Risk</span> <span className="text-slate-300">&gt;= {thresholds.Critical.min * 100}% prob</span></div>
                </div>
              ) : (
                <div className="text-sm text-slate-500">Loading thresholds...</div>
              )}
            </div>
            <p className="text-xs text-slate-500 bg-surface p-3 rounded-lg border border-border">
              To update risk thresholds, an administrator must update the backend configuration files.
            </p>
          </div>
        </div>

        {/* Dataset Info */}
        <div className="bg-card border border-border rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-3 mb-6">
            <Database className="w-6 h-6 text-slate-400" />
            <h3 className="text-lg font-semibold text-slate-100">Data & Model Usage</h3>
          </div>
          
          <div className="space-y-4 text-sm text-slate-300 leading-relaxed">
            <p>
              BhoomiGuard AI utilizes the <strong>Land Acquisition Delay Dataset</strong> consisting of 10,000 historical records across 20 districts.
            </p>
            <p>
              <strong>Constraint Notice:</strong> The <code className="bg-slate-800 text-primary-400 px-1 rounded">delay_status</code> target variable is strictly excluded from all model inference inputs. 
              The system predicts this outcome based solely on the operational metrics provided.
            </p>
            <p className="text-xs text-slate-500 mt-4 border-t border-border pt-4">
              Project: SIH26017 — Ministry of Rural Development<br/>
              Developed for Smart Automation Theme.
            </p>
          </div>
        </div>
      </div>
      
    </div>
  );
}
