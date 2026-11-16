# Autonomous Agentic AI Cryptocurrency Trading System with RAG & Telegram Integration

[![Python 3.13+](https://img.shields.io/badge/Python-3.13+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/Frontend-React_18-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Build-Vite-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An advanced, multi-agent AI-powered cryptocurrency trading and market analytics platform. Features autonomous signal extraction from Telegram MTProto channels, technical validation, Retrieval-Augmented Generation (RAG) context retrieval, real-time global stock exchange session tracking, and a simulated paper-trading engine with real-time risk controls.

---

## 📑 Table of Contents

- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
  - [1. Agentic AI Pipeline](#1-agentic-ai-pipeline)
  - [2. Telegram MTProto Integration](#2-telegram-mtproto-integration)
  - [3. Real-Time Global Stock Market Hours & Dates](#3-real-time-global-stock-market-hours--dates)
  - [4. Retrieval-Augmented Generation (RAG)](#4-retrieval-augmented-generation-rag)
  - [5. Paper Trading Engine](#5-paper-trading-engine)
  - [6. Modern Web Dashboard](#6-modern-web-dashboard)
- [Tech Stack](#-tech-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Prerequisites & Requirements](#-prerequisites--requirements)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Clone and Configure Environment](#1-clone-and-configure-environment)
  - [2. Backend Setup](#2-backend-setup)
  - [3. Frontend Setup](#3-frontend-setup)
  - [4. Telegram Secure Authentication](#4-telegram-secure-authentication)
  - [5. Run the Application](#5-run-the-application)
- [API Reference](#-api-reference)
- [Safety, Security & Risk Management](#-safety-security--risk-management)
- [License](#-license)

---

## 🏛️ System Architecture

```text
                                 [ Telegram Channels ]
                                           │
                                           ▼ (MTProto / Telethon)
                            ┌───────────────────────────────┐
                            │    Telegram Monitoring Agent   │
                            └──────────────┬────────────────┘
                                           │ Parsed Raw Signal
                                           ▼
                            ┌───────────────────────────────┐
                            │     Signal Analysis Agent     │
                            │  (Validation, Bounds, S/L, TP)│
                            └──────────────┬────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
     ┌─────────────────────────────┐               ┌─────────────────────────────┐
     │    Market Research Agent    │               │     RAG Knowledge Agent     │
     │  (Live Prices, Indicators,  │               │  (Vector Store, Strategy,   │
     │   Global Exchange Sessions) │               │   Historical Case Analysis) │
     └──────────────┬──────────────┘               └──────────────┬──────────────┘
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                            ┌───────────────────────────────┐
                            │    Risk Management Agent      │
                            │ (Drawdown, Sizing, Kelly/Cap) │
                            └──────────────┬────────────────┘
                                           │ Validated Risk Payload
                                           ▼
                            ┌───────────────────────────────┐
                            │    Trading Decision Agent     │
                            │ (BUY / SELL / HOLD / REJECT)  │
                            └──────────────┬────────────────┘
                                           │
                                           ▼
                            ┌───────────────────────────────┐
                            │      Paper Trading Engine     │
                            │   (Slippage, Fees, P&L Track) │
                            └──────────────┬────────────────┘
                                           │
                                           ▼
                      [ SQLite / PostgreSQL Database ] ◄──► [ React Web Terminal ]
```

---

## ✨ Key Features

### 1. Agentic AI Pipeline
- **Telegram Monitoring Agent** (`backend/app/agents/telegram_monitor.py`): Continuously monitors designated Telegram channels, extracts raw messages, and maps unstructured signal text into standardized `ParsedSignal` representations.
- **Signal Analysis Agent** (`backend/app/agents/signal_analysis.py`): Validates trading pairs, price bounds (Stop-Loss < Entry < Take-Profit for Longs, inverse for Shorts), confidence scores, and leverage limits.
- **Market Research Agent**: Queries live market feeds, computes technical metrics (RSI, MACD, EMA, Bollinger Bands), and observes session volatility.
- **RAG Knowledge Agent**: Queries local vector stores (`rag_index.json`) for historical trade context, strategy documentation, and risk guidelines.
- **Risk Management Agent**: Enforces a strict 2.0% maximum risk-per-trade, daily portfolio drawdown limits (5.0%), and maximum concurrent open positions.
- **Trading Decision Agent**: Synthesizes market trend, signal validity, and risk metrics into actionable recommendations.
- **Portfolio Management Agent**: Tracks balance, equity curves, win rate, and realized vs. unrealized P&L.
- **Supervisor Agent**: Orchestrates agent messaging queues, manages retries, and maintains comprehensive audit logs.

### 2. Telegram MTProto Integration
- Direct connection via **Telethon** to personal Telegram accounts or bot accounts.
- Multi-step secure authentication:
  - Phone number verification
  - In-terminal or secure UI OTP code confirmation
  - Telegram Two-Step Verification (2FA) password support
- Zero credential leakage: OTP and 2FA credentials are never passed to an LLM or stored in plain text.
- Session string encryption and storage outside public directories (`~/.telegram_sessions/`).
- Session revocation and logout capabilities.

### 3. Real-Time Global Stock Market Hours & Dates
- Real-time trading session and market status tracking across the world's leading exchanges:
  - **NYSE / NASDAQ** (United States, `America/New_York`) — 09:30 AM to 04:00 PM EST (Pre-market: 04:00 AM, After-hours: 08:00 PM)
  - **NSE / BSE** (India, `Asia/Kolkata`) — 09:15 AM to 03:30 PM IST (Pre-market: 09:00 AM)
  - **LSE** (United Kingdom, `Europe/London`) — 08:00 AM to 04:30 PM GMT/BST
  - **TSE** (Japan, `Asia/Tokyo`) — 09:00 AM to 03:30 PM JST
  - **HKEX** (Hong Kong, `Asia/Hong_Kong`) — 09:30 AM to 04:00 PM HKT
  - **XETRA / Deutsche Börse** (Germany/EU, `Europe/Berlin`) — 09:00 AM to 05:30 PM CET
- **Live Market Dates**: Accurately computes localized trading dates across international date lines.
- **Dynamic Status Badges**: `🟢 OPEN`, `🟡 PRE-MARKET`, `🟣 AFTER-HOURS`, `🔴 CLOSED`, `⚪ WEEKEND`.
- **Session Countdowns**: Real-time ticking timers calculating exact time until market open or close.
- **24/7 Crypto Liquidity Windows**: Identifies high-volatility overlap periods (e.g. US Wall Street Open + London Session overlap).

### 4. Retrieval-Augmented Generation (RAG)
- Document ingestion and chunking pipeline for trading guidelines, PDF/TXT strategies, and risk manuals.
- Semantic vector storage with local fallback or embedding providers (Gemini / OpenAI / Local).
- Citation-backed AI Copilot providing factual explanations without financial hallucinations.
- Historical trade similarity matching comparing current setups against past win/loss patterns.

### 5. Paper Trading Engine
- **Non-negotiable simulated execution mode**: Real capital is protected; live order execution is blocked by default.
- Initial virtual balance (default `$10,000 USDT`).
- Gaussian execution slippage simulation (default 5 bps).
- Maker/Taker exchange fee simulation (0.05% per fill).
- Automated position mark-to-market calculations and Trailing Stop-Loss / Take-Profit tracking.

### 6. Modern Web Dashboard
- Cyberpunk dark-themed UI built with React 18, Vite, and Tailwind CSS.
- **Overview Dashboard**: Equity curves, KPI stat cards, portfolio performance, and live market sessions.
- **Telegram Signals Feed**: Incoming signal cards with confidence scoring, validation checks, and instant simulated execution.
- **AI Copilot Page**: Interactive conversational assistant with document grounded citations.
- **Positions & Orders**: Real-time management of active open positions and historical order records.
- **Global Stock Markets Widget**: Live clocks, dates, session progress bars, and countdowns.

---

## 🛠️ Tech Stack

### Backend
- **Language**: Python 3.13+
- **Framework**: FastAPI (Asynchronous REST & WebSockets)
- **Database**: SQLite (via `aiosqlite` & `SQLAlchemy 2.0 async`) / PostgreSQL ready
- **MTProto Engine**: Telethon
- **Market Data**: CCXT, Binance Public API, Custom `zoneinfo` Market Hours Engine
- **RAG & Embeddings**: NumPy Cosine Similarity, Vector Store, Google Gemini / OpenAI SDKs
- **Validation**: Pydantic v2 & Pydantic-Settings

### Frontend
- **Framework**: React 18 (TypeScript)
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS, Class Variance Authority, Tailwind Merge
- **State & Data Fetching**: TanStack React Query v5, Axios
- **Icons & Visuals**: Lucide React, Recharts (Responsive SVG Charts)
- **Routing**: React Router v6

---

## 📂 Project Directory Structure

```text
crypto-signal-trader/
├── backend/
│   ├── alembic/                      # Database migrations
│   ├── app/
│   │   ├── adapters/                 # External service adapters
│   │   ├── agents/                   # Autonomous AI Agents
│   │   │   ├── telegram_monitor.py   # Telegram Monitoring Agent
│   │   │   └── signal_analysis.py    # Signal Validation & Analysis Agent
│   │   ├── api/v1/                   # FastAPI endpoints
│   │   │   ├── endpoints/
│   │   │   │   ├── analytics.py      # Performance & Market Hours endpoints
│   │   │   │   ├── channels.py       # Monitored Telegram channels
│   │   │   │   ├── dashboard.py      # Terminal overview aggregator
│   │   │   │   ├── orders.py         # Paper trading orders
│   │   │   │   ├── portfolio.py      # Portfolio balances & equity
│   │   │   │   ├── positions.py      # Active & closed positions
│   │   │   │   ├── rag.py            # RAG knowledge base & Copilot
│   │   │   │   └── signals.py        # Parsed signals management
│   │   ├── core/                     # Configuration (Pydantic Settings) & logging
│   │   ├── db/                       # SQLAlchemy models & async engine
│   │   ├── models/                   # Database entity models
│   │   ├── schemas/                  # Pydantic request/response schemas
│   │   └── services/                 # Core business logic
│   │       ├── market_data_service.py # Live crypto price fetcher
│   │       ├── market_hours_service.py# Global stock exchange session tracker
│   │       ├── paper_broker.py       # Simulated execution broker
│   │       ├── portfolio_service.py  # Portfolio accounting
│   │       ├── risk_engine.py        # Sizing & drawdown guards
│   │       ├── signal_parser.py      # Regex signal extractor
│   │       ├── telegram_service.py   # Telethon client wrapper
│   │       └── rag/                  # RAG vector store & embedding engine
│   ├── tests/                        # Pytest suite
│   ├── requirements.txt              # Backend dependencies
│   └── crypto_signal_trader.db       # SQLite local database
├── frontend/
│   ├── src/
│   │   ├── components/               # UI components
│   │   │   ├── common/               # Navbar, Sidebar, StatCard, Badge
│   │   │   ├── dashboard/            # StockMarketHoursWidget, EquityChart, etc.
│   │   │   └── rag/                  # Copilot & RAG modal dialogs
│   │   ├── layouts/                  # Root application layout
│   │   ├── pages/                    # Terminal pages (Dashboard, Signals, Copilot, etc.)
│   │   ├── services/                 # Axios API client & WebSockets
│   │   ├── types/                    # TypeScript interfaces
│   │   └── utils/                    # Formatters & tailwind merge
│   ├── package.json                  # Frontend dependencies
│   ├── vite.config.ts                # Vite proxy & build configuration
│   └── tailwind.config.js            # Color palettes & UI theme
├── .env.example                      # Template environment variables
├── seed_demo.py                      # Database seeding script with realistic data
└── README.md                         # Project documentation
```

---

## 📋 Prerequisites & Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.10 to 3.13
- **Node.js**: v18.0.0 or higher
- **Package Managers**: `pip` and `npm`
- **Telegram Developer Credentials**: Obtain your `api_id` and `api_hash` from [my.telegram.org](https://my.telegram.org) (optional for demo/simulation mode).

---

## 🚀 Quick Start Guide

### 1. Clone and Configure Environment

```bash
git clone <repository-url>
cd "Te major project/crypto-signal-trader"
```

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your preferred configurations:

```dotenv
# Application
APP_NAME="CryptoSignal AI"
APP_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./crypto_signal_trader.db

# Telegram (Optional for live channel listening)
TELEGRAM_API_ID=0
TELEGRAM_API_HASH=
TELEGRAM_SESSION_STRING=

# Paper Trading & Risk Parameters
PAPER_TRADING_ENABLED=true
PAPER_INITIAL_BALANCE_USDT=10000.0
PAPER_DEFAULT_POSITION_SIZE_PCT=2.0
RISK_MAX_DRAWDOWN_PCT=20.0
RISK_MAX_DAILY_LOSS_PCT=5.0

# Optional RAG API Keys
GEMINI_API_KEY=
OPENAI_API_KEY=
```

---

### 2. Backend Setup

Create and activate a virtual environment:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r backend/requirements.txt
```

Initialize and seed the database with sample trading signals and history:

```bash
python seed_demo.py
```

---

### 3. Frontend Setup

Navigate to the `frontend` folder and install dependencies:

```bash
cd frontend
npm install
```

Test production build:

```bash
npm run build
cd ..
```

---

### 4. Telegram Secure Authentication

To connect your personal Telegram account safely without transmitting credentials across third-party prompts:

```bash
python -m backend.app.services.telegram_auth
```

Follow the secure CLI prompts:
1. Enter your phone number (e.g. `+1234567890`).
2. Input the verification OTP code sent by Telegram.
3. If enabled, provide your Two-Factor Authentication (2FA) password.
4. The encrypted session string will be saved to your local user directory.

---

### 5. Run the Application

#### Option A: Running with Two Terminals

**Terminal 1 (Backend FastAPI server):**
```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend React dev server):**
```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

#### Option B: Access via Browser
Once running, open your web browser:
- **Terminal Web Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Interactive Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check (Telegram, DB, and Market Data status) |
| `GET` | `/api/v1/analytics/market-hours` | **Real-time stock market dates, opening/closing times, and countdowns** |
| `GET` | `/api/v1/dashboard/summary` | Aggregated dashboard stats, recent signals, and equity curve |
| `GET` | `/api/v1/signals` | List all parsed cryptocurrency trading signals |
| `POST` | `/api/v1/signals` | Submit a raw or structured signal for parsing and validation |
| `GET` | `/api/v1/positions?status=OPEN` | Query active paper positions with live mark-to-market |
| `POST` | `/api/v1/positions/{id}/close` | Close an active simulated position at current market price |
| `GET` | `/api/v1/orders` | Fetch full order execution history |
| `GET` | `/api/v1/portfolio` | Retrieve virtual equity, cash balance, and win/loss statistics |
| `POST` | `/api/v1/rag/query` | Ask AI Copilot trading questions with vector-retrieved citations |
| `POST` | `/api/v1/rag/evaluate` | Evaluate an incoming trade signal against historical performance |
| `WS` | `/ws` | Real-time WebSocket feed for price updates and parsed signals |

---

## 🛡️ Safety, Security & Risk Management

- **Enforced Simulation**: `PAPER_TRADING_ENABLED` is hard-enforced in code. Orders are never routed to live crypto exchange endpoints without architectural restructuring and explicit user consent.
- **Deterministic Risk Engine**: Every signal must pass strict stop-loss, position-sizing, and daily loss threshold checks before it can enter simulated execution.
- **Untrusted Signal Sanitization**: Inbound Telegram messages are treated as untrusted input. Regex tokenization and bounds verification mitigate prompt injection and malformed trade inputs.
- **No Stored Plaintext Secrets**: Telegram session data is stored in isolated directories and ignored in `.gitignore`.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
