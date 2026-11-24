import React from 'react';
import { TaskItem } from '../types';
import { Clock, CheckCircle2, AlertTriangle, ArrowRight } from 'lucide-react';

interface OutcomeLedgerProps {
  tasks: TaskItem[];
  onCompleteTask: (id: string) => void;
}

export const OutcomeLedger: React.FC<OutcomeLedgerProps> = ({ tasks, onCompleteTask }) => {
  const getBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">Completed</span>;
      case 'overdue':
        return <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30">Overdue</span>;
      case 'stalled':
        return <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30">Stalled</span>;
      default:
        return <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">Active</span>;
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Outcome Ledger</h2>
          <p className="text-xs text-slate-400">Tracking follow-through & verified results</p>
        </div>
        <span className="text-xs font-mono text-slate-500">{tasks.length} Tracked Items</span>
      </div>

      <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
        {tasks.length === 0 ? (
          <p className="text-sm text-slate-500 text-center py-8">No commitments tracked yet. Ask the assistant to track a task!</p>
        ) : (
          tasks.map((task) => (
            <div
              key={task.id}
              className="flex items-center justify-between p-3.5 rounded-xl border border-slate-800/80 bg-slate-950/60 hover:border-slate-700 transition"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-slate-200">{task.title}</span>
                  {getBadge(task.status)}
                </div>
                {task.deadline && (
                  <div className="flex items-center gap-1.5 text-xs text-slate-400">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>Due: {new Date(task.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                )}
              </div>
              {task.status !== 'completed' && (
                <button
                  onClick={() => onCompleteTask(task.id)}
                  title="Mark Completed"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition"
                >
                  <CheckCircle2 className="w-5 h-5" />
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};
