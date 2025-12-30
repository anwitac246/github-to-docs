# Setup Guide - Healthcare AI Agent

> **Complete installation and configuration guide for development and production environments**

## Table of Contents

- [System Requirements](#system-requirements)
- [Development Setup](#development-setup)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [External Services](#external-services)
- [Running the Application](#running-the-application)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **Operating System** | Windows 10+, macOS 10.15+, Ubuntu 18.04+ |
| **Python** | 3.8+ (recommended: 3.11) |
| **Node.js** | 16.0+ (recommended: 18 LTS) |
| **Memory** | 8 GB RAM minimum, 16 GB recommended |
| **Storage** | 10 GB free space |
| **Network** | Stable internet connection for API services |

### Recommended Development Tools

- **IDE**: VS Code, PyCharm, or WebStorm
- **Git**: Latest version
- **Docker**: For containerized development (optional)
- **Postman**: For API testing

## Development Setup

### 1. Clone the Repository

```bash
# Clone the repository
git clone https://github.com/anwitac246/healthcare-ai-agent.git
cd healthcare-ai-agent

# Create development branch
git checkout -b development
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv healthcare_env

# Activate virtual environment
# Windows:
healthcare_env\Scripts\activate
# macOS/Linux:
source healthcare_env/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**requirements.txt**:
```txt
Flask==2.3.3
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
groq==0.4.1
firebase-admin==6.2.0
opencv-python==4.8.1.78
tensorflow==2.13.0
numpy==1.24.3
Pillow==10.0.1
gunicorn==21.2.0
pytest==7.4.2
```

### 3. Node.js Environment Setup

```bash
# Install Node.js dependencies
npm install

# Install development dependencies
npm install --save-dev

# Verify installation
node --version
npm --version
```

**package.json** (key dependencies):
```json
{
  "dependencies": {
    "next": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "firebase": "^10.4.0",
    "axios": "^1.5.0",
    "framer-motion": "^10.16.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "@types/node": "^20.6.0",
    "@types/react": "^18.2.0",
    "eslint": "^8.49.0",
    "typescript": "^5.2.0"
  }
}
```

## Environment Configuration

### 1. Create Environment Files

```bash
# Copy environment template
cp .env.example .env

# Create environment files for different stages
cp .env.example .env.development
cp .env.example .env.production
```

### 2. Configure Environment Variables

**.env** file:
```env
# Application Configuration
NODE_ENV=development
PORT=3000
API_BASE_URL=http://localhost:3000

# Python Services Ports
AMBULANCE_SERVICE_PORT=5001
CHATBOT_SERVICE_PORT=5002
DOCUMENT_SERVICE_PORT=5003
LOCATION_SERVICE_PORT=5004
YOGA_SERVICE_PORT=5005

# Firebase Configuration
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abcdef123456

# Firebase Admin SDK (for backend)
FIREBASE_ADMIN_SDK_PATH=./config/firebase-admin-sdk.json

# Groq API Configuration
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Google Maps API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key

# Email Service (SendGrid/SMTP)
SENDGRID_API_KEY=your_sendgrid_api_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password

# Security
JWT_SECRET=your_jwt_secret_key_here
ENCRYPTION_KEY=your_32_character_encryption_key

# External APIs
OPENAI_API_KEY=your_openai_api_key (optional)
TWILIO_ACCOUNT_SID=your_twilio_sid (for SMS)
TWILIO_AUTH_TOKEN=your_twilio_token

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/healthcare_db
REDIS_URL=redis://localhost:6379

# Monitoring & Analytics
SENTRY_DSN=your_sentry_dsn (optional)
GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX (optional)

# Development Settings
DEBUG=true
LOG_LEVEL=debug
ENABLE_CORS=true
```

### 3. Secure Configuration Management

```bash
# Create config directory
mkdir -p config

# Add Firebase Admin SDK key (download from Firebase Console)
# Place firebase-admin-sdk.json in config/ directory

# Set proper permissions
chmod 600 .env
chmod 600 config/firebase-admin-sdk.json
```

## Database Setup

### 1. Firebase Setup

1. **Create Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com)
   - Create new project: "healthcare-ai-agent"
   - Enable Authentication, Firestore, and Storage

2. **Configure Authentication**:
   ```javascript
   // Enable sign-in methods:
   // - Email/Password
   // - Google
   // - Phone (optional)
   ```

3. **Setup Firestore Database**:
   ```javascript
   // Create collections:
   // - users
   // - appointments  
   // - medical_records
   // - chat_sessions
   // - emergency_requests
   ```

4. **Firestore Security Rules**:
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       // Users can only access their own data
       match /users/{userId} {
         allow read, write: if request.auth != null && request.auth.uid == userId;
       }
       
       // Medical records - strict access control
       match /medical_records/{recordId} {
         allow read, write: if request.auth != null && 
           resource.data.patient_id == request.auth.uid;
       }
       
       // Appointments
       match /appointments/{appointmentId} {
         allow read, write: if request.auth != null && 
           (resource.data.patient_id == request.auth.uid || 
            resource.data.doctor_id == request.auth.uid);
       }
     }
   }
   ```

### 2. Local Database (Optional)

For development, you can use local PostgreSQL:

```bash
# Install PostgreSQL
# Windows: Download from postgresql.org
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql

# Create database
createdb healthcare_ai_agent

# Run migrations (if using SQLAlchemy)
python manage.py db upgrade
```

## External Services

### 1. Groq API Setup

1. Sign up at [Groq Console](https://console.groq.com)
2. Create API key
3. Add to environment variables
4. Test connection:

```python
from groq import Groq

client = Groq(api_key="your_api_key")
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    model="llama-3.1-8b-instant"
)
print(response.choices[0].message.content)
```

### 2. Google Maps API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable Maps JavaScript API, Places API, Geocoding API
3. Create API key with restrictions
4. Add to environment variables

### 3. Email Service Setup

**Option A: SendGrid**
```bash
# Sign up at sendgrid.com
# Create API key
# Add to SENDGRID_API_KEY in .env
```

**Option B: Gmail SMTP**
```bash
# Enable 2-factor authentication
# Generate app password
# Add credentials to .env
```

## Running the Application

### 1. Start Backend Services

```bash
# Terminal 1 - Emergency Services
cd healthcare-ai-agent
source healthcare_env/bin/activate  # or healthcare_env\Scripts\activate on Windows
python ambulance.py

# Terminal 2 - AI Diagnosis
python chatbot.py

# Terminal 3 - Document Processing  
python document.py

# Terminal 4 - Location Services
python location.py

# Terminal 5 - Wellness Tracking
python yoga.py
```

### 2. Start Frontend Application

```bash
# Terminal 6 - Frontend
npm run dev
```

### 3. Using Process Manager (Recommended)

Create **start_services.py**:
```python
import subprocess
import sys
import time

services = [
    {"name": "ambulance", "file": "ambulance.py", "port": 5001},
    {"name": "chatbot", "file": "chatbot.py", "port": 5002},
    {"name": "document", "file": "document.py", "port": 5003},
    {"name": "location", "file": "location.py", "port": 5004},
    {"name": "yoga", "file": "yoga.py", "port": 5005}
]

processes = []

try:
    for service in services:
        print(f"Starting {service['name']} service on port {service['port']}...")
        process = subprocess.Popen([sys.executable, service['file']])
        processes.append(process)
        time.sleep(2)
    
    print("All services started. Press Ctrl+C to stop all services.")
    
    # Keep running
    while True:
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nStopping all services...")
    for process in processes:
        process.terminate()
    print("All services stopped.")
```

Run with:
```bash
python start_services.py
```

### 4. Docker Setup (Alternative)

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  frontend:
    build: 
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
    volumes:
      - .:/app
      - /app/node_modules

  ambulance-service:
    build:
      context: .
      dockerfile: Dockerfile.python
    ports:
      - "5001:5001"
    environment:
      - FLASK_APP=ambulance.py
      - FLASK_ENV=development
    volumes:
      - .:/app

  chatbot-service:
    build:
      context: .
      dockerfile: Dockerfile.python
    ports:
      - "5002:5002"
    environment:
      - FLASK_APP=chatbot.py
    volumes:
      - .:/app

  # Add other services...

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: healthcare_ai_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with Docker:
```bash
docker-compose up -d
```

## Verification

### 1. Health Checks

Test each service:

```bash
# Test all services
curl http://localhost:5001/  # Emergency services
curl http://localhost:5002/  # AI diagnosis
curl http://localhost:5003/test  # Document processing
curl http://localhost:5004/  # Location services
curl http://localhost:5005/health  # Wellness tracking
curl http://localhost:3000/  # Frontend
```

### 2. Integration Tests

```bash
# Run backend tests
python -m pytest tests/ -v

# Run frontend tests
npm test

# Run integration tests
npm run test:integration
```

### 3. Manual Testing Checklist

- [ ] Frontend loads without errors
- [ ] User registration/login works
- [ ] AI chat responds to messages
- [ ] Location services find nearby doctors
- [ ] Document upload and analysis works
- [ ] Video feed displays for yoga tracking
- [ ] Emergency services can be accessed

## Troubleshooting

### Common Issues

**1. Port Already in Use**
```bash
# Find process using port
lsof -i :5001  # macOS/Linux
netstat -ano | findstr :5001  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows
```

**2. Python Module Not Found**
```bash
# Ensure virtual environment is activated
source healthcare_env/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**3. Firebase Connection Issues**
```bash
# Verify Firebase config
# Check .env file has correct Firebase credentials
# Ensure firebase-admin-sdk.json is in config/ directory
```

**4. API Key Issues**
```bash
# Verify all API keys are set in .env
# Check API key permissions and quotas
# Test API keys individually
```

**5. CORS Issues**
```bash
# Ensure Flask-CORS is installed and configured
# Check frontend URL is allowed in CORS settings
```

### Getting Help

- **Documentation**: [Full documentation](../README.md)
- **Issues**: [GitHub Issues](https://github.com/anwitac246/healthcare-ai-agent/issues)
- **Discord**: [Developer Community](https://discord.gg/healthcare-ai)
- **Email**: dev-support@healthcare-ai-agent.com

### Development Tips

1. **Use environment-specific configs**: `.env.development`, `.env.production`
2. **Enable debug logging**: Set `DEBUG=true` and `LOG_LEVEL=debug`
3. **Use hot reload**: Both Flask and Next.js support hot reload in development
4. **Monitor logs**: Use `tail -f` to monitor service logs in real-time
5. **Use API testing tools**: Postman, Insomnia, or curl for API testing

---

**Next Steps**: Once setup is complete, check out the [API Reference](./API_REFERENCE.md) and [Architecture Guide](./ARCHITECTURE.md).