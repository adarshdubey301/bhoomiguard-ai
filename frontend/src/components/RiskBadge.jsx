import { getRiskColor, getRiskBg } from '../utils/helpers';

export function RiskBadge({ level }) {
  if (!level) return null;
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${getRiskBg(level)} ${getRiskColor(level)} uppercase tracking-wider`}>
      {level}
    </span>
  );
}

export function PredictionBadge({ prediction }) {
  if (!prediction) return null;
  const isYes = prediction.toLowerCase() === 'yes';
  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-semibold border ${
      isYes 
        ? 'bg-red-500/10 border-red-500/20 text-red-500' 
        : 'bg-green-500/10 border-green-500/20 text-green-500'
    } uppercase tracking-wider`}>
      {isYes ? 'Delay Likely' : 'No Delay'}
    </span>
  );
}
