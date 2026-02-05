# Smart EV Charging Platform - Project Documentation

## Team Details
- **Team Name:** CodeCrafters
- **Team Members:**
  - Prince Jha
  - Sachin Jha
  - Bhavesh Jadhav

---

## Domain of Your Project
**Electric Vehicle (EV) Charging Infrastructure & Services** - A comprehensive platform for discovering, booking, and managing EV charging stations with AI-powered features for enhanced user experience.

---

## Idea

### Problem Statement
The electric vehicle adoption is rapidly increasing, but users face significant challenges:
- **Lack of Visibility**: No unified platform to discover available charging stations
- **Inefficient Planning**: Users cannot predict peak hours or plan cost-effective charging
- **Poor User Experience**: Complex interfaces for finding and booking stations
- **Limited Insights**: Users don't understand their charging patterns or environmental impact
- **Communication Gap**: No easy way to get support for charging-related queries

### Solution
**Smart EV Charging Platform** - An intelligent, all-in-one web application that provides:

1. **Interactive Station Discovery** - Google Maps integration with color-coded stations based on availability, pricing, and eco-friendliness
2. **AI-Powered Chatbot** - 24/7 support for station queries, pricing information, and troubleshooting
3. **Predictive Analytics** - Real-time forecasts of station demand, peak hours, and price trends
4. **Personalized Insights** - Comprehensive dashboard showing user charging habits, spending trends, and environmental impact
5. **Natural Language Search** - Find stations by describing needs in natural language (e.g., "cheap and fast stations nearby")
6. **Multi-User Platform** - Support for Users, Station Owners, and Administrators with role-based dashboards

---

## Tech Stack Used

### Backend
- **Flask 2.3.2** - Python web framework for backend API and routing
- **SQLite** - Lightweight database for storing users, stations, and charging sessions
- **Python 3.8+** - Core programming language

### AI/ML Services
- **Google Generative AI (Gemini)** - Powers chatbot, analytics, insights, and NL search features
- **Natural Language Processing** - For intelligent query understanding and responses

### Frontend
- **HTML5/CSS3** - Responsive web templates
- **JavaScript** - Interactive features and dynamic UI
- **Bootstrap/Tailwind CSS** - Responsive design framework
- **Google Maps JavaScript API** - Interactive mapping and geolocation services

### Additional Technologies
- **python-dotenv** - Environment variable management for API keys
- **Session Management** - Flask sessions for user authentication
- **Geolocation API** - Browser geolocation for finding nearby stations
- **Haversine Formula** - Distance calculation between coordinates

---

## How to Execute the Code

### Prerequisites
- Python 3.8 or higher installed
- Google Cloud API Keys:
  - Google Maps JavaScript API Key
  - Google Generative AI (Gemini) API Key
- pip package manager
- Web browser (Chrome, Firefox, Edge, Safari)
- Windows/Mac/Linux operating system

### Step-by-Step Setup Instructions

#### 1. **Clone/Download the Project**
```bash
# Navigate to project directory
cd "Smart EV Charging"
```

#### 2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

**Required Packages:**
- Flask==2.3.2
- google-generativeai>=0.3.0
- python-dotenv>=1.0.0

#### 3. **Set Up Environment Variables**

Create a `.env` file in the project root directory with the following:

```
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
GEMINI_API_KEY=your_google_gemini_api_key_here
```

**Getting API Keys:**

**Google Maps API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "Maps JavaScript API"
4. Go to Credentials → Create API Key
5. Restrict to HTTP referrers (optional but recommended)
6. Copy the key to your `.env` file

**Google Gemini API Key:**
1. Go to [Google AI Studio](https://console.ai.google.com/)
2. Click "Create API Key"
3. Copy the key to your `.env` file

#### 4. **Initialize the Database** (First Time Only)
```bash
python verify_db.py
```

This will:
- Create SQLite database
- Initialize all tables (users, stations, charging_sessions, admin)
- Create a default admin account (username: `admin`, password: `admin123`)

#### 5. **Seed Demo Data** (Optional - For Testing)
```bash
python seed_demo_data.py
```

This populates the database with sample stations and test data.

#### 6. **Run the Application**

**On Windows (PowerShell):**
```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
python app.py
```

**On Mac/Linux:**
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py
```

#### 7. **Access the Application**
Open your web browser and navigate to:
```
http://localhost:5000
```

### Default Login Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Access: http://localhost:5000/admin/login

**Demo User Accounts:** (After running seed_demo_data.py)
- Create new accounts via registration at http://localhost:5000/register

## Troubleshooting(If required)

### Common Issues & Solutions

**Issue:** "ModuleNotFoundError: No module named 'flask'"
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Issue:** "Google Maps API key not valid"
- Verify API key in `.env` file
- Ensure Maps JavaScript API is enabled in Google Cloud Console
- Check API key restrictions

**Issue:** "GEMINI_API_KEY environment variable not found"
- Create `.env` file with your API key
- Restart the Flask application
- Or set environment variable: `$env:GEMINI_API_KEY = "your_key"`

**Issue:** "Database is locked"
- Close any open database connections
- Restart the Flask application
- Check no other instances are running

---

## Demo Video/Link to Hosted Website & Repository

## <span style="color:#1f6feb; font-size:1.35em;">📦 GitHub Repository</span>

🔗 **Repository Link:**  
https://github.com/jadhavbhavesh032-code/smart-ev-charging


## <span style="color:#1f6feb; font-size:1.35em;">🚀 Deployment</span> 

- **Production:**  
  https://smart-ev-charging.onrender.com


## <span style="color:#1f6feb; font-size:1.35em;">🎥 Demo Video</span>

▶️ **Watch Demo:**  
https://drive.google.com/file/d/1sxRucvn68sS_PPAdoi_TwBxTrCbmyPyT/view?usp=drive_link

### API Keys Required
- Google Maps API: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- Gemini AI API: [https://console.ai.google.com/](https://console.ai.google.com/)

### Documentation Files
- `FEATURES_OVERVIEW.md` - Detailed feature descriptions
- `DEPLOYMENT_CHECKLIST.md` - Production deployment guide
- `GOOGLE_MAPS_FEATURE_GUIDE.md` - Maps feature documentation
- `GEMINI_SETUP_COMPLETE.md` - AI setup instructions

---

## Code Sample

### Running the Application

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API keys in .env file
# GOOGLE_MAPS_API_KEY=your_key
# GEMINI_API_KEY=your_key

# 3. Initialize database
python verify_db.py

# 4. Seed demo data (optional)
python seed_demo_data.py

# 5. Run the Flask app
python app.py

# 6. Open browser
# http://localhost:5000
```

### Example: Creating a Charging Session
```python
# From routes/user_routes.py
from models.db import get_db

def book_charging_session(station_name, units, user_id):
    conn = get_db()
    cur = conn.cursor()
    
    # Calculate cost
    price_per_unit = get_station_price(station_name)
    amount = units * price_per_unit
    
    # Create session
    cur.execute("""
        INSERT INTO charging_sessions 
        (user_id, station_name, units, amount, status)
        VALUES (?, ?, ?, ?, 'Pending')
    """, (user_id, station_name, units, amount))
    
    conn.commit()
    conn.close()
    return True
```

### Example: AI Chat Query
```python
# From ai/chatbot.py
import google.generativeai as genai

def get_chatbot_response(user_query, context):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    You are a helpful EV Charging Station Assistant.
    Context: {context}
    User Query: {user_query}
    """
    
    response = model.generate_content(prompt)
    return response.text
```



