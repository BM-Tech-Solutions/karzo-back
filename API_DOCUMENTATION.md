# Karzo API Documentation

## Overview

This document provides documentation for the Karzo API endpoints. The API is built using FastAPI and provides endpoints for managing jobs, interviews, and candidates.

## Base URL

During development, the API is accessible at:

```
http://localhost:8000
```

## Authentication

Most endpoints require authentication using a Bearer token. Include the token in the Authorization header:

```
Authorization: Bearer <your_token>
```

To obtain a token, use the login endpoint.

## Endpoints

### Authentication

#### Register a new user

```
POST /api/auth/register
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "User Name",
  "role": "candidate"  // "candidate" or "admin"
}
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User Name",
  "role": "candidate"
}
```

#### Login

```
POST /api/auth/login
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "User Name",
    "role": "candidate"
  }
}
```

#### Validate Token

```
GET /api/auth/validate-token
```

Headers:
```
Authorization: Bearer <your_token>
```

Response:
```json
{
  "valid": true
}
```

### Jobs

#### Get all jobs

```
GET /api/jobs
```

Query parameters:
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Maximum number of records to return (default: 100)

Response:
```json
[
  {
    "id": 1,
    "title": "Software Engineer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "description": "Job description...",
    "posted_date": "2023-01-01T00:00:00",
    "requirements": ["Python", "JavaScript", "SQL"]
  },
  // More jobs...
]
```

### Interviews

#### Get interviews for a candidate

```
GET /api/interviews/candidates/{candidate_id}
```

Authorization: Only admins or the candidate themselves can access their interviews.

Response:
```json
[
  {
    "id": 1,
    "date": "2023-01-15T14:00:00",
    "status": "scheduled",
    "job_title": "Software Engineer",
    "company": "Tech Corp"
  },
  // More interviews...
]
```

#### Get a specific interview

```
GET /api/interviews/{interview_id}
```

Authorization: Only admins or the candidate associated with the interview can access it.

Response:
```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 2,
  "date": "2023-01-15T14:00:00",
  "status": "scheduled"
}
```

#### Create a new interview

```
POST /api/interviews/
```

Authorization: Candidates can only create interviews for themselves, while admins can create interviews for any candidate.

Request body:
```json
{
  "candidate_id": 1,
  "job_id": 2,
  "date": "2023-01-15T14:00:00",
  "status": "scheduled"
}
```

Response:
```json
{
  "id": 1,
  "candidate_id": 1,
  "job_id": 2,
  "date": "2023-01-15T14:00:00",
  "status": "scheduled"
}
```

### Candidates

Candidate endpoints are managed through the standard router and follow RESTful conventions:

- `GET /api/candidates` - Get all candidates
- `GET /api/candidates/{candidate_id}` - Get a specific candidate
- `POST /api/candidates` - Create a new candidate
- `PUT /api/candidates/{candidate_id}` - Update a candidate
- `DELETE /api/candidates/{candidate_id}` - Delete a candidate

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request:

- `200 OK` - The request was successful
- `201 Created` - A new resource was created
- `400 Bad Request` - The request was invalid
- `401 Unauthorized` - Authentication is required
- `403 Forbidden` - The user does not have permission to access the resource
- `404 Not Found` - The resource was not found
- `405 Method Not Allowed` - The HTTP method is not supported for the requested resource
- `500 Internal Server Error` - An unexpected error occurred

Error responses include a detail message:

```json
{
  "detail": "Error message"
}
```

## CORS

The API supports Cross-Origin Resource Sharing (CORS) to allow requests from the frontend application. During development, all origins are allowed.
