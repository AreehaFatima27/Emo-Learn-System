# 🧠 EmoLearn — Emotion-Aware AI Quiz Platform

EmoLearn is an AI-powered education platform that generates quizzes on any topic using **Mistral AI**, monitors the student's emotional response in real-time using **Google MediaPipe Face Mesh** via webcam, and analyzes their comprehension level dynamically based on answer accuracy, response times, and facial expressions.

---

## 🛠️ Tech Stack
- **Frontend**: Vite + Vanilla JS, HTML5, Vanilla CSS (Premium Glassmorphism Theme), Chart.js
- **Backend**: FastAPI (Python), SQLAlchemy ORM, Pydantic
- **Database**: PostgreSQL (pgAdmin)
- **AI Integrations**: Mistral AI API (`mistral-large-latest`), Google MediaPipe (`@mediapipe/tasks-vision`)

---

## 🚀 Quick Start (Run Once Launcher)

Double-click the **`run.bat`** file in the root folder.
This script will automatically:
1. Create a Python virtual environment (`venv`) inside `backend/`.
2. Install all required Python packages from `requirements.txt`.
3. Set up and seed the PostgreSQL database tables.
4. Launch the backend API server (`http://localhost:8000`).
5. Install all frontend `npm` dependencies.
6. Launch the frontend development server (`http://localhost:5173`).

## ⚙️ Environment Configuration

To keep sensitive keys and credentials secure, the `.env` configuration file is excluded from Git via `.gitignore`. When importing this project, you must set up your environment file:

1. Go to the `backend/` folder and copy `.env.example` to create a new `.env` file:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Open `backend/.env` and configure your local settings:
   - **`DATABASE_URL`**: Set your PostgreSQL connection string.
   - **`MISTRAL_API_KEY`**: Insert your Mistral AI API key (required for quiz generation).
   - **`SECRET_KEY`**: Set a secure secret key for token authentication.

---

## 🐘 Setting up PostgreSQL Database with pgAdmin

Follow these steps to connect and configure the database before launching:

1. **Open pgAdmin** on your machine.
2. In the left browser tree, right-click on **Databases** -> **Create** -> **Database...**
3. Set the database name to: **`emolearn`**
4. Click **Save**.
5. Check your PostgreSQL connection credentials. Make sure they match the `DATABASE_URL` in your `backend/.env` file. By default, the database URL is set to:
   ```ini
   DATABASE_URL=postgresql://rough:rough@localhost:5432/emolearn
   ```

---

## 🔑 Default Credentials
Once the database is initialized, a default super-administrator account is seeded:
- **Email**: `superadmin@gmail.com`
- **Password**: `admin123`

---

## 📂 Project Structure
- **/backend**: FastAPI application, database schemas, and AI endpoints
  - `main.py`: Application entrypoint
  - `routes/`: Auth, Quiz submissions, Sentiment & emotion analysis routes
  - `database/`: Database connection and model tables
  - `services/`: Mistral AI quiz generator & sentiment analyzer service wrappers
- **/frontend**: HTML, CSS styles, and client router pages
  - `src/main.js`: Vanilla JS client-side router
  - `src/style/index.css`: Glassmorphic styling system
  - `src/components/webcam-panel.js`: Webcam activation, face mesh rendering, and MediaPipe emotion classification
  - `src/pages/`: Dashboard, Quiz setup/running, Profile settings, Results report, Admin management
