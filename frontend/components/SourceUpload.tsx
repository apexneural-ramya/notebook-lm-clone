'use client';

import { useState } from 'react';
import { useStore } from '@/lib/store';
import { documentAPI } from '@/lib/api-client';
import { Upload, Globe, Youtube, FileText, Loader2 } from 'lucide-react';

export default function SourceUpload() {
  const { addSource, setLoading, isLoading } = useStore();
  const [activeMethod, setActiveMethod] = useState<'files' | 'urls' | 'youtube' | 'text'>('files');
  const [urls, setUrls] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [textContent, setTextContent] = useState('');
  const [textTitle, setTextTitle] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await documentAPI.uploadFiles(Array.from(files));
      if (response.status && response.data) {
        response.data.sources.forEach((source: any) => addSource(source));
        setSuccess(`Processed ${response.data.sources.length} file(s) successfully`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload files');
    } finally {
      setLoading(false);
    }
  };

  const handleUrls = async () => {
    if (!urls.trim()) return;

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const urlList = urls.split('\n').filter(u => u.trim());
      const response = await documentAPI.processURLs(urlList);
      if (response.status && response.data) {
        response.data.sources.forEach((source: any) => addSource(source));
        setSuccess(`Processed ${response.data.sources.length} URL(s) successfully`);
        setUrls('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process URLs');
    } finally {
      setLoading(false);
    }
  };

  const handleYouTube = async () => {
    if (!youtubeUrl.trim()) return;

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await documentAPI.processYouTube(youtubeUrl.trim());
      if (response.status && response.data) {
        addSource(response.data.source);
        setSuccess('YouTube video processed successfully');
        setYoutubeUrl('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process YouTube video');
    } finally {
      setLoading(false);
    }
  };

  const handleText = async () => {
    if (!textContent.trim()) return;

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const response = await documentAPI.processText(textContent, textTitle || undefined);
      if (response.status && response.data) {
        addSource(response.data.source);
        setSuccess('Text processed successfully');
        setTextContent('');
        setTextTitle('');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process text');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">📁 Add sources</h2>
        <p className="text-gray-400">
          Sources let NotebookLM base its responses on the information that matters most to you.
          (Examples: marketing plans, course reading, research notes, meeting transcripts, sales documents, etc.)
        </p>
      </div>

      {error && (
        <div className="bg-primary/20 border border-primary/50 text-primary px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-accent/20 border border-accent/50 text-accent px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {/* Method Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-700">
        <button
          onClick={() => setActiveMethod('files')}
          className={`px-4 py-2 flex items-center gap-2 transition-colors ${
            activeMethod === 'files'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-400 hover:text-foreground'
          }`}
        >
          <Upload size={18} />
          Upload Files
        </button>
        <button
          onClick={() => setActiveMethod('urls')}
          className={`px-4 py-2 flex items-center gap-2 transition-colors ${
            activeMethod === 'urls'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-400 hover:text-foreground'
          }`}
        >
          <Globe size={18} />
          Website URLs
        </button>
        <button
          onClick={() => setActiveMethod('youtube')}
          className={`px-4 py-2 flex items-center gap-2 transition-colors ${
            activeMethod === 'youtube'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-400 hover:text-foreground'
          }`}
        >
          <Youtube size={18} />
          YouTube
        </button>
        <button
          onClick={() => setActiveMethod('text')}
          className={`px-4 py-2 flex items-center gap-2 transition-colors ${
            activeMethod === 'text'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-400 hover:text-foreground'
          }`}
        >
          <FileText size={18} />
          Paste Text
        </button>
      </div>

      {/* Content */}
      <div className="bg-secondary rounded-lg p-6">
        {activeMethod === 'files' && (
          <div>
            <h3 className="font-semibold mb-4">Upload sources</h3>
            {isLoading ? (
              <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center">
                <Loader2 size={32} className="mx-auto mb-2 text-primary animate-spin" />
                <p className="text-gray-400">Processing files...</p>
                <p className="text-sm text-gray-500 mt-2">Please wait while we process your files</p>
              </div>
            ) : (
              <label className="block">
                <div className="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors">
                  <Upload size={32} className="mx-auto mb-2 text-gray-400" />
                  <p className="text-gray-400">Drag & drop or choose file to upload</p>
                  <p className="text-sm text-gray-500 mt-2">
                    Supported: PDF, .txt, Markdown, Audio (mp3, wav, m4a, ogg)
                  </p>
                </div>
                <input
                  type="file"
                  multiple
                  accept=".pdf,.txt,.md,.mp3,.wav,.m4a,.ogg"
                  onChange={handleFileUpload}
                  className="hidden"
                  disabled={isLoading}
                />
              </label>
            )}
          </div>
        )}

        {activeMethod === 'urls' && (
          <div>
            <h3 className="font-semibold mb-4">Website URLs</h3>
            {isLoading && (
              <div className="mb-4 flex items-center gap-2 text-gray-400">
                <Loader2 size={20} className="animate-spin" />
                <span>Processing URLs...</span>
              </div>
            )}
            <textarea
              value={urls}
              onChange={(e) => setUrls(e.target.value)}
              placeholder="https://example.com&#10;https://another-site.com"
              className="w-full h-32 px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary mb-4"
              disabled={isLoading}
            />
            <p className="text-sm text-gray-400 mb-4">
              To add multiple URLs, separate with a space or new line. Only the visible text on the website will be imported.
            </p>
            <button
              onClick={handleUrls}
              disabled={!urls.trim() || isLoading}
              className="px-6 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Processing...
                </>
              ) : (
                'Process URLs'
              )}
            </button>
          </div>
        )}

        {activeMethod === 'youtube' && (
          <div>
            <h3 className="font-semibold mb-4">YouTube Videos</h3>
            {isLoading && (
              <div className="mb-4 flex items-center gap-2 text-gray-400">
                <Loader2 size={20} className="animate-spin" />
                <span>Processing YouTube video...</span>
              </div>
            )}
            <input
              type="text"
              value={youtubeUrl}
              onChange={(e) => setYoutubeUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary mb-4"
              disabled={isLoading}
            />
            <p className="text-sm text-gray-400 mb-4">
              Paste a YouTube video URL to extract and transcribe its audio content
            </p>
            <button
              onClick={handleYouTube}
              disabled={!youtubeUrl.trim() || isLoading}
              className="px-6 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Processing...
                </>
              ) : (
                'Process YouTube Video'
              )}
            </button>
          </div>
        )}

        {activeMethod === 'text' && (
          <div>
            <h3 className="font-semibold mb-4">Paste copied text</h3>
            {isLoading && (
              <div className="mb-4 flex items-center gap-2 text-gray-400">
                <Loader2 size={20} className="animate-spin" />
                <span>Processing text...</span>
              </div>
            )}
            <input
              type="text"
              value={textTitle}
              onChange={(e) => setTextTitle(e.target.value)}
              placeholder="Title (optional)"
              className="w-full px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary mb-4"
              disabled={isLoading}
            />
            <textarea
              value={textContent}
              onChange={(e) => setTextContent(e.target.value)}
              placeholder="Paste your text here..."
              className="w-full h-48 px-4 py-2 bg-secondary-light border border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary mb-4"
              disabled={isLoading}
            />
            <button
              onClick={handleText}
              disabled={!textContent.trim() || isLoading}
              className="px-6 py-2 bg-primary hover:bg-primary-hover rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Processing...
                </>
              ) : (
                'Process Text'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

