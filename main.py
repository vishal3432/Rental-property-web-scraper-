from flask import Flask, send_file, jsonify
from scraper_engine import run_scraper

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Rental Scraper API</h1><p>Use /scrape to start and /download to get the CSV.</p>"

@app.route('/scrape')
def scrape():
    try:
        path = run_scraper()
        return jsonify({"status": "success", "message": "Data scraped!", "file": path})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/download')
def download():
    path = "results/rental_data.csv"
    return send_file(path, as_attachment=True)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)