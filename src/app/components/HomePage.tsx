'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Zap, FileText, Code, Github, BookOpen, Upload, Download, Menu, X, ArrowRight, GitBranch, Clock } from 'lucide-react';
import Navbar from './Navbar';
import Image from 'next/image';
import Link from 'next/link';
export default function Git2Docs() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  
  const steps = [
    { title: 'Connect Repository', desc: 'Paste your GitHub repo URL or connect via OAuth for private repos.', icon: <Github />, color: 'bg-blue-400' },
    { title: 'AI Analyzes Code', desc: 'Smart parsing of your codebase structure, functions, and relationships automatically.', icon: <Code />, color: 'bg-slate-400' },
    { title: 'Generate Docs', desc: 'Beautiful documentation with syntax highlighting, smart formatting, and AI-powered descriptions.', icon: <BookOpen />, color: 'bg-blue-600' },
  ];

  const features = [
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Lightning Fast',
      desc: 'Generate comprehensive documentation from your GitHub repos in seconds, not hours. No manual work required.',
      side: 'left'
    },
    {
      icon: <Code className="w-8 h-8" />,
      title: 'Code-Aware Analysis',
      desc: 'Understands your codebase structure, dependencies, and relationships. Detects patterns and conventions automatically.',
      side: 'right'
    },
    {
      icon: <GitBranch className="w-8 h-8" />,
      title: 'Branch Support',
      desc: 'Generate docs from any branch. Keep documentation in sync with your code across all branches effortlessly.',
      side: 'left'
    },
    {
      icon: <Clock className="w-8 h-8" />,
      title: 'Auto Updates',
      desc: 'Set up webhooks to auto-regenerate docs when you push changes. Always up-to-date documentation.',
      side: 'right'
    },
    {
      icon: <BookOpen className="w-8 h-8" />,
      title: 'Beautiful Output',
      desc: 'Clean, readable documentation with syntax highlighting and smart formatting that developers love.',
      side: 'left'
    },
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: 'AI-Powered',
      desc: 'Leverages AI to create meaningful descriptions and explanations that make sense.',
      side: 'right'
    }
  ];

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      
      {/* Hero Section */}
      <section id="about" className="pt-32 pb-20 px-6 relative z-0">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-6xl md:text-6xl font-bold mb-6 text-blue-600 leading-tight">
                Transform GitHub Repos Into Beautiful Docs
              </h1>
              <p className="text-xl text-gray-700 mb-8 leading-relaxed">
                Git2Docs automatically generates clean, comprehensive documentation from your codebase. Save hours of manual work and keep your docs always up-to-date.
              </p>
              <div className="flex gap-4">
                <Link href='/git-to-docs'>
                <button className="px-8 py-4 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-all flex items-center gap-2 text-xl shadow-lg">
                  Start for Free
                </button></Link>
                <button className="px-8 py-4 border-2 border-blue-600 text-blue-600 rounded-full font-semibold hover:bg-blue-50 transition-all flex items-center gap-2 text-xl">
                  <Github className="w-5 h-5" />
                  View on GitHub
                </button>
              </div>
            </div>

            <div className="relative">
              <div className="rounded-2xl overflow-hidden">
                <img
                  src="/2885174.jpg"
                  alt="Hero"
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

     

   
      <section id="features" className="py-16 px-6 relative bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-20">
            <h2 className="text-5xl font-bold mb-4 text-gray-900">Powerful Features</h2>
            <p className="text-xl text-gray-600">Everything you need to document your code effortlessly</p>
          </div>

          <div className="relative">
            {/* Central Timeline Line */}
            <div className="absolute left-1/2 transform -translate-x-1/2 h-full w-1 bg-gradient-to-b from-blue-200 via-blue-400 to-blue-200 hidden md:block"></div>

            {/* Features */}
            <div className="space-y-16">
              {features.map((feature, i) => (
                <div key={i} className={`relative flex items-center ${feature.side === 'left' ? 'md:flex-row' : 'md:flex-row-reverse'} flex-col`}>
                  {/* Content */}
                  <div className={`md:w-5/12 ${feature.side === 'left' ? 'md:text-right md:pr-12' : 'md:text-left md:pl-12'} text-center mb-8 md:mb-0`}>
                    <div className="group">
                      <div className={`inline-flex items-center gap-4 ${feature.side === 'left' ? 'md:flex-row-reverse' : 'md:flex-row'} flex-col mb-4`}>
                        <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center text-white shadow-lg group-hover:scale-110 transition-transform duration-300">
                          {feature.icon}
                        </div>
                        <h3 className="text-2xl font-bold text-gray-900">{feature.title}</h3>
                      </div>
                      <p className="text-gray-600 text-lg leading-relaxed">{feature.desc}</p>
                    </div>
                  </div>

                  {/* Center Dot */}
                  <div className="absolute left-1/2 transform -translate-x-1/2 hidden md:block">
                    <div className="w-6 h-6 bg-blue-600 rounded-full border-4 border-white shadow-lg animate-pulse"></div>
                  </div>

                  {/* Spacer */}
                  <div className="md:w-5/12"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 bg-gradient-to-br from-blue-50 to-slate-50 overflow-x-auto">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-5xl font-bold mb-4 text-gray-900">How It Works</h2>
          <p className="text-xl text-gray-600 mb-16">Three simple steps to beautiful documentation</p>

          <div className="flex items-center gap-4 justify-center min-w-max px-6">
            <div className="flex flex-col items-center">
              <div className="px-8 py-3 rounded-full border-4 border-blue-600 bg-white flex items-center justify-center shadow-sm font-semibold text-gray-900">
                Start
              </div>
            </div>

            {steps.map((step, i) => (
              <React.Fragment key={i}>
                <ArrowRight className="w-8 h-8 text-gray-400" />

                <div className="flex flex-col items-center max-w-[220px] text-center">
                  <div className="flex flex-col items-center mb-1">
                    {React.cloneElement(step.icon, { className: "w-5 h-5 text-blue-600 mb-1" })}
                    <h3 className="font-bold text-gray-900 text-md">{step.title}</h3>
                  </div>
                  <p className="text-gray-700 text-sm">{step.desc}</p>
                </div>
              </React.Fragment>
            ))}

            <ArrowRight className="w-8 h-8 text-gray-400" />

            <div className="flex flex-col items-center">
              <div className="px-8 py-3 rounded-full border-4 border-slate-700 bg-white flex items-center justify-center shadow-sm font-semibold text-gray-900">
                Done
              </div>
            </div>
          </div>
        </div>
      </section>

      
      {/* Footer */}
      <footer className="bg-gradient-to-br from-slate-800 to-slate-900 py-12 px-6 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="flex h-9 w-9 items-center justify-center">
                              <Image 
                                src="/favicon.svg" 
                                alt="Git2Docs Logo" 
                                width={36} 
                                height={36}
                                className="transition-transform duration-300 group-hover:scale-110"
                              />
                            </div>
                <span className="text-2xl font-bold">Git2Docs</span>
              </div>
              <p className="text-slate-300">AI-powered documentation generation for modern developers</p>
            </div>
            <div>
              <h4 className="font-bold mb-3">Product</h4>
              <div className="space-y-2 text-slate-300">
                <div className="hover:text-blue-400 cursor-pointer transition-colors">Features</div>
                <div className="hover:text-blue-400 cursor-pointer transition-colors">Pricing</div>
                <div className="hover:text-blue-400 cursor-pointer transition-colors">API</div>
              </div>
            </div>
            <div>
              <h4 className="font-bold mb-3">Resources</h4>
              <div className="space-y-2 text-slate-300">
                <div className="hover:text-blue-400 cursor-pointer transition-colors">Documentation</div>
                <div className="hover:text-blue-400 cursor-pointer transition-colors">Tutorials</div>
                <div className="hover:text-blue-400 cursor-pointer transition-colors">Blog</div>
              </div>
            </div>
            <div>
              <h4 className="font-bold mb-3">Company</h4>
              <div className="space-y-2 text-slate-300">
                <div className="hover:text-blue-400 cursor-pointer transition-colors">About</div>
                <div className="hover:text-blue-400 cursor-pointer transition-colors">Contact</div>
                <div className="hover:text-blue-400 cursor-pointer transition-colors">GitHub</div>
              </div>
            </div>
          </div>
          <div className="border-t border-slate-700 pt-8 text-center text-slate-400">
            <p>© 2024 Git2Docs. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}