import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Terminal, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Sparkles, 
  Layers, 
  Clock, 
  ExternalLink,
  RefreshCw,
  Trash2,
  Cpu,
  ChevronRight
} from 'lucide-react';

import Header from './components/Header';
import ToolTracePanel from './components/ToolTracePanel';
import CitationsCard from './components/CitationsCard';
import ApprovalModal from './components/ApprovalModal';
import QuickPrompts from './components/QuickPrompts';
import MarkdownRenderer from './components/MarkdownRenderer';

export default function App() {
  const [currentRole, setCurrentRole] = useState('staff');
  const [currentUser, setCurrentUser] = useState('Dimas Pratama');
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTracePanel, setShowTracePanel] = useState(true);
  const [activeTrace, setActiveTrace] = useState(null);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState(false);

  const [messages, setMessages] = useState([
    {
      id: 'msg-init-1',
      sender: 'agent',
      text: `Halo **${currentUser}**! Saya **OpsAgent**, asisten AI operasional internal **PT Nusantara Coal Operations**.\n\nSaya siap membantu Anda memproses query operasional harian:\n- 📊 **Stok Batubara:** Query database stockpile (Palaran, Muara Berau) & batas suhu aman.\n- 🚢 **Logistik Tongkang:** Posisi kapal, status berlayar, dan estimasi tiba (ETA) di PLTU.\n- 📑 **ERP & Purchase Order:** Cek tagihan invoice, supplier, serta pembuatan draft PO dengan otorisasi Human-in-the-Loop.\n- 📚 **SOP Internal (RAG):** Pedoman penanganan batubara panas, mitigasi cuaca buruk di jetty, dan standar deviasi timbangan.\n- 📅 **Integrasi M365:** Cek jadwal rapat koordinasi jetty harian dan draft memo internal.\n\nSilakan pilih saran cepat di bawah atau ketikkan pertanyaan Anda.`,
      status: 'done',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: [],
      trace: null,
    },
  ]);

  const messagesEndRef = useRef(null);

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch pending approvals on mount and role change
  const fetchApprovals = async () => {
    try {
      const res = await fetch('/api/v1/approvals');
      if (res.ok) {
        const data = await res.json();
        setPendingApprovals(data || []);
      }
    } catch (err) {
      console.warn('Could not fetch approvals:', err);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [currentRole]);

  // Clear chat history
  const handleClearChat = () => {
    setMessages([
      {
        id: `msg-clear-${Date.now()}`,
        sender: 'agent',
        text: `Percakapan telah dibersihkan. Silakan ajukan pertanyaan operasional baru untuk PT Nusantara Coal Operations.`,
        status: 'done',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        citations: [],
        trace: null,
      },
    ]);
    setActiveTrace(null);
  };

  // Handle SSE query submission
  const handleSendMessage = async (queryText) => {
    const query = (queryText || inputValue).trim();
    if (!query || isLoading) return;

    setInputValue('');
    setIsLoading(true);

    const userMessageId = `usr-${Date.now()}`;
    const agentMessageId = `agt-${Date.now()}`;

    // Add user message
    const userMsg = {
      id: userMessageId,
      sender: 'user',
      text: query,
      senderName: currentUser,
      role: currentRole,
      status: 'done',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    // Add placeholder agent message
    const agentMsg = {
      id: agentMessageId,
      sender: 'agent',
      text: '',
      status: 'streaming',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      citations: [],
      trace: {
        traceId: null,
        intent: null,
        confidence: null,
        routerLatency: null,
        toolCall: null,
        toolResult: null,
        isBlocked: false,
        requiresApproval: false,
        totalLatency: null,
        totalTokens: 0,
        costUsd: 0,
      },
    };

    setMessages((prev) => [...prev, userMsg, agentMsg]);
    setActiveTrace(agentMsg.trace);

    const currentTraceState = { ...agentMsg.trace };

    try {
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          user_role: currentRole,
          user_id: currentRole === 'manager' ? 'USR-MGR-01' : 'USR-STAFF-01',
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          if (!part.trim()) continue;

          let eventName = 'message';
          let dataStr = '';

          const lines = part.split('\n');
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              eventName = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              dataStr = line.slice(6);
            }
          }

          let parsedData = dataStr;
          try {
            parsedData = JSON.parse(dataStr);
          } catch (e) {
            // Raw string
          }

          // Handle specific SSE events
          if (eventName === 'trace_init') {
            currentTraceState.traceId = parsedData.trace_id;
            setActiveTrace({ ...currentTraceState });
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, trace: { ...currentTraceState } } : m
              )
            );
          } else if (eventName === 'router_step') {
            currentTraceState.intent = parsedData.intent;
            currentTraceState.confidence = parsedData.confidence;
            currentTraceState.routerLatency = parsedData.latency_ms;
            setActiveTrace({ ...currentTraceState });
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, trace: { ...currentTraceState } } : m
              )
            );
          } else if (eventName === 'tool_call') {
            currentTraceState.toolCall = parsedData;
            setActiveTrace({ ...currentTraceState });
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, trace: { ...currentTraceState } } : m
              )
            );
          } else if (eventName === 'tool_result') {
            currentTraceState.toolResult = parsedData;
            setActiveTrace({ ...currentTraceState });
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, trace: { ...currentTraceState } } : m
              )
            );
          } else if (eventName === 'citations') {
            const citList = Array.isArray(parsedData) ? parsedData : [];
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, citations: citList } : m
              )
            );
          } else if (eventName === 'approval_required') {
            currentTraceState.requiresApproval = true;
            setActiveTrace({ ...currentTraceState });
            fetchApprovals();
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId
                  ? { ...m, requiresApproval: true, approvalData: parsedData, trace: { ...currentTraceState } }
                  : m
              )
            );
          } else if (eventName === 'guardrail_blocked') {
            currentTraceState.isBlocked = true;
            setActiveTrace({ ...currentTraceState });
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId
                  ? { ...m, isBlocked: true, guardrailData: parsedData, trace: { ...currentTraceState } }
                  : m
              )
            );
          } else if (eventName === 'token') {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId ? { ...m, text: m.text + parsedData } : m
              )
            );
          } else if (eventName === 'done') {
            const finalState = typeof parsedData === 'object' ? parsedData : {};
            const totalLat = finalState.step_latencies?.total || 320;
            const tokens = finalState.token_usage?.total_tokens || 420;
            const cost = finalState.token_usage?.total_cost_usd || 0.00032;

            currentTraceState.totalLatency = totalLat;
            currentTraceState.totalTokens = tokens;
            currentTraceState.costUsd = cost;

            setActiveTrace({ ...currentTraceState });
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId
                  ? { ...m, status: 'done', trace: { ...currentTraceState } }
                  : m
              )
            );
          } else if (eventName === 'error') {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === agentMessageId
                  ? {
                      ...m,
                      status: 'error',
                      text: m.text || `Terjadi kesalahan saat memproses permintaan: ${parsedData.error || parsedData}`,
                    }
                  : m
              )
            );
          }
        }
      }
    } catch (err) {
      console.error('Chat stream failed:', err);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentMessageId
            ? {
                ...m,
                status: 'error',
                text: `Koneksi ke backend gagal: ${err.message}. Pastikan service backend FastAPI berjalan di port 8000.`,
              }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-coal-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Navigation Bar */}
      <Header
        currentRole={currentRole}
        setCurrentRole={setCurrentRole}
        currentUser={currentUser}
        setCurrentUser={setCurrentUser}
        pendingApprovalsCount={pendingApprovals.length}
        onOpenApprovalModal={() => setIsApprovalModalOpen(true)}
        showTracePanel={showTracePanel}
        setShowTracePanel={setShowTracePanel}
      />

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden relative">
        {/* Central Chat Stream */}
        <main className="flex-1 flex flex-col h-full bg-radial-gradient min-w-0">
          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto px-4 md:px-6 lg:px-8 py-6 space-y-5">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${
                  msg.sender === 'user' ? 'items-end' : 'items-start'
                } max-w-4xl mx-auto w-full`}
              >
                {/* Sender badge & time */}
                <div className="flex items-center space-x-2 text-[11px] text-slate-400 mb-1 px-1">
                  {msg.sender === 'user' ? (
                    <>
                      <span className="font-semibold text-sky-400">{msg.senderName || currentUser}</span>
                      <span className="text-slate-600">•</span>
                      <span>{msg.timestamp}</span>
                      <div className="w-5 h-5 rounded-full bg-sky-600/30 border border-sky-500/40 flex items-center justify-center text-sky-300">
                        <User className="w-3 h-3" />
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="w-5 h-5 rounded-full bg-emerald-600/30 border border-emerald-500/40 flex items-center justify-center text-emerald-300">
                        <Bot className="w-3 h-3" />
                      </div>
                      <span className="font-semibold text-emerald-400">OpsAgent AI</span>
                      <span className="text-slate-600">•</span>
                      <span>{msg.timestamp}</span>
                      {msg.trace?.intent && (
                        <span className="px-1.5 py-0.2 rounded bg-coal-900 border border-slate-800 text-[10px] font-mono text-slate-400 uppercase">
                          {msg.trace.intent}
                        </span>
                      )}
                    </>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={`p-4 rounded-2xl text-xs md:text-sm max-w-[92%] sm:max-w-[85%] ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-sky-600 to-cyan-600 text-white rounded-tr-none shadow-lg shadow-sky-600/10'
                      : 'bg-coal-900/90 border border-slate-800 rounded-tl-none text-slate-200 shadow-xl backdrop-blur-sm'
                  }`}
                >
                  {/* Guardrail Violation Banner */}
                  {msg.isBlocked && (
                    <div className="mb-3 p-3 rounded-xl bg-rose-950/80 border border-rose-800/80 text-rose-200 flex items-start space-x-2.5">
                      <ShieldAlert className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold text-xs uppercase tracking-wide text-rose-300">
                          {msg.guardrailData?.violation || 'Intervensi Guardrail Keamanan'}
                        </p>
                        <p className="text-[11px] text-rose-300/90 mt-0.5">
                          {msg.guardrailData?.reason || 'Permintaan ditolak oleh sistem audit keamanan.'}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Human-in-the-Loop Notification Banner */}
                  {msg.requiresApproval && (
                    <div className="mb-3 p-3 rounded-xl bg-amber-950/70 border border-amber-800/80 text-amber-200 flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                        <div>
                          <p className="font-bold text-xs text-amber-300">Memerlukan Persetujuan Manager (HITL)</p>
                          <p className="text-[10px] text-amber-400/80">Draft PO tersimpan dalam status PENDING</p>
                        </div>
                      </div>
                      <button
                        onClick={() => setIsApprovalModalOpen(true)}
                        className="px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-400 text-coal-950 font-bold text-[11px] flex items-center space-x-1 transition-all"
                      >
                        <span>Review</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </div>
                  )}

                  {/* Text / Markdown Content */}
                  {msg.sender === 'user' ? (
                    <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                  ) : (
                    <>
                      <MarkdownRenderer content={msg.text} />
                      {msg.status === 'streaming' && (
                        <span className="inline-block w-2 h-4 ml-1 bg-sky-400 animate-pulse rounded-sm align-middle" />
                      )}
                    </>
                  )}

                  {/* Verified SOP Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <CitationsCard citations={msg.citations} />
                  )}

                  {/* Trace details button */}
                  {msg.trace && (
                    <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
                      <span className="flex items-center gap-1.5 font-mono text-[10px]">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {msg.trace.totalLatency ? `${msg.trace.totalLatency} ms` : 'Memproses...'}
                      </span>
                      <button
                        onClick={() => {
                          setActiveTrace(msg.trace);
                          setShowTracePanel(true);
                        }}
                        className="text-sky-400 hover:text-sky-300 flex items-center space-x-1 font-semibold group transition-colors"
                      >
                        <span>Audit Tool Trace</span>
                        <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts Bar */}
          <div className="border-t border-slate-800/80 bg-coal-950/60 backdrop-blur-md">
            <QuickPrompts onSelectPrompt={(q) => handleSendMessage(q)} />
          </div>

          {/* Bottom Chat Input Bar */}
          <div className="p-3 md:p-4 bg-coal-950 border-t border-slate-800 z-10">
            <div className="max-w-4xl mx-auto flex items-center space-x-2">
              <button
                onClick={handleClearChat}
                title="Bersihkan Percakapan"
                className="p-2.5 rounded-xl border border-slate-800 bg-coal-900 text-slate-400 hover:text-rose-400 hover:border-rose-900/50 hover:bg-coal-850 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>

              <div className="flex-1 relative flex items-center">
                <input
                  id="input-user-query"
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage();
                    }
                  }}
                  disabled={isLoading}
                  placeholder={`Tanyakan urusan operasional batubara (${currentRole === 'manager' ? 'Akses Manager' : 'Akses Staff'})...`}
                  className="w-full pl-4 pr-12 py-3 rounded-xl bg-coal-900 border border-slate-800 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500/50 transition-all shadow-inner disabled:opacity-50"
                />

                <button
                  id="btn-send-message"
                  onClick={() => handleSendMessage()}
                  disabled={isLoading || !inputValue.trim()}
                  className="absolute right-2 p-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 disabled:text-slate-600 text-white shadow-md shadow-sky-600/20 transition-all"
                >
                  {isLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin text-sky-300" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
            <div className="max-w-4xl mx-auto flex items-center justify-between mt-2 px-1 text-[11px] text-slate-500 font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Backend: FastAPI v0.111 • SSE Stream Live
              </span>
              <span>Guardrails: Direct/Indirect Injection & PII Active</span>
            </div>
          </div>
        </main>

        {/* Real-time Audit & Tool Trace Panel (Drawer) */}
        {showTracePanel && (
          <ToolTracePanel
            activeTrace={activeTrace}
            onClose={() => setShowTracePanel(false)}
          />
        )}
      </div>

      {/* Human-in-the-Loop Approval Modal */}
      <ApprovalModal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        approvals={pendingApprovals}
        currentRole={currentRole}
        currentUser={currentUser}
        onDecisionSubmit={() => fetchApprovals()}
        onSwitchToManager={() => {
          setCurrentRole('manager');
          setCurrentUser('Hendra Setiawan');
        }}
      />
    </div>
  );
}
