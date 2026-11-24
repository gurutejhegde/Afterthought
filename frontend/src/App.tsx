import React, { useState, useEffect } from 'react';
import { DailyBriefing } from './components/DailyBriefing';
import { OutcomeLedger } from './components/OutcomeLedger';
import { VoiceChat } from './components/VoiceChat';
import { TaskItem, ChatMessage } from './types';
import { Sparkles, Layers, ShieldCheck } from 'lucide-react';

export const App: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [briefing, setBriefing] = useState<string | null>(null);
  const [isBriefingLoading, setIsBriefingLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init-1',
      sender: 'assistant',
      text: "Hello Gurutej! I'm Afterthought. I've connected to your Google Workspace and Outcome Ledger. How can I help follow through on your commitments today?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [isSending, setIsSending] = useState(false);

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks');
      if (res.ok) {
        const data = await res.json();
        setTasks(data);
      }
    } catch (e) {
      console.error("Failed to fetch tasks", e);
    }
  };

  const fetchBriefing = async () => {
    setIsBriefingLoading(true);
    try {
      const res = await fetch('/api/briefing');
      if (res.ok) {
        const data = await res.json();
        setBriefing(data.response);
      }
    } catch (e) {
      console.error("Failed to fetch briefing", e);
    } finally {
      setIsBriefingLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
    fetchBriefing();
  }, []);

  const handleSendMessage = async (msg: string) => {
    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: 'user',
      text: msg,
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsSending(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      });
      if (res.ok) {
        const data = await res.json();
        const aiMsg: ChatMessage = {
          id: String(Date.now() + 1),
          sender: 'assistant',
          text: data.response,
          actionRequired: data.action_required,
          sourcesChecked: data.sources_checked,
          timestamp: new Date().toISOString()
        };
        setMessages((prev) => [...prev, aiMsg]);
        fetchTasks();
      }
    } catch (e) {
      console.error("Chat error", e);
    } finally {
      setIsSending(false);
    }
  };

  const handleApproveAction = async (actionId: string) => {
    try {
      const res = await fetch(`/api/actions/${actionId}/approve`, { method: 'POST' });
      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            sender: 'assistant',
            text: "Action approved and executed successfully. Logged in audit trail.",
            timestamp: new Date().toISOString()
          }
        ]);
        fetchTasks();
      }
    } catch (e) {
      console.error("Approve error", e);
    }
  };

  const handleRejectAction = async (actionId: string) => {
    try {
      const res = await fetch(`/api/actions/${actionId}/reject`, { method: 'POST' });
      if (res.ok) {
        setMessages((prev) => [
          ...prev,
          {
            id: String(Date.now()),
            sender: 'assistant',
            text: "Action rejected. No changes were made.",
            timestamp: new Date().toISOString()
          }
        ]);
      }
    } catch (e) {
      console.error("Reject error", e);
    }
  };

  const handleCompleteTask = async (taskId: string) => {
    try {
      const res = await fetch(`/api/tasks/${taskId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'completed', verification_evidence: 'User confirmed via Outcome Ledger' })
      });
      if (res.ok) {
        fetchTasks();
      }
    } catch (e) {
      console.error("Failed to complete task", e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-slate-800/80 bg-slate-950/60 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
            A
          </div>
          <div>
            <h1 className="font-semibold text-sm leading-tight text-white flex items-center gap-2">
              Afterthought
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                Track 01 MVP
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Team Nebula · wHACKiest 2026</p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-indigo-400" /> MCP Ready
          </span>
          <span className="flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Guardrails Active
          </span>
        </div>
      </header>

      {/* Main Content Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7 flex flex-col gap-6">
          <DailyBriefing
            briefingText={briefing}
            isLoading={isBriefingLoading}
            onRefresh={fetchBriefing}
          />
          <VoiceChat
            messages={messages}
            onSendMessage={handleSendMessage}
            onApproveAction={handleApproveAction}
            onRejectAction={handleRejectAction}
            isSending={isSending}
          />
        </div>

        <div className="lg:col-span-5 flex flex-col gap-6">
          <OutcomeLedger
            tasks={tasks}
            onCompleteTask={handleCompleteTask}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
