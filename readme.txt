
## Project Structure
- `main.py` : Main FastAPI application (API endpoints, web pages)
- `login.py` : Handles authentication (login, JWT token, user roles)
- `backend/models.py` : SQLAlchemy ORM models (Contest, Solver, Problem, Standing)
- `backend/sign_url.py` : Utility for signing Codeforces API requests
- `templates/` : HTML templates (home.html, login.html, etc.)
- `static/` : Static files (CSS, JS)
- `contests.db` : SQLite database

## Features
- View contests and standings
- View top problem solvers
- Admin login and problem management
- Role-based access (admin/user)
- Update contests and problems from Codeforces

## Usage
1. Install dependencies:
2. Launch the server (see above).
3. Open your browser at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Admin
- Login as admin to access problem update features.
- Default admin credentials (if using the example):  
  - Username: `admin`  
  - Password: `admin123`

---