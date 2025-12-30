# API Reference - Healthcare AI Agent

> **Complete API documentation with examples, authentication, and integration guides**

## Table of Contents

- [Authentication](#authentication)
- [Emergency Services API](#emergency-services-api)
- [AI Diagnosis API](#ai-diagnosis-api)
- [Document Processing API](#document-processing-api)
- [Location Services API](#location-services-api)
- [Wellness Tracking API](#wellness-tracking-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDKs & Libraries](#sdks--libraries)

## Authentication

All API endpoints use **Bearer Token** authentication with Firebase JWT tokens.

### Getting an Auth Token

```javascript
// Frontend - Firebase Auth
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const token = await userCredential.user.getIdToken();

// Use token in API calls
const response = await fetch('/api/endpoint', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### API Headers

```http
Authorization: Bearer <firebase-jwt-token>
Content-Type: application/json
X-API-Version: v1
```

---

## Emergency Services API

**Base URL**: `http://localhost:5001`  
**Service**: `ambulance.py`

### GET / - Service Status

Check if the emergency services API is running.

**Endpoint**: `GET /`

**Response**:
```json
{
  "status": "ok",
  "service": "Emergency Services API",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example**:
```bash
curl -X GET http://localhost:5001/
```

### POST /nearby-ambulance-services - Find Nearby Ambulances

Find ambulance services near a specific location.

**Endpoint**: `POST /nearby-ambulance-services`

**Request Body**:
```json
{
  "lat": 40.7128,
  "lng": -74.0060,
  "radius": 5000,
  "emergency_type": "medical"
}
```

**Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | number | Yes | Latitude coordinate |
| `lng` | number | Yes | Longitude coordinate |
| `radius` | number | No | Search radius in meters (default: 5000) |
| `emergency_type` | string | No | Type of emergency (medical, trauma, cardiac) |

**Response**:
```json
{
  "success": true,
  "ambulances": [
    {
      "id": "amb_001",
      "name": "City Medical Ambulance",
      "distance": 1200,
      "eta": "8 minutes",
      "phone": "+1-555-0123",
      "address": "123 Medical Center Dr",
      "rating": 4.8,
      "available": true,
      "specializations": ["emergency", "cardiac"]
    }
  ],
  "total_found": 5,
  "search_radius": 5000
}
```

**Example**:
```javascript
const response = await fetch('http://localhost:5001/nearby-ambulance-services', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    lat: 40.7128,
    lng: -74.0060,
    radius: 5000,
    emergency_type: 'medical'
  })
});

const data = await response.json();
console.log('Nearby ambulances:', data.ambulances);
```

### POST /call-ambulance - Book Emergency Ambulance

Request an emergency ambulance for immediate dispatch.

**Endpoint**: `POST /call-ambulance`

**Request Body**:
```json
{
  "patient_name": "John Doe",
  "phone_number": "+1-555-0123",
  "emergency_contact": "+1-555-0456",
  "location": {
    "lat": 40.7128,
    "lng": -74.0060,
    "address": "123 Main St, New York, NY 10001"
  },
  "emergency_details": {
    "type": "cardiac",
    "severity": "high",
    "description": "Chest pain and difficulty breathing",
    "conscious": true,
    "age": 45
  },
  "medical_history": ["diabetes", "hypertension"]
}
```

**Response**:
```json
{
  "success": true,
  "booking_id": "EMG_20240115_001",
  "ambulance": {
    "id": "amb_001",
    "driver_name": "Mike Johnson",
    "phone": "+1-555-0789",
    "vehicle_number": "AMB-001-NYC"
  },
  "eta": "6 minutes",
  "status": "dispatched",
  "tracking_url": "https://track.ambulance.com/EMG_20240115_001",
  "estimated_cost": "$450-650"
}
```

---

## AI Diagnosis API

**Base URL**: `http://localhost:5002`  
**Service**: `chatbot.py`

### POST /chat - AI Medical Consultation

Get AI-powered medical advice and diagnosis assistance.

**Endpoint**: `POST /chat`

**Request Body**:
```json
{
  "message": "I have been experiencing chest pain and shortness of breath for the past 2 hours",
  "patient_info": {
    "age": 45,
    "gender": "male",
    "medical_history": ["hypertension", "diabetes"],
    "current_medications": ["lisinopril", "metformin"],
    "allergies": ["penicillin"]
  },
  "conversation_history": [
    {
      "role": "user",
      "content": "Hello, I need medical advice",
      "timestamp": "2024-01-15T10:25:00Z"
    }
  ],
  "severity_assessment": true
}
```

**Response**:
```json
{
  "success": true,
  "response": {
    "message": "Based on your symptoms of chest pain and shortness of breath, especially given your history of hypertension and diabetes, this could indicate a serious cardiac event. I strongly recommend seeking immediate emergency medical attention.",
    "severity_level": "high",
    "recommendations": [
      "Call 911 immediately",
      "Take aspirin if not allergic (325mg)",
      "Sit upright and try to stay calm",
      "Have someone stay with you"
    ],
    "possible_conditions": [
      {
        "condition": "Myocardial Infarction",
        "probability": "high",
        "description": "Heart attack - requires immediate medical attention"
      },
      {
        "condition": "Angina",
        "probability": "medium", 
        "description": "Chest pain due to reduced blood flow to heart"
      }
    ],
    "follow_up_questions": [
      "Is the pain radiating to your arm, jaw, or back?",
      "Are you experiencing nausea or sweating?",
      "Have you taken any heart medications today?"
    ]
  },
  "conversation_id": "conv_20240115_001",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### POST /classify - Symptom Classification

Classify and categorize medical symptoms for triage purposes.

**Endpoint**: `POST /classify`

**Request Body**:
```json
{
  "symptoms": [
    "chest pain",
    "shortness of breath", 
    "dizziness",
    "nausea"
  ],
  "duration": "2 hours",
  "severity": "moderate to severe",
  "patient_age": 45,
  "patient_gender": "male"
}
```

**Response**:
```json
{
  "success": true,
  "classification": {
    "primary_category": "cardiovascular",
    "urgency_level": "emergency",
    "triage_priority": 1,
    "estimated_wait_time": "immediate",
    "department": "emergency_cardiology"
  },
  "risk_factors": [
    "age_over_40",
    "male_gender", 
    "cardiac_symptoms"
  ],
  "recommended_actions": [
    "immediate_medical_attention",
    "ecg_monitoring",
    "cardiac_enzymes_test"
  ]
}
```

---

## Document Processing API

**Base URL**: `http://localhost:5003`  
**Service**: `document.py`

### POST /diagnosis - Medical Document Analysis

Analyze medical documents, lab results, and reports using AI.

**Endpoint**: `POST /diagnosis`

**Request**: Multipart form data

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('document_type', 'lab_report');
formData.append('patient_id', 'patient_123');

const response = await fetch('http://localhost:5003/diagnosis', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
  },
  body: formData
});
```

**Supported File Types**:
- PDF documents
- Images (JPG, PNG, TIFF)
- DICOM files (medical imaging)

**Response**:
```json
{
  "success": true,
  "document_id": "doc_20240115_001",
  "analysis": {
    "document_type": "lab_report",
    "extracted_data": {
      "patient_name": "John Doe",
      "test_date": "2024-01-10",
      "tests": [
        {
          "name": "Complete Blood Count",
          "results": {
            "hemoglobin": "12.5 g/dL",
            "white_blood_cells": "7200/μL",
            "platelets": "250000/μL"
          },
          "reference_ranges": {
            "hemoglobin": "13.5-17.5 g/dL",
            "white_blood_cells": "4500-11000/μL", 
            "platelets": "150000-450000/μL"
          },
          "abnormal_values": ["hemoglobin"]
        }
      ]
    },
    "ai_interpretation": {
      "summary": "Lab results show mild anemia with hemoglobin below normal range",
      "concerns": ["mild_anemia"],
      "recommendations": [
        "Follow up with primary care physician",
        "Consider iron studies",
        "Dietary counseling for iron-rich foods"
      ]
    }
  },
  "processing_time": "2.3 seconds"
}
```

---

## Location Services API

**Base URL**: `http://localhost:5004`  
**Service**: `location.py`

### GET /specializations - Medical Specializations

Get list of available medical specializations.

**Endpoint**: `GET /specializations`

**Response**:
```json
{
  "success": true,
  "specializations": [
    {
      "id": "cardiology",
      "name": "Cardiology",
      "description": "Heart and cardiovascular system",
      "icon": "heart",
      "average_wait_time": "2-3 weeks"
    },
    {
      "id": "dermatology", 
      "name": "Dermatology",
      "description": "Skin, hair, and nail conditions",
      "icon": "skin",
      "average_wait_time": "1-2 weeks"
    }
  ]
}
```

### POST /nearby-doctors - Find Nearby Doctors

Find doctors near a location with specific specializations.

**Endpoint**: `POST /nearby-doctors`

**Request Body**:
```json
{
  "location": {
    "lat": 40.7128,
    "lng": -74.0060
  },
  "specialization": "cardiology",
  "radius": 10000,
  "insurance": "blue_cross",
  "availability": "this_week",
  "sort_by": "distance"
}
```

**Response**:
```json
{
  "success": true,
  "doctors": [
    {
      "id": "dr_001",
      "name": "Dr. Sarah Johnson",
      "specialization": "Cardiology",
      "rating": 4.9,
      "reviews_count": 156,
      "distance": 1.2,
      "address": "456 Medical Plaza, New York, NY",
      "phone": "+1-555-0199",
      "next_available": "2024-01-18T14:00:00Z",
      "accepts_insurance": ["blue_cross", "aetna", "cigna"],
      "languages": ["English", "Spanish"],
      "hospital_affiliations": ["Mount Sinai", "NYU Langone"]
    }
  ],
  "total_found": 12,
  "search_params": {
    "radius": 10000,
    "specialization": "cardiology"
  }
}
```

---

## Wellness Tracking API

**Base URL**: `http://localhost:5005`  
**Service**: `yoga.py`

### GET /video_feed - Live Pose Detection Stream

Get real-time pose detection video stream for yoga/exercise tracking.

**Endpoint**: `GET /video_feed`

**Response**: Video stream (MJPEG format)

**Usage**:
```html
<img src="http://localhost:5005/video_feed" alt="Live pose detection" />
```

### POST /update_session - Update Workout Session

Update current workout session with pose data and progress.

**Endpoint**: `POST /update_session`

**Request Body**:
```json
{
  "session_id": "session_20240115_001",
  "pose_data": {
    "pose_name": "warrior_pose",
    "accuracy": 0.85,
    "duration": 30,
    "keypoints": [
      {"name": "left_shoulder", "x": 150, "y": 200, "confidence": 0.9},
      {"name": "right_shoulder", "x": 250, "y": 200, "confidence": 0.9}
    ]
  },
  "session_stats": {
    "total_poses": 5,
    "average_accuracy": 0.82,
    "calories_burned": 45
  }
}
```

**Response**:
```json
{
  "success": true,
  "session_updated": true,
  "feedback": {
    "pose_quality": "good",
    "improvements": [
      "Straighten your back leg more",
      "Lift your arms higher"
    ],
    "next_pose": "tree_pose"
  },
  "progress": {
    "session_completion": 0.6,
    "total_time": 180,
    "poses_completed": 5,
    "poses_remaining": 3
  }
}
```

---

## Error Handling

All APIs use consistent error response format:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The request body is missing required fields",
    "details": {
      "missing_fields": ["lat", "lng"],
      "provided_fields": ["radius"]
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_20240115_001"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request or missing parameters |
| `UNAUTHORIZED` | 401 | Invalid or missing authentication token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limiting

All APIs implement rate limiting to ensure fair usage:

| Service | Limit | Window |
|---------|-------|--------|
| Emergency Services | 100 requests | per hour |
| AI Diagnosis | 50 requests | per hour |
| Document Processing | 20 requests | per hour |
| Location Services | 200 requests | per hour |
| Wellness Tracking | 1000 requests | per hour |

**Rate Limit Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

---

## SDKs & Libraries

### JavaScript/TypeScript SDK

```bash
npm install healthcare-ai-agent-sdk
```

```javascript
import { HealthcareAI } from 'healthcare-ai-agent-sdk';

const client = new HealthcareAI({
  apiKey: 'your-api-key',
  baseUrl: 'http://localhost:5000'
});

// AI Diagnosis
const diagnosis = await client.diagnosis.chat({
  message: 'I have chest pain',
  patientInfo: { age: 45, gender: 'male' }
});

// Find nearby doctors
const doctors = await client.location.findDoctors({
  lat: 40.7128,
  lng: -74.0060,
  specialization: 'cardiology'
});
```

### Python SDK

```bash
pip install healthcare-ai-agent-sdk
```

```python
from healthcare_ai_agent import HealthcareAI

client = HealthcareAI(
    api_key='your-api-key',
    base_url='http://localhost:5000'
)

# Emergency services
ambulances = client.emergency.find_ambulances(
    lat=40.7128,
    lng=-74.0060,
    radius=5000
)

# Document analysis
result = client.documents.analyze(
    file_path='lab_report.pdf',
    document_type='lab_report'
)
```

---

## Postman Collection

Import our complete Postman collection for easy API testing:

[![Run in Postman](https://run.pstmn.io/button.svg)](https://app.getpostman.com/run-collection/healthcare-ai-agent)

---

**Need help?** Check our [troubleshooting guide](./TROUBLESHOOTING.md) or [open an issue](https://github.com/anwitac246/healthcare-ai-agent/issues).