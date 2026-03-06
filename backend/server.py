from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Request
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

# Stripe API Key
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# Super Admin Configuration
SUPER_ADMIN_EMAIL = "Antoniohoshaw6@gmail.com"

# Agent Definitions with System Prompts
AGENT_CONFIGS = {
    "nova": {
        "name": "Nova",
        "role": "Lead Architect & Developer",
        "capabilities": ["Full-stack development", "API design", "Database architecture", "Code optimization"],
        "system_prompt": """You are Nova, the Lead Architect & Developer agent in the ATOM Core system.

Your expertise:
- Full-stack application development (frontend & backend)
- API design and REST/GraphQL architecture
- Database modeling and optimization (SQL, NoSQL)
- Clean code principles and design patterns
- Performance optimization and scalability

Guidelines:
- Write production-ready, maintainable code
- Follow best practices for the language/framework being used
- Explain architectural decisions clearly
- Suggest improvements when you see anti-patterns
- Use proper error handling and edge case management

When writing code:
- Always use markdown code blocks with language identifiers
- Include comments for complex logic
- Consider security implications
- Think about testability"""
    },
    "forge": {
        "name": "Forge",
        "role": "Infrastructure & DevOps",
        "capabilities": ["CI/CD pipelines", "Container orchestration", "Cloud deployment", "System automation"],
        "system_prompt": """You are Forge, the Infrastructure & DevOps agent in the ATOM Core system.

Your expertise:
- Docker and Kubernetes container orchestration
- CI/CD pipeline design (GitHub Actions, Jenkins, GitLab CI)
- Cloud platforms (AWS, GCP, Azure)
- Infrastructure as Code (Terraform, Pulumi)
- System monitoring and observability
- Automated deployment strategies

Guidelines:
- Prioritize reliability and reproducibility
- Implement proper secrets management
- Design for horizontal scaling
- Include health checks and rollback strategies
- Document deployment procedures

When providing solutions:
- Use markdown code blocks for configs (yaml, docker, terraform)
- Consider cost optimization
- Implement proper logging and monitoring
- Think about disaster recovery"""
    },
    "sentinel": {
        "name": "Sentinel",
        "role": "Security & Trust",
        "capabilities": ["Authentication systems", "Encryption", "Vulnerability scanning", "Compliance"],
        "system_prompt": """You are Sentinel, the Security & Trust agent in the ATOM Core system.

Your expertise:
- Authentication and authorization (OAuth, JWT, RBAC)
- Encryption and cryptography best practices
- Security vulnerability assessment (OWASP Top 10)
- Secure coding practices
- Compliance frameworks (SOC2, GDPR, HIPAA)
- Penetration testing methodologies

Guidelines:
- Always assume zero trust
- Never expose sensitive data in logs or responses
- Use parameterized queries to prevent injection
- Implement proper input validation
- Follow principle of least privilege

When providing solutions:
- Highlight security implications
- Suggest additional hardening measures
- Include audit logging considerations
- Consider both known and emerging threats"""
    },
    "atlas": {
        "name": "Atlas",
        "role": "Analytics & Intelligence",
        "capabilities": ["Data analysis", "Metrics dashboards", "A/B testing", "Performance optimization"],
        "system_prompt": """You are Atlas, the Analytics & Intelligence agent in the ATOM Core system.

Your expertise:
- Data analysis and visualization
- Metrics design and KPI definition
- A/B testing and experimentation frameworks
- Database query optimization
- Machine learning model integration
- Real-time analytics pipelines

Guidelines:
- Focus on actionable insights
- Design for statistical significance
- Consider data privacy and anonymization
- Optimize for query performance
- Make dashboards intuitive and informative

When providing solutions:
- Include sample queries and visualizations
- Explain statistical concepts clearly
- Consider edge cases in data
- Think about data freshness and latency"""
    },
    "pulse": {
        "name": "Pulse",
        "role": "Growth & Marketing",
        "capabilities": ["Campaign automation", "User acquisition", "Branding", "Content strategy"],
        "system_prompt": """You are Pulse, the Growth & Marketing agent in the ATOM Core system.

Your expertise:
- Marketing automation and email campaigns
- User acquisition and retention strategies
- Brand identity and messaging
- Content strategy and SEO optimization
- Social media integration
- Conversion funnel optimization

Guidelines:
- Focus on user engagement and conversion
- Write compelling copy that converts
- Consider brand consistency
- Design for A/B testing
- Think about user psychology

When providing solutions:
- Include marketing copy examples
- Suggest tracking and attribution
- Consider multi-channel strategies
- Focus on measurable outcomes"""
    }
}

