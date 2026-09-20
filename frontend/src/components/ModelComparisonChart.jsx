import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ModelComparisonChart({ data }) {
  if (!data || data.length === 0) return <div className="text-slate-400">Loading chart...</div>;

  const chartData = data.map(m => ({
    name: m.model_name,
    Accuracy: Number((m.accuracy * 100).toFixed(1)),
    Precision: Number((m.precision * 100).toFixed(1)),
    Recall: Number((m.recall * 100).toFixed(1)),
    F1: Number((m.f1_score * 100).toFixed(1)),
    F2: Number((m.f2_score * 100).toFixed(1)),
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border p-3 rounded-lg shadow-xl">
          <p className="font-semibold text-slate-100 mb-2">{label}</p>
          {payload.map(p => (
            <p key={p.dataKey} style={{ color: p.color }} className="text-sm">
              {p.name}: {p.value}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-80 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
          <XAxis dataKey="name" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
          <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} domain={[40, 100]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '20px' }} />
          <Bar dataKey="Accuracy" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          <Bar dataKey="F1" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
          <Bar dataKey="F2" fill="#ec4899" radius={[4, 4, 0, 0]} />
          <Bar dataKey="Recall" fill="#10b981" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
