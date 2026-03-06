from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import asyncio
import base64
import aiofiles
import httpx
import subprocess
import tempfile
import sys
import io
import traceback

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

# Media storage directory
MEDIA_DIR = ROOT_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# Projects directory
PROJECTS_DIR = ROOT_DIR / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)

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
    role: str
    content: str
    timestamp: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[str] = None
    project_id: Optional[str] = None
    auto_fix: bool = False

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    code_blocks: Optional[List[Dict[str, str]]] = None
    auto_fix_applied: bool = False

class VideoGenRequest(BaseModel):
    prompt: str
    size: str = "1280x720"
    duration: int = 4

class VideoGenResponse(BaseModel):
    video_id: str
    status: str
    video_url: Optional[str] = None

class ImageGenRequest(BaseModel):
    prompt: str

class ImageGenResponse(BaseModel):
    image_id: str
    image_data: str
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

# New Models for Code Execution & Projects
class CodeExecuteRequest(BaseModel):
    code: str
    language: str  # python, javascript, html
    project_id: Optional[str] = None

class CodeExecuteResponse(BaseModel):
    output: str
    error: Optional[str] = None
    execution_time: float
    success: bool

class AutoFixRequest(BaseModel):
    code: str
    language: str
    error: str
    project_id: Optional[str] = None

class AutoFixResponse(BaseModel):
    fixed_code: str
    explanation: str
    changes_made: List[str]
    success: bool

class ProjectFile(BaseModel):
    name: str
    path: str
    content: str
    language: str

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    files: List[Dict[str, Any]]
    created_at: str
    updated_at: str

class FileCreate(BaseModel):
    name: str
    content: str = ""
    language: Optional[str] = None

class FileUpdate(BaseModel):
    content: str

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

# ==================== CODE EXECUTION ====================

def detect_language(filename: str) -> str:
    """Detect programming language from filename"""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.md': 'markdown',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.sql': 'sql',
        '.sh': 'bash',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
    }
    ext = Path(filename).suffix.lower()
    return ext_map.get(ext, 'text')

def execute_python(code: str, timeout: int = 10) -> tuple:
    """Execute Python code safely"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        result = subprocess.run(
            [sys.executable, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir()
        )
        
        os.unlink(temp_file)
        
        output = result.stdout
        error = result.stderr if result.returncode != 0 else None
        
        return output, error, result.returncode == 0
        
    except subprocess.TimeoutExpired:
        return "", "Execution timed out (10s limit)", False
    except Exception as e:
        return "", str(e), False

def execute_javascript(code: str, timeout: int = 10) -> tuple:
    """Execute JavaScript code using Node.js"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir()
        )
        
        os.unlink(temp_file)
        
        output = result.stdout
        error = result.stderr if result.returncode != 0 else None
        
        return output, error, result.returncode == 0
        
    except subprocess.TimeoutExpired:
        return "", "Execution timed out (10s limit)", False
    except FileNotFoundError:
        return "", "Node.js not available", False
    except Exception as e:
        return "", str(e), False

@api_router.post("/code/execute", response_model=CodeExecuteResponse)
async def execute_code(request: CodeExecuteRequest, current_user: dict = Depends(get_current_user)):
    """Execute code and return output"""
    import time
    start_time = time.time()
    
    language = request.language.lower()
    
    if language == 'python':
        output, error, success = execute_python(request.code)
    elif language in ['javascript', 'js']:
        output, error, success = execute_javascript(request.code)
    elif language == 'html':
        # HTML doesn't need execution, just return it for preview
        output = "HTML code ready for preview"
        error = None
        success = True
    else:
        output = ""
        error = f"Language '{language}' execution not supported yet. Supported: Python, JavaScript, HTML"
        success = False
    
    execution_time = time.time() - start_time
    
    return CodeExecuteResponse(
        output=output,
        error=error,
        execution_time=execution_time,
        success=success
    )

# ==================== AUTO-FIX ====================

