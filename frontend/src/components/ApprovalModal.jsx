import React, { useState } from 'react';
import { 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  UserCheck, 
  DollarSign, 
  Building2, 
  Scale, 
  MapPin, 
  Calendar,
  X
} from 'lucide-react';

export default function ApprovalModal({ 
  isOpen, 
  onClose, 
  approvals, 
  currentRole, 
  currentUser, 
  onDecisionSubmit,
  onSwitchToManager 
}) {
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [managerNotes, setManagerNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState(null);

  if (!isOpen) return null;

  const currentItem = selectedApproval || approvals[0];

  const handleDecision = async (decision) => {
    if (!currentItem) return;
    setSubmitting(true);
    setFeedbackMsg(null);
    try {
      const res = await fetch(`/api/v1/approvals/${currentItem.approval_id}/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision: decision,
          decided_by: currentUser,
          user_role: currentRole,
          manager_notes: managerNotes || (decision === 'APPROVE' ? 'Disetujui via UI OpsAgent' : 'Ditolak via UI OpsAgent'),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        setFeedbackMsg({ type: 'error', text: data.detail || 'Gagal memproses persetujuan.' });
      } else {
        setFeedbackMsg({ type: 'success', text: data.message });
        if (onDecisionSubmit) onDecisionSubmit(data);
        setTimeout(() => {
          onClose();
        }, 1500);
      }
    } catch (err) {
      setFeedbackMsg({ type: 'error', text: String(err) });
    } finally {
      setSubmitting(false);
    }
  };

  const payload = currentItem?.payload || {};
  const items = payload.items || [];
  const firstItem = items[0] || {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-2xl bg-coal-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-coal-950/60">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
                Human-in-the-Loop Otorisasi Aksi
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 font-mono font-bold">
                  SOP-PROC-003
                </span>
              </h2>
              <p className="text-xs text-slate-400">Verifikasi dan persetujuan bertingkat mutasi Purchase Order</p>
            </div>
          </div>
          <button 
            id="btn-close-approval-modal"
            onClick={onClose} 
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 overflow-y-auto space-y-4 flex-1">
          {(!approvals || approvals.length === 0) ? (
            <div className="text-center py-12">
              <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-2" />
              <h3 className="text-sm font-semibold text-slate-200">Tidak Ada Antrean Persetujuan</h3>
              <p className="text-xs text-slate-400 mt-1">Seluruh pengajuan aksi tulis dan Purchase Order telah selesai diproses.</p>
            </div>
          ) : (
            <>
              {/* Approval ID and status */}
              <div className="flex items-center justify-between bg-coal-950 p-3 rounded-xl border border-slate-800">
                <div>
                  <span className="text-[10px] text-slate-500 font-mono block">APPROVAL ID</span>
                  <span className="text-xs font-mono font-bold text-sky-400">{currentItem?.approval_id}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 font-mono block">STATUS</span>
                  <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-950/70 text-amber-300 border border-amber-800">
                    {currentItem?.status}
                  </span>
                </div>
              </div>

              {/* Detail purchase order card */}
              <div className="rounded-xl p-4 bg-coal-950/70 border border-slate-800 space-y-3">
                <div className="text-xs font-semibold text-slate-200 border-b border-slate-800 pb-2">
                  Detail Pengajuan Draft Purchase Order
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Supplier Tambang:</span>
                    <span className="font-semibold text-slate-200 flex items-center gap-1.5 mt-0.5">
                      <Building2 className="w-3.5 h-3.5 text-sky-400" />
                      {payload.supplier_name || 'PT Kaltim Prima Mining'}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[11px]">Jetty Tujuan:</span>
                    <span className="font-semibold text-slate-200 flex items-center gap-1.5 mt-0.5">
                      <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                      {payload.delivery_jetty || 'Palaran Jetty, Samarinda'}
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[11px]">Spesifikasi & Tonase:</span>
                    <span className="font-semibold text-slate-200 flex items-center gap-1.5 mt-0.5">
                      <Scale className="w-3.5 h-3.5 text-amber-400" />
                      {firstItem.grade || payload.coal_grade || 'GAR 4200'} • {(payload.total_tonnage_mt || firstItem.quantity_mt || 7500).toLocaleString()} MT
                    </span>
                  </div>

                  <div>
                    <span className="text-slate-400 block text-[11px]">Total Nilai PO:</span>
                    <span className="font-mono font-bold text-emerald-400 text-sm flex items-center gap-1 mt-0.5">
                      <DollarSign className="w-3.5 h-3.5" />
                      ${(payload.total_amount_usd || (firstItem.quantity_mt * firstItem.unit_price_usd) || 438750).toLocaleString()} USD
                    </span>
                  </div>
                </div>

                {payload.notes && (
                  <div className="mt-2 pt-2 border-t border-slate-800/80 text-[11px] text-slate-400">
                    <span className="font-semibold text-slate-300">Catatan Pembuat:</span> {payload.notes}
                  </div>
                )}
              </div>

              {/* RBAC Warning or Manager Action */}
              {currentRole !== 'manager' ? (
                <div className="p-3.5 rounded-xl bg-blue-950/40 border border-blue-800/60 text-xs">
                  <div className="flex items-start space-x-2">
                    <ShieldAlert className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="font-semibold text-blue-200">Pembatasan Otorisasi (RBAC Staff)</p>
                      <p className="text-slate-300 text-[11px] mt-1 leading-relaxed">
                        Anda saat ini masuk sebagai <strong>Staff Operasional ({currentUser})</strong>. 
                        Berdasarkan SOP-PROC-003, Staff hanya berhak membuat DRAFT PO. 
                        Persetujuan final wajib dilakukan oleh <strong>Manager Operasional</strong>.
                      </p>
                      <button
                        id="btn-switch-to-manager"
                        onClick={onSwitchToManager}
                        className="mt-2.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 text-white transition-all shadow-sm"
                      >
                        Beralih ke Role Manager untuk Review
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-1">
                      Catatan Verifikasi Manager (Opsional):
                    </label>
                    <input
                      id="input-manager-notes"
                      type="text"
                      value={managerNotes}
                      onChange={(e) => setManagerNotes(e.target.value)}
                      placeholder="Contoh: Telah dicek sesuai kuota kontrak bulanan PLTU Suralaya."
                      className="w-full px-3 py-2 rounded-lg bg-coal-950 border border-slate-700 text-xs text-slate-200 focus:outline-none focus:border-sky-500 transition-colors"
                    />
                  </div>

                  {feedbackMsg && (
                    <div className={`p-2.5 rounded-lg text-xs flex items-center space-x-2 ${
                      feedbackMsg.type === 'success' ? 'bg-emerald-950/70 border border-emerald-800 text-emerald-300' : 'bg-rose-950/70 border border-rose-800 text-rose-300'
                    }`}>
                      {feedbackMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                      <span>{feedbackMsg.text}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-end space-x-3 pt-2">
                    <button
                      id="btn-reject-po"
                      disabled={submitting}
                      onClick={() => handleDecision('REJECT')}
                      className="px-4 py-2 rounded-xl text-xs font-bold border border-rose-600/50 text-rose-400 hover:bg-rose-950/60 transition-all flex items-center space-x-1.5 disabled:opacity-50"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Tolak (Reject)</span>
                    </button>

                    <button
                      id="btn-approve-po"
                      disabled={submitting}
                      onClick={() => handleDecision('APPROVE')}
                      className="px-5 py-2 rounded-xl text-xs font-bold bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white shadow-lg shadow-emerald-600/20 transition-all flex items-center space-x-1.5 disabled:opacity-50"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Setujui (Approve PO)</span>
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
