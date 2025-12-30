# Healthcare AI Agent - Complete Developer Documentation

> **A comprehensive healthcare platform with AI-powered diagnosis, telemedicine, and emergency services**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg)](https://javascript.info)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![Next.js](https://img.shields.io/badge/Next.js-13+-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)

## 🏥 Project Overview

Healthcare AI Agent is a full-stack healthcare platform that combines artificial intelligence with telemedicine to provide:

- **AI-Powered Diagnosis**: Intelligent symptom analysis and medical recommendations
- **Emergency Services**: Real-time ambulance booking and location services
- **Telemedicine**: Video consultations and appointment scheduling
- **Document Analysis**: Medical document processing and analysis
- **Wellness Programs**: Yoga and fitness tracking with pose detection

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend APIs  │    │   AI Services   │
│   (Next.js)     │◄──►│   (Flask)       │◄──►│   (Groq/ML)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Components │    │   Database      │    │   External APIs │
│   (React)       │    │   (Firebase)    │    │   (Maps/Email)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm/yarn
- **Firebase Account** for database
- **Groq API Key** for AI services
- **Google Maps API Key** for location services

### Installation

```bash
# Clone the repository
git clone https://github.com/anwitac246/healthcare-ai-agent.git
cd healthcare-ai-agent

# Backend setup
pip install -r requirements.txt

# Frontend setup
npm install

# Environment configuration
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start backend services (in separate terminals)
python ambulance.py      # Port 5001 - Emergency services
python chatbot.py        # Port 5002 - AI diagnosis
python document.py       # Port 5003 - Document analysis
python location.py       # Port 5004 - Location services
python yoga.py          # Port 5005 - Wellness tracking

# Start frontend
npm run dev             # Port 3000 - Main application
```

## 📚 Documentation Structure

| Document | Description | Audience |
|----------|-------------|----------|
| [**API Reference**](./API_REFERENCE.md) | Complete API documentation with examples | Developers |
| [**Setup Guide**](./SETUP_GUIDE.md) | Detailed installation and configuration | DevOps/Developers |
| [**Architecture Guide**](./ARCHITECTURE.md) | System design and component relationships | Architects/Leads |
| [**Deployment Guide**](./DEPLOYMENT.md) | Production deployment instructions | DevOps |
| [**User Guide**](./USER_GUIDE.md) | End-user application guide | Users/Support |
| [**Contributing**](./CONTRIBUTING.md) | Development guidelines and standards | Contributors |

## 🔗 API Endpoints Overview

### Emergency Services (`ambulance.py`)
- `GET /` - Service status
- `POST /nearby-ambulance-services` - Find nearby ambulances
- `POST /call-ambulance` - Emergency ambulance booking

### AI Diagnosis (`chatbot.py`)
- `GET /` - Service status  
- `POST /chat` - AI-powered medical consultation
- `POST /classify` - Symptom classification

### Document Processing (`document.py`)
- `POST /diagnosis` - Medical document analysis
- `GET /test` - Service health check

### Location Services (`location.py`)
- `GET /` - Service status
- `GET /specializations` - Medical specializations
- `POST /nearby-doctors` - Find nearby doctors
- `GET /doctor-details/<place_id>` - Doctor information

### Wellness Tracking (`yoga.py`)
- `GET /video_feed` - Live pose detection stream
- `POST /update_session` - Update workout session
- `POST /reset_session` - Reset session data
- `GET /health` - Service health check

## 🛠 Technology Stack

### Backend
- **Flask** - Web framework
- **Groq** - AI/ML processing
- **Firebase** - Database and authentication
- **OpenCV** - Computer vision for pose detection
- **TensorFlow** - Machine learning models

### Frontend
- **Next.js 13** - React framework with App Router
- **React 18** - UI library
- **Tailwind CSS** - Styling framework
- **Framer Motion** - Animations
- **Firebase SDK** - Backend integration

### External Services
- **Google Maps API** - Location and mapping
- **Groq API** - Large language models
- **Email Services** - Notifications
- **WebRTC** - Video calling

## 📈 Performance Metrics

- **API Response Time**: < 200ms average
- **AI Diagnosis**: < 3s response time
- **Video Processing**: 30 FPS real-time
- **Concurrent Users**: 1000+ supported
- **Uptime**: 99.9% target

## 🔒 Security Features

- **Authentication**: Firebase Auth with JWT
- **Data Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Input Validation**: Comprehensive sanitization
- **Rate Limiting**: API endpoint protection
- **CORS**: Configured for secure cross-origin requests

## 🧪 Testing

```bash
# Backend tests
python -m pytest tests/

# Frontend tests  
npm run test

# Integration tests
npm run test:integration

# Load testing
npm run test:load
```

## 📊 Monitoring & Analytics

- **Health Checks**: All services include `/health` endpoints
- **Logging**: Structured logging with correlation IDs
- **Metrics**: Performance and usage analytics
- **Alerts**: Automated monitoring and notifications

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for:

- Development setup
- Coding standards
- Pull request process
- Issue reporting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/anwitac246/healthcare-ai-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/anwitac246/healthcare-ai-agent/discussions)
- **Email**: support@healthcare-ai-agent.com

## 🗺 Roadmap

- [ ] **Q1 2024**: Mobile app development
- [ ] **Q2 2024**: Advanced AI diagnostics
- [ ] **Q3 2024**: Integration with EHR systems
- [ ] **Q4 2024**: Multi-language support

---

**Built with ❤️ for better healthcare accessibility**