@api_router.post("/code/autofix", response_model=AutoFixResponse)
async def auto_fix_code(request: AutoFixRequest, current_user: dict = Depends(get_current_user)):
    """Automatically fix code errors using AI"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"autofix_{uuid.uuid4()}",
            system_message="""You are an expert code debugger. When given code with an error, you:
1. Identify the exact problem
2. Fix the code
3. Return ONLY the fixed code wrapped in ```language``` blocks
4. After the code, briefly explain what you fixed

Be concise. Fix the actual error, don't add unnecessary changes."""
        )
        chat.with_model("openai", "gpt-5.2")
        
        prompt = f"""Fix this {request.language} code that has an error:

```{request.language}
{request.code}
```

Error message:
{request.error}

Return the fixed code and a brief explanation."""
        
        response = await chat.send_message(UserMessage(text=prompt))
        
        # Extract code from response
        fixed_code = request.code  # Default to original
        if "```" in response:
            parts = response.split("```")
            for i, part in enumerate(parts):
                if i % 2 == 1:  # Code blocks are at odd indices
                    # Remove language identifier from first line
                    lines = part.strip().split('\n')
                    if lines[0].lower() in ['python', 'javascript', 'js', 'html', 'css', request.language.lower()]:
                        fixed_code = '\n'.join(lines[1:])
                    else:
                        fixed_code = part.strip()
                    break
        
        # Extract explanation
        explanation = response.split("```")[-1].strip() if "```" in response else response
        
        return AutoFixResponse(
            fixed_code=fixed_code,
            explanation=explanation,
            changes_made=["Auto-fixed based on error analysis"],
            success=True
        )
        
    except Exception as e:
        logger.error(f"Auto-fix error: {e}")
        return AutoFixResponse(
            fixed_code=request.code,
            explanation=f"Could not auto-fix: {str(e)}",
            changes_made=[],
            success=False
        )

# ==================== AUTO-FIX LOOP ====================

@api_router.post("/code/autofix-loop")
async def auto_fix_loop(request: CodeExecuteRequest, current_user: dict = Depends(get_current_user)):
    """Keep fixing code until it works (max 5 attempts)"""
    max_attempts = 5
    current_code = request.code
    language = request.language.lower()
    attempts = []
    
    for attempt in range(max_attempts):
        # Execute current code
        if language == 'python':
            output, error, success = execute_python(current_code)
        elif language in ['javascript', 'js']:
            output, error, success = execute_javascript(current_code)
        else:
            return {
                "success": False,
                "final_code": current_code,
                "output": "",
                "attempts": [{"error": f"Language '{language}' not supported for auto-fix loop"}],
                "total_attempts": 1
            }
        
        attempts.append({
            "attempt": attempt + 1,
            "success": success,
            "output": output[:500] if output else "",
            "error": error[:500] if error else None
        })
        
        if success:
            return {
                "success": True,
                "final_code": current_code,
                "output": output,
                "attempts": attempts,
                "total_attempts": attempt + 1
            }
        
        # Try to fix
        fix_request = AutoFixRequest(
            code=current_code,
            language=language,
            error=error or "Unknown error"
        )
        fix_response = await auto_fix_code(fix_request, current_user)
        
        if fix_response.success and fix_response.fixed_code != current_code:
            current_code = fix_response.fixed_code
        else:
            break
    
    return {
        "success": False,
        "final_code": current_code,
        "output": output if 'output' in dir() else "",
        "attempts": attempts,
        "total_attempts": len(attempts),
        "message": "Could not fix after maximum attempts"
    }

# ==================== PROJECT MANAGEMENT ====================

