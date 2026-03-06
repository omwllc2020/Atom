# ATOM - AI Coding & Media Generation App

## Original Problem Statement
Build an AI coding app with ALL features like an AI assistant: code execution, automatic testing, auto-fix that keeps trying until code works, multi-file projects, video generation (Sora 2), image generation (Nano Banana), and site cloning. Includes multi-agent system (ATOM Core) with specialized agents and super admin functionality.

## User Personas
1. **Developers** - Need AI assistance + code execution + auto-debugging
2. **Content Creators** - Generate videos and images from text
3. **Web Designers** - Clone websites and preview HTML live
4. **Super Admin** - Full platform access without restrictions

## Core Requirements
- [x] AI Code Assistant with GPT-5.2
- [x] Code Execution (Python & JavaScript)
- [x] Auto-Fix Loop (keeps fixing until code works)
- [x] Multi-File Projects with File Tree
- [x] Live HTML Preview
- [x] Text-to-Video generation with Sora 2
- [x] Image-to-Video generation with Sora 2
- [x] Text-to-Image generation with Nano Banana
- [x] Site Cloning
- [x] User Authentication (JWT)
- [x] Conversation History
- [x] Modern UI with ATOM branding
- [x] Multi-Agent System (ATOM Core)
- [x] Super Admin Role System
- [x] Credits System
- [x] Subscription Plans
- [x] Usage Tracking
- [x] Admin Dashboard API

## Implementation History

### Phase 1: Core Features
- Landing page, auth, chat workspace
- Video, image, site clone panels
- MongoDB persistence

### Phase 2: Rebranding & Mobile
- Forge → ATOM
- Blue/purple color scheme
- Mobile responsive design

### Phase 3: IDE Features
- Code Execution: Python & JavaScript run in sandbox
- Auto-Fix Loop: AI fixes errors automatically (up to 5 attempts)
- Multi-File Projects: Create projects with multiple files
- File Tree: Visual file browser with icons
- Monaco Editor: Full-featured code editor
- Console Output: See execution results
- Live Preview: HTML renders in iframe

### Phase 4: Multi-Agent System (December 2025)
- **Specialized Agents**: 
  - Nova - Software architecture & coding
  - Forge - Infrastructure & DevOps
  - Sentinel - Security & authentication
  - Atlas - Analytics & optimization
  - Pulse - Marketing & growth
- **Execution Modes**:
  - E-1: Stable & thorough
  - E-2: Thorough & relentless (Pro)
  - Prototype: Experimental
  - Mobile: Mobile-first focus
- **Ultra Thinking Mode**: Deep multi-step reasoning
- **Super Admin**: Antoniohoshaw6@gmail.com with unlimited access
- **Credits System**: 10 credits for regular users, unlimited for super admin

### Phase 5: Subscription & Admin System (December 2025)
- **Subscription Plans**:
  - Free: $0/month, 10 credits, limited features
  - Pro: $29/month, 500 credits, all features
  - Enterprise: $99/month, unlimited everything
- **Usage Tracking**: All actions logged with timestamps, credits, metadata
- **Admin Dashboard API**: User management, stats, credit control
- **Role-Based Access Control**: Admin-only endpoints with 403 protection

## API Endpoints

### Authentication
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/auth/register | Public |
| POST | /api/auth/login | Public |
| GET | /api/auth/me | Required |

### User & Credits
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | /api/user/credits | Required |
| GET | /api/user/usage | Required |
| GET | /api/user/usage/history | Required |
| GET | /api/user/preferences | Required |
| PUT | /api/user/preferences | Required |

### Subscription
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | /api/subscription/plans | Public |
| GET | /api/subscription | Required |
| POST | /api/subscription/upgrade | Required |

### Agents
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | /api/agents | Public |

### Chat
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/chat | Required |
| GET | /api/conversations | Required |
| GET | /api/conversations/{id} | Required |
| DELETE | /api/conversations/{id} | Required |

### Code Execution
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/code/execute | Required |
| POST | /api/code/autofix | Required |
| POST | /api/code/autofix-loop | Required |

### Projects
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/projects | Required |
| GET | /api/projects | Required |
| GET | /api/projects/{id} | Required |
| DELETE | /api/projects/{id} | Required |
| POST | /api/projects/{id}/files | Required |
| PUT | /api/projects/{id}/files/{name} | Required |
| DELETE | /api/projects/{id}/files/{name} | Required |

### Media Generation
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/video/generate | Required |
| POST | /api/video/from-media | Required |
| GET | /api/video/status/{id} | Required |
| POST | /api/image/generate | Required |
| POST | /api/clone/site | Required |

### Admin (Super Admin Only)
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | /api/admin/stats | Admin |
| GET | /api/admin/users | Admin |
| GET | /api/admin/users/{id} | Admin |
| PUT | /api/admin/users/{id} | Admin |
| POST | /api/admin/users/{id}/credits | Admin |
| DELETE | /api/admin/users/{id} | Admin |
| GET | /api/admin/usage | Admin |

## Database Schema

### users
```javascript
{
  "id": "uuid",
  "email": "string",
  "password": "bcrypt hash",
  "name": "string",
  "role": "user|premium|super_admin",
  "credits": "number (-1 = unlimited)",
  "is_super_admin": "boolean",
  "subscription": {
    "plan": "free|pro|enterprise",
    "status": "active|canceled",
    "current_period_start": "datetime",
    "current_period_end": "datetime"
  },
  "usage": {
    "chat_messages": "number",
    "code_executions": "number",
    "video_generations": "number",
    "image_generations": "number",
    "credits_used": "number"
  },
  "preferences": {
    "default_agent": "nova|forge|sentinel|atlas|pulse",
    "default_mode": "e1|e2|prototype|mobile",
    "ultra_thinking": "boolean",
    "theme": "dark|light"
  }
}
```

### usage_logs
```javascript
{
  "id": "uuid",
  "user_id": "string",
  "action": "chat_message|code_execution|video_generation|image_generation",
  "agent": "string",
  "mode": "string",
  "credits_used": "number",
  "success": "boolean",
  "metadata": "object",
  "created_at": "datetime"
}
```

## Credit Costs
| Action | Cost |
|--------|------|
| Chat Message | 0.10 |
| Ultra Thinking (extra) | 0.20 |
| Code Execution | 0.05 |
| Video Generation | 5.00 |
| Image Generation | 0.50 |
| Site Clone | 1.00 |

## Test Results
- Backend: 100% (24/24 tests passed)
- Frontend: 100% (all UI features verified)

## Super Admin Configuration
- Email: Antoniohoshaw6@gmail.com
- Privileges: Unlimited usage, all premium features, billing exempt, admin dashboard access

## Architecture
```
/app/
├── backend/
│   ├── server.py          # Main FastAPI app
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── lib/api.js     # API functions
│   │   ├── pages/
│   │   │   └── WorkspacePage.js
│   │   └── components/ui/
│   └── package.json
└── memory/
    ├── PRD.md
    └── IMPLEMENTATION_SPEC.md
```

## Next Tasks (P1)
1. Browser Extension Architecture
2. Stripe Payment Integration
3. Admin Dashboard UI
4. Self-Debug Loop Enhancement

## Future Tasks (P2)
1. Multi-agent Orchestration
2. Real-time Collaboration
3. Git Integration
4. Additional Language Support
