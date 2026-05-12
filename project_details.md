# Divya Nirankari - Portfolio (Historical Details)

This file contains the original project details migrated from the README.

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
   ```
3. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

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
