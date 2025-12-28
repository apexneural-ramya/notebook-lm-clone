'use client';

import { useState } from 'react';
import { useStore } from '@/lib/store';
import { podcastAPI } from '@/lib/api-client';
import { Mic, Loader2 } from 'lucide-react';

export default function StudioTab() {
  const { sources, setLoading, isLoading } = useStore();
  const [selectedSource, setSelectedSource] = useState('');
  const [podcastStyle, setPodcastStyle] = useState('Conversational');
  const [podcastLength, setPodcastLength] = useState('10 minutes');
  const [error, setError] = useState('');
  const [result, setResult] = useState<any>(null);

  const handleGenerate = async () => {
    if (!selectedSource) {
      setError('Please select a source');
      return;
    }

    setError('');
    setResult(null);
    setLoading(true);

    try {
      const response = await podcastAPI.generatePodcast(selectedSource, podcastStyle, podcastLength);
      if (response.status && response.data) {
        setResult(response.data);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate podcast');
    } finally {
      setLoading(false);
    }
  };

  if (sources.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-400">
          <p className="text-lg mb-2">Studio output will be saved here.</p>
          <p>After adding sources, click to add Podcast Generation and more!</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">🎙️ Generate Podcast</h2>
        <p className="text-gray-400">
          Create an AI-generated podcast discussion from your documents
        </p>
      </div>

      {error && (
        <div className="bg-primary/20 border border-primary/50 text-primary px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="bg-secondary rounded-lg p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Select source for podcast</label>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Choose a document...</option>
              {sources.map((source, idx) => (
                <option key={idx} value={source.name}>
                  {source.name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Podcast Style</label>
              <select
                value={podcastStyle}
                onChange={(e) => setPodcastStyle(e.target.value)}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option>Conversational</option>
                <option>Interview</option>
                <option>Debate</option>
                <option>Educational</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Duration</label>
              <select
                value={podcastLength}
                onChange={(e) => setPodcastLength(e.target.value)}
                className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option>5 minutes</option>
                <option>10 minutes</option>
                <option>15 minutes</option>
                <option>20 minutes</option>
              </select>
            </div>
          </div>

          <button
            onClick={handleGenerate}
            disabled={!selectedSource || isLoading}
            className="w-full px-6 py-3 bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
          >
            {isLoading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                Generating Podcast...
              </>
            ) : (
              <>
                <Mic size={20} />
                Generate Podcast
              </>
            )}
          </button>
        </div>
      </div>

      {isLoading && (
        <div className="bg-secondary rounded-lg p-6 mb-6">
          <div className="flex items-center justify-center gap-3 text-gray-400">
            <Loader2 size={24} className="animate-spin" />
            <span>Processing podcast generation...</span>
          </div>
        </div>
      )}

      {result && (() => {
        let scriptData: any = null;
        try {
          scriptData = typeof result.script === 'string' ? JSON.parse(result.script) : result.script;
        } catch (e) {
          console.error('Failed to parse script:', e);
        }

        const scriptArray = scriptData?.script || [];
        const metadata = scriptData?.metadata || result.script_metadata || {};

        return (
          <div className="bg-secondary rounded-lg p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <span>📝</span> Generated Podcast Script
            </h3>
            
            {/* Metrics */}
            <div className="mb-4 grid grid-cols-3 gap-4">
              <div className="bg-secondary-light p-3 rounded">
                <div className="text-sm text-gray-400 flex items-center gap-1">
                  <span>📊</span> Total Lines
                </div>
                <div className="text-lg font-semibold">{metadata.total_lines || scriptArray.length || 0}</div>
              </div>
              <div className="bg-secondary-light p-3 rounded">
                <div className="text-sm text-gray-400 flex items-center gap-1">
                  <span>⏱️</span> Est. Duration
                </div>
                <div className="text-lg font-semibold">{metadata.estimated_duration || result.script_metadata?.length || 'N/A'}</div>
              </div>
              <div className="bg-secondary-light p-3 rounded">
                <div className="text-sm text-gray-400 flex items-center gap-1">
                  <span>📄</span> Source Type
                </div>
                <div className="text-lg font-semibold">
                  {metadata.source_type || result.script_metadata?.source_type || 
                   (selectedSource.includes('.pdf') ? 'Document' : 
                    selectedSource.includes('http') ? 'Website' : 
                    selectedSource.includes('youtube') || selectedSource.includes('youtu.be') ? 'YouTube Video' : 
                    'Text')}
                </div>
              </div>
            </div>
            
            {result.audio_available && result.audio_files && result.audio_files.length > 0 && (
              <div className="mb-4">
                <h4 className="font-semibold mb-2 flex items-center gap-2">
                  <span>🎵</span> Generated Podcast
                </h4>
                <div className="bg-secondary-light p-4 rounded-lg">
                  <audio controls className="w-full">
                    <source src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${result.audio_files[0]}`} type="audio/wav" />
                    Your browser does not support the audio element.
                  </audio>
                  {result.audio_files.length > 1 && (
                    <div className="mt-2 text-sm text-gray-400">
                      {result.audio_files.length} audio files generated
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Script Display */}
            <div className="bg-secondary-light p-4 rounded">
              <div className="mb-2 flex items-center justify-between">
                <h4 className="font-semibold">View Complete Script</h4>
                <span className="text-gray-400">👁️👁️</span>
              </div>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {scriptArray.map((item: any, index: number) => {
                  const speaker = Object.keys(item)[0];
                  const dialogue = item[speaker];
                  const isSpeaker1 = speaker === 'Speaker 1';
                  
                  return (
                    <div
                      key={index}
                      className={`p-4 rounded-lg ${
                        isSpeaker1
                          ? 'bg-speaker1/30 border border-speaker1/60'
                          : 'bg-speaker2/30 border border-speaker2/60'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">
                          {isSpeaker1 ? '😊' : '😊'}
                        </span>
                        <div className="flex-1">
                          <div className="font-semibold mb-1 text-sm text-gray-300">
                            {speaker}
                          </div>
                          <div className="text-gray-100 leading-relaxed">
                            {dialogue}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}