# Mode Configurations
MODE_CONFIGS = {
    "e1": {
        "name": "E-1",
        "description": "Stable & thorough",
        "temperature": 0.7,
        "modifier": "Be thorough and explain your reasoning. Focus on stability and correctness."
    },
    "e2": {
        "name": "E-2", 
        "description": "Thorough & Relentless",
        "temperature": 0.8,
        "modifier": "Be extremely thorough. Explore multiple approaches. Don't give up easily - keep iterating until the solution is optimal."
    },
    "prototype": {
        "name": "Prototype",
        "description": "Experimental Agent",
        "temperature": 0.9,
        "modifier": "Be creative and experimental. Try unconventional approaches. Prioritize innovation over convention."
    },
    "mobile": {
        "name": "Mobile",
        "description": "Agent for mobile apps",
        "temperature": 0.7,
        "modifier": "Focus on mobile-first design patterns. Consider touch interfaces, responsive layouts, offline capabilities, and mobile performance optimization."
    }
}

# Subscription Plans (Replit-style pricing)
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0.0,
        "credits_monthly": 10.0,
        "features": {
            "chat_messages": 50,
            "code_executions": 20,
            "video_generations": 2,
            "image_generations": 10,
            "agents": ["nova"],
            "modes": ["e1"],
            "ultra_thinking": False,
            "priority_support": False
        }
    },
    "core": {
        "name": "Core",
        "price_monthly": 20.0,
        "credits_monthly": 25.0,
        "features": {
            "chat_messages": 500,
            "code_executions": 200,
            "video_generations": 10,
            "image_generations": 50,
            "agents": ["nova", "forge", "sentinel", "atlas", "pulse"],
            "modes": ["e1", "e2"],
            "ultra_thinking": True,
            "priority_support": False
        }
    },
    "pro": {
        "name": "Pro",
        "price_monthly": 40.0,
        "credits_monthly": 50.0,
        "features": {
            "chat_messages": 2000,
            "code_executions": 500,
            "video_generations": 25,
            "image_generations": 150,
            "agents": ["nova", "forge", "sentinel", "atlas", "pulse"],
            "modes": ["e1", "e2", "prototype", "mobile"],
            "ultra_thinking": True,
            "priority_support": True
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 99.0,
        "credits_monthly": -1,
        "features": {
            "chat_messages": -1,
            "code_executions": -1,
            "video_generations": -1,
            "image_generations": -1,
            "agents": ["nova", "forge", "sentinel", "atlas", "pulse"],
            "modes": ["e1", "e2", "prototype", "mobile"],
            "ultra_thinking": True,
            "priority_support": True,
            "dedicated_support": True
        }
    }
}

# Credit Packages for top-ups (Replit-style)
CREDIT_PACKAGES = {
    "small": {"name": "Small", "credits": 10.0, "price": 5.0},
    "medium": {"name": "Medium", "credits": 25.0, "price": 10.0},
    "large": {"name": "Large", "credits": 50.0, "price": 18.0},
    "xlarge": {"name": "XL", "credits": 100.0, "price": 30.0}
}

# Credit Costs per action (Replit-style)
CREDIT_COSTS = {
    "chat_message": 0.10,
    "chat_ultra_thinking": 0.15,
    "code_execution": 0.05,
    "video_generation": 2.50,
    "image_generation": 0.25,
    "agent_checkpoint": 0.25,
    "site_clone": 1.0
}

# Create the main app
app = FastAPI(title="ATOM AI Platform", version="2.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Media storage directory
MEDIA_DIR = ROOT_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# Uploads directory for user files
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

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
    role: str = "user"
    credits: float = 10.0
    is_super_admin: bool = False
    subscription: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Subscription Models
class SubscriptionPlan(BaseModel):
    id: str
    name: str
    price_monthly: float
    credits_monthly: int
    features: Dict[str, Any]

class UsageStats(BaseModel):
    chat_messages: int = 0
    code_executions: int = 0
    video_generations: int = 0
    image_generations: int = 0
    credits_used: float = 0.0
    period_start: str
    period_end: str

class UsageLogEntry(BaseModel):
    action: str
    agent: Optional[str] = None
    mode: Optional[str] = None
    credits_used: float
    success: bool
    created_at: str

class UserPreferences(BaseModel):
    default_agent: str = "nova"
    default_mode: str = "e1"
    ultra_thinking: bool = False
    theme: str = "dark"

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
    agent: Optional[str] = "nova"  # nova, forge, sentinel, atlas, pulse
    mode: Optional[str] = "e1"  # e1, e2, prototype, mobile
    ultra_thinking: bool = False

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

def is_super_admin(email: str) -> bool:
    """Check if user is super admin based on email"""
    return email.lower() == SUPER_ADMIN_EMAIL.lower()

def get_user_role(email: str) -> str:
    """Get user role based on email"""
    return "super_admin" if is_super_admin(email) else "user"

def get_user_credits(email: str) -> float:
    """Get user credits - -1 for super admin (unlimited)"""
    return -1 if is_super_admin(email) else 10.0

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        # Add computed fields
        user["role"] = get_user_role(user.get("email", ""))
        user["is_super_admin"] = is_super_admin(user.get("email", ""))
        # -1 credits indicates unlimited for super admin
        if user["is_super_admin"]:
            user["credits"] = -1
        else:
            user["credits"] = user.get("credits", 10.0)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def require_admin(current_user: dict = Depends(get_current_user)):
    """Middleware to require super admin access"""
    if not current_user.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# ==================== USAGE & CREDITS HELPERS ====================

async def log_usage(user_id: str, action: str, agent: str = None, mode: str = None, 
                    credits_used: float = 0, success: bool = True, metadata: dict = None):
    """Log usage for tracking and analytics"""
    log_entry = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "action": action,
        "agent": agent,
        "mode": mode,
        "credits_used": credits_used,
        "success": success,
        "metadata": metadata or {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.usage_logs.insert_one(log_entry)
    
    # Update user's usage counters
    usage_field = f"usage.{action}s"
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {usage_field: 1, "usage.credits_used": credits_used}}
    )

