import React from 'react';
import { Calendar, AlertCircle, ArrowUpRight, Sparkles } from 'lucide-react';

interface DailyBriefingProps {
  onRefresh: () => void;
  isLoading: boolean;
  briefingText: string | null;
}

export const DailyBriefing: React.FC<DailyBriefingProps> = ({ onRefresh, isLoading, briefingText }) => {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl shadow-lg relative overflow-hidden">
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Daily Briefing</h2>
            <p className="text-xs text-slate-400">Aggregated from Google Calendar, Drive & Ledger</p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="text-xs px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition flex items-center gap-1.5 disabled:opacity-50"
        >
          {isLoading ? "Generating..." : "Regenerate"}
          <ArrowUpRight className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 text-sm text-slate-300 leading-relaxed font-mono whitespace-pre-line max-h-60 overflow-y-auto">
        {briefingText || "Click 'Regenerate' to compile today's agenda, deadlines, and stalled commitments."}
      </div>
    </div>
  );
};
