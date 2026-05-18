# Live More App API Documentation

This document lists the available API endpoints for the Live More App, designed for testing purposes (e.g., Postman).

## Base URLs
*   **Users API:** `http://localhost:8000/api/users/`
*   **Health API:** `http://localhost:8000/api/health/`

---

## 1. Authentication & Registration (Users API)

### **Signup (Register User)**
*   **Method:** `POST`
*   **URL:** `/api/users/signup/`
*   **Auth:** None
*   **Request Body (JSON):**
    ```json
    {
        "email": "user@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "full_name": "John Doe"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
        "success": true,
        "message": "OTP sent.",
        "data": { "user": { "id": "uuid", "email": "user@example.com" } }
    }
    ```

### **Verify OTP (Email Verification)**
*   **Method:** `POST`
*   **URL:** `/api/users/verify-otp/`
*   **Auth:** None
*   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "otp": "1234"
    }
    ```
*   **Response:** Returns JWT access and refresh tokens.

### **Login**
*   **Method:** `POST`
*   **URL:** `/api/users/login/`
*   **Auth:** None
*   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "Password123!"
    }
    ```

### **Resend OTP**
*   **Method:** `POST`
*   **URL:** `/api/users/resend-otp/`
*   **Auth:** None
*   **Request Body:** 
    ```json
    { 
        "email": "user@example.com" 
    }
    ```

---

## 2. Password Management (Users API)

### **Request Password Reset (Send OTP)**
*   **Method:** `POST`
*   **URL:** `/api/users/password-reset/`
*   **Auth:** None
*   **Request Body:** 
    ```json
    { 
        "email": "user@example.com" 
    }
    ```

### **Verify Password Reset OTP**
*   **Method:** `POST`
*   **URL:** `/api/users/password-reset-otp-verify/`
*   **Auth:** None
*   **Request Body:** 
    ```json
    { 
        "email": "user@example.com", 
        "otp": "1234" 
    }
    ```

### **Confirm Password Reset**
*   **Method:** `POST`
*   **URL:** `/api/users/password-reset-confirm/`
*   **Auth:** None
*   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    }
    ```

### **Change Password (Authenticated)**
*   **Method:** `POST`
*   **URL:** `/api/users/password-change/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "old_password": "OldPassword123!",
        "new_password": "NewPassword123!",
        "confirm_password": "NewPassword123!"
    }
    ```

---

## 3. Profile & Health Management

### **Get My Profile (Users API)**
*   **Method:** `GET`
*   **URL:** `/api/users/profile/`
*   **Auth:** `Bearer <Access Token>`

### **Update My Profile (Users API)**
*   **Method:** `PATCH` or `PUT`
*   **URL:** `/api/users/profile/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body (Partial):**
    ```json
    {
        "full_name": "Johnny Doe",
        "gender": "male",
        "date_of_birth": "1995-05-15"
    }
    ```

### **Update Fitness Info (Users API)**
*   **Method:** `POST`
*   **URL:** `/api/users/fitness-info/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "age": 25,
        "gender": "male",
        "goal": "lose_weight",
        "height": 180,
        "height_unit": "cm",
        "current_weight": 85.0,
        "goal_weight": 75.0
    }
    ```

### **Dashboard Data (Health API)**
*   **Method:** `GET`
*   **URL:** `/api/health/dashboard/`
*   **Auth:** `Bearer <Access Token>`

### **BMI Details (Health API)**
*   **Method:** `GET`
*   **URL:** `/api/health/bmi/`
*   **Auth:** `Bearer <Access Token>`
*   **Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "BMI details retrieved successfully",
        "data": {
            "current_bmi": 22.5,
            "category": "Normal weight",
            "label": "normal",
            "message": "You are in a healthy range. Maintain your current weight with regular exercise and a balanced diet to stay on track.",
            "scale": [
                {"label": "Underweight", "range": "Below 18.5"},
                {"label": "Normal weight", "range": "18.5 - 24.9"},
                {"label": "Overweight", "range": "25.0 - 29.9"},
                {"label": "Obesity", "range": "30.0 or greater"}
            ]
        }
    }
    ```

### **Weight Update (Health API)**
*   **Method:** `POST`
*   **URL:** `/api/health/weight-update/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "weight": 75.5,
        "date": "2026-05-06",
        "notes": "Feeling great after morning run."
    }
    ```
*   **Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Weight updated successfully",
        "data": {
            "id": 1,
            "weight": "75.50",
            "date": "2026-05-06",
            "notes": "Feeling great after morning run.",
            "created_at": "2026-05-06T12:00:00Z"
        }
    }
    ```

