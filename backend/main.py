from fastapi import FastAPI, HTTPException, Header, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB client
mongodb_client = None

# Pydantic Models
class UserCreate(BaseModel):
    uid: str
    email: EmailStr
    displayName: Optional[str] = ""
    photoURL: Optional[str] = ""

class UserUpdate(BaseModel):
    displayName: Optional[str] = None
    photoURL: Optional[str] = None

# Firebase Token Verification
async def verify_firebase_token(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No token provided"
        )
    
    try:
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format"
            )
        
        token = authorization.split("Bearer ")[1]
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
        
    except Exception as e:
        print(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        print("Firebase Admin initialized successfully")
    except Exception as e:
        print(f"Firebase Admin initialization error: {e}")
    
    mongodb_client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    app.state.db = mongodb_client[os.getenv("DATABASE_NAME", "your_database_name")]
    print("MongoDB connected successfully")
    
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()
        print("MongoDB connection closed")

# FastAPI app
app = FastAPI(
    title="Authentication API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    return {"message": "Server is running!"}

@app.post("/api/users", status_code=status.HTTP_200_OK)
async def create_or_update_user(user_data: UserCreate, request: Request):
    try:
        db = request.app.state.db
        users_collection = db.users
        
        if not user_data.uid or not user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="UID and email are required"
            )
        
        existing_user = await users_collection.find_one({"uid": user_data.uid})
        
        if existing_user:
            update_data = {
                "displayName": user_data.displayName or existing_user.get("displayName", ""),
                "photoURL": user_data.photoURL or existing_user.get("photoURL", ""),
                "lastLoginAt": datetime.utcnow()
            }
            
            await users_collection.update_one(
                {"uid": user_data.uid},
                {"$set": update_data}
            )
            
            updated_user = await users_collection.find_one({"uid": user_data.uid})
            user_response = {
                "uid": updated_user["uid"],
                "email": updated_user["email"],
                "displayName": updated_user["displayName"],
                "photoURL": updated_user["photoURL"],
                "createdAt": updated_user["createdAt"],
                "lastLoginAt": updated_user["lastLoginAt"]
            }
        else:
            new_user = {
                "uid": user_data.uid,
                "email": user_data.email,
                "displayName": user_data.displayName or "",
                "photoURL": user_data.photoURL or "",
                "createdAt": datetime.utcnow(),
                "lastLoginAt": datetime.utcnow()
            }
            
            await users_collection.insert_one(new_user)
            
            user_response = {
                "uid": new_user["uid"],
                "email": new_user["email"],
                "displayName": new_user["displayName"],
                "photoURL": new_user["photoURL"],
                "createdAt": new_user["createdAt"],
                "lastLoginAt": new_user["lastLoginAt"]
            }
        
        return {
            "message": "User saved successfully",
            "user": user_response
        }
        
    except Exception as e:
        print(f"Error saving user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save user"
        )

@app.get("/api/users/profile")
async def get_user_profile(
    request: Request,
    decoded_token: dict = Depends(verify_firebase_token)
):
    try:
        db = request.app.state.db
        users_collection = db.users
        
        user = await users_collection.find_one({"uid": decoded_token["uid"]})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user": {
                "uid": user["uid"],
                "email": user["email"],
                "displayName": user["displayName"],
                "photoURL": user["photoURL"],
                "createdAt": user["createdAt"],
                "lastLoginAt": user["lastLoginAt"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile"
        )

@app.put("/api/users/profile")
async def update_user_profile(
    user_update: UserUpdate,
    request: Request,
    decoded_token: dict = Depends(verify_firebase_token)
):
    try:
        db = request.app.state.db
        users_collection = db.users
        
        user = await users_collection.find_one({"uid": decoded_token["uid"]})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = {}
        if user_update.displayName is not None:
            update_data["displayName"] = user_update.displayName
        if user_update.photoURL is not None:
            update_data["photoURL"] = user_update.photoURL
        
        if update_data:
            await users_collection.update_one(
                {"uid": decoded_token["uid"]},
                {"$set": update_data}
            )
        
        updated_user = await users_collection.find_one({"uid": decoded_token["uid"]})
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "uid": updated_user["uid"],
                "email": updated_user["email"],
                "displayName": updated_user["displayName"],
                "photoURL": updated_user["photoURL"],
                "createdAt": updated_user["createdAt"],
                "lastLoginAt": updated_user["lastLoginAt"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@app.delete("/api/users/profile")
async def delete_user_account(
    request: Request,
    decoded_token: dict = Depends(verify_firebase_token)
):
    try:
        db = request.app.state.db
        users_collection = db.users
        
        await users_collection.delete_one({"uid": decoded_token["uid"]})
        firebase_auth.delete_user(decoded_token["uid"])
        
        return {"message": "User account deleted successfully"}
        
    except Exception as e:
        print(f"Error deleting user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user account"
        )

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)