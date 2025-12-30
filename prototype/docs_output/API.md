# API Documentation

Complete API reference with examples and usage instructions.

## Table of Contents

- [ambulance.py](#ambulancepy)
- [chatbot.py](#chatbotpy)
- [document.py](#documentpy)
- [location.py](#locationpy)
- [yoga.py](#yogapy)
- [pages\api\send-email.js](#pages\api\send-emailjs)

---

## ambulance.py

**Ambulance API Documentation**

**FILE_OVERVIEW**

### Purpose and Role

The `ambulance.py` file implements a RESTful API for ambulance services, providing endpoints for users to find nearby ambulance services and call for emergency assistance. The API is designed to be scalable, secure, and easy to integrate with various frontend applications.

### Architecture Context and Relationships

The API is built using the Flask web framework and utilizes the Google Maps API for geolocation services. The API has three main endpoints:

1. `/`: A simple welcome page.
2. `/nearby-ambulance-services`: A POST endpoint that takes user input (latitude, longitude, and text) to find nearby ambulance services.
3. `/call-ambulance`: A POST endpoint that takes user input (name, phone number, override phone number, confirmation, latitude, and longitude) to call for emergency assistance.

### Key Responsibilities and Functionality

The API is responsible for:

1. Handling user input for nearby ambulance services and emergency assistance.
2. Validating user input for correctness and security.
3. Integrating with the Google Maps API for geolocation services.
4. Providing a secure and scalable API for frontend applications.

**API_DOCUMENTATION**

### GET /

#### Purpose and Business Logic

The `/` endpoint is a simple welcome page that returns a "Welcome to the ambulance API" message.

#### Parameter Documentation

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| None | None | None | N/A |

#### Request/Response Examples

**Request**

* Method: GET
* URL: `/`
* Headers: None
* Body: None

**Response**

* Status Code: 200 OK
* Response Body: "Welcome to the ambulance API"

#### Authentication and Authorization Requirements

None

#### Error Handling

None

#### Rate Limiting and Usage Guidelines

None

#### Integration Examples

```javascript
fetch('/').then(response => response.text()).then(text => console.log(text));
```

### POST /nearby-ambulance-services

#### Purpose and Business Logic

The `/nearby-ambulance-services` endpoint takes user input (latitude, longitude, and text) to find nearby ambulance services. It uses the Google Maps API to retrieve the nearest ambulance services.

#### Parameter Documentation

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| lat | float | Latitude of the user's location | Yes |
| lng | float | Longitude of the user's location | Yes |
| text | string | Text to search for nearby ambulance services | Yes |

#### Request/Response Examples

**Request**

* Method: POST
* URL: `/nearby-ambulance-services`
* Headers: `Content-Type: application/json`
* Body: `{"lat": 37.7749, "lng": -122.4194, "text": "ambulance services in San Francisco"}`

**Response**

* Status Code: 200 OK
* Response Body: JSON object containing nearby ambulance services

#### Authentication and Authorization Requirements

None

#### Error Handling

* `400 Bad Request`: Invalid user input
* `500 Internal Server Error`: Google Maps API error

#### Rate Limiting and Usage Guidelines

* 100 requests per minute
* Do not use this endpoint for commercial purposes without permission

#### Integration Examples

```javascript
fetch('/nearby-ambulance-services', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ lat: 37.7749, lng: -122.4194, text: 'ambulance services in San Francisco' }),
}).then(response => response.json()).then(data => console.log(data));
```

### POST /call-ambulance

#### Purpose and Business Logic

The `/call-ambulance` endpoint takes user input (name, phone number, override phone number, confirmation, latitude, and longitude) to call for emergency assistance.

#### Parameter Documentation

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| name | string | Name of the person calling for assistance | Yes |
| phone_number | string | Phone number of the person calling for assistance | Yes |
| override_phone_number | string | Override phone number for emergency assistance | No |
| confirm | boolean | Confirmation of the emergency assistance | No |
| lat | float | Latitude of the user's location | Yes |
| lng | float | Longitude of the user's location | Yes |

#### Request/Response Examples

**Request**

* Method: POST
* URL: `/call-ambulance`
* Headers: `Content-Type: application/json`
* Body: `{"name": "John Doe", "phone_number": "1234567890", "lat": 37.7749, "lng": -122.4194}`

**Response**

* Status Code: 200 OK
* Response Body: JSON object containing the emergency assistance details

#### Authentication and Authorization Requirements

None

#### Error Handling

* `400 Bad Request`: Invalid user input
* `500 Internal Server Error`: Database error

#### Rate Limiting and Usage Guidelines

* 100 requests per minute
* Do not use this endpoint for commercial purposes without permission

#### Integration Examples

```javascript
fetch('/call-ambulance', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'John Doe', phone_number: '1234567890', lat: 37.7749, lng: -122.4194 }),
}).then(response => response.json()).then(data => console.log(data));
```

**FUNCTION_DOCUMENTATION**

### normalize_phone_number(number)

#### Purpose and Algorithm Description

The `normalize_phone_number` function takes a phone number as input and returns a normalized phone number in the format `+91xxxxxxxxxx`.

#### Parameter Documentation

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| number | string | Phone number to normalize | Yes |

#### Return Value Documentation

| Return Value | Type | Description |
| --- | --- | --- |
| normalized_phone_number | string | Normalized phone number in the format `+91xxxxxxxxxx` |

#### Usage Examples

```python
print(normalize_phone_number('1234567890'))  # Output: +911234567890
print(normalize_phone_number('+91 1234567890'))  # Output: +911234567890
```

#### Error Handling

None

#### Performance Considerations

This function is designed to be lightweight and efficient, with a time complexity of O(1).

### home()

#### Purpose and Algorithm Description

The `home` function returns a simple welcome message.

#### Parameter Documentation

None

#### Return Value Documentation

| Return Value | Type | Description |
| --- | --- | --- |
| welcome_message | string | Welcome message |

#### Usage Examples

```python
print(home())  # Output: Welcome to the ambulance API
```

#### Error Handling

None

#### Performance Considerations

This function is designed to be lightweight and efficient, with a time complexity of O(1).

### get_nearby_ambulance_services()

#### Purpose and Algorithm Description

The `get_nearby_ambulance_services` function takes user input (latitude, longitude, and text) to find nearby ambulance services. It uses the Google Maps API to retrieve the nearest ambulance services.

#### Parameter Documentation

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| lat | float | Latitude of the user's location | Yes |
| lng | float | Longitude of the user's location | Yes |
| text | string | Text to search for nearby ambulance services | Yes |

#### Return Value Documentation

| Return Value | Type | Description |
| --- | --- | --- |
| nearby_ambulance_services | JSON object | Nearby ambulance services |

#### Usage Examples

```python
print(get_nearby_ambulance_services(lat=37.7749, lng=-122.4194, text='ambulance services in San Francisco'))
```

#### Error Handling

* `400 Bad Request`: Invalid user input
* `500 Internal Server Error`: Google Maps API error

#### Performance Considerations

This function is designed to be efficient, with a time complexity of O(1). However, it may take some time to retrieve the nearby ambulance services from the Google Maps API.

### call_ambulance()

#### Purpose and Algorithm Description

The `call_ambulance` function takes user input (name, phone number, override phone number, confirmation, latitude, and longitude) to call for emergency assistance.

#### Parameter Documentation

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| name | string | Name of the person calling for assistance | Yes |
| phone_number | string | Phone number of the person calling for assistance | Yes |
| override_phone_number | string | Override phone number for emergency assistance | No |
| confirm | boolean | Confirmation of the emergency assistance | No |
| lat | float | Latitude of the user's location | Yes |
| lng | float | Longitude of the user's location | Yes |

#### Return Value Documentation

| Return Value | Type | Description |
| --- | --- | --- |
| emergency_assistance_details | JSON object | Emergency assistance details |

#### Usage Examples

```python
print(call_ambulance(name='John Doe', phone_number='1234567890', lat=37.7749, lng=-122.4194))
```

#### Error Handling

* `400 Bad Request`: Invalid user input
* `500 Internal Server Error`: Database error

#### Performance Considerations

This

---

## chatbot.py

**FILE_OVERVIEW**

### Purpose and Role

The `chatbot.py` file is a Python implementation of a RESTful API that provides a chatbot functionality. The API allows users to interact with the chatbot through two main endpoints: `/chat` and `/classify`. The `/chat` endpoint enables users to have a conversation with the chatbot, while the `/classify` endpoint allows users to classify text inputs.

### Architecture Context and Relationships

The API is built using the Flask web framework and utilizes the Groq library for natural language processing (NLP) tasks. The API also relies on several dependencies, including CORS, PubmedTools, and img_to_array, to provide additional functionality.

### Key Responsibilities and Functionality

The API's key responsibilities include:

* Providing a chatbot functionality through the `/chat` endpoint
* Classifying text inputs through the `/classify` endpoint
* Handling user input and generating responses
* Utilizing NLP techniques to analyze and understand user input

**API_DOCUMENTATION**

### GET /

#### Purpose and Business Logic

The `/` endpoint is the API's home page, providing a welcome message and instructions on how to use the API.

#### Parameters

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| None |  |  |  |

#### Request/Response Examples

**Request**

* Method: GET
* URL: `/`
* Response:

```json
{
  "message": "Welcome to the Diagnosis API. Please POST your data to /chat or /classify."
}
```

#### Authentication and Authorization Requirements

None

#### Error Handling

* 200 OK: Successful response
* 400 Bad Request: Invalid request

#### Rate Limiting and Usage Guidelines

None

#### Integration Examples

```javascript
fetch('/').then(response => response.json()).then(data => console.log(data));
```

### POST /chat

#### Purpose and Business Logic

The `/chat` endpoint enables users to have a conversation with the chatbot. The chatbot will respond to user input based on its understanding of the conversation.

#### Parameters

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| message | string | User input | Yes |
| history | string | Conversation history | No |

#### Request/Response Examples

**Request**

* Method: POST
* URL: `/chat`
* Body:

```json
{
  "message": "Hello, how are you?",
  "history": "[{\"content\": \"Hello\"}]"
}
```

**Response**

```json
{
  "response": "I'm doing well, thank you for asking!",
  "conversation_history": "[{\"content\": \"Hello\"}, {\"content\": \"I'm doing well, thank you for asking!\"}]"
}
```

#### Authentication and Authorization Requirements

None

#### Error Handling

* 200 OK: Successful response
* 400 Bad Request: Invalid request
* 500 Internal Server Error: Server error

#### Rate Limiting and Usage Guidelines

None

#### Integration Examples

```javascript
fetch('/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'Hello, how are you?',
    history: '[{"content": "Hello"}]'
  })
}).then(response => response.json()).then(data => console.log(data));
```

### POST /classify

#### Purpose and Business Logic

The `/classify` endpoint allows users to classify text inputs. The chatbot will analyze the input and provide a classification based on its understanding.

#### Parameters

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| message | string | User input | Yes |
| history | string | Conversation history | No |

#### Request/Response Examples

**Request**

* Method: POST
* URL: `/classify`
* Body:

```json
{
  "message": "This is a test message",
  "history": "[{\"content\": \"Hello\"}]"
}
```

**Response**

```json
{
  "classification": "Test message",
  "conversation_history": "[{\"content\": \"Hello\"}, {\"content\": \"This is a test message\"}]"
}
```

#### Authentication and Authorization Requirements

None

#### Error Handling

* 200 OK: Successful response
* 400 Bad Request: Invalid request
* 500 Internal Server Error: Server error

#### Rate Limiting and Usage Guidelines

None

#### Integration Examples

```javascript
fetch('/classify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'This is a test message',
    history: '[{"content": "Hello"}]'
  })
}).then(response => response.json()).then(data => console.log(data));
```

**FUNCTION_DOCUMENTATION**

### process_image(file)

#### Purpose and Algorithm Description

The `process_image` function takes an image file as input and processes it for use in the chatbot's NLP tasks.

#### Parameters

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| file | string | Image file path | Yes |

#### Return Value

The function returns the processed image array.

#### Usage Examples

```python
image_array = process_image('image.jpg')
```

#### Error Handling

* None

#### Performance Considerations

The function uses the `img_to_array` function to convert the image to an array, which may be computationally expensive for large images.

### home()

#### Purpose and Algorithm Description

The `home` function returns a welcome message and instructions on how to use the API.

#### Parameters

None

#### Return Value

The function returns a string containing the welcome message.

#### Usage Examples

```python
print(home())
```

#### Error Handling

* None

#### Performance Considerations

The function is a simple string return, so it has minimal performance considerations.

### chat()

#### Purpose and Algorithm Description

The `chat` function handles user input and generates responses based on the chatbot's understanding of the conversation.

#### Parameters

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| message | string | User input | Yes |
| history | string | Conversation history | No |

#### Return Value

The function returns a dictionary containing the response and conversation history.

#### Usage Examples

```python
response = chat('Hello, how are you?')
print(response)
```

#### Error Handling

* 200 OK: Successful response
* 400 Bad Request: Invalid request
* 500 Internal Server Error: Server error

#### Performance Considerations

The function uses the `Groq` library for NLP tasks, which may be computationally expensive for large inputs.

### classify_endpoint()

#### Purpose and Algorithm Description

The `classify_endpoint` function allows users to classify text inputs. The chatbot will analyze the input and provide a classification based on its understanding.

#### Parameters

| Parameter | Type | Description | Required |
| --- | --- | --- | --- |
| message | string | User input | Yes |
| history | string | Conversation history | No |

#### Return Value

The function returns a dictionary containing the classification and conversation history.

#### Usage Examples

```python
response = classify_endpoint('This is a test message')
print(response)
```

#### Error Handling

* 200 OK: Successful response
* 400 Bad Request: Invalid request
* 500 Internal Server Error: Server error

#### Performance Considerations

The function uses the `Groq` library for NLP tasks, which may be computationally expensive for large inputs.

**SETUP_AND_DEPLOYMENT**

### Environment Setup Instructions

1. Install the required dependencies using pip: `pip install -r requirements.txt`
2. Set up the environment variables in the `.env` file
3. Run the API using `python chatbot.py`

### Required Dependencies

* Flask
* Groq
* CORS
* PubmedTools
* img_to_array

### Environment Variables

* `API_KEY`: API key for the Groq library
* `DATABASE_URL`: URL for the database

### Database Setup and Configuration

1. Create a database using a tool like PostgreSQL
2. Configure the database URL in the `.env` file

### Step-by-Step Deployment Instructions

1. Deploy the API to a cloud platform like Heroku
2. Configure the environment variables in the cloud platform
3. Run the API using the cloud platform's deployment tool

### Docker Configuration

1. Create a Dockerfile for the API
2. Build the Docker image using `docker build -t chatbot .`
3. Run the Docker container using `docker run -p 5000:5000 chatbot`

### Testing Instructions

1. Run the API using `python chatbot.py`
2. Use a tool like Postman to test the API endpoints
3. Verify that the API is working correctly by checking the response codes and data

**USAGE_EXAMPLES**

### cURL Commands

* `curl http://localhost:5000/`: Test the `/` endpoint
* `curl -X POST -H "Content-Type: application/json" -d '{"message": "Hello, how are you?", "history": "[{\"content\": \"Hello\"}]"}' http://localhost:5000/chat`: Test the `/chat` endpoint
* `curl -X POST -H "Content-Type: application/json" -d '{"message": "This is a test message", "history": "[{\"content\": \"Hello\"}]"}' http://localhost:5000/classify`: Test the `/classify

---

## document.py

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5994, Requested 1829. Please try again in 18.23s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## location.py

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5987, Requested 2106. Please try again in 20.93s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## yoga.py

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5981, Requested 1881. Please try again in 18.62s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## pages\api\send-email.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5976, Requested 913. Please try again in 8.89s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\layout.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5970, Requested 571. Please try again in 5.41s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5965, Requested 515. Please try again in 4.8s. Need more tokens? Upgrade to Dev Tier today at https://consol

---

## src\app\about\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5960, Requested 688. Please try again in 6.48s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\ambulance\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5954, Requested 928. Please try again in 8.82s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\appointment\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5949, Requested 1061. Please try again in 10.1s. Need more tokens? Upgrade to Dev Tier today at https://cons

---

## src\app\contact\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5944, Requested 830. Please try again in 7.74s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\diagnosis\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5939, Requested 1304. Please try again in 12.43s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## src\app\doctor_profile\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5933, Requested 709. Please try again in 6.42s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\location_docs\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5927, Requested 1107. Please try again in 10.34s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## src\app\login\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5922, Requested 961. Please try again in 8.83s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\profile\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5916, Requested 793. Please try again in 7.09s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\room\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5911, Requested 635. Please try again in 5.46s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\app\room\[roomId]\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5906, Requested 1340. Please try again in 12.46s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## src\app\yoga\page.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5900, Requested 1343. Please try again in 12.43s. Need more tokens? Upgrade to Dev Tier today at https://con

---

## src\components\homepage.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5895, Requested 757. Please try again in 6.52s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\components\navbar.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5890, Requested 659. Please try again in 5.49s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

## src\components\ui\input.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5884, Requested 538. Please try again in 4.219999999s. Need more tokens? Upgrade to Dev Tier today at https:

---

## src\lib\utils.js

API Error 429: {"error":{"message":"Rate limit reached for model `llama-3.1-8b-instant` in organization `org_01jhhs77ptezwtgjjgjdjmbjg6` service tier `on_demand` on tokens per minute (TPM): Limit 6000, Used 5879, Requested 504. Please try again in 3.83s. Need more tokens? Upgrade to Dev Tier today at https://conso

---