@api_router.post("/projects", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Create a new project"""
    project_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Create default files
    default_files = [
        {"name": "index.html", "content": "<!DOCTYPE html>\n<html>\n<head>\n  <title>My Project</title>\n  <link rel=\"stylesheet\" href=\"styles.css\">\n</head>\n<body>\n  <h1>Hello World</h1>\n  <script src=\"script.js\"></script>\n</body>\n</html>", "language": "html"},
        {"name": "styles.css", "content": "body {\n  font-family: Arial, sans-serif;\n  margin: 0;\n  padding: 20px;\n}", "language": "css"},
        {"name": "script.js", "content": "console.log('Hello from JavaScript!');", "language": "javascript"},
        {"name": "main.py", "content": "# Python code\nprint('Hello from Python!')", "language": "python"}
    ]
    
    project_doc = {
        "id": project_id,
        "user_id": current_user["id"],
        "name": project.name,
        "description": project.description,
        "files": default_files,
        "created_at": now,
        "updated_at": now
    }
    
    await db.projects.insert_one(project_doc)
    
    return ProjectResponse(**{k: v for k, v in project_doc.items() if k != "_id" and k != "user_id"})

@api_router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(current_user: dict = Depends(get_current_user)):
    """Get all user projects"""
    projects = await db.projects.find(
        {"user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    ).sort("updated_at", -1).to_list(100)
    
    return [ProjectResponse(**p) for p in projects]

@api_router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific project"""
    project = await db.projects.find_one(
        {"id": project_id, "user_id": current_user["id"]},
        {"_id": 0, "user_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(**project)

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project"""
    result = await db.projects.delete_one({"id": project_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}

@api_router.post("/projects/{project_id}/files")
async def add_file(project_id: str, file: FileCreate, current_user: dict = Depends(get_current_user)):
    """Add a file to project"""
    project = await db.projects.find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    language = file.language or detect_language(file.name)
    
    new_file = {
        "name": file.name,
        "content": file.content,
        "language": language
    }
    
    await db.projects.update_one(
        {"id": project_id},
        {
            "$push": {"files": new_file},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return new_file

@api_router.put("/projects/{project_id}/files/{filename}")
async def update_file(project_id: str, filename: str, file: FileUpdate, current_user: dict = Depends(get_current_user)):
    """Update a file in project"""
    project = await db.projects.find_one({"id": project_id, "user_id": current_user["id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find and update the file
    files = project.get("files", [])
    file_found = False
    for f in files:
        if f["name"] == filename:
            f["content"] = file.content
            file_found = True
            break
    
    if not file_found:
        raise HTTPException(status_code=404, detail="File not found")
    
    await db.projects.update_one(
        {"id": project_id},
        {
            "$set": {
                "files": files,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"status": "updated", "filename": filename}

@api_router.delete("/projects/{project_id}/files/{filename}")
async def delete_file(project_id: str, filename: str, current_user: dict = Depends(get_current_user)):
    """Delete a file from project"""
    result = await db.projects.update_one(
        {"id": project_id, "user_id": current_user["id"]},
        {
            "$pull": {"files": {"name": filename}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"status": "deleted", "filename": filename}

# ==================== CHAT/CODE GENERATION ====================

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    conversation_id = request.conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
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
    
    # Enhanced system message for coding assistant
    system_message = """You are ATOM, an expert AI coding assistant. You can:
- Write code in ANY programming language
- Debug and fix errors automatically
- Explain complex concepts clearly
- Adapt to new languages and frameworks
- Generate complete, working solutions

Guidelines:
- Always provide complete, runnable code
- Use markdown code blocks with language identifiers
- Explain your code briefly
- If you detect an error, fix it automatically
- Be concise but thorough

When writing code, always wrap it in proper markdown code blocks like:
```python
# code here
```"""

    if request.context:
        system_message += f"\n\nProject context:\n{request.context}"
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"atom_{conversation_id}",
        system_message=system_message
    )
    chat.with_model("openai", "gpt-5.2")
    
    user_msg = UserMessage(text=request.message)
    response = await chat.send_message(user_msg)
    
    # Extract code blocks
    code_blocks = []
    if "```" in response:
        parts = response.split("```")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                lines = part.strip().split('\n')
                lang = lines[0].lower() if lines else 'text'
                code = '\n'.join(lines[1:]) if len(lines) > 1 else part.strip()
                code_blocks.append({"language": lang, "code": code})
    
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
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": conversation},
        upsert=True
    )
    
    return ChatResponse(
        response=response,
        conversation_id=conversation_id,
        message_id=message_id,
        code_blocks=code_blocks if code_blocks else None,
        auto_fix_applied=False
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
            await db.video_generations.update_one(
                {"id": video_id},
                {"$set": {"status": "completed", "video_path": str(output_path)}}
            )
        else:
            video_generation_status[video_id] = {"status": "failed", "error": "Video generation failed"}
            await db.video_generations.update_one({"id": video_id}, {"$set": {"status": "failed"}})
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        video_generation_status[video_id] = {"status": "failed", "error": str(e)}
        await db.video_generations.update_one({"id": video_id}, {"$set": {"status": "failed", "error": str(e)}})

@api_router.post("/video/generate", response_model=VideoGenResponse)
async def generate_video(request: VideoGenRequest, background_tasks: BackgroundTasks, current_user: dict = Depends(get_current_user)):
    video_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    valid_sizes = ["1280x720", "1792x1024", "1024x1792", "1024x1024"]
    valid_durations = [4, 8, 12]
    
    if request.size not in valid_sizes:
        raise HTTPException(status_code=400, detail=f"Invalid size. Must be one of: {valid_sizes}")
    if request.duration not in valid_durations:
        raise HTTPException(status_code=400, detail=f"Invalid duration. Must be one of: {valid_durations}")
    
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
    background_tasks.add_task(generate_video_task, video_id, request.prompt, request.size, request.duration, current_user["id"])
    
    return VideoGenResponse(video_id=video_id, status="processing")

@api_router.get("/video/status/{video_id}", response_model=VideoGenResponse)
async def get_video_status(video_id: str, current_user: dict = Depends(get_current_user)):
    if video_id in video_generation_status:
        status_info = video_generation_status[video_id]
        return VideoGenResponse(
            video_id=video_id,
            status=status_info.get("status", "unknown"),
            video_url=status_info.get("video_url")
        )
    
    record = await db.video_generations.find_one({"id": video_id, "user_id": current_user["id"]}, {"_id": 0})
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
    videos = await db.video_generations.find({"user_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
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
        
        image_data = images[0]["data"]
        
        image_bytes = base64.b64decode(image_data)
        image_path = MEDIA_DIR / f"{image_id}.png"
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(image_bytes)
        
        await db.image_generations.insert_one({
            "id": image_id,
            "user_id": current_user["id"],
            "prompt": request.prompt,
            "image_path": str(image_path),
            "text_response": text_response,
            "created_at": now
        })
        
        return ImageGenResponse(image_id=image_id, image_data=image_data, text_response=text_response)
        
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
    images = await db.image_generations.find({"user_id": current_user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for img in images:
        img["image_url"] = f"/api/media/image/{img['id']}"
    return images

# ==================== SITE CLONER ====================

@api_router.post("/clone/site", response_model=SiteCloneResponse)
async def clone_site(request: SiteCloneRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    clone_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False, follow_redirects=True) as client:
            response = await client.get(request.url)
            page_html = response.text[:5000]
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"clone_{clone_id}",
            system_message="""You are an expert web developer. Generate clean, modern HTML/CSS/JS code that recreates the website design. 
Use Tailwind CSS via CDN. Make it responsive and production-ready.
Return ONLY the complete HTML code, no explanations."""
        )
        chat.with_model("openai", "gpt-5.2")
        
        msg = UserMessage(text=f"""Clone this website:
URL: {request.url}

HTML snippet:
{page_html}

Generate a complete, standalone HTML file with Tailwind CSS CDN.""")
        
        generated_code = await chat.send_message(msg)
        
        if "```html" in generated_code:
            generated_code = generated_code.split("```html")[1].split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1].split("```")[0]
        
        clone_path = MEDIA_DIR / f"{clone_id}.html"
        async with aiofiles.open(clone_path, 'w') as f:
            await f.write(generated_code)
        
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
    clones = await db.site_clones.find({"user_id": current_user["id"]}, {"_id": 0, "clone_path": 0}).sort("created_at", -1).to_list(50)
    for clone in clones:
        clone["preview_url"] = f"/api/clone/preview/{clone['id']}"
    return clones

# ==================== STATUS ====================

@api_router.get("/")
async def root():
    return {"message": "ATOM AI API is running", "version": "2.0.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include the router
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
