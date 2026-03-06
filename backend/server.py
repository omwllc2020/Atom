from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import asyncio
import base64
import aiofiles
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'fallback_secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Video/Image storage directory
MEDIA_DIR = ROOT_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None  # For code context

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str

class VideoGenRequest(BaseModel):
    prompt: str
    size: str = "1280x720"  # 1280x720, 1792x1024, 1024x1792, 1024x1024
    duration: int = 4  # 4, 8, or 12 seconds

class VideoGenResponse(BaseModel):
    video_id: str
    status: str
    video_url: Optional[str] = None

class ImageGenRequest(BaseModel):
    prompt: str

class ImageGenResponse(BaseModel):
    image_id: str
    image_data: str  # base64
    text_response: Optional[str] = None

class SiteCloneRequest(BaseModel):
    url: str

class SiteCloneResponse(BaseModel):
    clone_id: str
    status: str
    code: Optional[str] = None
    preview_url: Optional[str] = None

class ConversationResponse(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "created_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user_data.email, name=user_data.name, created_at=now)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ==================== CHAT/CODE GENERATION ====================

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    conversation_id = request.conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Get existing conversation or create new
    conversation = await db.conversations.find_one({"id": conversation_id, "user_id": current_user["id"]}, {"_id": 0})
    
    if not conversation:
        conversation = {
            "id": conversation_id,
            "user_id": current_user["id"],
            "title": request.message[:50] + "..." if len(request.message) > 50 else request.message,
            "messages": [],
            "created_at": now,
            "updated_at": now
        }
    
    # Build system message for coding assistant
    system_message = """You are an expert AI coding assistant called 'Forge AI'. You help developers with:
- Writing clean, efficient code in any language
- Debugging and fixing issues
- Explaining complex concepts
- Code reviews and best practices
- Architecture and design patterns

Always provide clear, well-structured code with explanations. Use markdown for code blocks.
If the user provides code context, analyze it and provide relevant suggestions."""

    if request.context:
        system_message += f"\n\nCode context provided by user:\n```\n{request.context}\n```"
    
    # Initialize chat
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"forge_{conversation_id}",
        system_message=system_message
    )
    chat.with_model("openai", "gpt-5.2")
    
    # Build message history for context
    for msg in conversation.get("messages", [])[-10:]:  # Last 10 messages
        if msg["role"] == "user":
            await chat.send_message(UserMessage(text=msg["content"]))
        # Note: We're just building context, not expecting responses here
    
    # Send current message
    user_msg = UserMessage(text=request.message)
    response = await chat.send_message(user_msg)
    
    # Store messages
    conversation["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": now
    })
    conversation["messages"].append({
        "role": "assistant", 
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    conversation["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update in DB
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": conversation},
        upsert=True
    )
    
    return ChatResponse(
        response=response,
        conversation_id=conversation_id,
        message_id=message_id
    )

@api_router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(current_user: dict = Depends(get_current_user)):
    conversations = await db.conversations.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(50)
    
    return [ConversationResponse(**conv) for conv in conversations]

@api_router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    conversation = await db.conversations.find_one(
        {"id": conversation_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse(**conversation)

@api_router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.conversations.delete_one({"id": conversation_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted"}

# ==================== VIDEO GENERATION (SORA 2) ====================

video_generation_status = {}

async def generate_video_task(video_id: str, prompt: str, size: str, duration: int, user_id: str):
    """Background task for video generation"""
    from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
    
    try:
        video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
        output_path = MEDIA_DIR / f"{video_id}.mp4"
        
        video_bytes = video_gen.text_to_video(
            prompt=prompt,
            model="sora-2",
            size=size,
            duration=duration,
            max_wait_time=600
        )
        
        if video_bytes:
            video_gen.save_video(video_bytes, str(output_path))
            video_generation_status[video_id] = {
                "status": "completed",
                "video_url": f"/api/media/video/{video_id}"
            }
            
            # Store in DB
            await db.video_generations.update_one(
                {"id": video_id},
                {"$set": {"status": "completed", "video_path": str(output_path)}}
            )
        else:
            video_generation_status[video_id] = {"status": "failed", "error": "Video generation failed"}
            await db.video_generations.update_one(
                {"id": video_id},
                {"$set": {"status": "failed"}}
            )
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        video_generation_status[video_id] = {"status": "failed", "error": str(e)}
        await db.video_generations.update_one(
            {"id": video_id},
            {"$set": {"status": "failed", "error": str(e)}}
        )

@api_router.post("/video/generate", response_model=VideoGenResponse)
async def generate_video(request: VideoGenRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    video_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Validate parameters
    valid_sizes = ["1280x720", "1792x1024", "1024x1792", "1024x1024"]
    valid_durations = [4, 8, 12]
    
    if request.size not in valid_sizes:
        raise HTTPException(status_code=400, detail=f"Invalid size. Must be one of: {valid_sizes}")
    if request.duration not in valid_durations:
        raise HTTPException(status_code=400, detail=f"Invalid duration. Must be one of: {valid_durations}")
    
    # Store initial record
    await db.video_generations.insert_one({
        "id": video_id,
        "user_id": current_user["id"],
        "prompt": request.prompt,
        "size": request.size,
        "duration": request.duration,
        "status": "processing",
        "created_at": now
    })
    
    video_generation_status[video_id] = {"status": "processing"}
    
    # Start background task
    background_tasks.add_task(
        generate_video_task, video_id, request.prompt, request.size, request.duration, current_user["id"]
    )
    
    return VideoGenResponse(video_id=video_id, status="processing")

@api_router.get("/video/status/{video_id}", response_model=VideoGenResponse)
async def get_video_status(video_id: str, current_user: dict = Depends(get_current_user)):
    # Check in-memory status first
    if video_id in video_generation_status:
        status_info = video_generation_status[video_id]
        return VideoGenResponse(
            video_id=video_id,
            status=status_info.get("status", "unknown"),
            video_url=status_info.get("video_url")
        )
    
    # Check DB
    record = await db.video_generations.find_one(
        {"id": video_id, "user_id": current_user["id"]},
        {"_id": 0}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_url = f"/api/media/video/{video_id}" if record.get("status") == "completed" else None
    return VideoGenResponse(video_id=video_id, status=record["status"], video_url=video_url)

@api_router.get("/media/video/{video_id}")
async def get_video(video_id: str):
    video_path = MEDIA_DIR / f"{video_id}.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video_path, media_type="video/mp4")

@api_router.get("/videos")
async def get_user_videos(current_user: dict = Depends(get_current_user)):
    videos = await db.video_generations.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    for video in videos:
        if video.get("status") == "completed":
            video["video_url"] = f"/api/media/video/{video['id']}"
    
    return videos

# ==================== IMAGE GENERATION (NANO BANANA) ====================

@api_router.post("/image/generate", response_model=ImageGenResponse)
async def generate_image(request: ImageGenRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    image_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"image_{image_id}",
            system_message="You are a helpful AI assistant that creates images based on descriptions."
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=f"Create an image: {request.prompt}")
        text_response, images = await chat.send_message_multimodal_response(msg)
        
        if not images:
            raise HTTPException(status_code=500, detail="Image generation failed - no images returned")
        
        image_data = images[0]["data"]  # Already base64 encoded
        
        # Save to file for persistence
        image_bytes = base64.b64decode(image_data)
        image_path = MEDIA_DIR / f"{image_id}.png"
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(image_bytes)
        
        # Store in DB
        await db.image_generations.insert_one({
            "id": image_id,
            "user_id": current_user["id"],
            "prompt": request.prompt,
            "image_path": str(image_path),
            "text_response": text_response,
            "created_at": now
        })
        
        return ImageGenResponse(
            image_id=image_id,
            image_data=image_data,
            text_response=text_response
        )
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

@api_router.get("/media/image/{image_id}")
async def get_image(image_id: str):
    image_path = MEDIA_DIR / f"{image_id}.png"
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path, media_type="image/png")

@api_router.get("/images")
async def get_user_images(current_user: dict = Depends(get_current_user)):
    images = await db.image_generations.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    for img in images:
        img["image_url"] = f"/api/media/image/{img['id']}"
    
    return images

# ==================== SITE CLONER ====================

@api_router.post("/clone/site", response_model=SiteCloneResponse)
async def clone_site(request: SiteCloneRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    
    clone_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    try:
        # Fetch the page HTML with SSL verification disabled for broader compatibility
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            response = await client.get(request.url)
            page_html = response.text[:5000]  # Limit to first 5000 chars
        
        # Use AI to generate code based on description
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"clone_{clone_id}",
            system_message="""You are an expert web developer. When given a URL or description, generate clean, modern HTML/CSS/JS code that recreates the website design. 
Use Tailwind CSS classes for styling. Make the code production-ready with:
- Responsive design
- Modern aesthetics
- Clean, well-structured code
Return ONLY the complete HTML code, no explanations."""
        )
        chat.with_model("openai", "gpt-5.2")
        
        msg = UserMessage(text=f"""Analyze this website and create a modern clone of it.
URL: {request.url}

Here's a snippet of the HTML structure:
{page_html}

Generate a complete, standalone HTML file with embedded Tailwind CSS (via CDN) that recreates this website's design and layout. Make it responsive and visually appealing.""")
        
        generated_code = await chat.send_message(msg)
        
        # Clean up the code (remove markdown code blocks if present)
        if "```html" in generated_code:
            generated_code = generated_code.split("```html")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
        
        # Save the generated code
        clone_path = MEDIA_DIR / f"{clone_id}.html"
        async with aiofiles.open(clone_path, 'w') as f:
            await f.write(generated_code)
        
        # Store in DB
        await db.site_clones.insert_one({
            "id": clone_id,
            "user_id": current_user["id"],
            "original_url": request.url,
            "clone_path": str(clone_path),
            "status": "completed",
            "created_at": now
        })
        
        return SiteCloneResponse(
            clone_id=clone_id,
            status="completed",
            code=generated_code,
            preview_url=f"/api/clone/preview/{clone_id}"
        )
        
    except Exception as e:
        logger.error(f"Site clone error: {e}")
        raise HTTPException(status_code=500, detail=f"Site cloning failed: {str(e)}")

@api_router.get("/clone/preview/{clone_id}")
async def preview_clone(clone_id: str):
    clone_path = MEDIA_DIR / f"{clone_id}.html"
    if not clone_path.exists():
        raise HTTPException(status_code=404, detail="Clone not found")
    return FileResponse(clone_path, media_type="text/html")

@api_router.get("/clones")
async def get_user_clones(current_user: dict = Depends(get_current_user)):
    clones = await db.site_clones.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "clone_path": 0}
    ).sort("created_at", -1).to_list(50)
    
    for clone in clones:
        clone["preview_url"] = f"/api/clone/preview/{clone['id']}"
    
    return clones

# ==================== STATUS ====================

@api_router.get("/")
async def root():
    return {"message": "Forge AI API is running", "version": "1.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
