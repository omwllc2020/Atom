# ATOM - AI Coding & Media Generation App

## Original Problem Statement
Build an AI coding app with ALL features like an AI assistant: code execution, automatic testing, auto-fix that keeps trying until code works, multi-file projects, video generation (Sora 2), image generation (Nano Banana), and site cloning. Includes multi-agent system (ATOM Core) with specialized agents, super admin functionality, and Stripe payment integration matching Replit's pricing model.

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
- [x] **Stripe Payment Integration**
- [x] **Subscription Plans (Replit-style)**
- [x] **Credit Top-ups**
- [x] **Mobile Responsive UI**

## Pricing Model (Replit-style)

### Subscription Plans
| Plan | Monthly Price | Credits/Month | Target User |
|------|---------------|---------------|-------------|
| Free | $0 | $10 | Beginners |
| Core | $20 | $25 | Solo developers |
| Pro | $40 | $50 | Power users |
| Enterprise | $99 | Unlimited | Large teams |

### Credit Packages (Top-ups)
| Package | Credits | Price |
|---------|---------|-------|
| Small | $10 | $5 |
| Medium | $25 | $10 |
| Large | $50 | $18 |
| XL | $100 | $30 |

### Credit Costs
| Action | Cost |
|--------|------|
| Chat message | $0.10 |
| Ultra Thinking (extra) | $0.15 |
| Code execution | $0.05 |
| Video generation | $2.50 |
| Image generation | $0.25 |
| Agent checkpoint | $0.25 |
| Site clone | $1.00 |

## Implementation History

### Phase 1-4: Core Features
- Landing page, auth, chat workspace
- ATOM branding, mobile responsive
- IDE with code execution, auto-fix
- Multi-agent system (Nova, Forge, Sentinel, Atlas, Pulse)

### Phase 5: Subscription & Admin (December 2025)
- Subscription plans with Stripe
- Credit top-up packages
- Usage tracking and logging
- Admin dashboard API

### Phase 6: Stripe Payment Integration (December 2025)
- **Stripe Checkout Sessions** for subscriptions and credits
- **Webhook handling** for payment confirmation
- **Payment status polling** for redirect handling
- **Payment history** tracking
- **Mobile-optimized** subscription modal
- **Safe area padding** for iOS devices
- **Keyboard-aware** layout

## API Endpoints

### Payment & Subscription
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /api/subscription | Get subscription + credit packages | Required |
| GET | /api/subscription/plans | List all plans | Public |
| POST | /api/checkout/subscription | Create Stripe checkout for plan | Required |
| POST | /api/checkout/credits | Create Stripe checkout for credits | Required |
| GET | /api/checkout/status/{id} | Check payment status | Required |
| GET | /api/payment/history | Get payment transactions | Required |
| POST | /api/webhook/stripe | Stripe webhook handler | Webhook |

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

### Chat & Code
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/chat | Required |
| POST | /api/code/execute | Required |
| POST | /api/code/autofix | Required |
| POST | /api/code/autofix-loop | Required |

### Media Generation
| Method | Endpoint | Auth |
|--------|----------|------|
| POST | /api/video/generate | Required |
| POST | /api/video/from-media | Required |
| POST | /api/image/generate | Required |
| POST | /api/clone/site | Required |

### Admin (Super Admin Only)
| Method | Endpoint | Auth |
|--------|----------|------|
| GET | /api/admin/stats | Admin |
| GET | /api/admin/users | Admin |
| PUT | /api/admin/users/{id} | Admin |
| POST | /api/admin/users/{id}/credits | Admin |
| DELETE | /api/admin/users/{id} | Admin |
| GET | /api/admin/usage | Admin |

## Test Results
- Backend Stripe Tests: **24/24 passed** (100%)
- All Stripe checkout endpoints working
- Mobile UI verified
- Super admin unlimited access confirmed

## Super Admin
- Email: Antoniohoshaw6@gmail.com
- Privileges: Unlimited usage, all premium features, billing exempt
- UI shows "UNLIMITED" badge instead of credits

## Architecture
```
/app/
├── backend/
│   ├── server.py          # FastAPI + Stripe integration
│   ├── tests/
│   │   └── test_stripe_checkout.py
│   ├── requirements.txt
│   └── .env (STRIPE_API_KEY)
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── WorkspacePage.js (SubscriptionModal)
│   │   ├── lib/api.js
│   │   └── index.css (mobile safe areas)
│   └── package.json
└── memory/
    ├── PRD.md
    └── IMPLEMENTATION_SPEC.md
```

## Next Tasks (P1)
1. Browser Extension Architecture
2. Admin Dashboard UI
3. Self-Debug Loop Enhancement
4. Stripe recurring billing (auto-renewal)

## Future Tasks (P2)
1. Multi-agent Orchestration (Atom Core coordinator)
2. Real-time Collaboration
3. Git Integration
4. Additional Language Support