async def check_and_deduct_credits(user: dict, action: str, extra_cost: float = 0) -> bool:
    """Check if user has enough credits and deduct them"""
    if user.get("is_super_admin"):
        return True  # Super admin has unlimited
    
    base_cost = CREDIT_COSTS.get(action, 0)
    total_cost = base_cost + extra_cost
    
    current_credits = user.get("credits", 0)
    if current_credits < total_cost:
        return False
    
    # Deduct credits
    await db.users.update_one(
        {"id": user["id"]},
        {"$inc": {"credits": -total_cost}}
    )
    return True

async def check_feature_access(user: dict, feature: str) -> bool:
    """Check if user has access to a feature based on their plan"""
    if user.get("is_super_admin"):
        return True
    
    plan_id = user.get("subscription", {}).get("plan", "free")
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
    
    # Check specific feature access
    if feature in ["agents", "modes"]:
        return True  # All plans have some agents/modes
    
    return plan["features"].get(feature, False)

async def check_usage_limit(user: dict, action: str) -> bool:
    """Check if user is within usage limits for their plan"""
    if user.get("is_super_admin"):
        return True
    
    plan_id = user.get("subscription", {}).get("plan", "free")
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
    
    limit = plan["features"].get(action, 0)
    if limit == -1:  # Unlimited
        return True
    
    current_usage = user.get("usage", {}).get(action, 0)
    return current_usage < limit

def get_period_dates():
    """Get current billing period start and end dates"""
    now = datetime.now(timezone.utc)
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = period_start.replace(month=period_start.month % 12 + 1)
    if period_start.month == 12:
        next_month = next_month.replace(year=period_start.year + 1)
    period_end = next_month - timedelta(seconds=1)
    return period_start.isoformat(), period_end.isoformat()

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    period_start, period_end = get_period_dates()
    
    # Determine role and credits based on email
    role = get_user_role(user_data.email)
    is_admin = is_super_admin(user_data.email)
    credits = -1 if is_admin else 10.0  # -1 indicates unlimited
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": role,
        "credits": credits,
        "is_super_admin": is_admin,
        "subscription": {
            "plan": "enterprise" if is_admin else "free",
            "status": "active",
            "current_period_start": period_start,
            "current_period_end": period_end
        },
        "usage": {
            "chat_messages": 0,
            "code_executions": 0,
            "video_generations": 0,
            "image_generations": 0,
            "credits_used": 0.0,
            "last_reset": now
        },
        "preferences": {
            "default_agent": "nova",
            "default_mode": "e1",
            "ultra_thinking": False,
            "theme": "dark"
        },
        "created_at": now,
        "updated_at": now
    }
    
    await db.users.insert_one(user_doc)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id, 
            email=user_data.email, 
            name=user_data.name, 
            created_at=now,
            role=role,
            credits=credits,
            is_super_admin=is_admin,
            subscription=user_doc["subscription"],
            usage=user_doc["usage"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Get role and credits
    role = get_user_role(user["email"])
    is_admin = is_super_admin(user["email"])
    credits = -1 if is_admin else user.get("credits", 10.0)  # -1 indicates unlimited
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"],
            role=role,
            credits=credits,
            is_super_admin=is_admin
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        created_at=current_user["created_at"],
        role=current_user.get("role", "user"),
        credits=current_user.get("credits", 10.0),
        is_super_admin=current_user.get("is_super_admin", False)
    )

@api_router.get("/user/credits")
async def get_user_credits_endpoint(current_user: dict = Depends(get_current_user)):
    """Get current user's credit balance"""
    is_admin = current_user.get("is_super_admin", False)
    return {
        "credits": None if is_admin else current_user.get("credits", 10.0),
        "is_super_admin": is_admin,
        "unlimited": is_admin
    }