### Sync Health Data (Health API)
*   **Method:** `POST`
*   **URL:** `/api/health/sync/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "heart_rate": 72,
        "step_count": 5000,
        
        "battery_level": 85
    }
    ```

### Calorie Burn History (Health API)
*   **Method:** `GET`
*   **URL:** `/api/health/calories-history/`
*   **Auth:** `Bearer <Access Token>`
*   **Query Parameters:** `period` (options: `day`, `week`, `month`, `year`. Default is `day`).
*   **Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "",
        "data": {
            "total_calories": 165.7,
            "highest_calories": 120.5,
            "average_calories": 82.85,
            "recent_workouts": [
                {
                    "id": 1,
                    "workout_type": "running",
                    "duration_minutes": 30,
                    "calories_burned": "250.00",
                    "completed_at": "2026-05-19T10:00:00Z"
                }
            ],
            "chart_data": [
                { "label": "08:00", "calories": 45.2 },
                { "label": "09:00", "calories": 120.5 }
            ]
        }
    }
    ```

### Start Workout Session (Health API)
*   **Method:** `POST`
*   **URL:** `/api/health/workout/start/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "workout_type": "running",
        "heart_rate": 72,
        "step_count": 1000
    }
    ```
*   **Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Running session started",
        "data": {
            "id": 5,
            "workout_type": "running",
            "is_active": true,
            "start_time": "2026-05-19T12:00:00Z",
            "start_steps": 1000,
            "avg_heart_rate": 72
        }
    }
    ```

### Finish Workout Session (Health API)
*   **Method:** `POST`
*   **URL:** `/api/health/workout/finish/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "workout_id": 5,
        "heart_rate": 145,
        "step_count": 5000,
        "duration_minutes": 35,
        "date": "2026-05-19T12:30:00Z"
    }
    ```
*   **Note:** `duration_minutes` and `date` are optional. If omitted, they are calculated automatically.
*   **Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "Workout completed",
        "data": {
            "id": 5,
            "workout_type": "running",
            "is_active": false,
            "duration_minutes": 30,
            "calories_burned": "320.50",
            "end_steps": 5000,
            "avg_heart_rate": 108,
            "completed_at": "2026-05-19T12:30:00Z"
        }
    }
    ```

### Workout Statistics (Health API)
*   **Method:** `GET`
*   **URL:** `/api/health/workout/stats/`
*   **Auth:** `Bearer <Access Token>`
*   **Response (200 OK):**
    ```json
    {
        "success": true,
        "message": "",
        "data": {
            "total_sessions": 5,
            "total_duration_minutes": 150,
            "total_calories_burned": 1200.5,
            "average_duration_minutes": 30.0,
            "best_day_session_count": 2,
            "chart_data": [
                { "label": "2026-05-13", "calories": 250.0 },
                { "label": "2026-05-14", "calories": 300.5 }
            ],
            "history": [
                {
                    "id": 10,
                    "workout_type": "running",
                    "duration_minutes": 30,
                    "calories_burned": "250.00",
                    "completed_at": "2026-05-19T10:00:00Z"
                }
            ]
        }
    }
    ```

### Get Other User Profile (Users API)

*   **Method:** `GET`
*   **URL:** `/api/users/profile/<uuid:user_id>/`
*   **Auth:** `Bearer <Access Token>`

---

## 4. Account & Token Management (Users API)

### **Token Refresh**
*   **Method:** `POST`
*   **URL:** `/api/users/token/refresh/`
*   **Auth:** None
*   **Request Body:** 
    ```json
    { 
        "refresh": "<Refresh Token>" 
    }
    ```

### **Token Verify**
*   **Method:** `POST`
*   **URL:** `/api/users/token/verify/`
*   **Auth:** None
*   **Request Body:** 
    ```json
    { 
        "token": "<Access Token>" 
    }
    ```

### **Logout**
*   **Method:** `POST`
*   **URL:** `/api/users/logout/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:** 
    ```json
    { 
        "refresh": "<Refresh Token>" 
    }
    ```

### **Delete Account**
*   **Method:** `DELETE`
*   **URL:** `/api/users/account-delete/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "password": "YourPassword123!",
        "confirm_deletion": true
    }
    ```

### **Support Ticket**
*   **Method:** `POST`
*   **URL:** `/api/users/support-ticket/`
*   **Auth:** `Bearer <Access Token>`
*   **Request Body:**
    ```json
    {
        "email_address": "user@example.com",
        "subject": "App Issue",
        "message": "I cannot sync my steps."
    }
    ```

https://www.figma.com/design/AkmbWlC7iViOzpUJDILAeE/LiveMore?node-id=13-408&t=L1heWtujsuTSpwyr-0