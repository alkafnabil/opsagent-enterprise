import React, { useState } from 'react';
import { 
  Ship, 
  ShieldCheck, 
  UserCheck, 
  Bell, 
  Cpu, 
  ChevronDown, 
  Activity,
  Layers,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

export default function Header({ 
  currentRole, 
  setCurrentRole, 
  currentUser, 
  setCurrentUser,
  pendingApprovalsCount, 
  onOpenApprovalModal,
  showTracePanel,
  setShowTracePanel
}) {
  const [showRoleDropdown, setShowRoleDropdown] = useState(false);

  const roles = [
    {
      id: 'staff',
      name: 'Dimas Pratama',
      roleTitle: 'Staff Operasional & Jetty Officer',
      badge: 'Staff',
      description: 'Dapat query data stok, RAG SOP, dan membuat draft PO (memerlukan approval).',
    },
    {
      id: 'manager',
      name: 'Hendra Setiawan',
      roleTitle: 'Operations & Procurement Manager',
      badge: 'Manager',
      description: 'Otoritas penuh untuk menyetujui (Approve) PO dan melihat limit kredit keuangan.',
    },
  ];

  const handleSelectRole = (r) => {
    setCurrentRole(r.id);
    setCurrentUser(r.name);
    setShowRoleDropdown(false);
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-coal-950/90 backdrop-blur-md px-4 lg:px-6 flex items-center justify-between z-30 select-none">
      {/* Brand & Identity */}
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-sky-500/20 border border-sky-400/30">
          <Ship className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-base font-bold text-white tracking-tight flex items-center gap-1.5">
              OpsAgent <span className="text-xs px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 font-mono font-medium">v1.0</span>
            </h1>
          </div>
          <p className="text-xs text-slate-400 hidden sm:block">
            PT Nusantara Coal Operations • Asisten Operasional Internal
          </p>
        </div>
      </div>

      {/* Center status indicator */}
      <div className="hidden md:flex items-center space-x-4 bg-coal-900/60 border border-slate-800 px-3 py-1.5 rounded-full text-xs">
        <div className="flex items-center space-x-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-slate-300 font-medium">Backend & Mock ERP</span>
        </div>
        <span className="text-slate-600">|</span>
        <div className="flex items-center space-x-1 text-slate-400">
          <Cpu className="w-3.5 h-3.5 text-sky-400" />
          <span>Dual-Model Router</span>
        </div>
      </div>

      {/* Right controls */}
      <div className="flex items-center space-x-2.5">
        {/* Tool Trace toggle button */}
        <button
          id="btn-toggle-trace"
          onClick={() => setShowTracePanel(!showTracePanel)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center space-x-1.5 transition-all ${
            showTracePanel 
              ? 'bg-sky-500/15 border-sky-500/40 text-sky-300 shadow-sm shadow-sky-500/10' 
              : 'bg-coal-900 border-slate-700/80 text-slate-400 hover:text-slate-200 hover:bg-coal-850'
          }`}
          title="Tampilkan / sembunyikan panel jejak tool realtime"
        >
          <Activity className="w-3.5 h-3.5 text-sky-400" />
          <span className="hidden sm:inline">Tool Trace</span>
        </button>

        {/* Approval Modal Trigger Button */}
        <button
          id="btn-open-approvals"
          onClick={onOpenApprovalModal}
          className={`relative px-3 py-1.5 rounded-lg text-xs font-medium border flex items-center space-x-1.5 transition-all ${
            pendingApprovalsCount > 0
              ? 'bg-amber-500/15 border-amber-500/40 text-amber-300 hover:bg-amber-500/25'
              : 'bg-coal-900 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Bell className="w-3.5 h-3.5" />
          <span>Approvals</span>
          {pendingApprovalsCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-amber-500 text-slate-950 font-mono animate-pulse">
              {pendingApprovalsCount}
            </span>
          )}
        </button>

        {/* Mock Role Switcher Dropdown */}
        <div className="relative">
          <button
            id="btn-user-role-menu"
            onClick={() => setShowRoleDropdown(!showRoleDropdown)}
            className="flex items-center space-x-2 bg-coal-900 hover:bg-coal-850 border border-slate-700/80 px-2.5 py-1.5 rounded-lg transition-all"
          >
            <div className={`w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold ${
              currentRole === 'manager' 
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
                : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
            }`}>
              {currentRole === 'manager' ? 'M' : 'S'}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-medium text-slate-200 leading-tight">{currentUser}</div>
              <div className="text-[10px] text-slate-400 leading-none capitalize font-mono">{currentRole}</div>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Role selection dropdown modal */}
          {showRoleDropdown && (
            <div 
              id="role-dropdown-menu"
              className="absolute right-0 mt-2 w-72 rounded-xl bg-coal-900 border border-slate-700 shadow-2xl p-2 z-50 glass-panel-elevated animate-fade-in"
            >
              <div className="px-3 py-2 border-b border-slate-800/80">
                <p className="text-xs font-semibold text-slate-200">Pilih Role Login Mock</p>
                <p className="text-[11px] text-slate-400">Simulasikan hak akses RBAC Staff vs Manager</p>
              </div>

              <div className="mt-1 space-y-1">
                {roles.map((r) => (
                  <button
                    key={r.id}
                    id={`role-option-${r.id}`}
                    onClick={() => handleSelectRole(r)}
                    className={`w-full text-left p-2.5 rounded-lg text-xs transition-all flex items-start space-x-2.5 ${
                      currentRole === r.id 
                        ? 'bg-sky-500/15 border border-sky-500/30 text-white' 
                        : 'hover:bg-slate-800/60 text-slate-300 border border-transparent'
                    }`}
                  >
                    <div className={`mt-0.5 p-1 rounded ${r.id === 'manager' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400'}`}>
                      <UserCheck className="w-3.5 h-3.5" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-100">{r.name}</span>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          r.id === 'manager' ? 'bg-purple-900/50 text-purple-300' : 'bg-blue-900/50 text-blue-300'
                        }`}>
                          {r.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5 leading-snug">{r.description}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