@api_router.get("/agents")
async def get_agents():
    """Get available agents and their capabilities"""
    return {
        "agents": [
            {
                "id": agent_id,
                "name": config["name"],
                "role": config["role"],
                "capabilities": config["capabilities"]
            }
            for agent_id, config in AGENT_CONFIGS.items()
        ],
        "modes": [
            {
                "id": mode_id,
                "name": config["name"],
                "description": config["description"]
            }
            for mode_id, config in MODE_CONFIGS.items()
        ]
    }

# ==================== USER PROFILE & USAGE ====================

@api_router.get("/user/usage")
async def get_user_usage(current_user: dict = Depends(get_current_user)):
    """Get user's usage statistics for current period"""
    period_start, period_end = get_period_dates()
    usage = current_user.get("usage", {})
    plan_id = current_user.get("subscription", {}).get("plan", "free")
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
    
    return {
        "usage": {
            "chat_messages": usage.get("chat_messages", 0),
            "code_executions": usage.get("code_executions", 0),
            "video_generations": usage.get("video_generations", 0),
            "image_generations": usage.get("image_generations", 0),
            "credits_used": usage.get("credits_used", 0.0)
        },
        "limits": {
            "chat_messages": plan["features"].get("chat_messages", 50),
            "code_executions": plan["features"].get("code_executions", 20),
            "video_generations": plan["features"].get("video_generations", 2),
            "image_generations": plan["features"].get("image_generations", 10)
        },
        "period": {
            "start": period_start,
            "end": period_end
        },
        "plan": plan_id,
        "is_unlimited": current_user.get("is_super_admin", False)
    }

@api_router.get("/user/usage/history")
async def get_usage_history(
    limit: int = 50,
    action: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user's usage history"""
    query = {"user_id": current_user["id"]}
    if action:
        query["action"] = action
    
    logs = await db.usage_logs.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"history": logs, "total": len(logs)}

@api_router.get("/user/preferences")
async def get_user_preferences(current_user: dict = Depends(get_current_user)):
    """Get user's preferences"""
    return current_user.get("preferences", {
        "default_agent": "nova",
        "default_mode": "e1",
        "ultra_thinking": False,
        "theme": "dark"
    })

