from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Secret key for JWT
SECRET_KEY = "280520063d4"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Fake database
fake_users_db = {
    "admin": {
        "username": "admin",
        "password": pwd_context.hash("admin123"),  # Hashed password
        "role": "admin"
    },
    "user": {
        "username": "user",
        "password": pwd_context.hash("user123"),  # Hashed password
        "role": "user"
    }
}

# Authenticate user
def authenticate_user(username: str, password: str):
    """
    Authenticate a user by username and password.

    Args:
        username (str): The username to authenticate.
        password (str): The plain text password to verify.

    Returns:
        dict or None: The user dictionary if authentication is successful, otherwise None.
    """
    user = fake_users_db.get(username)
    if not user or not pwd_context.verify(password, user["password"]):
        return None
    return user

# Create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Create a JWT access token.

    Args:
        data (dict): The data to encode in the token (e.g., user info).
        expires_delta (timedelta, optional): The time until the token expires. Defaults to 15 minutes.

    Returns:
        str: The encoded JWT token as a string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Render the login page.

    Args:
        request (Request): The incoming HTTP request.

    Returns:
        TemplateResponse: The rendered login.html template.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and return an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing username and password.

    Raises:
        HTTPException: If authentication fails.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Include the user's role in the token
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}


from fastapi import Depends

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Retrieve the current user from the JWT token.

    Args:
        token (str): The JWT token from the Authorization header.

    Raises:
        HTTPException: If the token is invalid or missing required fields.

    Returns:
        dict: A dictionary containing the username and role of the user.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"username": username, "role": role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def admin_required(current_user: dict = Depends(get_current_user)):
    """
    Dependency to ensure the current user is an admin.

    Args:
        current_user (dict): The current user dictionary, injected by Depends(get_current_user).

    Raises:
        HTTPException: If the user is not an admin.

    Returns:
        dict: The current user dictionary if the user is an admin.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user