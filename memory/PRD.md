# Forge AI - AI Coding & Media Generation App

## Original Problem Statement
Build an AI coding app like an AI coding assistant with text-to-video (Sora 2), text-to-image (Nano Banana), and site cloning capability. User wants OpenAI GPT-5.2 for coding, all features including code generation, debugging, video generation, image generation, and site cloning. Using Emergent LLM key for all AI integrations.

## User Personas
1. **Developers** - Need AI assistance for coding, debugging, code explanations
2. **Content Creators** - Want to generate videos and images from text prompts
3. **Web Designers** - Need to quickly clone/recreate website designs

## Core Requirements (Static)
- [x] AI Code Assistant with GPT-5.2
- [x] Text-to-Video generation with Sora 2
- [x] Text-to-Image generation with Nano Banana
- [x] Site Cloning (URL to HTML/CSS code)
- [x] User Authentication (JWT)
- [x] Conversation History
- [x] Modern Dark UI (Cyber-Void theme)

## What's Been Implemented
**Date: 2026-03-06**
- Complete landing page with feature showcase
- User registration and login with JWT auth
- AI Chat workspace with GPT-5.2 integration
- Video generation panel (Sora 2) with size/duration options
- Image generation panel (Nano Banana)
- Site cloner with HTML code preview
- Conversation history management
- MongoDB persistence for all data
- Monaco code editor for generated code

## Architecture
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI Services**: 
  - GPT-5.2 for code generation
  - Sora 2 for video generation
  - Nano Banana (Gemini) for image generation
- **Auth**: JWT tokens

## Prioritized Backlog

### P0 (Critical)
- All core features implemented ✓

### P1 (Important)
- Add code execution preview/sandbox
- Improve video generation status polling
- Add image editing with reference images

### P2 (Nice to Have)
- Multi-file project support
- Code version history
- Share generated content
- Dark/Light theme toggle

## Next Tasks
1. Add code syntax highlighting themes
2. Implement real-time collaboration
3. Add export options (PDF, ZIP)
4. Integrate more AI models
