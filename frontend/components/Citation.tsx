'use client';

import { useState } from 'react';

interface CitationProps {
  source: {
    source_file: string;
    source_type?: string;
    page_number?: number;
    chunk_id?: string;
    content?: string;
  };
  number: number;
}

export default function Citation({ source, number }: CitationProps) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <span
      className="citation-number relative"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {number}
      {showTooltip && (
        <div className="citation-tooltip">
          <div className="tooltip-source">
            Source: {source.source_file}
            {source.page_number && `, Page: ${source.page_number}`}
          </div>
          {source.content && (
            <div className="tooltip-content text-xs mt-2 max-h-48 overflow-y-auto">
              {source.content}
            </div>
          )}
        </div>
      )}
    </span>
  );
}

