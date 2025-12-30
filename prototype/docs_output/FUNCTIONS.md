# Function Reference

Complete reference for all functions in the codebase.

## Table of Contents

- [ambulance.py](#ambulancepy)
- [chatbot.py](#chatbotpy)
- [document.py](#documentpy)
- [location.py](#locationpy)
- [yoga.py](#yogapy)
- [src\app\layout.js](#src\app\layoutjs)
- [src\app\page.js](#src\app\pagejs)
- [src\app\about\page.js](#src\app\about\pagejs)
- [src\app\ambulance\page.js](#src\app\ambulance\pagejs)
- [src\app\appointment\page.js](#src\app\appointment\pagejs)
- [src\app\contact\page.js](#src\app\contact\pagejs)
- [src\app\diagnosis\page.js](#src\app\diagnosis\pagejs)
- [src\app\doctor_profile\page.js](#src\app\doctor_profile\pagejs)
- [src\app\location_docs\page.js](#src\app\location_docs\pagejs)
- [src\app\login\page.js](#src\app\login\pagejs)
- [src\app\profile\page.js](#src\app\profile\pagejs)
- [src\app\room\page.js](#src\app\room\pagejs)
- [src\app\room\[roomId]\page.js](#src\app\room\[roomid]\pagejs)
- [src\app\yoga\page.js](#src\app\yoga\pagejs)
- [src\components\homepage.js](#src\components\homepagejs)
- [src\components\navbar.js](#src\components\navbarjs)
- [src\components\ui\input.js](#src\components\ui\inputjs)
- [src\lib\utils.js](#src\lib\utilsjs)

---

## ambulance.py

### `normalize_phone_number(number)`

**Parameters**: number

**Complexity**: Low

---

### `home()`

**Parameters**: None

**Complexity**: Low

---

### `get_nearby_ambulance_services()`

**Parameters**: None

**Complexity**: Low

---

### `call_ambulance()`

**Parameters**: None

**Complexity**: Low

---

## chatbot.py

### `process_image(file)`

**Parameters**: file

**Complexity**: Medium

---

### `home()`

**Parameters**: None

**Complexity**: High

---

### `chat()`

**Parameters**: None

**Complexity**: High

---

### `classify_endpoint()`

**Parameters**: None

**Complexity**: High

---

## document.py

### `__init__(self)`

**Parameters**: self

**Complexity**: Medium

---

### `extract_text(self, file_path)`

**Parameters**: self, file_path

**Returns**: str

**Complexity**: Medium

---

### `preprocess_text(self, text)`

**Parameters**: self, text

**Returns**: str

**Complexity**: Low

---

### `rule_based_extraction(text)`

**Parameters**: text

**Returns**: Dict[str, List[str]]

**Complexity**: Low

---

### `create_analysis_task(text)`

**Parameters**: text

**Returns**: Task

**Complexity**: Low

---

### `create_summary_task(analysis_output, Any])`

**Parameters**: analysis_output, Any]

**Returns**: Task

**Complexity**: Low

---

### `process_diagnosis()`

**Parameters**: None

**Complexity**: Medium

---

### `test()`

**Parameters**: None

**Complexity**: Low

---

## location.py

### `calculate_distance(lat1, lng1, lat2, lng2)`

**Description**: """Calculate distance between two points using Haversine formula"""

**Parameters**: lat1, lng1, lat2, lng2

**Complexity**: Low

---

### `get_place_details(place_id)`

**Description**: """Get detailed information about a place"""

**Parameters**: place_id

**Complexity**: Medium

---

### `sort_doctors(doctors, sort_by, user_lat=None, user_lng=None)`

**Description**: """Sort doctors based on the specified criteria"""

**Parameters**: doctors, sort_by, user_lat=None, user_lng=None

**Complexity**: Medium

---

### `home()`

**Parameters**: None

**Complexity**: Low

---

### `get_specializations()`

**Description**: """Return list of medical specializations"""

**Parameters**: None

**Complexity**: Low

---

### `get_nearby_doctors()`

**Parameters**: None

**Complexity**: Medium

---

### `get_doctor_details(place_id)`

**Description**: """Get detailed information about a specific doctor/clinic"""

**Parameters**: place_id

**Complexity**: Medium

---

### `not_found(error)`

**Parameters**: error

**Complexity**: Low

---

### `internal_error(error)`

**Parameters**: error

**Complexity**: Low

---

## yoga.py

### `detectPose(image, pose)`

**Description**: """ """

**Parameters**: image, pose

**Complexity**: Medium

---

### `calculateAngle(landmark1, landmark2, landmark3)`

**Description**: """ """

**Parameters**: landmark1, landmark2, landmark3

**Complexity**: Medium

---

### `classifyPose(landmarks, output_image)`

**Description**: """ """

**Parameters**: landmarks, output_image

**Complexity**: Low

---

### `webcam_feed()`

**Description**: """ """

**Parameters**: None

**Complexity**: Medium

---

### `video_feed()`

**Description**: """ """

**Parameters**: None

**Complexity**: Medium

---

### `update_session()`

**Description**: """ """

**Parameters**: None

**Complexity**: Medium

---

### `reset_session()`

**Description**: """ """

**Parameters**: None

**Complexity**: Low

**Type**: API Handler Function

---

### `health_check()`

**Description**: """ """

**Parameters**: None

**Complexity**: Medium

---

## src\app\about\page.js

### `About()`

**Parameters**: None

**Complexity**: Low

---

### `handleConsultationClick()`

**Parameters**: None

**Complexity**: Low

---

## src\app\appointment\page.js

### `BookAppointment()`

**Parameters**: None

**Complexity**: Low

---

### `handleSubmit(e)`

**Parameters**: e

**Complexity**: Medium

---

### `getFilteredAppointments()`

**Description**: // Filter appointments based on search and filters

**Parameters**: None

**Complexity**: Medium

---

### `getStatusIcon(status)`

**Parameters**: status

**Complexity**: Low

---

### `getModeIcon(mode)`

**Parameters**: mode

**Complexity**: Low

---

## src\app\diagnosis\page.js

### `Diagnosis()`

**Parameters**: None

**Complexity**: Low

---

### `toggleRecording()`

**Parameters**: None

**Complexity**: Medium

---

### `speakText(text, index)`

**Parameters**: text, index

**Complexity**: Low

---

### `handleSpeakInput()`

**Parameters**: None

**Complexity**: Low

---

### `handleSpeakMessage(content, index)`

**Parameters**: content, index

**Complexity**: Low

---

### `load()`

**Parameters**: None

**Complexity**: Medium

---

### `onScroll()`

**Parameters**: None

**Complexity**: Low

---

### `scrollToBottom()`

**Parameters**: None

**Complexity**: Low

---

### `startNewChat(firebaseDb, u)`

**Parameters**: firebaseDb, u

**Complexity**: Low

---

### `handleSendMessage(overrideText)`

**Parameters**: overrideText

**Complexity**: Low

---

### `handleDocumentUpload(e)`

**Parameters**: e

**Complexity**: Medium

---

### `generatePDFReport(name, email, dob, diag, conf)`

**Parameters**: name, email, dob, diag, conf

**Complexity**: Low

---

## src\app\login\page.js

### `Login()`

**Parameters**: None

**Complexity**: Low

---

### `handleSignUp(e)`

**Parameters**: e

**Complexity**: Medium

---

### `handleLogin(e)`

**Parameters**: e

**Complexity**: Medium

---

### `handleGoogle()`

**Parameters**: None

**Complexity**: Medium

---

### `handleExtraInfo(e)`

**Parameters**: e

**Complexity**: Medium

---

## src\app\profile\page.js

### `ProfilePage()`

**Description**: // Register GSAP ScrollTrigger

**Parameters**: None

**Complexity**: Low

---

### `handleChange(e)`

**Parameters**: e

**Complexity**: Low

---

### `handleSave()`

**Parameters**: None

**Complexity**: Medium

---

## src\app\room\page.js

### `Home()`

**Parameters**: None

**Complexity**: Low

---

### `createRoom()`

**Parameters**: None

**Complexity**: Low

---

## src\app\room\[roomId]\page.js

### `Room()`

**Parameters**: None

**Complexity**: Low

---

### `debugLog(message)`

**Description**: // Debug logging function

**Parameters**: message

**Complexity**: Low

---

### `connectToNewUser(userId, stream)`

**Parameters**: userId, stream

**Complexity**: Low

---

### `addVideoStream(video, stream, id, isLocal)`

**Parameters**: video, stream, id, isLocal

**Complexity**: Medium

---

### `removeVideo(id)`

**Parameters**: id

**Complexity**: Medium

---

### `toggleAudio()`

**Parameters**: None

**Complexity**: Low

---

### `toggleVideo()`

**Parameters**: None

**Complexity**: Low

---

### `shareLink()`

**Parameters**: None

**Complexity**: Medium

---

### `endCall()`

**Parameters**: None

**Complexity**: Medium

---

### `formatTime(sec)`

**Parameters**: sec

**Complexity**: Medium

---

## src\components\homepage.js

### `Homepage()`

**Parameters**: None

**Complexity**: Low

---

### `handleScroll()`

**Parameters**: None

**Complexity**: Low

---

### `handleConsultationClick()`

**Parameters**: None

**Complexity**: Low

---

