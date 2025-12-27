'use client';

import React, { useState, useEffect } from 'react';
import { Sparkles, Zap, FileText, Code, Github, BookOpen, Upload, Download, Menu, X, ArrowRight, GitBranch, Clock } from 'lucide-react';
import Navbar from './Navbar';

export default function Git2Docs() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  
  const steps = [
    { title: 'Connect Repository', desc: 'Paste your GitHub repo URL or connect via OAuth for private repos.', icon: <Github />, color: 'bg-blue-400' },
    { title: 'AI Analyzes Code', desc: 'Smart parsing of your codebase structure, functions, and relationships automatically.', icon: <Code />, color: 'bg-slate-400' },
    { title: 'Generate Docs', desc: 'Beautiful documentation with syntax highlighting, smart formatting, and AI-powered descriptions.', icon: <BookOpen />, color: 'bg-blue-600' },
  ];

  const leftFeatures = [
    {
      icon: <Zap className="w-10 h-10" />,
      title: 'Lightning Fast',
      desc: 'Generate comprehensive documentation from your GitHub repos in seconds, not hours. No manual work required.',
      color: 'from-blue-100 to-blue-200',
      borderColor: '#3B82F6'
    },
    {
      icon: <Code className="w-10 h-10" />,
      title: 'Code-Aware Analysis',
      desc: 'Understands your codebase structure, dependencies, and relationships. Detects patterns and conventions automatically.',
      color: 'from-slate-100 to-slate-200',
      borderColor: '#64748B'
    }
  ];

  const rightFeatures = [
    {
      icon: <GitBranch className="w-10 h-10" />,
      title: 'Branch Support',
      desc: 'Generate docs from any branch. Keep documentation in sync with your code across all branches effortlessly.',
      color: 'from-blue-200 to-blue-300',
      borderColor: '#2563EB'
    },
    {
      icon: <Clock className="w-10 h-10" />,
      title: 'Auto Updates',
      desc: 'Set up webhooks to auto-regenerate docs when you push changes. Always up-to-date documentation.',
      color: 'from-slate-200 to-slate-300',
      borderColor: '#475569'
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
                <button className="px-8 py-4 bg-blue-600 text-white rounded-full font-semibold hover:bg-blue-700 transition-all flex items-center gap-2 text-xl shadow-lg">
                  <Zap className="w-5 h-5" />
                  Start for Free
                </button>
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

      {/* Mission & Vision Section */}
      <section id="mission" className="py-20 px-6 relative z-0 bg-slate-50">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundImage: `
              linear-gradient(rgba(100, 100, 120, 0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(100, 100, 120, 0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
          }}
        ></div>

        <div className="relative max-w-5xl mx-auto grid md:grid-cols-2 gap-12 z-10">
          <div
            className="relative bg-white rounded-3xl p-8 overflow-hidden shadow-lg"
            style={{
              borderTop: '3px solid #1E293B',
              borderLeft: '3px solid #1E293B',
              borderRight: '10px solid #3B82F6',
              borderBottom: '10px solid #64748B',
            }}
          >
            <h2 className="text-4xl font-bold mb-4 text-gray-900 text-center">Our Mission</h2>
            <p className="text-gray-700 leading-relaxed text-center">
              At Git2Docs, we believe documentation should be effortless. Our mission is to empower developers worldwide by automating the documentation process, allowing them to focus on building great software instead of writing docs.
            </p>
          </div>

          <div
            className="relative bg-white rounded-3xl p-8 overflow-hidden shadow-lg"
            style={{
              borderTop: '3px solid #1E293B',
              borderLeft: '3px solid #1E293B',
              borderRight: '10px solid #3B82F6',
              borderBottom: '10px solid #64748B',
            }}
          >
            <h2 className="text-4xl font-bold mb-4 text-gray-900 text-center">Our Vision</h2>
            <p className="text-gray-700 leading-relaxed text-center">
              Git2Docs sets the standard for AI-powered documentation generation. We envision a future where every codebase has beautiful, up-to-date documentation that helps teams collaborate better and ship faster.
            </p>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 relative bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold mb-4 text-gray-900">Key Features</h2>
            <p className="text-xl text-gray-600">Everything you need to document your code effortlessly</p>
          </div>

          <div className="relative max-w-5xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {[...leftFeatures, ...rightFeatures].map((feature, i) => (
                <div
                  key={i}
                  className="bg-white p-6 rounded-2xl border-4 transition-all hover:-translate-y-1 hover:shadow-xl min-h-[300px] flex flex-col justify-between"
                  style={{ borderColor: feature.borderColor }}
                >
                  <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-xl flex items-center justify-center text-gray-900 mb-4`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold mb-3 text-gray-900">{feature.title}</h3>
                  <p className="text-gray-700 leading-relaxed text-sm">{feature.desc}</p>
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

      {/* CTA Section */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-blue-600 to-cyan-500 rounded-3xl p-12 shadow-2xl">
            <h2 className="text-4xl font-bold text-white mb-4">
              Ready to Transform Your Documentation?
            </h2>
            <p className="text-xl text-blue-50 mb-8">
              Join thousands of developers who have simplified their documentation workflow.
            </p>
            <button className="px-8 py-4 bg-white text-blue-600 rounded-full font-semibold hover:bg-blue-50 transition-all flex items-center gap-2 text-xl mx-auto shadow-lg">
              <Zap className="w-5 h-5" />
              Try Git2Docs Now
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gradient-to-br from-slate-800 to-slate-900 py-12 px-6 text-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <FileText className="w-6 h-6 text-blue-400" />
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