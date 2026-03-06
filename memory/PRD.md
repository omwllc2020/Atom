# ATOM - AI Coding & Media Generation App

## Original Problem Statement
Build an AI coding app with ALL features like an AI assistant: code execution, automatic testing, auto-fix that keeps trying until code works, multi-file projects, video generation (Sora 2), image generation (Nano Banana), and site cloning.

## User Personas
1. **Developers** - Need AI assistance + code execution + auto-debugging
2. **Content Creators** - Generate videos and images from text
3. **Web Designers** - Clone websites and preview HTML live

## Core Requirements (Static)
- [x] AI Code Assistant with GPT-5.2
- [x] Code Execution (Python & JavaScript)
- [x] Auto-Fix Loop (keeps fixing until code works)
- [x] Multi-File Projects with File Tree
- [x] Live HTML Preview
- [x] Text-to-Video generation with Sora 2
- [x] Text-to-Image generation with Nano Banana
- [x] Site Cloning
- [x] User Authentication (JWT)
- [x] Conversation History
- [x] Modern UI with ATOM branding

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
- **Auto-Fix Toggle**: Enable/disable automatic fixing

## API Endpoints Added
- POST /api/code/execute - Run code
- POST /api/code/autofix - Fix single error
- POST /api/code/autofix-loop - Keep fixing until success
- POST /api/projects - Create project
- GET /api/projects - List projects
- POST /api/projects/{id}/files - Add file
- PUT /api/projects/{id}/files/{name} - Update file
- DELETE /api/projects/{id}/files/{name} - Delete file

## Architecture
- **Frontend**: React + Tailwind + Shadcn + Monaco Editor
- **Backend**: FastAPI + Python subprocess for code execution
- **Database**: MongoDB
- **AI**: GPT-5.2, Sora 2, Nano Banana

## Test Results
- Backend: 81.8% (18/22 tests passed)
- All IDE features working
- Code execution verified for Python & JS

## Next Tasks
1. Add more language support (TypeScript, Go, Rust)
2. Real-time collaboration
3. Git integration
4. Deploy to production
