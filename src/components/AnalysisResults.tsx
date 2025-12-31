"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { 
  FileText, 
  Code, 
  Server, 
  Clock, 
  GitBranch, 
  Download,
  ExternalLink,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';

interface AnalysisResult {
  analysis_id: string;
  repository_url: string;
  repository_info: {
    name: string;
    owner: string;
    description: string;
  };
  analysis_time: number;
  summary: {
    total_files: number;
    backend_files: number;
    total_apis: number;
    total_functions: number;
    languages: string[];
  };
  all_files: any[];
  backend_files: any[];
  llm_analysis: Record<string, any>;
  documentation: {
    output_directory: string;
    generated_files: string[];
    timestamp: number;
  };
  created_at: string;
}

interface AnalysisResultsProps {
  results: AnalysisResult;
  onDownload?: (directory: string) => void;
}

export function AnalysisResults({ results, onDownload }: AnalysisResultsProps) {
  const { repository_info, summary, documentation, llm_analysis } = results;

  const handleDownload = () => {
    if (onDownload) {
      onDownload(documentation.output_directory);
    }
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                {repository_info.name}
              </CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {repository_info.description}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-green-600">
                <CheckCircle className="h-3 w-3 mr-1" />
                Completed
              </Badge>
              <Button onClick={handleDownload} size="sm">
                <Download className="h-4 w-4 mr-2" />
                Download Docs
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">{summary.total_files}</p>
                <p className="text-xs text-muted-foreground">Total Files</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-green-500" />
              <div>
                <p className="text-2xl font-bold">{summary.backend_files}</p>
                <p className="text-xs text-muted-foreground">Backend Files</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Code className="h-4 w-4 text-purple-500" />
              <div>
                <p className="text-2xl font-bold">{summary.total_apis}</p>
                <p className="text-xs text-muted-foreground">API Endpoints</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-orange-500" />
              <div>
                <p className="text-2xl font-bold">{formatDuration(results.analysis_time)}</p>
                <p className="text-xs text-muted-foreground">Analysis Time</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Languages */}
      <Card>
        <CardHeader>
          <CardTitle>Programming Languages</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {summary.languages.map((language) => (
              <Badge key={language} variant="secondary">
                {language}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Detailed Results */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="backend">Backend Files</TabsTrigger>
          <TabsTrigger value="ai-insights">AI Insights</TabsTrigger>
          <TabsTrigger value="documentation">Documentation</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Repository Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium">Repository URL</p>
                  <a 
                    href={results.repository_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline flex items-center gap-1"
                  >
                    {results.repository_url}
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
                <div>
                  <p className="text-sm font-medium">Owner</p>
                  <p className="text-sm text-muted-foreground">{repository_info.owner}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Total Functions</p>
                  <p className="text-sm text-muted-foreground">{summary.total_functions}</p>
                </div>
                <div>
                  <p className="text-sm font-medium">Analysis Date</p>
                  <p className="text-sm text-muted-foreground">
                    {new Date(results.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="backend" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Backend Files ({summary.backend_files})</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {results.backend_files.slice(0, 10).map((file, index) => (
                  <div key={index} className="border rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-sm">{file.file_path}</p>
                        <p className="text-xs text-muted-foreground">{file.file_purpose}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge variant="outline" size="sm">
                          {file.language}
                        </Badge>
                        {file.api_count > 0 && (
                          <Badge variant="secondary" size="sm">
                            {file.api_count} APIs
                          </Badge>
                        )}
                        {file.function_count > 0 && (
                          <Badge variant="secondary" size="sm">
                            {file.function_count} Functions
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {results.backend_files.length > 10 && (
                  <p className="text-sm text-muted-foreground text-center">
                    ... and {results.backend_files.length - 10} more files
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai-insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Generated Insights</CardTitle>
            </CardHeader>
            <CardContent>
              {Object.keys(llm_analysis).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(llm_analysis).map(([filePath, analysis]: [string, any]) => (
                    <div key={filePath} className="border rounded-lg p-4">
                      <h4 className="font-medium mb-2">{filePath}</h4>
                      <p className="text-sm text-muted-foreground mb-2">
                        {analysis.description}
                      </p>
                      <div className="flex gap-2">
                        <Badge variant="outline" size="sm">
                          {analysis.file_purpose}
                        </Badge>
                        {analysis.api_count > 0 && (
                          <Badge variant="secondary" size="sm">
                            {analysis.api_count} APIs
                          </Badge>
                        )}
                        {analysis.function_count > 0 && (
                          <Badge variant="secondary" size="sm">
                            {analysis.function_count} Functions
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground">No AI insights available</p>
                  <p className="text-sm text-muted-foreground">
                    AI analysis may have been skipped due to rate limiting or configuration.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="documentation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Generated Documentation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">Output Directory</p>
                  <code className="text-sm bg-muted px-2 py-1 rounded">
                    {documentation.output_directory}
                  </code>
                </div>
                
                <div>
                  <p className="text-sm font-medium mb-2">Generated Files</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {documentation.generated_files.map((file, index) => (
                      <div key={index} className="flex items-center gap-2 p-2 border rounded">
                        <FileText className="h-4 w-4 text-blue-500" />
                        <span className="text-sm">{file}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button onClick={handleDownload}>
                    <Download className="h-4 w-4 mr-2" />
                    Download All Documentation
                  </Button>
                  <Button variant="outline" asChild>
                    <a href={`/results/${documentation.output_directory}`} target="_blank">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Online
                    </a>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface AnalysisProgressProps {
  status: string;
  progress: number;
  message: string;
}

export function AnalysisProgress({ status, progress, message }: AnalysisProgressProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            {status === 'processing' ? (
              <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
            ) : status === 'completed' ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : status === 'failed' ? (
              <AlertCircle className="h-5 w-5 text-red-500" />
            ) : (
              <Clock className="h-5 w-5 text-gray-500" />
            )}
            <h3 className="font-medium">
              {status === 'pending' && 'Analysis Queued'}
              {status === 'processing' && 'Analyzing Repository'}
              {status === 'completed' && 'Analysis Complete'}
              {status === 'failed' && 'Analysis Failed'}
            </h3>
          </div>
          
          <Progress value={progress} className="w-full" />
          
          <p className="text-sm text-muted-foreground">{message}</p>
        </div>
      </CardContent>
    </Card>
  );
}