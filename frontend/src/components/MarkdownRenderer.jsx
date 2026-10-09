import React, { useState } from 'react';
import { Copy, Check, Terminal } from 'lucide-react';

export default function MarkdownRenderer({ content }) {
  if (!content) return null;

  // Simple and robust parser for operational AI responses
  const renderFormattedLine = (text) => {
    // Process bold, inline code, and links/citations
    const parts = [];
    let currentIndex = 0;
    
    // Regex matches: **bold**, `code`, [link](url)
    const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }

      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={match.index} className="font-semibold text-white">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code
            key={match.index}
            className="px-1.5 py-0.5 rounded bg-coal-800 text-sky-300 font-mono text-[11px] border border-slate-700/60"
          >
            {token.slice(1, -1)}
          </code>
        );
      }
      currentIndex = regex.lastIndex;
    }

    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  const lines = content.split('\n');
  const elements = [];
  let inCodeBlock = false;
  let codeBlockLines = [];
  let codeBlockLang = '';
  let inTable = false;
  let tableRows = [];

  const flushTable = (key) => {
    if (tableRows.length === 0) return null;
    const headerRow = tableRows[0];
    const dataRows = tableRows.slice(1).filter((r) => !r.every((cell) => /^[-:| ]+$/.test(cell)));

    const tableEl = (
      <div key={`table-${key}`} className="my-3 overflow-x-auto rounded-xl border border-slate-800 bg-coal-950/80">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-coal-900/90 text-sky-300">
              {headerRow.map((h, i) => (
                <th key={i} className="p-2.5 font-semibold font-mono text-[11px]">
                  {renderFormattedLine(h.trim())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-slate-300">
            {dataRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-900/40 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="p-2.5 font-mono text-[11px]">
                    {renderFormattedLine(cell.trim())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableRows = [];
    return tableEl;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block toggle
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        // Close code block
        const codeText = codeBlockLines.join('\n');
        elements.push(
          <CodeBlockCard key={`code-${i}`} code={codeText} language={codeBlockLang} />
        );
        codeBlockLines = [];
        codeBlockLang = '';
        inCodeBlock = false;
      } else {
        // Open code block
        inCodeBlock = true;
        codeBlockLang = line.trim().slice(3).trim();
      }
      continue;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      continue;
    }

    // Markdown Table check
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      inTable = true;
      const cells = line.split('|').slice(1, -1);
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      inTable = false;
      elements.push(flushTable(i));
    }

    // Headers
    if (line.startsWith('### ')) {
      elements.push(
        <h3 key={i} className="text-sm font-bold text-sky-400 mt-3 mb-1.5 flex items-center gap-2">
          {renderFormattedLine(line.replace('### ', ''))}
        </h3>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={i} className="text-base font-bold text-white mt-4 mb-2 border-b border-slate-800 pb-1">
          {renderFormattedLine(line.replace('## ', ''))}
        </h2>
      );
    } else if (line.startsWith('# ')) {
      elements.push(
        <h1 key={i} className="text-lg font-bold text-white mt-4 mb-2">
          {renderFormattedLine(line.replace('# ', ''))}
        </h1>
      );
    } else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      elements.push(
        <li key={i} className="ml-4 list-disc text-slate-300 text-xs my-0.5 leading-relaxed marker:text-sky-400">
          {renderFormattedLine(line.trim().replace(/^[-*]\s+/, ''))}
        </li>
      );
    } else if (/^\d+\.\s/.test(line.trim())) {
      elements.push(
        <li key={i} className="ml-4 list-decimal text-slate-300 text-xs my-0.5 leading-relaxed marker:text-amber-400 font-mono">
          {renderFormattedLine(line.trim().replace(/^\d+\.\s+/, ''))}
        </li>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-1.5" />);
    } else {
      elements.push(
        <p key={i} className="text-xs text-slate-200 leading-relaxed my-1">
          {renderFormattedLine(line)}
        </p>
      );
    }
  }

  if (inTable && tableRows.length > 0) {
    elements.push(flushTable(lines.length));
  }

  if (inCodeBlock && codeBlockLines.length > 0) {
    elements.push(
      <CodeBlockCard key="code-end" code={codeBlockLines.join('\n')} language={codeBlockLang} />
    );
  }

  return <div className="space-y-1">{elements}</div>;
}

function CodeBlockCard({ code, language }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="my-3 rounded-xl border border-slate-800 bg-coal-950 overflow-hidden shadow-md">
      <div className="flex items-center justify-between px-3 py-1.5 bg-coal-900 border-b border-slate-800 text-[11px] text-slate-400">
        <span className="flex items-center gap-1.5 font-mono uppercase text-sky-400">
          <Terminal className="w-3.5 h-3.5" />
          {language || 'text'}
        </span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 hover:text-slate-200 transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span className="text-[10px]">{copied ? 'Tersalin' : 'Salin'}</span>
        </button>
      </div>
      <pre className="p-3 font-mono text-[11px] text-emerald-300 overflow-x-auto leading-relaxed">
        {code}
      </pre>
    </div>
  );
}
