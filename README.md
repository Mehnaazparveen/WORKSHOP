# Smart Campus Lost & Found Matcher 🎓🔍

A lightweight web application designed for college campuses and hands-on workshops that connects students who lost personal items with students who found them. It uses natural language processing (TF-IDF vectorization and Cosine Similarity via Scikit-learn) to automatically identify and rank matches between lost and found item reports.

---

## 🏛️ Project Architecture

```
                    +-----------------------------+
                    |        Web Browser          |
                    | (Responsive HTML5/CSS3/JS)  |
                    +--------------+--------------+
                                   | HTTP Requests
                                   v
                    +-----------------------------+
                    |       Flask Web App         |
                    |          (app.py)           |
                    +-------+-------------+-------+
                            |             |
                            v             v
            +---------------------+ +----------------------+
            |   Database Layer    | |   Matching Engine    |
            |    (database.py)    | |    (matcher.py)      |
            |     SQLite DB       | | Scikit-learn TF-IDF  |
            +---------------------+ +----------------------+
```

### Components:
1. **Presentation Layer (Frontend):**
   - Jinja2 templates (`templates/`) with modern UI styling (`static/css/style.css`) and responsive layout.
   - Interactive client script (`static/js/main.js`) for dynamic filtering and status updates.

2. **Application Layer (Flask Controller - `app.py`):**
   - Handles HTTP routing, form validations, flash notifications, and renders views.
   - Coordinates between the database and the similarity matching engine.

3. **Data Layer (SQLite - `database.py`):**
   - Native SQLite database (`campus_lost_found.db`).
   - Stores item details: title, category, color, description, date reported, location, contact info, and status (`Active` / `Returned`).

4. **Intelligence Layer (NLP Matching Engine - `matcher.py`):**
   - Merges item attributes into contextual text representations.
   - Uses `TfidfVectorizer` to extract term frequencies and importance weights (ignoring common English stopwords).
   - Computes pairwise `cosine_similarity` scores between lost and found items.
   - Returns top candidate matches ranked by confidence percentage.

---

## 📁 Folder Structure

```text
campus_lost_found/
├── app.py                  # Main Flask application and route controllers
├── database.py             # SQLite database connection, schema setup & queries
├── matcher.py              # Scikit-learn TF-IDF & Cosine Similarity matching logic
├── requirements.txt        # Python package dependencies
├── README.md               # Architecture documentation & setup guide
├── static/
│   ├── css/
│   │   └── style.css       # Clean, modern, responsive styling
│   └── js/
│       └── main.js         # Frontend interactivity (filtering, status toggles)
├── templates/
│   ├── base.html           # Base layout with navbar, alerts, footer
│   ├── index.html          # Dashboard with overview metrics & quick actions
│   ├── report_lost.html    # Form to submit a lost item
│   ├── report_found.html   # Form to submit a found item
│   ├── items.html          # Browse lost and found items in separate sections
│   ├── matches.html        # Smart matcher view with similarity scores
│   └── item_detail.html    # Detailed item view with on-the-fly match recommendations
└── tests/
    └── test_app.py         # Automated test suite (database, matcher, routes)
```

---

## 🚀 Getting Started & Local Setup

### 1. Prerequisites
- Python 3.9+ (Python 3.12 supported)
- `pip` (Python package installer)

### 2. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 4. Running Automated Tests
To run the automated test suite:
```bash
python -m unittest discover tests/
```

---

## 💡 Workshop Demonstration Guide

1. **Report a Lost Item:** Go to **Report Lost Item** and report e.g. "Matte Black HP Pavilion Laptop with stickers in Central Library".
2. **Report a Found Item:** Go to **Report Found Item** and report e.g. "Black HP laptop discovered near library 2nd floor study carrel".
3. **View Smart Matches:** Navigate to **Smart Matcher** to see the system automatically pair these two reports with similarity scores, highlighting matching attributes.
4. **Mark as Returned:** Once an item is claimed, click **Mark as Returned** to update its status and remove it from active matches.
