import React from 'react';
import { Database, Ship, FilePlus, Flame, Receipt } from 'lucide-react';

export default function QuickPrompts({ onSelectPrompt }) {
  const prompts = [
    {
      id: 'prompt-stock',
      label: 'Stok Batubara Palaran',
      query: 'Berapa sisa stok batubara dan suhu tumpukan di Stockpile Palaran?',
      icon: <Database className="w-3.5 h-3.5 text-emerald-400" />,
      tag: 'SQL Tool',
    },
    {
      id: 'prompt-shipment',
      label: 'Posisi Tongkang Berlayar',
      query: 'Cek status dan jadwal tongkang pengiriman yang sedang berlayar ke PLTU Suralaya',
      icon: <Ship className="w-3.5 h-3.5 text-sky-400" />,
      tag: 'SQL / Shipments',
    },
    {
      id: 'prompt-po',
      label: 'Buat Draft PO Batubara',
      query: 'Tolong buat draft PO batubara 7500 MT GAR 4200 ke supplier PT Kaltim Prima Mining',
      icon: <FilePlus className="w-3.5 h-3.5 text-purple-400" />,
      tag: 'ERP / Write Action',
    },
    {
      id: 'prompt-fire',
      label: 'SOP Suhu Batubara > 55°C',
      query: 'Bagaimana SOP tindakan darurat jika suhu batubara di stockpile mencapai 55 C?',
      icon: <Flame className="w-3.5 h-3.5 text-rose-400" />,
      tag: 'RAG SOP-002',
    },
    {
      id: 'prompt-invoice',
      label: 'Toleransi Timbangan Invoice',
      query: 'Berapa batas toleransi selisih timbangan pada tagihan invoice customer?',
      icon: <Receipt className="w-3.5 h-3.5 text-amber-400" />,
      tag: 'RAG SOP-004',
    },
  ];

  return (
    <div className="py-2 px-4 flex items-center space-x-2 overflow-x-auto select-none no-scrollbar">
      <span className="text-[11px] font-semibold text-slate-500 whitespace-nowrap hidden sm:inline">
        Saran Cepat:
      </span>
      {prompts.map((p) => (
        <button
          key={p.id}
          id={p.id}
          onClick={() => onSelectPrompt(p.query)}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-coal-900 hover:bg-coal-850 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white transition-all whitespace-nowrap shadow-sm group"
        >
          {p.icon}
          <span>{p.label}</span>
          <span className="text-[9px] font-mono px-1 py-0.2 rounded bg-slate-800 text-slate-400 group-hover:text-slate-300">
            {p.tag}
          </span>
        </button>
      ))}
    </div>
  );
}
