# Setup Guide

Complete setup instructions for healthcare-ai-agent.

## Prerequisites

Based on the analysis, this project uses:
javascript, python

### System Requirements


#### Python Requirements
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Node.js Requirements
- Node.js 16.0 or higher
- npm or yarn package manager

```bash
# Check Node.js version
node --version

# Check npm version
npm --version
```

## Installation Steps

### 1. Clone the Repository

```bash
git clone [repository-url]
cd [repository-name]
```

### 2. Install Dependencies


#### Python Dependencies
```bash
pip install -r requirements.txt
```

#### Node.js Dependencies
```bash
npm install
# or
yarn install
```

### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# Add your environment variables here
# Example:
# DATABASE_URL=your_database_url
# API_KEY=your_api_key
```

### 4. Database Setup (if applicable)

```bash
# Run database migrations
# Add specific commands based on your database setup
```

### 5. Start the Application


#### Python Application
```bash
python app.py
# or
flask run
# or
uvicorn main:app --reload
```

#### Node.js Application
```bash
npm start
# or
npm run dev
# or
yarn start
```

## Verification

After setup, verify the installation:

1. Check if the application starts without errors
2. Test API endpoints (see [API Documentation](./API.md))
3. Run any available tests

## Next Steps

- Review the [API Documentation](./API.md)
- Check the [Architecture Overview](./ARCHITECTURE.md)
- See [Deployment Guide](./DEPLOYMENT.md) for production setup
