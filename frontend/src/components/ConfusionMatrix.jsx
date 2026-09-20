export default function ConfusionMatrix({ confusionMatrix }) {
  if (!confusionMatrix) return <div className="text-slate-400">Loading...</div>;

  const { TN, FP, FN, TP } = confusionMatrix;
  const total = TN + FP + FN + TP;

  const getPct = (val) => total > 0 ? ((val / total) * 100).toFixed(1) : 0;

  return (
    <div className="w-full">
      <div className="grid grid-cols-[auto_1fr_1fr] gap-1 text-sm">
        <div className="flex items-center justify-center -rotate-90 text-slate-400 font-semibold uppercase text-xs tracking-widest row-span-2 mr-2">
          Actual
        </div>
        
        {/* Header */}
        <div className="col-start-2 flex flex-col justify-end text-center pb-2">
          <span className="font-semibold text-slate-200">Predicted</span>
          <span className="text-green-500 font-medium">No Delay</span>
        </div>
        <div className="col-start-3 flex flex-col justify-end text-center pb-2">
          <span className="font-semibold text-slate-200">Predicted</span>
          <span className="text-red-500 font-medium">Delay</span>
        </div>

        {/* Row 1 (Actual No Delay) */}
        <div className="flex items-center justify-end pr-3 font-medium text-slate-200">
          No Delay
        </div>
        <div className="bg-primary-900/30 border border-primary-500/20 rounded p-4 text-center">
          <div className="text-2xl font-bold text-slate-100">{TN}</div>
          <div className="text-xs text-slate-400">True Negative ({getPct(TN)}%)</div>
        </div>
        <div className="bg-red-900/20 border border-red-500/20 rounded p-4 text-center">
          <div className="text-2xl font-bold text-slate-100">{FP}</div>
          <div className="text-xs text-slate-400">False Positive ({getPct(FP)}%)</div>
        </div>

        {/* Row 2 (Actual Delay) */}
        <div className="flex items-center justify-end pr-3 font-medium text-slate-200">
          Delay
        </div>
        <div className="bg-orange-900/20 border border-orange-500/20 rounded p-4 text-center">
          <div className="text-2xl font-bold text-slate-100">{FN}</div>
          <div className="text-xs text-slate-400">False Negative ({getPct(FN)}%)</div>
        </div>
        <div className="bg-primary-900/30 border border-primary-500/20 rounded p-4 text-center">
          <div className="text-2xl font-bold text-slate-100">{TP}</div>
          <div className="text-xs text-slate-400">True Positive ({getPct(TP)}%)</div>
        </div>
      </div>
      
      <div className="mt-4 text-xs text-slate-400">
        <p><span className="text-orange-400 font-semibold">False Negatives (FN)</span> are the most dangerous in this domain, as they represent delayed projects the system failed to predict.</p>
      </div>
    </div>
  );
}
