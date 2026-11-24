import React, { useState } from 'react';
import { Send, Mic, MicOff, Bot, User } from 'lucide-react';
import { ChatMessage } from '../types';
import { ApprovalCard } from './ApprovalCard';

interface VoiceChatProps {
  messages: ChatMessage[];
  onSendMessage: (msg: string) => void;
  onApproveAction: (actionId: string) => void;
  onRejectAction: (actionId: string) => void;
  isSending: boolean;
}

export const VoiceChat: React.FC<VoiceChatProps> = ({
  messages,
  onSendMessage,
  onApproveAction,
  onRejectAction,
  isSending
}) => {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;
    onSendMessage(input);
    setInput('');
  };

  const toggleMic = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Web Speech recognition not supported in this browser.");
      return;
    }

    if (!isListening) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        onSendMessage(transcript);
      };

      recognition.start();
    }
  };

  return (
    <div className="flex flex-col h-[520px] rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center gap-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <h2 className="text-sm font-semibold text-white">Assistant Chat & Voice</h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">Gemini & MCP Active</span>
      </div>

      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'assistant' && (
              <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 shrink-0">
                <Bot className="w-4 h-4" />
              </div>
            )}
            <div className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.sender === 'user'
                ? 'bg-indigo-600 text-white rounded-br-none'
                : 'bg-slate-950/80 border border-slate-800 text-slate-200 rounded-bl-none whitespace-pre-line'
            }`}>
              <p>{msg.text}</p>
              {msg.actionRequired && (
                <ApprovalCard
                  action={msg.actionRequired}
                  onApprove={onApproveAction}
                  onReject={onRejectAction}
                />
              )}
            </div>
            {msg.sender === 'user' && (
              <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 shrink-0">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="p-3 border-t border-slate-800 bg-slate-950/60 flex items-center gap-2">
        <button
          type="button"
          onClick={toggleMic}
          className={`p-2.5 rounded-xl border transition ${
            isListening
              ? 'bg-rose-500 text-white border-rose-400 animate-pulse'
              : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700'
          }`}
          title="Voice Input (Speech-to-Text)"
        >
          {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for briefing, organize drive files, or add tasks..."
          className="flex-1 bg-slate-900 border border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
        />
        <button
          type="submit"
          disabled={!input.trim() || isSending}
          className="p-2.5 rounded-xl bg-indigo-600 text-white hover:bg-indigo-500 transition disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
