"use client";

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Upload, Github, FileArchive, AlertCircle, FileText, ArrowRight, Download, File, Folder, ChevronRight, ChevronDown, X, Loader2 } from 'lucide-react';

const GitToDocsPage = () => {
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [githubUrl, setGithubUrl] = useState('');
  const [githubError, setGithubError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [activeMethod, setActiveMethod] = useState<'zip' | 'github' | null>(null);
  const [submitError, setSubmitError] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);
  const [progress, setProgress] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['root']));
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  useEffect(() => {
    if (selectedFile && results?.output_directory) {
      fetchFileContent(selectedFile);
    }
  }, [selectedFile, results]);

  const githubRegex = /^https?:\/\/(www\.)?github\.com\/[^\/]+\/[^\/]+\/?$/;

  const validateGithubUrl = (url: string) => {
    if (!url) {
      setGithubError('');
      return true;
    }
    if (!githubRegex.test(url)) {
      setGithubError('Please enter a valid GitHub repository URL');
      return false;
    }
    setGithubError('');
    return true;
  };

  const handleGithubUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const url = e.target.value;
    setGithubUrl(url);
    validateGithubUrl(url);
    if (url) {
      setActiveMethod('github');
      setZipFile(null);
    } else {
      setActiveMethod(zipFile ? 'zip' : null);
    }
    setSubmitError('');
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.zip')) {
        setZipFile(file);
        setActiveMethod('zip');
        setGithubUrl('');
        setGithubError('');
        setSubmitError('');
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.name.endsWith('.zip')) {
        setZipFile(file);
        setActiveMethod('zip');
        setGithubUrl('');
        setGithubError('');
        setSubmitError('');
      }
    }
  };

  const handleGenerate = async () => {
    if (!zipFile && !githubUrl) {
      setSubmitError('Please upload a ZIP file or enter a GitHub repository URL');
      return;
    }
    if (githubUrl && !githubRegex.test(githubUrl)) {
      setSubmitError('Please enter a valid GitHub repository URL');
      return;
    }

    setIsGenerating(true);
    setSubmitError('');
    setProgress(0);
    setResults(null);
    setSelectedFile(null);

    try {
      if (githubUrl) {
        const response = await fetch('http://localhost:8000/api/analysis/github', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            github_url: githubUrl,
            groq_api_keys: [] 
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        setAnalysisId(data.analysis_id);
        pollAnalysisStatus(data.analysis_id);
      } else if (zipFile) {
        setSubmitError('File upload analysis coming soon!');
        setIsGenerating(false);
      }
    } catch (error) {
      console.error('Error starting analysis:', error);
      setSubmitError('Failed to start analysis. Please try again.');
      setIsGenerating(false);
    }
  };

  const pollAnalysisStatus = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/analysis/status/${id}`);
      const data = await response.json();
      
      setProgress(data.progress || 0);
      
      if (data.status === 'completed') {
        const resultsResponse = await fetch(`http://localhost:8000/api/analysis/results/${id}`);
        const resultsData = await resultsResponse.json();
        setResults(resultsData);
        setIsGenerating(false);
        
        if (resultsData.output_directory) {
          setSelectedFile('README.md');
        }
      } else if (data.status === 'failed') {
        setSubmitError(data.error || 'Analysis failed');
        setIsGenerating(false);
      } else {
        setTimeout(() => pollAnalysisStatus(id), 2000);
      }
    } catch (error) {
      console.error('Error polling status:', error);
      setSubmitError('Failed to get analysis status');
      setIsGenerating(false);
    }
  };

  const fetchFileContent = async (fileName: string) => {
    if (!results?.output_directory) return;
    
    setIsLoadingContent(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/analysis/file/${results.output_directory}/${fileName}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch file content');
      }
      
      const data = await response.json();
      setFileContent(data.content || '');
    } catch (error) {
      console.error('Error fetching file:', error);
      setFileContent('# Error\n\nFailed to load file content.');
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleDownloadDocs = async () => {
    if (!results?.output_directory) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/analysis/download/${results.output_directory}`);
      if (!response.ok) throw new Error('Download failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${results.output_directory}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
      alert('Failed to download documentation');
    }
  };

  const toggleFolder = (folder: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folder)) {
      newExpanded.delete(folder);
    } else {
      newExpanded.add(folder);
    }
    setExpandedFolders(newExpanded);
  };

  const getDocumentationFiles = () => {
    if (!results) return [];
    
    return [
      { name: 'README.md', type: 'file', badge: 'Main' },
      { name: 'API_DOCUMENTATION.md', type: 'file', badge: 'API' },
      { name: 'CODE_OF_CONDUCT.md', type: 'file', badge: 'Community' },
      { name: 'PROJECT_SUMMARY.md', type: 'file', badge: 'Summary' },
      { name: 'SETUP.md', type: 'file', badge: 'Setup' },
      { name: 'ARCHITECTURE.md', type: 'file', badge: 'Architecture' },
      { name: 'DEPLOYMENT.md', type: 'file', badge: 'Deploy' },
      { name: 'TROUBLESHOOTING.md', type: 'file', badge: 'Help' },
      { name: 'files', type: 'folder', badge: null }
    ];
  };

  const renderMarkdown = (markdown: string) => {
    let html = markdown;

    html = html.replace(/^# (.*$)/gim, '<h1 class="text-4xl font-bold text-gray-900 mb-6 mt-8">$1</h1>');
    html = html.replace(/^## (.*$)/gim, '<h2 class="text-3xl font-bold text-gray-900 mb-4 mt-6">$1</h2>');
    html = html.replace(/^### (.*$)/gim, '<h3 class="text-2xl font-semibold text-gray-900 mb-3 mt-5">$1</h3>');
    html = html.replace(/^#### (.*$)/gim, '<h4 class="text-xl font-semibold text-gray-900 mb-2 mt-4">$1</h4>');
    html = html.replace(/^##### (.*$)/gim, '<h5 class="text-lg font-semibold text-gray-900 mb-2 mt-3">$1</h5>');

    html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>');
    html = html.replace(/\*(.+?)\*/g, '<em class="italic">$1</em>');
    html = html.replace(/__(.+?)__/g, '<strong class="font-semibold text-gray-900">$1</strong>');
    html = html.replace(/_(.+?)_/g, '<em class="italic">$1</em>');

    html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>');

    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre class="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto my-4"><code class="text-sm font-mono">${code.trim()}</code></pre>`;
    });

    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-blue-600 hover:text-blue-800 underline">$1</a>');

    html = html.replace(/^- (.+)$/gim, '<li class="ml-4">$1</li>');
    html = html.replace(/^(\d+)\. (.+)$/gim, '<li class="ml-4">$2</li>');
    html = html.replace(/(<li class="ml-4">.*<\/li>\n?)+/g, '<ul class="list-disc list-inside space-y-1 my-3 text-gray-700">$&</ul>');

    html = html.replace(/^> (.+)$/gim, '<blockquote class="border-l-4 border-blue-500 pl-4 italic text-gray-600 my-3">$1</blockquote>');

    html = html.replace(/^---$/gim, '<hr class="my-6 border-t border-gray-300">');

    html = html.replace(/\n\n/g, '</p><p class="text-gray-700 leading-relaxed mb-4">');
    html = '<p class="text-gray-700 leading-relaxed mb-4">' + html + '</p>';

    return html;
  };

  const renderFileTree = () => {
    const files = getDocumentationFiles();
    
    return (
      <div className="space-y-1">
        {files.map((item) => (
          <div key={item.name}>
            {item.type === 'folder' ? (
              <div>
                <button
                  onClick={() => toggleFolder(item.name)}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors text-left group"
                >
                  {expandedFolders.has(item.name) ? (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  )}
                  <Folder className="w-4 h-4 text-blue-500" />
                  <span className="text-sm font-medium text-gray-700">{item.name}</span>
                  <span className="ml-auto text-xs text-gray-400">Individual docs</span>
                </button>
                {expandedFolders.has(item.name) && (
                  <div className="ml-6 mt-1 space-y-1 border-l-2 border-gray-100 pl-2">
                    <div className="px-3 py-2 text-xs text-gray-400">
                      Per-file documentation
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setSelectedFile(item.name)}
                className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg transition-all ${
                  selectedFile === item.name
                    ? 'bg-blue-50 border-2 border-blue-200'
                    : 'hover:bg-gray-50 border-2 border-transparent'
                }`}
              >
                <File className="w-4 h-4 text-gray-500" />
                <div className="flex-1 text-left">
                  <div className="text-sm font-medium text-gray-700">{item.name}</div>
                </div>
                {item.badge && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                    {item.badge}
                  </span>
                )}
              </button>
            )}
          </div>
        ))}
      </div>
    );
  };

  const renderFileContent = () => {
    if (!selectedFile) {
      return (
        <div className="h-full flex flex-col items-center justify-center text-center p-8">
          <FileText className="w-16 h-16 text-gray-300 mb-4" />
          <p className="text-gray-500 text-lg mb-2">Select a file to preview</p>
          <p className="text-gray-400 text-sm">
            Choose from the documentation files on the left
          </p>
        </div>
      );
    }

    if (isLoadingContent) {
      return (
        <div className="h-full flex flex-col items-center justify-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mb-4" />
          <p className="text-gray-600">Loading {selectedFile}...</p>
        </div>
      );
    }

    return (
      <div className="h-full overflow-auto">
        <div className="bg-gradient-to-br from-blue-50 to-white p-6 border-b border-gray-200 sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500 flex items-center justify-center text-white">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">{selectedFile}</h2>
                <p className="text-xs text-gray-500">Auto-generated documentation</p>
              </div>
            </div>
            <button
              onClick={() => setSelectedFile(null)}
              className="p-2 hover:bg-white rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        <div className="p-8">
          <div 
            className="prose prose-blue max-w-none"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(fileContent) }}
          />
        </div>
      </div>
    );
  };

  const isButtonDisabled = !zipFile && (!githubUrl || !githubRegex.test(githubUrl));

  return (
    <div className="min-h-screen bg-white">
      <div className="h-16" />

      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50 via-white to-white" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23000000%22%20fill-opacity%3D%220.02%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')] opacity-50" />
      </div>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12 lg:py-20">
        <div 
          className={`text-center mb-16 lg:mb-24 transition-all duration-1000 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          <h1 className="text-5xl lg:text-7xl font-bold text-[#0A0A0A] tracking-tight mb-6">
            Git{' '}
            <span className="inline-flex items-center">
              <ArrowRight className="w-10 h-10 lg:w-14 lg:h-14 mx-2 text-blue-500" />
            </span>{' '}
            Docs Generator
          </h1>
          
          <p className="text-xl lg:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Upload your code or connect your GitHub repo to generate{' '}
            <span className="text-[#0A0A0A] font-medium">rich semantic documentation</span>.
          </p>
        </div>

        {!results ? (
          <div 
            className={`grid lg:grid-cols-5 gap-8 lg:gap-12 transition-all duration-1000 delay-300 ${
              isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
            }`}
          >
            <div className="lg:col-span-3">
              <div className="bg-white rounded-3xl border border-gray-200 p-8 lg:p-10 shadow-xl shadow-gray-100/50">
                <h2 className="text-2xl font-semibold text-[#0A0A0A] mb-8">Upload Source</h2>
                
                <div 
                  className={`relative mb-8 transition-all duration-300 ${
                    activeMethod === 'zip' ? 'ring-2 ring-blue-500 ring-offset-4' : ''
                  }`}
                >
                  <div
                    onClick={() => fileInputRef.current?.click()}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`
                      relative cursor-pointer rounded-2xl border-2 border-dashed p-12 lg:p-16
                      transition-all duration-300 ease-out
                      ${isDragging 
                        ? 'border-blue-500 bg-blue-50 shadow-[0_0_40px_rgba(37,99,235,0.15)]' 
                        : 'border-gray-300 bg-gray-50/50 hover:border-blue-400 hover:bg-blue-50/50'
                      }
                      ${zipFile ? 'border-blue-500 bg-blue-50' : ''}
                    `}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".zip"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    
                    <div className="flex flex-col items-center text-center">
                      <div className={`
                        w-16 h-16 rounded-2xl flex items-center justify-center mb-6
                        transition-all duration-300
                        ${zipFile 
                          ? 'bg-blue-500 text-white' 
                          : 'bg-gray-100 text-gray-400 group-hover:bg-blue-100 group-hover:text-blue-500'
                        }
                      `}>
                        {zipFile ? <FileArchive className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
                      </div>
                      
                      {zipFile ? (
                        <>
                          <p className="text-lg font-medium text-[#0A0A0A] mb-1">{zipFile.name}</p>
                          <p className="text-sm text-gray-500">
                            {(zipFile.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              setZipFile(null);
                              setActiveMethod(null);
                            }}
                            className="mt-4 text-sm text-blue-600 hover:text-blue-700 font-medium"
                          >
                            Remove file
                          </button>
                        </>
                      ) : (
                        <>
                          <p className="text-lg font-medium text-[#0A0A0A] mb-2">
                            Drag & Drop ZIP folder here
                          </p>
                          <p className="text-gray-500">
                            or <span className="text-blue-600 font-medium">click to upload</span>
                          </p>
                          <p className="text-sm text-gray-400 mt-3">Only .zip files accepted</p>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                <div className="relative my-8">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center">
                    <span className="bg-white px-4 text-sm text-gray-500">or</span>
                  </div>
                </div>

                <div className={`transition-all duration-300 ${
                  activeMethod === 'github' ? 'ring-2 ring-blue-500 ring-offset-4 rounded-2xl' : ''
                }`}>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    GitHub Repository URL
                  </label>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                      <Github className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      type="url"
                      value={githubUrl}
                      onChange={handleGithubUrlChange}
                      placeholder="https://github.com/username/repository"
                      className={`
                        w-full pl-12 pr-4 py-4 rounded-xl border-2 bg-gray-50/50
                        text-[#0A0A0A] placeholder:text-gray-400
                        transition-all duration-300
                        focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10
                        ${githubError 
                          ? 'border-red-300 bg-red-50/50' 
                          : 'border-gray-200 hover:border-gray-300'
                        }
                      `}
                    />
                  </div>
                  {githubError && (
                    <div className="flex items-center gap-2 mt-3 text-red-500 text-sm">
                      <AlertCircle className="w-4 h-4" />
                      <span>{githubError}</span>
                    </div>
                  )}
                </div>

                {submitError && (
                  <div className="flex items-center gap-2 mt-6 p-4 bg-red-50 rounded-xl text-red-600 text-sm">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <span>{submitError}</span>
                  </div>
                )}

                <button
                  onClick={handleGenerate}
                  disabled={isButtonDisabled || isGenerating}
                  className={`
                    w-full mt-8 py-4 px-8 rounded-xl text-lg font-semibold
                    transition-all duration-300 ease-out
                    ${isButtonDisabled || isGenerating
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-blue-500 text-white hover:from-blue-700 hover:to-blue-600 hover:shadow-xl hover:shadow-blue-500/25 hover:-translate-y-0.5 active:translate-y-0'
                    }
                  `}
                >
                  {isGenerating ? (
                    <div className="flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Analyzing... {progress}%
                    </div>
                  ) : (
                    'Generate Docs'
                  )}
                </button>
              </div>
            </div>

            <div className="lg:col-span-2">
              <div className="bg-white rounded-3xl border border-gray-200 p-8 lg:p-10 shadow-xl shadow-gray-100/50 h-full min-h-[500px] flex flex-col">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-gray-500" />
                  </div>
                  <h2 className="text-2xl font-semibold text-[#0A0A0A]">Documentation Preview</h2>
                </div>
                
                <div className="flex-1 rounded-2xl bg-gray-50 border border-gray-100 p-6 overflow-auto">
                  {isGenerating ? (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                      <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-500 rounded-full animate-spin mb-4" />
                      <p className="text-gray-600 text-lg mb-2">Analyzing Repository...</p>
                      <div className="w-full max-w-xs bg-gray-200 rounded-full h-2 mb-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <p className="text-sm text-gray-500">{progress}% complete</p>
                    </div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center">
                      <div className="w-20 h-20 rounded-2xl bg-gray-100 flex items-center justify-center mb-6">
                        <FileText className="w-10 h-10 text-gray-300" />
                      </div>
                      <p className="text-gray-400 text-lg max-w-xs">
                        Documentation will appear here after generation.
                      </p>
                      <div className="mt-8 flex flex-col gap-3 w-full max-w-xs">
                        <div className="h-3 bg-gray-200 rounded-full w-full animate-pulse" />
                        <div className="h-3 bg-gray-200 rounded-full w-4/5 animate-pulse" />
                        <div className="h-3 bg-gray-200 rounded-full w-3/5 animate-pulse" />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid lg:grid-cols-4 gap-6">
            <div className="lg:col-span-1">
              <div className="bg-white rounded-2xl border border-gray-200 shadow-lg sticky top-24">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">Documentation</h3>
                    <button
                      onClick={handleDownloadDocs}
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm font-medium"
                    >
                      <Download className="w-4 h-4" />
                      ZIP
                    </button>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-gray-500">
                    <FileArchive className="w-4 h-4" />
                    <span>{getDocumentationFiles().length} files</span>
                  </div>
                </div>
                
                <div className="p-4 max-h-[calc(100vh-300px)] overflow-y-auto">
                  {renderFileTree()}
                </div>
              </div>
            </div>

            <div className="lg:col-span-3">
              <div className="bg-white rounded-2xl border border-gray-200 shadow-lg h-[calc(100vh-200px)]">
                {renderFileContent()}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GitToDocsPage;