@api_router.put("/user/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update user's preferences"""
    await db.users.update_one(
        {"id": current_user["id"]},
        {"$set": {
            "preferences": preferences.dict(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"status": "updated", "preferences": preferences.dict()}

# ==================== SUBSCRIPTION MANAGEMENT ====================

@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {
        "plans": [
            {
                "id": plan_id,
                "name": plan["name"],
                "price_monthly": plan["price_monthly"],
                "credits_monthly": plan["credits_monthly"],
                "features": plan["features"]
            }
            for plan_id, plan in SUBSCRIPTION_PLANS.items()
        ]
    }

@api_router.get("/subscription")
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's current subscription"""
    subscription = current_user.get("subscription", {
        "plan": "free",
        "status": "active"
    })
    plan_details = SUBSCRIPTION_PLANS.get(subscription.get("plan", "free"))
    
    return {
        "subscription": subscription,
        "plan_details": plan_details,
        "is_super_admin": current_user.get("is_super_admin", False),
        "credits": current_user.get("credits", 0),
        "credit_packages": CREDIT_PACKAGES
    }

# ==================== STRIPE PAYMENT ENDPOINTS ====================

class CheckoutRequest(BaseModel):
    package_id: Optional[str] = None  # For credit top-ups
    plan_id: Optional[str] = None  # For subscriptions
    origin_url: str

@api_router.post("/checkout/subscription")
async def create_subscription_checkout(
    request: Request,
    checkout_request: CheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe checkout session for subscription"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    
    if not checkout_request.plan_id or checkout_request.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    if checkout_request.plan_id == "free":
        raise HTTPException(status_code=400, detail="Cannot checkout free plan")
    
    plan = SUBSCRIPTION_PLANS[checkout_request.plan_id]
    amount = plan["price_monthly"]
    
    # Build URLs dynamically from frontend origin
    success_url = f"{checkout_request.origin_url}/workspace?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_request.origin_url}/workspace?payment=cancelled"
    
    # Initialize Stripe
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_req = CheckoutSessionRequest(
        amount=float(amount),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["id"],
            "type": "subscription",
            "plan_id": checkout_request.plan_id,
            "credits": str(plan["credits_monthly"])
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_req)
    
    # Create pending transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": current_user["id"],
        "type": "subscription",
        "plan_id": checkout_request.plan_id,
        "amount": amount,
        "currency": "usd",
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"checkout_url": session.url, "session_id": session.session_id}

@api_router.post("/checkout/credits")
async def create_credits_checkout(
    request: Request,
    checkout_request: CheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe checkout session for credit top-up"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
    
    if not checkout_request.package_id or checkout_request.package_id not in CREDIT_PACKAGES:
        raise HTTPException(status_code=400, detail="Invalid credit package")
    
    package = CREDIT_PACKAGES[checkout_request.package_id]
    amount = package["price"]
    credits = package["credits"]
    
    # Build URLs dynamically
    success_url = f"{checkout_request.origin_url}/workspace?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{checkout_request.origin_url}/workspace?payment=cancelled"
    
    # Initialize Stripe
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_req = CheckoutSessionRequest(
        amount=float(amount),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": current_user["id"],
            "type": "credits",
            "package_id": checkout_request.package_id,
            "credits": str(credits)
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_req)
    
    # Create pending transaction record
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "user_id": current_user["id"],
        "type": "credits",
        "package_id": checkout_request.package_id,
        "credits": credits,
        "amount": amount,
        "currency": "usd",
        "status": "pending",
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"checkout_url": session.url, "session_id": session.session_id}

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    request: Request,
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check payment status and update user credits/subscription"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    # Check if already processed
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already completed, return cached status
    if transaction.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "message": "Payment already processed"
        }
    
    # Initialize Stripe and check status
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction
    await db.payment_transactions.update_one(
        {"session_id": session_id},
        {"$set": {
            "status": status.status,
            "payment_status": status.payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # If payment successful, update user
    if status.payment_status == "paid" and transaction.get("payment_status") != "paid":
        user_id = transaction.get("user_id") or status.metadata.get("user_id")
        
        if transaction.get("type") == "subscription":
            plan_id = transaction.get("plan_id") or status.metadata.get("plan_id")
            plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
            period_start, period_end = get_period_dates()
            
            await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "subscription.plan": plan_id,
                    "subscription.status": "active",
                    "subscription.current_period_start": period_start,
                    "subscription.current_period_end": period_end,
                    "credits": plan["credits_monthly"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        elif transaction.get("type") == "credits":
            credits_to_add = float(transaction.get("credits") or status.metadata.get("credits", 0))
            await db.users.update_one(
                {"id": user_id},
                {"$inc": {"credits": credits_to_add}}
            )
        
        # Log the transaction
        await log_usage(
            user_id=user_id,
            action=f"payment_{transaction.get('type')}",
            credits_used=-float(transaction.get("credits", 0)),
            metadata={
                "session_id": session_id,
                "amount": transaction.get("amount"),
                "type": transaction.get("type")
            }
        )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update transaction based on webhook event
        if webhook_response.session_id:
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {"$set": {
                    "status": webhook_response.event_type,
                    "payment_status": webhook_response.payment_status,
                    "webhook_event_id": webhook_response.event_id,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Process successful payment
            if webhook_response.payment_status == "paid":
                transaction = await db.payment_transactions.find_one(
                    {"session_id": webhook_response.session_id},
                    {"_id": 0}
                )
                
                if transaction and transaction.get("payment_status") != "paid":
                    user_id = transaction.get("user_id") or webhook_response.metadata.get("user_id")
                    
                    if transaction.get("type") == "subscription":
                        plan_id = transaction.get("plan_id") or webhook_response.metadata.get("plan_id")
                        plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
                        period_start, period_end = get_period_dates()
                        
                        await db.users.update_one(
                            {"id": user_id},
                            {"$set": {
                                "subscription.plan": plan_id,
                                "subscription.status": "active",
                                "subscription.current_period_start": period_start,
                                "subscription.current_period_end": period_end,
                                "credits": plan["credits_monthly"]
                            }}
                        )
                    elif transaction.get("type") == "credits":
                        credits_to_add = float(transaction.get("credits") or webhook_response.metadata.get("credits", 0))
                        await db.users.update_one(
                            {"id": user_id},
                            {"$inc": {"credits": credits_to_add}}
                        )
        
        return {"received": True}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"received": True, "error": str(e)}

@api_router.get("/payment/history")
async def get_payment_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's payment history"""
    transactions = await db.payment_transactions.find(
        {"user_id": current_user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"transactions": transactions}

# ==================== ADMIN ENDPOINTS ====================

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    """Get platform statistics (admin only)"""
    total_users = await db.users.count_documents({})
    active_users = await db.users.count_documents({"subscription.status": "active"})
    premium_users = await db.users.count_documents({"subscription.plan": {"$in": ["pro", "enterprise"]}})
    
    total_conversations = await db.conversations.count_documents({})
    total_projects = await db.projects.count_documents({})
    total_videos = await db.video_generations.count_documents({})
    total_images = await db.image_generations.count_documents({})
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "premium": premium_users,
            "free": total_users - premium_users
        },
        "content": {
            "conversations": total_conversations,
            "projects": total_projects,
            "videos": total_videos,
            "images": total_images
        }
    }

@api_router.get("/admin/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(require_admin)
):
    """Get all users (admin only)"""
    users = await db.users.find(
        {},
        {"_id": 0, "password": 0}
    ).skip(skip).limit(limit).to_list(limit)
    
    total = await db.users.count_documents({})
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.get("/admin/users/{user_id}")
async def get_user_admin(user_id: str, admin: dict = Depends(require_admin)):
    """Get user details (admin only)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/admin/users/{user_id}")
async def update_user_admin(
    user_id: str,
    updates: Dict[str, Any],
    admin: dict = Depends(require_admin)
):
    """Update user (admin only)"""
    # Don't allow updating password or id directly
    updates.pop("password", None)
    updates.pop("id", None)
    updates.pop("_id", None)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": updates}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"status": "updated", "user_id": user_id}

@api_router.post("/admin/users/{user_id}/credits")
async def add_user_credits(
    user_id: str,
    amount: float,
    admin: dict = Depends(require_admin)
):
    """Add credits to user (admin only)"""
    result = await db.users.update_one(
        {"id": user_id},
        {"$inc": {"credits": amount}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log the credit addition
    await log_usage(
        user_id=user_id,
        action="admin_credit_add",
        credits_used=-amount,  # Negative because credits were added
        metadata={"added_by": admin["id"], "amount": amount}
    )
    
    return {"status": "credits_added", "amount": amount, "user_id": user_id}

@api_router.delete("/admin/users/{user_id}")
async def delete_user_admin(user_id: str, admin: dict = Depends(require_admin)):
    """Delete user (admin only)"""
    # Don't allow deleting super admin
    user = await db.users.find_one({"id": user_id})
    if user and is_super_admin(user.get("email", "")):
        raise HTTPException(status_code=403, detail="Cannot delete super admin")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Clean up user's data
    await db.conversations.delete_many({"user_id": user_id})
    await db.projects.delete_many({"user_id": user_id})
    await db.usage_logs.delete_many({"user_id": user_id})
    
    return {"status": "deleted", "user_id": user_id}

@api_router.get("/admin/usage")
async def get_platform_usage(
    days: int = 30,
    admin: dict = Depends(require_admin)
):
    """Get platform usage statistics (admin only)"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": cutoff.isoformat()}}},
        {"$group": {
            "_id": "$action",
            "count": {"$sum": 1},
            "total_credits": {"$sum": "$credits_used"}
        }}
    ]
    
    results = await db.usage_logs.aggregate(pipeline).to_list(100)
    
    return {
        "period_days": days,
        "usage_by_action": {r["_id"]: {"count": r["count"], "credits": r["total_credits"]} for r in results}
    }

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
    
    # Check credits
    if not await check_and_deduct_credits(current_user, "code_execution"):
        raise HTTPException(status_code=402, detail="Insufficient credits for code execution")
    
    language = request.language.lower()
    
    if language == 'python':
        output, error, success = execute_python(request.code)
    elif language in ['javascript', 'js']:
        output, error, success = execute_javascript(request.code)
    elif language == 'html':
        output = "HTML code ready for preview"
        error = None
        success = True
    else:
        output = ""
        error = f"Language '{language}' execution not supported yet. Supported: Python, JavaScript, HTML"
        success = False
    
    execution_time = time.time() - start_time
    
    # Log usage
    await log_usage(
        user_id=current_user["id"],
        action="code_execution",
        credits_used=CREDIT_COSTS["code_execution"],
        success=success,
        metadata={"language": language, "execution_time": execution_time}
    )
    
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

def build_agent_system_prompt(agent: str, mode: str, ultra_thinking: bool, context: Optional[str] = None) -> str:
    """Build the complete system prompt based on agent, mode, and settings"""
    agent_config = AGENT_CONFIGS.get(agent, AGENT_CONFIGS["nova"])
    mode_config = MODE_CONFIGS.get(mode, MODE_CONFIGS["e1"])
    
    # Start with agent's base prompt
    system_prompt = agent_config["system_prompt"]
    
    # Add mode modifier
    system_prompt += f"\n\nExecution Mode: {mode_config['name']}\n{mode_config['modifier']}"
    
    # Add ultra thinking if enabled
    if ultra_thinking:
        system_prompt += """

ULTRA THINKING MODE ACTIVATED:
- Break down complex problems into smaller steps
- Show your reasoning process explicitly
- Consider multiple approaches before settling on one
- Validate your assumptions
- Think about edge cases and potential issues
- Provide more detailed explanations"""
    
    # Add context if provided
    if context:
        system_prompt += f"\n\nProject context:\n{context}"
    
    return system_prompt

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    conversation_id = request.conversation_id or str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Check credits for non-super-admin users
    if not current_user.get("is_super_admin", False):
        user_credits = current_user.get("credits", 0)
        if user_credits <= 0:
            raise HTTPException(status_code=402, detail="Insufficient credits. Please upgrade your plan.")
    
    conversation = await db.conversations.find_one({"id": conversation_id, "user_id": current_user["id"]}, {"_id": 0})
    
    if not conversation:
        conversation = {
            "id": conversation_id,
            "user_id": current_user["id"],
            "title": request.message[:50] + "..." if len(request.message) > 50 else request.message,
            "messages": [],
            "agent": request.agent,
            "mode": request.mode,
            "created_at": now,
            "updated_at": now
        }
    
    # Build dynamic system prompt based on agent, mode, and settings
    system_message = build_agent_system_prompt(
        agent=request.agent or "nova",
        mode=request.mode or "e1",
        ultra_thinking=request.ultra_thinking,
        context=request.context
    )
    
    # Get agent config for session naming
    agent_config = AGENT_CONFIGS.get(request.agent or "nova", AGENT_CONFIGS["nova"])
    mode_config = MODE_CONFIGS.get(request.mode or "e1", MODE_CONFIGS["e1"])
    
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"atom_{agent_config['name'].lower()}_{conversation_id}",
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
    
    # Store messages with agent/mode metadata
    conversation["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": now
    })
    conversation["messages"].append({
        "role": "assistant", 
        "content": response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": request.agent,
        "mode": request.mode
    })
    conversation["updated_at"] = datetime.now(timezone.utc).isoformat()
    conversation["agent"] = request.agent
    conversation["mode"] = request.mode
    
    await db.conversations.update_one(
        {"id": conversation_id},
        {"$set": conversation},
        upsert=True
    )
    
    # Deduct credits for non-super-admin users
    credits_used = CREDIT_COSTS["chat_message"]
    if request.ultra_thinking:
        credits_used += CREDIT_COSTS["chat_ultra_thinking"]
    
    if not current_user.get("is_super_admin", False):
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$inc": {"credits": -credits_used}}
        )
    
    # Log usage
    await log_usage(
        user_id=current_user["id"],
        action="chat_message",
        agent=request.agent,
        mode=request.mode,
        credits_used=credits_used,
        success=True,
        metadata={"ultra_thinking": request.ultra_thinking, "conversation_id": conversation_id}
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

# ==================== IMAGE/VIDEO TO VIDEO (SORA 2) ====================

async def resize_image_to_match_video(image_path: str, size: str) -> str:
    """Resize image to match video dimensions"""
    from PIL import Image
    
    width, height = map(int, size.split('x'))
    
    with Image.open(image_path) as img:
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        # Resize to exact dimensions
        img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
        
        # Save as JPEG (better compatibility)
        resized_path = image_path.rsplit('.', 1)[0] + '_resized.jpg'
        img_resized.save(resized_path, 'JPEG', quality=95)
        
        return resized_path

async def generate_video_from_image_direct(video_id: str, prompt: str, image_path: str, size: str, duration: int) -> bool:
    """Generate video from image using direct API call"""
    import time
    
    try:
        # Resize image to match video dimensions
        resized_path = await resize_image_to_match_video(image_path, size)
        logger.info(f"Resized image saved to: {resized_path}")
        
        # Read image data
        with open(resized_path, 'rb') as f:
            image_data = f.read()
        
        # Make direct API call to emergent integrations
        async with httpx.AsyncClient(timeout=600.0) as client:
            # Step 1: Initiate video generation
            files = {
                'input_reference': ('image.jpg', image_data, 'image/jpeg')
            }
            data = {
                'prompt': prompt,
                'model': 'sora-2',
                'size': size,
                'seconds': str(duration)  # API uses 'seconds' not 'duration'
            }
            headers = {
                'Authorization': f'Bearer {EMERGENT_LLM_KEY}'
            }
            
            response = await client.post(
                'https://integrations.emergentagent.com/llm/openai/v1/videos',
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code != 200 and response.status_code != 202:
                logger.error(f"Video initiation failed: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            task_id = result.get('id') or result.get('task_id')
            
            if not task_id:
                logger.error(f"No task ID in response: {result}")
                return False
            
            logger.info(f"Video generation started with task ID: {task_id}")
            
            # Step 2: Poll for completion
            max_wait = 600  # 10 minutes
            poll_interval = 10
            elapsed = 0
            
            while elapsed < max_wait:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                
                status_response = await client.get(
                    f'https://integrations.emergentagent.com/llm/openai/v1/videos/{task_id}',
                    headers=headers
                )
                
                if status_response.status_code != 200:
                    continue
                
                status_data = status_response.json()
                status = status_data.get('status', '')
                
                logger.info(f"Video status: {status}")
                
                if status == 'completed' or status == 'succeeded':
                    # Get video content via separate endpoint
                    video_content_response = await client.get(
                        f'https://integrations.emergentagent.com/llm/openai/v1/videos/{task_id}/content',
                        headers=headers
                    )
                    
                    if video_content_response.status_code == 200:
                        output_path = MEDIA_DIR / f"{video_id}.mp4"
                        async with aiofiles.open(output_path, 'wb') as f:
                            await f.write(video_content_response.content)
                        logger.info(f"Video saved to {output_path}")
                        return True
                    else:
                        logger.error(f"Failed to download video: {video_content_response.status_code}")
                        return False
                
                elif status == 'failed' or status == 'error':
                    logger.error(f"Video generation failed: {status_data}")
                    return False
            
            logger.error("Video generation timed out")
            return False
            
    except Exception as e:
        logger.error(f"Direct video generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def generate_video_from_media_task(video_id: str, prompt: str, media_path: str, media_type: str, size: str, duration: int, user_id: str):
    """Background task for generating video from uploaded image/video"""
    from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration
    
    try:
        output_path = MEDIA_DIR / f"{video_id}.mp4"
        
        if media_type == "image":
            # Try direct API call first (workaround for library bug)
            success = await generate_video_from_image_direct(video_id, prompt, media_path, size, duration)
            
            if success:
                video_generation_status[video_id] = {
                    "status": "completed",
                    "video_url": f"/api/media/video/{video_id}"
                }
                await db.video_generations.update_one(
                    {"id": video_id},
                    {"$set": {"status": "completed", "video_path": str(output_path)}}
                )
                return
            
            # Fallback to library method (may not work)
            video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
            ext = media_path.split('.')[-1].lower()
            mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}
            mime_type = mime_map.get(ext, 'image/jpeg')
            
            video_bytes = video_gen.text_to_video(
                prompt=prompt,
                image_path=media_path,
                mime_type=mime_type,
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
                return
        else:
            # For video input, just use text-to-video with enhanced prompt
            video_gen = OpenAIVideoGeneration(api_key=EMERGENT_LLM_KEY)
            video_bytes = video_gen.text_to_video(
                prompt=f"Based on the style: {prompt}",
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
                return
        
        # If we got here, generation failed
        video_generation_status[video_id] = {"status": "failed", "error": "Video generation failed"}
        await db.video_generations.update_one({"id": video_id}, {"$set": {"status": "failed"}})
        
    except Exception as e:
        logger.error(f"Video from media generation error: {e}")
        video_generation_status[video_id] = {"status": "failed", "error": str(e)}
        await db.video_generations.update_one({"id": video_id}, {"$set": {"status": "failed", "error": str(e)}})

@api_router.post("/video/from-media")
async def generate_video_from_media(
    background_tasks: BackgroundTasks,
    prompt: str = Form(...),
    size: str = Form("1280x720"),
    duration: int = Form(4),
    media: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Generate video from uploaded image or video"""
    video_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Validate parameters
    valid_sizes = ["1280x720", "1792x1024", "1024x1792", "1024x1024"]
    valid_durations = [4, 8, 12]
    
    if size not in valid_sizes:
        raise HTTPException(status_code=400, detail=f"Invalid size. Must be one of: {valid_sizes}")
    if duration not in valid_durations:
        raise HTTPException(status_code=400, detail=f"Invalid duration. Must be one of: {valid_durations}")
    
    # Determine media type
    content_type = media.content_type or ""
    filename = media.filename or ""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    
    if content_type.startswith("image/") or ext in ["jpg", "jpeg", "png", "webp", "gif"]:
        media_type = "image"
        save_ext = ext if ext else "png"
    elif content_type.startswith("video/") or ext in ["mp4", "mov", "avi", "webm"]:
        media_type = "video"
        save_ext = ext if ext else "mp4"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload an image (jpg, png, webp) or video (mp4, mov)")
    
    # Save uploaded file
    media_path = UPLOADS_DIR / f"{video_id}_source.{save_ext}"
    async with aiofiles.open(media_path, 'wb') as f:
        content = await media.read()
        await f.write(content)
    
    # Store in DB
    await db.video_generations.insert_one({
        "id": video_id,
        "user_id": current_user["id"],
        "prompt": prompt,
        "size": size,
        "duration": duration,
        "source_type": media_type,
        "source_path": str(media_path),
        "status": "processing",
        "created_at": now
    })
    
    video_generation_status[video_id] = {"status": "processing"}
    
    # Start background task
    background_tasks.add_task(
        generate_video_from_media_task, 
        video_id, prompt, str(media_path), media_type, size, duration, current_user["id"]
    )
    
    return {
        "video_id": video_id,
        "status": "processing",
        "source_type": media_type,
        "message": f"Generating video from {media_type}. This may take a few minutes."
    }

@api_router.get("/uploads/{file_id}")
async def get_upload(file_id: str):
    """Serve uploaded files"""
    for ext in ["png", "jpg", "jpeg", "webp", "gif", "mp4", "mov", "avi", "webm"]:
        file_path = UPLOADS_DIR / f"{file_id}.{ext}"
        if file_path.exists():
            media_type = "image/" + ext if ext in ["png", "jpg", "jpeg", "webp", "gif"] else "video/" + ext
            return FileResponse(file_path, media_type=media_type)
    raise HTTPException(status_code=404, detail="File not found")

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
