'use client';

import { useEffect, useState } from 'react';
import { useStore } from '@/lib/store';
import { documentAPI } from '@/lib/api-client';
import { Trash2, Loader2 } from 'lucide-react';

export default function SourcesSidebar() {
  const { sources, setSources, removeSource } = useStore();
  const [deletingSource, setDeletingSource] = useState<string | null>(null);

  useEffect(() => {
    // Load sources on mount
    loadSources();
  }, []);

  const loadSources = async () => {
    try {
      const response = await documentAPI.getSources();
      if (response.status && response.data) {
        setSources(response.data.sources || []);
      }
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const handleDeleteSource = async (sourceName: string) => {
    if (!confirm(`Are you sure you want to delete "${sourceName}"? This action cannot be undone.`)) {
      return;
    }

    setDeletingSource(sourceName);
    try {
      const response = await documentAPI.deleteSource(sourceName);
      if (response.status) {
        removeSource(sourceName);
      } else {
        alert(response.message || 'Failed to delete source');
      }
    } catch (error: any) {
      console.error('Failed to delete source:', error);
      alert(error.response?.data?.detail || error.message || 'Failed to delete source');
    } finally {
      setDeletingSource(null);
    }
  };

  return (
    <div className="w-64 bg-secondary border-r border-gray-700 flex flex-col">
      <div className="p-4 border-b border-gray-700">
        <h2 className="font-semibold text-lg">Sources</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        {sources.length === 0 ? (
          <div className="text-center text-gray-400 py-8">
            <p className="mb-2">Saved sources will appear here</p>
            <p className="text-sm">Click Add source above to add PDFs, websites, text, videos, or audio files.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {sources.map((source, index) => (
              <div
                key={index}
                className="bg-secondary-light p-3 rounded-lg border border-gray-700 hover:border-primary transition-colors group relative"
              >
                <div className="font-medium text-sm mb-1 break-words leading-tight pr-8">
                  {source.name}
                </div>
                <div className="text-xs text-gray-400 mt-1.5">
                  <span className="capitalize">{source.type.toLowerCase()}</span> • {source.chunks} chunks
                </div>
                {source.uploaded_at && (
                  <div className="text-xs text-gray-500 mt-1">
                    {source.uploaded_at}
                  </div>
                )}
                <button
                  onClick={() => handleDeleteSource(source.name)}
                  disabled={deletingSource === source.name}
                  className="absolute top-2 right-2 p-1.5 text-gray-400 hover:text-primary transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Delete source"
                >
                  {deletingSource === source.name ? (
                    <Loader2 size={16} className="animate-spin" />
                  ) : (
                    <Trash2 size={16} />
                  )}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

