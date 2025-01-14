from flask import Flask, render_template, request, redirect, url_for
from sqlite3 import connect
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Database operations
def db_query(query, args=()):
    conn = connect('vibe_bot.db')
    cursor = conn.cursor()
    cursor.execute(query, args)
    conn.commit()
    result = cursor.fetchall()
    conn.close()
    return result

# Initialize database tables
def init_db():
    db_query('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            context TEXT,
            location TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db_query('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            reputation INTEGER DEFAULT 0
        )
    ''')

# Home page
@app.route('/')
def home():
    welcome_message = "🌟 Welcome to the Vibe Check Web App! 🌟"
    return render_template_string(home_html, message=welcome_message)

# Report submission page
@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        category = request.form['category']
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        context = request.form['context']
        user_id = 1  # Hardcoded user ID for now

        # Save the report to the database
        location = f"{latitude},{longitude}"
        db_query('''
            INSERT INTO reports (user_id, category, context, location)
            VALUES (?, ?, ?, ?)
        ''', (user_id, category, context, location))

        return redirect(url_for('home'))

    categories = ['Crowded', 'Noisy', 'Festive', 'Calm', 'Suspicious']
    return render_template_string(report_html, categories=categories)

# List all reports
@app.route('/reports')
def list_reports():
    reports = db_query('SELECT id, category, context, location, timestamp FROM reports ORDER BY timestamp DESC')
    return render_template_string(reports_html, reports=reports)

# HTML Templates (Embedded in the code)
home_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Check Web App</title>
</head>
<body>
    <h1>Vibe Check Web App</h1>
    <p>{{ message }}</p>
    <a href="/report">Submit a Report</a><br>
    <a href="/reports">View Reports</a>
</body>
</html>
'''

report_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Submit a Vibe Report</title>
</head>
<body>
    <h1>Submit a Vibe Report</h1>
    <form method="POST">
        <label for="category">Category:</label>
        <select name="category" id="category">
            {% for category in categories %}
                <option value="{{ category }}">{{ category }}</option>
            {% endfor %}
        </select><br><br>

        <label for="latitude">Latitude:</label>
        <input type="text" name="latitude" id="latitude" required><br><br>

        <label for="longitude">Longitude:</label>
        <input type="text" name="longitude" id="longitude" required><br><br>

        <label for="context">Context:</label>
        <textarea name="context" id="context" rows="4" cols="50" required></textarea><br><br>

        <button type="submit">Submit Report</button>
    </form>
</body>
</html>
'''

reports_html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vibe Reports</title>
</head>
<body>
    <h1>Vibe Reports</h1>
    <ul>
        {% for report in reports %}
            <li>
                <strong>Category:</strong> {{ report[1] }}<br>
                <strong>Context:</strong> {{ report[2] }}<br>
                <strong>Location:</strong> {{ report[3] }}<br>
                <strong>Timestamp:</strong> {{ report[4] }}
            </li>
            <hr>
        {% endfor %}
    </ul>
</body>
</html>
'''

# Initialize the database and run the app
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
