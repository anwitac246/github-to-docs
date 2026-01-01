"use client";

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Upload, Github, FileArchive, Sparkles, AlertCircle, FileText, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';

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
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setIsVisible(true);
  }, []);

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

    try {
      if (githubUrl) {
        // Analyze GitHub repository
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
        
        // Start polling for progress
        pollAnalysisStatus(data.analysis_id);
      } else if (zipFile) {
        // Handle file upload (placeholder)
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
        // Get the results
        const resultsResponse = await fetch(`http://localhost:8000/api/analysis/results/${id}`);
        const resultsData = await resultsResponse.json();
        setResults(resultsData);
        setIsGenerating(false);
      } else if (data.status === 'failed') {
        setSubmitError(data.error || 'Analysis failed');
        setIsGenerating(false);
      } else {
        // Continue polling
        setTimeout(() => pollAnalysisStatus(id), 2000);
      }
    } catch (error) {
      console.error('Error polling status:', error);
      setSubmitError('Failed to get analysis status');
      setIsGenerating(false);
    }
  };

  const isButtonDisabled = !zipFile && (!githubUrl || !githubRegex.test(githubUrl));

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar Placeholder */}
      <Navbar /> 
      <div className="h-16" />

      {/* Subtle Background Pattern */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-50 via-white to-white" />
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23000000%22%20fill-opacity%3D%220.02%22%3E%3Cpath%20d%3D%22M36%2034v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6%2034v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6%204V0H4v4H0v2h4v4h2V6h4V4H6z%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')] opacity-50" />
      </div>

      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-12 lg:py-20">
        {/* Hero Section */}
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

        {/* Main Content Grid */}
        <div 
          className={`grid lg:grid-cols-5 gap-8 lg:gap-12 transition-all duration-1000 delay-300 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          {/* Upload Panel - Left Side */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-3xl border border-gray-200 p-8 lg:p-10 shadow-xl shadow-gray-100/50">
              <h2 className="text-2xl font-semibold text-[#0A0A0A] mb-8">Upload Source</h2>
              
              {/* Drag & Drop Zone */}
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

              {/* Divider */}
              <div className="relative my-8">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-200" />
                </div>
                <div className="relative flex justify-center">
                  <span className="bg-white px-4 text-sm text-gray-500">or</span>
                </div>
              </div>

              {/* GitHub URL Input */}
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

              {/* Error Message */}
              {submitError && (
                <div className="flex items-center gap-2 mt-6 p-4 bg-red-50 rounded-xl text-red-600 text-sm">
                  <AlertCircle className="w-5 h-5 flex-shrink-0" />
                  <span>{submitError}</span>
                </div>
              )}

              {/* Generate Button */}
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

          {/* Documentation Preview Panel - Right Side */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-3xl border border-gray-200 p-8 lg:p-10 shadow-xl shadow-gray-100/50 h-full min-h-[500px] flex flex-col">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-gray-500" />
                </div>
                <h2 className="text-2xl font-semibold text-[#0A0A0A]">Documentation Preview</h2>
              </div>
              
              <div className="flex-1 rounded-2xl bg-gray-50 border border-gray-100 p-6 overflow-auto">
                {results ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm font-medium text-green-600">Analysis Complete</span>
                    </div>
                    
                    <div className="bg-white rounded-xl p-4 border border-gray-200">
                      <h3 className="font-semibold text-gray-900 mb-2">Project Summary</h3>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-500">Files:</span>
                          <span className="ml-2 font-medium">{results.summary?.total_files || 0}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">APIs:</span>
                          <span className="ml-2 font-medium">{results.summary?.total_apis || 0}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Functions:</span>
                          <span className="ml-2 font-medium">{results.summary?.total_functions || 0}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Languages:</span>
                          <span className="ml-2 font-medium">{results.summary?.languages?.join(', ') || 'N/A'}</span>
                        </div>
                      </div>
                    </div>
                    
                    {results.output_directory && (
                      <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
                        <h3 className="font-semibold text-blue-900 mb-2">Documentation Generated</h3>
                        <p className="text-sm text-blue-700">
                          Documentation files created in: <code className="bg-blue-100 px-2 py-1 rounded">{results.output_directory}</code>
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {['README.md', 'API_DOCUMENTATION.md', 'CODE_OF_CONDUCT.md'].map((file) => (
                            <span key={file} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                              {file}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : isGenerating ? (
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

        {/* Bottom Decorative Element */}
        <div 
          className={`mt-20 text-center transition-all duration-1000 delay-500 ${
            isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
          }`}
        >
          
        </div>
      </div>
    </div>
  );
};

export default GitToDocsPage;
