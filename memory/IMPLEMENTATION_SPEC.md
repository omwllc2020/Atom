# ATOM Core - Developer Implementation Specification

## Table of Contents
1. [System Overview](#system-overview)
2. [Database Schema](#database-schema)
3. [Backend API Routes](#backend-api-routes)
4. [Agent State Flow](#agent-state-flow)
5. [Admin Logic](#admin-logic)
6. [Premium Subscription Logic](#premium-subscription-logic)
7. [Browser Extension Architecture](#browser-extension-architecture)
8. [Security Considerations](#security-considerations)

---

## 1. System Overview

### Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                        ATOM Platform                             │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + Tailwind)                                    │
│  ├── Auth Pages (Login/Register)                                │
│  ├── Workspace (Chat, IDE, Video, Image, Clone)                 │
│  ├── Agent Selector Modal                                        │
│  ├── Admin Dashboard                                             │
│  └── Subscription Management                                     │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                               │
│  ├── Auth Service (JWT + Role-based)                            │
│  ├── Agent Orchestrator (ATOM Core)                             │
│  ├── Code Execution Engine                                       │
│  ├── Media Generation Service                                    │
│  ├── Subscription Service (Stripe)                               │
│  └── Usage Tracking Service                                      │
├─────────────────────────────────────────────────────────────────┤
│  Database (MongoDB)                                              │
│  ├── users                                                       │
│  ├── subscriptions                                               │
│  ├── usage_logs                                                  │
│  ├── conversations                                               │
│  ├── projects                                                    │
│  └── media_generations                                           │
├─────────────────────────────────────────────────────────────────┤
│  External Services                                               │
│  ├── OpenAI GPT-5.2 (Chat)                                      │
│  ├── Sora 2 (Video)                                             │
│  ├── Nano Banana (Image)                                         │
│  └── Stripe (Payments)                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack
- **Frontend**: React 18, TailwindCSS, Shadcn/UI, Monaco Editor, Framer Motion
- **Backend**: FastAPI, Python 3.11, Motor (async MongoDB)
- **Database**: MongoDB
- **Auth**: JWT with RBAC (Role-Based Access Control)
- **Payments**: Stripe Subscriptions
- **AI**: Emergent Integrations (GPT-5.2, Sora 2, Nano Banana)

---

## 2. Database Schema

### users
```javascript
{
  "_id": ObjectId,
  "id": String (UUID),           // Public ID
  "email": String,               // Unique, indexed
  "password": String,            // bcrypt hashed
  "name": String,
  "role": String,                // "user" | "premium" | "super_admin"
  "is_super_admin": Boolean,     // Computed from email
  "credits": Number,             // -1 for unlimited
  "subscription": {
    "plan": String,              // "free" | "pro" | "enterprise"
    "status": String,            // "active" | "canceled" | "past_due"
    "stripe_customer_id": String,
    "stripe_subscription_id": String,
    "current_period_start": DateTime,
    "current_period_end": DateTime,
    "cancel_at_period_end": Boolean
  },
  "usage": {
    "chat_messages": Number,     // Monthly count
    "code_executions": Number,
    "video_generations": Number,
    "image_generations": Number,
    "last_reset": DateTime       // Monthly reset date
  },
  "preferences": {
    "default_agent": String,     // "nova" | "forge" | "sentinel" | "atlas" | "pulse"
    "default_mode": String,      // "e1" | "e2" | "prototype" | "mobile"
    "ultra_thinking": Boolean,
    "theme": String              // "dark" | "light"
  },
  "created_at": DateTime,
  "updated_at": DateTime,
  "last_login": DateTime
}
```

### subscriptions
```javascript
{
  "_id": ObjectId,
  "id": String (UUID),
  "user_id": String,             // Reference to users.id
  "plan": String,                // "free" | "pro" | "enterprise"
  "status": String,              // "active" | "canceled" | "past_due" | "trialing"
  "stripe_customer_id": String,
  "stripe_subscription_id": String,
  "stripe_price_id": String,
  "current_period_start": DateTime,
  "current_period_end": DateTime,
  "cancel_at_period_end": Boolean,
  "canceled_at": DateTime,
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### usage_logs
```javascript
{
  "_id": ObjectId,
  "id": String (UUID),
  "user_id": String,
  "action": String,              // "chat" | "code_execute" | "video_gen" | "image_gen" | "clone"
  "agent": String,               // Which agent was used
  "mode": String,                // Which mode was active
  "credits_used": Number,
  "tokens_used": Number,         // For chat
  "duration_ms": Number,         // Execution time
  "success": Boolean,
  "error": String,               // If failed
  "metadata": Object,            // Action-specific data
  "created_at": DateTime
}
```

### conversations
```javascript
{
  "_id": ObjectId,
  "id": String (UUID),
  "user_id": String,
  "title": String,
  "agent": String,               // Last used agent
  "mode": String,                // Last used mode
  "messages": [
    {
      "role": String,            // "user" | "assistant"
      "content": String,
      "agent": String,           // Which agent responded
      "mode": String,
      "ultra_thinking": Boolean,
      "tokens_used": Number,
      "timestamp": DateTime
    }
  ],
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### projects
```javascript
{
  "_id": ObjectId,
  "id": String (UUID),
  "user_id": String,
  "name": String,
  "description": String,
  "files": [
    {
      "name": String,
      "content": String,
      "language": String
    }
  ],
  "execution_history": [
    {
      "file": String,
      "output": String,
      "error": String,
      "timestamp": DateTime
    }
  ],
  "created_at": DateTime,
  "updated_at": DateTime
}
```

### Indexes
```javascript
// users
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "id": 1 }, { unique: true })
db.users.createIndex({ "subscription.stripe_customer_id": 1 })

// usage_logs
db.usage_logs.createIndex({ "user_id": 1, "created_at": -1 })
db.usage_logs.createIndex({ "action": 1, "created_at": -1 })

// conversations
db.conversations.createIndex({ "user_id": 1, "updated_at": -1 })

// projects
db.projects.createIndex({ "user_id": 1, "updated_at": -1 })
```

---

## 3. Backend API Routes

### Authentication
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/auth/register | Create new user | Public |
| POST | /api/auth/login | Login, get JWT | Public |
| GET | /api/auth/me | Get current user | Required |
| POST | /api/auth/refresh | Refresh JWT token | Required |
| POST | /api/auth/logout | Invalidate token | Required |
| POST | /api/auth/forgot-password | Send reset email | Public |
| POST | /api/auth/reset-password | Reset with token | Public |

### Users & Credits
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/user/credits | Get credit balance | Required |
| GET | /api/user/usage | Get usage stats | Required |
| GET | /api/user/usage/history | Get usage history | Required |
| PUT | /api/user/preferences | Update preferences | Required |
| GET | /api/user/preferences | Get preferences | Required |

### Agents
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/agents | List all agents & modes | Public |
| GET | /api/agents/{agent_id} | Get agent details | Public |
| POST | /api/agents/orchestrate | Multi-agent task | Required |

### Chat
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/chat | Send message | Required |
| GET | /api/conversations | List conversations | Required |
| GET | /api/conversations/{id} | Get conversation | Required |
| DELETE | /api/conversations/{id} | Delete conversation | Required |
| POST | /api/conversations/{id}/fork | Fork conversation | Required |

### Code Execution
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/code/execute | Execute code | Required |
| POST | /api/code/autofix | Fix single error | Required |
| POST | /api/code/autofix-loop | Keep fixing | Required |
| POST | /api/code/analyze | Analyze code | Required |

### Projects
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/projects | Create project | Required |
| GET | /api/projects | List projects | Required |
| GET | /api/projects/{id} | Get project | Required |
| PUT | /api/projects/{id} | Update project | Required |
| DELETE | /api/projects/{id} | Delete project | Required |
| POST | /api/projects/{id}/files | Add file | Required |
| PUT | /api/projects/{id}/files/{name} | Update file | Required |
| DELETE | /api/projects/{id}/files/{name} | Delete file | Required |
| POST | /api/projects/{id}/export | Export as ZIP | Required |

### Media Generation
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /api/video/generate | Text to video | Required |
| POST | /api/video/from-media | Image/video to video | Required |
| GET | /api/video/status/{id} | Check status | Required |
| GET | /api/videos | List user videos | Required |
| POST | /api/image/generate | Generate image | Required |
| GET | /api/images | List user images | Required |
| POST | /api/clone/site | Clone website | Required |
| GET | /api/clones | List clones | Required |

### Subscriptions (Stripe)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/subscription | Get subscription | Required |
| GET | /api/subscription/plans | List available plans | Public |
| POST | /api/subscription/create-checkout | Create Stripe checkout | Required |
| POST | /api/subscription/create-portal | Create billing portal | Required |
| POST | /api/subscription/cancel | Cancel subscription | Required |
| POST | /api/subscription/resume | Resume subscription | Required |
| POST | /api/webhook/stripe | Stripe webhooks | Webhook |

### Admin (Super Admin Only)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/admin/users | List all users | Admin |
| GET | /api/admin/users/{id} | Get user details | Admin |
| PUT | /api/admin/users/{id} | Update user | Admin |
| DELETE | /api/admin/users/{id} | Delete user | Admin |
| POST | /api/admin/users/{id}/credits | Add credits | Admin |
| GET | /api/admin/stats | Platform statistics | Admin |
| GET | /api/admin/usage | Platform usage | Admin |
| POST | /api/admin/broadcast | Send announcement | Admin |

---

## 4. Agent State Flow

### Agent Selection Flow
```
┌─────────────────┐
│   User Opens    │
│   Workspace     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Load User      │
│  Preferences    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  Default Agent  │────▶│  Agent Selector │
│  (Nova)         │     │  Modal          │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Select Mode    │   │  Select Agent   │   │  Toggle Ultra   │
│  (E-1/E-2/etc)  │   │  (Nova/Forge/..)│   │  Thinking       │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         └──────────────────┬──┴─────────────────────┘
                            │
                            ▼
                  ┌─────────────────┐
                  │  Update State   │
                  │  & Preferences  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Ready for Chat │
                  └─────────────────┘
```

### Chat Processing Flow
```
┌─────────────────┐
│  User Message   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Check Credits  │───No──▶ [402 Error]
│  (if not admin) │
└────────┬────────┘
         │ Yes
         ▼
┌─────────────────┐
│  Build System   │
│  Prompt         │
│  ├─ Agent Config│
│  ├─ Mode Config │
│  └─ Ultra Think │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Call LLM API   │
│  (GPT-5.2)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Log Usage      │
│  Deduct Credits │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Return Response│
│  + Code Blocks  │
└─────────────────┘
```

### Multi-Agent Orchestration (Future)
```
┌─────────────────┐
│  Complex Task   │
│  "Build full app│
│   with auth"    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ATOM Core      │
│  (Orchestrator) │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┐
    │         │        │        │
    ▼         ▼        ▼        ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│ Nova  │ │Sentinel│ │ Forge │ │ Atlas │
│ Code  │ │ Auth   │ │Deploy │ │Monitor│
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    │         │        │        │
    └────┬────┴────────┴────────┘
         │
         ▼
┌─────────────────┐
│  Merge Results  │
│  Return to User │
└─────────────────┘
```

---

## 5. Admin Logic

### Role Hierarchy
```
super_admin > premium > user

super_admin:
  - ALL permissions
  - No credit limits
  - No usage limits
  - Access to admin dashboard
  - Can manage all users
  - Can broadcast messages

premium:
  - Higher usage limits
  - Priority support
  - Advanced features (E-2 mode, etc.)
  - No ads

user (free):
  - Basic features
  - Limited credits (10/month)
  - Limited usage
```

### Super Admin Detection
```python
SUPER_ADMIN_EMAIL = "Antoniohoshaw6@gmail.com"

def is_super_admin(email: str) -> bool:
    return email.lower() == SUPER_ADMIN_EMAIL.lower()

def get_user_role(email: str) -> str:
    if is_super_admin(email):
        return "super_admin"
    # Check subscription status
    return "user"  # or "premium" based on subscription
```

### Admin Middleware
```python
async def require_admin(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_super_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

---

## 6. Premium Subscription Logic

### Plan Definitions
```python
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "price_monthly": 0,
        "credits_monthly": 10,
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
    "pro": {
        "name": "Pro",
        "price_monthly": 29,
        "stripe_price_id": "price_xxx",
        "credits_monthly": 500,
        "features": {
            "chat_messages": 2000,
            "code_executions": 500,
            "video_generations": 20,
            "image_generations": 100,
            "agents": ["nova", "forge", "sentinel", "atlas", "pulse"],
            "modes": ["e1", "e2", "prototype", "mobile"],
            "ultra_thinking": True,
            "priority_support": True
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": 99,
        "stripe_price_id": "price_yyy",
        "credits_monthly": -1,  # Unlimited
        "features": {
            "chat_messages": -1,
            "code_executions": -1,
            "video_generations": -1,
            "image_generations": -1,
            "agents": ["nova", "forge", "sentinel", "atlas", "pulse"],
            "modes": ["e1", "e2", "prototype", "mobile"],
            "ultra_thinking": True,
            "priority_support": True,
            "dedicated_support": True,
            "custom_agents": True
        }
    }
}
```

### Credit Costs
```python
CREDIT_COSTS = {
    "chat_message": 0.1,        # Per message
    "chat_ultra_thinking": 0.2, # Extra for ultra thinking
    "code_execution": 0.05,     # Per execution
    "video_generation": 5.0,    # Per video (expensive)
    "image_generation": 0.5,    # Per image
    "site_clone": 1.0           # Per clone
}
```

### Usage Check Flow
```python
async def check_usage_limits(user: dict, action: str, amount: int = 1) -> bool:
    # Super admin bypasses all limits
    if user.get("is_super_admin"):
        return True
    
    plan = SUBSCRIPTION_PLANS.get(user.get("subscription", {}).get("plan", "free"))
    limit = plan["features"].get(action, 0)
    
    # -1 means unlimited
    if limit == -1:
        return True
    
    current_usage = user.get("usage", {}).get(action, 0)
    return (current_usage + amount) <= limit
```

---

## 7. Browser Extension Architecture

### Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    ATOM Browser Extension                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Popup     │  │  Content    │  │ Background  │              │
│  │   UI        │  │  Script     │  │  Service    │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          │                                       │
│                          ▼                                       │
│                 ┌─────────────────┐                              │
│                 │  ATOM Backend   │                              │
│                 │  API            │                              │
│                 └─────────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Extension Features
1. **Quick Chat** - Open chat panel on any page
2. **Page Summarizer** - Summarize current webpage
3. **Code Helper** - Detect code blocks, offer fixes
4. **Screenshot to Code** - Convert page to HTML
5. **Context Menu** - Right-click to analyze/fix

### Manifest (manifest.json)
```json
{
  "manifest_version": 3,
  "name": "ATOM AI Assistant",
  "version": "1.0.0",
  "description": "AI coding assistant in your browser",
  "permissions": [
    "activeTab",
    "storage",
    "contextMenus",
    "scripting"
  ],
  "host_permissions": [
    "https://*.atom-ai.com/*"
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "css": ["content.css"]
    }
  ],
  "options_page": "options.html"
}
```

### Extension API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/extension/summarize | Summarize page content |
| POST | /api/extension/analyze-code | Analyze selected code |
| POST | /api/extension/screenshot-to-code | Convert screenshot |
| POST | /api/extension/quick-chat | Quick chat message |
| GET | /api/extension/auth-status | Check if logged in |

---

## 8. Security Considerations

### Authentication
- JWT tokens expire after 24 hours
- Refresh tokens for extended sessions
- Password hashed with bcrypt (cost factor 12)
- Rate limiting on auth endpoints

### Authorization
- Role-based access control (RBAC)
- Resource ownership validation
- Admin endpoints protected

### Data Protection
- All MongoDB queries exclude `_id` and `password`
- Sensitive data never logged
- CORS configured properly
- HTTPS enforced

### Rate Limiting
```python
RATE_LIMITS = {
    "auth": "5/minute",
    "chat": "30/minute",
    "code_execution": "20/minute",
    "video_generation": "5/hour",
    "image_generation": "20/minute"
}
```

---

## Implementation Checklist

### Phase 1: Core (DONE)
- [x] User authentication (JWT)
- [x] Agent system (5 agents)
- [x] Mode system (4 modes)
- [x] Ultra Thinking mode
- [x] Super admin role
- [x] Basic credits system

### Phase 2: Subscriptions (TODO)
- [ ] Stripe integration
- [ ] Plan management
- [ ] Billing portal
- [ ] Webhook handling
- [ ] Usage limits enforcement

### Phase 3: Admin Dashboard (TODO)
- [ ] User management
- [ ] Platform statistics
- [ ] Usage analytics
- [ ] Broadcast system

### Phase 4: Browser Extension (TODO)
- [ ] Extension manifest
- [ ] Popup UI
- [ ] Content scripts
- [ ] Background service
- [ ] Extension API endpoints

### Phase 5: Advanced Features (TODO)
- [ ] Multi-agent orchestration
- [ ] Self-debug loop
- [ ] Real-time collaboration
- [ ] Git integration
