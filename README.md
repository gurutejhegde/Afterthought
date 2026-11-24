# Afterthought

> **An intelligent assistant built on MCP that connects scattered apps, turns findings into tracked tasks, and follows up on unfinished work.**

Developed for **wHACKiest 2026** (Track 01) by **Team Nebula**.

---

## 📌 Overview

People struggle to stay organized because their commitments, tasks, and information are fragmented across multiple disconnected platforms (Gmail, Google Drive, Google Calendar, WhatsApp, etc.). 

**Afterthought** acts as a unified proactive assistant that:
- Connects disparate tools via the **Model Context Protocol (MCP)**.
- Maintains an **Outcome Ledger** tracking commitments through to verification.
- Proactively flags stalled or overdue work instead of merely acting on demand.
- Enforces **Controlled Execution** with user approval previews and prompt injection safeguards.
- Delivers a unified **Daily Briefing** via text and voice.

---

## 🏗️ Architecture

- **Frontend**: React (Vite) + Tailwind CSS + TypeScript
- **Voice**: ElevenLabs API with Web Speech API fallback
- **AI Reasoning**: Google Gemini API
- **Backend**: Python + FastAPI
- **Task & Memory / Integrations**: Model Context Protocol (MCP) servers (Google Calendar, Google Drive, Custom Task & Outcome Ledger)
- **Database**: SQLite with SQLAlchemy
- **Scheduling**: APScheduler (automated overdue & stalled task detection)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- [Optional] Google Gemini API Key & ElevenLabs API Key

### Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 👥 Team Nebula
- **Gurutej Hegde** (Lead)
- **Shridhar Madival**
- **Manish Patgar**
