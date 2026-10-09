import React, { useState } from 'react';
import { BookOpen, ExternalLink, ChevronDown, ChevronRight, FileText } from 'lucide-react';

export default function CitationsCard({ citations }) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-800/80">
      <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-300 mb-2">
        <BookOpen className="w-3.5 h-3.5 text-amber-400" />
        <span>Referensi & Sitasi SOP Resmi:</span>
      </div>

      <div className="grid grid-cols-1 gap-2">
        {citations.map((cit, idx) => (
          <div
            key={idx}
            className="p-2.5 rounded-lg bg-coal-900/90 border border-slate-800 hover:border-amber-500/40 transition-all flex items-start space-x-2.5 group"
          >
            <div className="mt-0.5 p-1 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <FileText className="w-3.5 h-3.5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-mono font-bold text-amber-300 truncate">
                {cit}
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Dokumen operasional tersertifikasi PT Nusantara Coal Operations
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
