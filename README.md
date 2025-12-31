# GitHub Documentation Generator

A comprehensive tool that transforms GitHub repositories into professional documentation using AI-powered analysis.

## 🚀 Features

- **AI-Powered Analysis**: Advanced code analysis using Groq LLM
- **Comprehensive Documentation**: Generates README, API docs, setup guides, and more
- **Real-time Progress**: Live updates during analysis
- **Rate Limiting**: Intelligent API key rotation to avoid limits
- **Beautiful UI**: Modern, responsive interface built with Next.js
- **Multiple Input Methods**: GitHub URL or ZIP file upload

## 📁 Project Structure

```
github-to-docs/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── core/              # Core analysis engine
│   │   │   ├── analyzer.py    # Main GitHub analyzer
│   │   │   ├── extractor.py   # Code extraction utilities
│   │   │   ├── llm_processor.py # LLM processing with rate limiting
│   │   │   └── doc_generator.py # Documentation generation
│   │   ├── services/          # Business logic services
│   │   │   └── analysis_service.py # Analysis orchestration
│   │   ├── routes/            # API endpoints
│   │   │   └── analysis.py    # Analysis API routes
│   │   ├── models.py          # Data models
│   │   └── config.py          # Configuration management
│   ├── main.py               # FastAPI application
│   ├── start_server.py       # Server startup script
│   └── requirements.txt      # Python dependencies
├── src/                      # Next.js frontend
│   ├── app/
│   │   └── git-to-docs/      # Main application page
│   └── components/
│       └── AnalysisResults.tsx # Results display component
├── prototype/                # Original prototype (reference)
└── .env                     # Environment variables
```

## 🛠️ Setup Instructions

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEYS=your_groq_api_key_1,your_groq_api_key_2,your_groq_api_key_3
   ```

4. **Start the backend server:**
   ```bash
   python start_server.py
   ```
   
   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The frontend will be available at `http://localhost:3000`

## 🔧 Configuration

### Environment Variables

- `GROQ_API_KEYS`: Comma-separated list of Groq API keys for rate limiting

### Backend Configuration

The backend automatically:
- Creates `results/` directory for generated documentation
- Creates `temp/` directory for temporary files
- Loads configuration from `.env` file
- Initializes rate limiting with multiple API keys

## 📖 API Documentation

### Endpoints

- `POST /api/analysis/github` - Start GitHub repository analysis
- `GET /api/analysis/status/{id}` - Get analysis status and progress
- `GET /api/analysis/results/{id}` - Get complete analysis results
- `GET /api/analysis/list` - List all analyses
- `GET /health` - Health check endpoint

### Example Usage

```bash
# Start analysis
curl -X POST http://localhost:8000/api/analysis/github \
  -H "Content-Type: application/json" \
  -d '{"github_url": "https://github.com/user/repo"}'

# Check status
curl http://localhost:8000/api/analysis/status/{analysis_id}

# Get results
curl http://localhost:8000/api/analysis/results/{analysis_id}
```

## 🎯 How It Works

1. **Repository Cloning**: Clones the GitHub repository to a temporary directory
2. **File Analysis**: Scans and analyzes code files for:
   - Programming languages
   - Functions and methods
   - API endpoints
   - File purposes and dependencies
3. **AI Processing**: Uses Groq LLM to generate intelligent insights about important files
4. **Documentation Generation**: Creates comprehensive documentation including:
   - README.md with project overview
   - API_DOCUMENTATION.md with endpoint details
   - PROJECT_SUMMARY.md with technical analysis
   - SETUP_GUIDE.md with installation instructions
   - LLM_INSIGHTS.md with AI-generated insights

## 🔄 Rate Limiting Strategy

The system implements intelligent rate limiting to handle Groq API limits:

- **Conservative Limits**: 15 requests/minute per API key (well below 60 limit)
- **Multiple API Keys**: Rotates between available keys automatically
- **Batch Processing**: Processes only the most important files (max 5)
- **Error Handling**: Graceful degradation when limits are reached
- **Progress Tracking**: Real-time updates during processing

## 🎨 Frontend Features

- **Real-time Progress**: Live updates during analysis
- **Beautiful Results Display**: Comprehensive visualization of results
- **Tabbed Interface**: Organized view of different result categories
- **Download Support**: Easy access to generated documentation
- **Error Handling**: User-friendly error messages and recovery

## 🚀 Production Deployment

### Backend Deployment

1. Set up environment variables on your server
2. Install dependencies: `pip install -r requirements.txt`
3. Run with production ASGI server: `uvicorn main:app --host 0.0.0.0 --port 8000`

### Frontend Deployment

1. Build the application: `npm run build`
2. Deploy to your preferred platform (Vercel, Netlify, etc.)
3. Update API endpoints to point to your production backend

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

---

*Built with ❤️ using FastAPI, Next.js, and Groq AI*