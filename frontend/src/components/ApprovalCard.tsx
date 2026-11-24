import React from 'react';
import { ShieldAlert, Check, X } from 'lucide-react';

interface ApprovalCardProps {
  action: {
    action_id: string;
    tool_name: string;
    risk_level: string;
    summary: string;
    parameters: any;
  };
  onApprove: (actionId: string) => void;
  onReject: (actionId: string) => void;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({ action, onApprove, onReject }) => {
  return (
    <div className="my-3 rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-slate-200">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-amber-500/20 text-amber-400">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 uppercase tracking-wider">
              {action.risk_level} Risk Action
            </span>
            <span className="text-xs text-slate-400 font-mono">{action.tool_name}</span>
          </div>
          <p className="mt-1 text-sm font-medium text-slate-100">{action.summary}</p>
          <pre className="mt-2 text-xs bg-slate-950/80 p-2.5 rounded-lg border border-slate-800 text-slate-400 overflow-x-auto">
            {JSON.stringify(action.parameters, null, 2)}
          </pre>
          <div className="mt-3 flex gap-2">
            <button
              onClick={() => onApprove(action.action_id)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-xs font-medium text-white transition"
            >
              <Check className="w-3.5 h-3.5" /> Approve Action
            </button>
            <button
              onClick={() => onReject(action.action_id)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition"
            >
              <X className="w-3.5 h-3.5" /> Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
