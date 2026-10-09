import React, { useState } from 'react';
import { 
  Activity, 
  Terminal, 
  Clock, 
  Coins, 
  ShieldCheck, 
  ShieldAlert, 
  Database, 
  BookOpen, 
  Calendar, 
  Cpu, 
  CheckCircle2, 
  XCircle, 
  ChevronRight, 
  ChevronDown,
  Copy,
  Check
} from 'lucide-react';

export default function ToolTracePanel({ activeTrace, onClose }) {
  const [copiedTrace, setCopiedTrace] = useState(false);
  const [expandArgs, setExpandArgs] = useState(true);
  const [expandResult, setExpandResult] = useState(true);

  if (!activeTrace) {
    return (
      <aside className="w-80 lg:w-96 border-l border-slate-800 bg-coal-950 p-4 flex flex-col items-center justify-center text-center select-none">
        <Activity className="w-10 h-10 text-slate-700 mb-2 animate-pulse-slow" />
        <h2 className="text-sm font-semibold text-slate-300">Tool Trace Realtime</h2>
        <p className="text-xs text-slate-500 mt-1 max-w-xs">
          Kirimkan pertanyaan untuk melihat langkah klasifikasi router, eksekusi tool, latensi, dan token secara realtime.
        </p>
      </aside>
    );
  }

  const handleCopyTraceId = () => {
    if (activeTrace.traceId) {
      navigator.clipboard.writeText(activeTrace.traceId);
      setCopiedTrace(true);
      setTimeout(() => setCopiedTrace(false), 2000);
    }
  };

  const getToolIcon = (toolName) => {
    switch (toolName) {
      case 'sql_query':
        return <Database className="w-4 h-4 text-emerald-400" />;
      case 'erp_api':
        return <Terminal className="w-4 h-4 text-blue-400" />;
      case 'm365':
        return <Calendar className="w-4 h-4 text-purple-400" />;
      case 'search_docs':
        return <BookOpen className="w-4 h-4 text-amber-400" />;
      default:
        return <Cpu className="w-4 h-4 text-sky-400" />;
    }
  };

  return (
    <aside className="w-80 lg:w-96 border-l border-slate-800 bg-coal-950 flex flex-col h-full text-slate-200 z-20">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800 flex items-center justify-between bg-coal-900/40">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-sky-400" />
          <h2 className="text-xs font-bold text-slate-100 uppercase tracking-wider">Audit & Tool Trace</h2>
        </div>
        <div className="flex items-center space-x-1.5">
          <button 
            onClick={handleCopyTraceId}
            className="text-[11px] font-mono px-2 py-0.5 rounded bg-coal-850 hover:bg-coal-800 border border-slate-700 text-slate-300 flex items-center space-x-1 transition-all"
            title="Salin Trace ID"
          >
            {copiedTrace ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
            <span className="truncate max-w-[80px]">{activeTrace.traceId?.slice(0, 10)}...</span>
          </button>
        </div>
      </div>

      {/* Trace Timeline Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Step 1: Two-Tier Intent Routing */}
        <div className="rounded-xl p-3 border border-slate-800 bg-coal-900/60 glass-panel">
          <div className="flex items-center justify-between text-xs mb-1.5">
            <span className="font-semibold text-sky-400 flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5" /> 1. Intent Router (8B)
            </span>
            {activeTrace.routerLatency && (
              <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-500" /> {activeTrace.routerLatency} ms
              </span>
            )}
          </div>
          
          <div className="mt-2 flex items-center justify-between text-xs bg-coal-950/80 p-2 rounded-lg border border-slate-800/80">
            <span className="text-slate-400">Classified Intent:</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold uppercase bg-sky-950 text-sky-300 border border-sky-800">
              {activeTrace.intent || 'Routing...'}
            </span>
          </div>

          {activeTrace.confidence && (
            <div className="mt-1.5 flex justify-between text-[11px] text-slate-400">
              <span>Confidence Score:</span>
              <span className="font-mono text-emerald-400 font-semibold">{Math.round(activeTrace.confidence * 100)}%</span>
            </div>
          )}
        </div>

        {/* Step 2: Tool Invocation */}
        {activeTrace.toolCall && (
          <div className="rounded-xl p-3 border border-slate-800 bg-coal-900/60 glass-panel">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                {getToolIcon(activeTrace.toolCall.tool)} 2. Tool Calling
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/70 text-emerald-300 border border-emerald-800/50">
                {activeTrace.toolCall.tool}
              </span>
            </div>

            <div className="mt-2">
              <button 
                onClick={() => setExpandArgs(!expandArgs)}
                className="w-full flex items-center justify-between text-[11px] text-slate-400 hover:text-slate-200 py-1"
              >
                <span>Arguments Input</span>
                {expandArgs ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>

              {expandArgs && (
                <pre className="mt-1 p-2 rounded-lg bg-coal-950 text-[11px] font-mono text-slate-300 overflow-x-auto border border-slate-800/80 max-h-36">
                  {JSON.stringify(activeTrace.toolCall.arguments, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Tool Execution Result */}
        {activeTrace.toolResult && (
          <div className="rounded-xl p-3 border border-slate-800 bg-coal-900/60 glass-panel">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-blue-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" /> 3. Output Ringkas
              </span>
              {activeTrace.toolResult.latency_ms && (
                <span className="text-[10px] font-mono text-slate-400 flex items-center gap-1">
                  <Clock className="w-3 h-3 text-slate-500" /> {activeTrace.toolResult.latency_ms} ms
                </span>
              )}
            </div>

            <p className="text-xs text-slate-300 bg-coal-950/70 p-2 rounded-lg border border-slate-800/80 leading-relaxed mt-1">
              {activeTrace.toolResult.summary}
            </p>

            {activeTrace.toolResult.output && (
              <div className="mt-2">
                <button 
                  onClick={() => setExpandResult(!expandResult)}
                  className="w-full flex items-center justify-between text-[11px] text-slate-400 hover:text-slate-200 py-1"
                >
                  <span>Raw Output Preview</span>
                  {expandResult ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                </button>
                {expandResult && (
                  <pre className="mt-1 p-2 rounded-lg bg-coal-950 text-[10px] font-mono text-slate-300 overflow-x-auto border border-slate-800/80 max-h-36">
                    {typeof activeTrace.toolResult.output === 'object' 
                      ? JSON.stringify(activeTrace.toolResult.output, null, 2)
                      : String(activeTrace.toolResult.output)
                    }
                  </pre>
                )}
              </div>
            )}
          </div>
        )}

        {/* Step 4: Guardrails Status */}
        <div className="rounded-xl p-3 border border-slate-800 bg-coal-900/60 glass-panel text-xs space-y-2">
          <div className="font-semibold text-slate-200 flex items-center gap-1.5 mb-2">
            <ShieldCheck className="w-4 h-4 text-sky-400" /> 4. Keamanan & Kepatuhan
          </div>
          
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Prompt Injection:</span>
            {activeTrace.isBlocked ? (
              <span className="text-rose-400 font-semibold flex items-center gap-1">
                <XCircle className="w-3 h-3" /> Blocked
              </span>
            ) : (
              <span className="text-emerald-400 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Safe
              </span>
            )}
          </div>

          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">PII Masking:</span>
            <span className="text-emerald-400 font-medium">Active (NIK/HP/Email)</span>
          </div>

          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400">Human-In-The-Loop:</span>
            <span className="text-amber-400 font-medium">
              {activeTrace.requiresApproval ? 'Approval Required' : 'Read Action'}
            </span>
          </div>
        </div>

        {/* Step 5: Metrics & Cost */}
        <div className="rounded-xl p-3 border border-slate-800 bg-coal-900/60 glass-panel text-xs">
          <div className="font-semibold text-slate-200 flex items-center gap-1.5 mb-2">
            <Coins className="w-4 h-4 text-amber-400" /> 5. Penggunaan Token & Latensi
          </div>

          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="bg-coal-950 p-2 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block">Total Latency</span>
              <span className="text-xs font-mono font-bold text-sky-400">
                {activeTrace.totalLatency ? `${activeTrace.totalLatency} ms` : 'Streaming...'}
              </span>
            </div>

            <div className="bg-coal-950 p-2 rounded-lg border border-slate-800/80">
              <span className="text-[10px] text-slate-400 block">Total Tokens</span>
              <span className="text-xs font-mono font-bold text-purple-400">
                {activeTrace.totalTokens || '—'}
              </span>
            </div>

            <div className="bg-coal-950 p-2 rounded-lg border border-slate-800/80 col-span-2 flex items-center justify-between">
              <span className="text-[10px] text-slate-400">Estimasi Biaya:</span>
              <span className="text-xs font-mono font-bold text-emerald-400">
                ${activeTrace.costUsd?.toFixed(6) || '0.000000'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
