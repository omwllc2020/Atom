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
- [x] **Multi-Agent System (ATOM Core)**
- [x] **Super Admin Role System**
- [x] **Credits System**

## What's Been Implemented

### Phase 1: Core Features (2026-03-06)
- Landing page, auth, chat workspace
- Video, image, site clone panels
- MongoDB persistence

### Phase 2: Rebranding & Mobile (2026-03-06)
- Forge → ATOM
- Blue/purple color scheme
- Mobile responsive design

### Phase 3: IDE Features (2026-03-06)
- **Code Execution**: Python & JavaScript run in sandbox
- **Auto-Fix Loop**: AI fixes errors automatically (up to 5 attempts)
- **Multi-File Projects**: Create projects with multiple files
- **File Tree**: Visual file browser with icons
- **Monaco Editor**: Full-featured code editor
- **Console Output**: See execution results
- **Live Preview**: HTML renders in iframe

### Phase 4: Multi-Agent System (2026-03-06)
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

## API Endpoints
### Auth
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

### Chat
- POST /api/chat - Accepts agent, mode, ultra_thinking params

### Code
- POST /api/code/execute
- POST /api/code/autofix
- POST /api/code/autofix-loop

### Projects
- POST /api/projects
- GET /api/projects
- GET /api/projects/{id}
- DELETE /api/projects/{id}
- POST /api/projects/{id}/files
- PUT /api/projects/{id}/files/{name}
- DELETE /api/projects/{id}/files/{name}

### Media
- POST /api/video/generate
- POST /api/video/from-media
- GET /api/video/status/{id}
- POST /api/image/generate
- POST /api/clone/site

### User/Credits
- GET /api/user/credits
- GET /api/agents

## Architecture
- **Frontend**: React + Tailwind + Shadcn + Monaco Editor + Framer Motion
- **Backend**: FastAPI + Python subprocess for code execution
- **Database**: MongoDB
- **AI**: GPT-5.2, Sora 2, Nano Banana
- **Auth**: JWT with role-based access control

## Test Results (Latest)
- Backend: 100% (15/15 tests passed)
- Frontend: 100% (all UI features verified)
- Multi-agent system fully operational

## Super Admin Configuration
- Email: Antoniohoshaw6@gmail.com
- Privileges: Unlimited usage, all premium features, billing exempt, no credit tracking

## Next Tasks (P1)
1. Implement Self-Debug Loop (auto-fix with iterative correction)
2. Browser Extension for premium features
3. Full Agent Specialization (distinct toolsets per agent)

## Future Tasks (P2)
1. Add more language support (TypeScript, Go, Rust)
2. Real-time collaboration
3. Git integration
4. Deploy to production
