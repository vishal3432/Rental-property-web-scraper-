# 🏠 Rental Property Web Scraper & API

A production-ready web scraping system that extracts rental listings and serves data through a RESTful Flask API. This project demonstrates backend development, data cleaning with Pandas, and cloud deployment on Render.

## 🚀 Live Demo
You can interact with the live API here:
* **Trigger Scraper:** [Run Scraper Engine](https://rental-property-web-scraper.onrender.com/scrape)
* **Download Results:** [Download CSV Data](https://rental-property-web-scraper.onrender.com/download)

---

## 🛠️ Tech Stack
* **Backend:** Python, Flask
* **Scraping:** BeautifulSoup4, Requests
* **Data Processing:** Pandas
* **Deployment:** Render (Cloud), Gunicorn (WSGI Server)
* **Version Control:** Git & GitHub

---

## 📂 Project Structure
```text
├── main.py            # Flask API routes and server config
├── scraper_engine.py  # Scraping logic and data cleaning
├── requirements.txt   # Project dependencies
└── results/           # Storage for generated CSV files
