export const formatPercent = (val) => {
  if (val === null || val === undefined) return '0.00%';
  return `${Number(val).toFixed(2)}%`;
};

export const getRiskColor = (level) => {
  switch (level?.toLowerCase()) {
    case 'low': return 'text-green-500';
    case 'medium': return 'text-yellow-500';
    case 'high': return 'text-orange-500';
    case 'critical': return 'text-red-500';
    default: return 'text-slate-400';
  }
};

export const getRiskBg = (level) => {
  switch (level?.toLowerCase()) {
    case 'low': return 'bg-green-500/10 border-green-500/20';
    case 'medium': return 'bg-yellow-500/10 border-yellow-500/20';
    case 'high': return 'bg-orange-500/10 border-orange-500/20';
    case 'critical': return 'bg-red-500/10 border-red-500/20';
    default: return 'bg-slate-500/10 border-slate-500/20';
  }
};

export const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

export const getPredictionColor = (pred) => {
  return pred === 'Yes' ? 'text-red-500' : 'text-green-500';
};
