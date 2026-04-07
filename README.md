# Divya Nirankari - Antigravity Portfolio

A modern, dynamic personal portfolio built with **React (Vite)** and **Python (FastAPI)**. 
Features an "Ivory Editorial Antigravity" aesthetic, Framer Motion animations, custom deterministic canvas-generated project cover images, and a fully functional hidden admin dashboard with AI capabilities.

## 🚀 Completed Features

- **Dynamic Portfolio Core**: Responsive React (Vite) frontend with a high-performance FastAPI backend.
- **Ivory Editorial Aesthetic**: Premium, light-mode "Antigravity" design with sophisticated Framer Motion transitions and custom cursor.
- **Hidden Admin Command Center**: Secure dashboard at `/admin` for full content management and system monitoring.
- **GitHub Integration**: Automatic fetching of repositories with granular visibility control (Show/Hide individual repos).
- **AI-Powered Content**: Integrated neural text rewriting for bios and summaries (Grok/X.AI integration).
- **Inbound Transmissions**: Robust message inbox for managing contact form submissions with "Mark as Read" and quick reply features.
- **Language Proficiency**: Visual progress bars for communication skills with proficiency-level mapping.
- **Artifact Manager**: Sortable, draggable editors for Experience, Achievements, Projects, Testimonials, Research, and Blog posts.
- **Activity Signal**: Tracking professional activity via a heatmap and detailed signal log.
- **Analytics Dashboard**: Real-time monitoring of page views, visitor engagement, and traffic sources.
- **SEO Optimized**: Semantic HTML5 and meta-tag structure for maximum visibility.

## 🛠️ Tech Stack
- **Frontend**: React 18, Vite, Tailwind CSS (light-mode only), Framer Motion, Lucide-React
- **Backend**: FastAPI (Python 3.10+), Uvicorn, httpx, python-dotenv
- **Database**: Persistent JSON storage (`data.json`)
- **AI Integrations**: Grok (X.AI) API for intelligent text editing

---

## ⚙️ Setup & Installation

### 1. Backend Setup
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   # Or install manually:
   pip install fastapi uvicorn httpx python-dotenv
   ```
3. Add your Grok API Key and GitHub Token to `backend/.env`:
   ```env
   GROK_API_KEY=your_key_here
   GITHUB_TOKEN=your_token_here
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8001
   ```
   > The server will run on `http://localhost:8001`

### 2. Frontend Setup
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
   > The app will run on `http://localhost:5173`

---

## 🔒 Admin Access
The admin dashboard is deliberately hidden for security and aesthetics.
- **URL**: [http://localhost:5173/admin](http://localhost:5173/admin)
- **Passphrase**: Managed via `AdminContext` (Default is typically defined in setup).

From the **Command Center**, you can toggle entire sections, sync GitHub pulse, and deposit new professional artifacts to refresh your identity.
