# Alex Sharma - Antigravity Portfolio

A modern, dynamic personal portfolio built with React (Vite) and Python (FastAPI). 
Features an "Ivory Editorial Antigravity" aesthetic, Framer Motion animations, custom deterministic canvas-generated project cover images, and a fully functional hidden admin dashboard with AI capabilities.

## Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Framer Motion
- **Backend**: FastAPI, Python, Uvicorn, httpx
- **Database**: Persistent JSON file (`data.json`)
- **AI Integrations**: Anthropic Claude API (Backend)

---

## Setup & Installation

### 1. Backend Setup
1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn httpx python-dotenv anthropic
   ```
3. Add your Anthropic API Key and GitHub Token to `backend/.env` (created automatically during setup):
   ```env
   ANTHROPIC_API_KEY=your_api_key_here
   GITHUB_TOKEN=your_optional_github_token
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
   > The server will run on `http://localhost:8000`

### 2. Frontend Setup
1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies (Ensure Node is installed):
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
   > The app will run on `http://localhost:5173` (or the port Vite provides)

---

## Admin Access
The admin dashboard is deliberately hidden from the navigation UI.
- Access it by navigating directly to `/admin` in your browser.
- **Passphrase:** `admin123`

From the Command Center, you can toggle sections using natural language commands, regenerate AI summaries for your projects, edit the portfolio copy natively, and manage your resume document.
