# Attendance System API - Postman Testing Guide

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run migrations:
   ```
   python manage.py migrate
   ```

3. Start the development server:
   ```
   python manage.py runserver
   ```

## API Endpoints

### Authentication Endpoints

#### 1. Register a new user
- **URL**: `POST http://127.0.0.1:8000/api/register/`
- **Body** (form-data or x-www-form-urlencoded):
  ```
  username: testuser
  email: test@example.com
  password: password123
  confirm_password: password123
  first_name: Test
  last_name: User
  ```
- **Response**: Returns a token that should be used for authentication in subsequent requests.

#### 2. Login
- **URL**: `POST http://127.0.0.1:8000/api/login/`
- **Body**:
  ```
  username: testuser
  password: password123
  ```
- **Response**: Returns authentication token.

### User Data Endpoints

All endpoints below require authentication. Add the token to your requests:
- In Headers: `Authorization: Token your_token_here`

#### 3. Get User Profile
- **URL**: `GET http://127.0.0.1:8000/api/profile/`

#### 4. Get Dashboard Data
- **URL**: `GET http://127.0.0.1:8000/api/dashboard/`

#### 5. List Subjects
- **URL**: `GET http://127.0.0.1:8000/api/subjects/`

#### 6. List Class Periods
- **URL**: `GET http://127.0.0.1:8000/api/periods/`

### Attendance Management

#### 7. Mark Daily Attendance
- **URL**: `POST http://127.0.0.1:8000/api/mark-attendance/`
- No body required, uses current time

#### 8. Mark Subject Attendance
- **URL**: `POST http://127.0.0.1:8000/api/mark-subject-attendance/`
- **Body**:
  ```
  subject_id: 1
  period_id: 1  # Optional
  status: present  # Options: present, absent, late
  notes: Attended full class  # Optional
  ```

#### 9. Get Attendance History
- **URL**: `GET http://127.0.0.1:8000/api/attendance-history/`

#### 10. Get Subject Attendance History
- **URL**: `GET http://127.0.0.1:8000/api/subject-attendance-history/`
- **Optional Query Parameters**:
  ```
  subject_id=1
  date_from=2023-10-01
  date_to=2023-10-31
  ```

## Postman Collection Setup

1. Create a new Postman Collection named "Attendance System API"
2. Create a Collection Variable named "token" (this will store your auth token)
3. For each authenticated request, add this to Headers: 
   `Authorization: Token {{token}}`
4. In the Login request, add a Test script to automatically extract and save the token:
   ```javascript
   if (pm.response.code === 200) {
       var jsonData = pm.response.json();
       if (jsonData.token) {
           pm.collectionVariables.set("token", jsonData.token);
           console.log("Token saved to collection variable: " + jsonData.token);
       }
   }
   ```

## Testing Workflow

1. Register a new user (or login if already registered)
2. Token is automatically saved and used for subsequent requests
3. List subjects and periods to get their IDs
4. Mark attendance and subject attendance
5. View attendance history

## Troubleshooting

- If you get a 401 Unauthorized error, check your token is correct
- If using DRF Browsable API, you might need to include CSRF token for POST requests
- If endpoints return 404, ensure your API URLs are correctly configured 