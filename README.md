# BhoomiGuard AI 🛡️
**Predictive Analytics System for Early Detection of Land Acquisition Delays**

BhoomiGuard AI is an advanced Smart Automation platform that assists district collectors and project administrators by leveraging Machine Learning to predict delays in land acquisition for rural infrastructure projects before they happen.

By combining **Explainable AI (SHAP)** with a robust **Geospatial Analytics Dashboard**, BhoomiGuard empowers decision-makers to proactively mitigate risks rather than reacting to them.

---

## 🌟 Key Features

### 1. Custom AI Branding & Clean Interface
* **Custom Logo Integration**: Features a custom AI/Satellite logo natively integrated into the login page and the inner system dashboard sidebar.
* **Minimalist Login Portal**: A clean, professional entry point stripped of hardcoded credentials and unnecessary text, featuring an instant theme toggle right on the login screen.

### 2. Explainable AI & Predictive Engine
* **Machine Learning Model**: Powered by a Random Forest Classifier trained on 14 project parameters to accurately predict if a land parcel acquisition will face delays.
* **Explainable AI (SHAP)**: Doesn't just give a "Yes/No" prediction. It breaks down the mathematical reasoning using SHAP values to explain exactly *why* a project is at risk.
* **Dynamic AI Recommendations**: Evaluates SHAP risk drivers to generate intelligent, actionable mitigation strategies.

### 3. Comprehensive Analytics Dashboard
* **Geospatial Risk Map**: A fully interactive Leaflet-based map rendering real-time, CSV-backed data across Gujarat districts. Features a clean OpenStreetMap tile design, small uniform risk dots, and **instant data hover tooltips**.
* **Dynamic Visualizations**: Utilizes Recharts to present delay rates, district leaderboards, and stage distributions derived dynamically from the dataset.
* **Model Performance Tracking**: Live tracking of test-set metrics including F1 Score, F2 Score (Recall prioritized), Accuracy, and a full Confusion Matrix.

### 4. Advanced UI/UX & Theming
* **Global Light / Dark Mode Customization**: A seamless theme switcher (Sun/Moon toggle) that instantly updates the entire UI without page refreshes. Starts seamlessly in Dark Mode by default across the entire app.
* **Role-Based Access Control (RBAC)**: Secure JWT-based authentication system structured into three strict tiers (Admin, District Officer, Project Officer) with specialized route guarding.

---

## 🏗️ Technology Stack

**Frontend**
* React 18 & Vite
* TailwindCSS 3 (Custom Light/Dark Theme System)
* React-Router-DOM (Role-guarded routes)
* Recharts (Data visualization)
* React-Leaflet & OpenStreetMap (Geospatial mapping)

**Backend**
* Python 3.14 & FastAPI
* SQLAlchemy & SQLite (Database)
* bcrypt & PyJWT (Security)
* Pandas & NumPy (Data Processing)

**Machine Learning**
* Scikit-Learn (Random Forest Pipeline)
* SHAP (TreeExplainer for Feature Importance)
* Joblib (Model persistence)

---

## 🚀 Running the Project Locally

### Step 1: Start the Backend Server
The backend requires Python and hosts the FastAPI server on port 8000.

```bash
cd backend
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload --port 8000
```
*Note: The SQLite database and the default user accounts will be seeded automatically when the backend starts for the first time.*

### Step 2: Start the Frontend Application
The frontend runs on Vite and communicates with the backend via a local proxy.

```bash
cd frontend

# Install Node modules
npm install

# Start the development server
npm run dev
```

### Step 3: Access the Application
Open your web browser and navigate to the Vite Local URL (usually `http://localhost:5173` or `http://localhost:5174`).

---

## 🔐 Default Login Credentials

Use any of the following credentials to log in and explore the role-based features:

| Role | Username | Password |
|------|----------|----------|
| **Administrator** | `admin` | `admin123` |
| **District Officer** | `districtofficer` | `district123` |
| **Project Officer** | `projectofficer` | `project123` |

---

## 📂 Project Structure

```text
Bhoomiguard/
├── backend/
│   ├── app/
│   │   ├── api/         # FastAPI Route controllers (predict, auth, analytics)
│   │   ├── core/        # Security and configuration
│   │   ├── models/      # SQLAlchemy Database schemas
│   │   └── services/    # Business logic (SHAP, Recommendations, ML loading)
│   ├── data/            # CSV Datasets
│   ├── ml/              # Model training scripts
│   └── models_store/    # Saved .joblib ML models and metadata
│
└── frontend/
    ├── src/
    │   ├── components/  # Reusable UI widgets (RiskMap, Charts, Sidebar)
    │   ├── hooks/       # React Context (useAuth)
    │   ├── layouts/     # Main Layouts with Theme Toggles
    │   ├── pages/       # Route Views (Dashboard, Predict, Analytics)
    │   └── services/    # Axios API communication
    ├── tailwind.config.js
    └── index.html
```
