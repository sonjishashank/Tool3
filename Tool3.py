import io
from flask import Flask, Response, jsonify, send_file
from flask_cors import CORS
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
from matplotlib.backends.backend_pdf import PdfPages
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set worker timeout to 600 seconds (10 minutes)
app.config['TIMEOUT'] = 1800

# Database credentials
DB_HOST = "dpg-cobrpren7f5s73ftpqrg-a.oregon-postgres.render.com"
DB_DATABASE = "sheshank_sonji"
DB_USER = "sheshank_sonji_user"
DB_PASSWORD = "Lo2Ze5zVZSRPGxDLCg5WAKUXUfxo7rrZ"

# Create engine for connecting to PostgreSQL database
engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}")

def plot_crime_occurrence(district_name):
    # Read data from PostgreSQL into a Pandas DataFrame
    query = f"SELECT * FROM tool3 WHERE district_name = '{district_name}'"
    df = pd.read_sql_query(query, engine)

    if df.empty:
        return None

    # Manually convert the date column to datetime format
    df['date_time'] = pd.to_datetime(df['date_time'])

    # Extract hour, day of week, month, and season from date_time
    df['hour'] = df['date_time'].dt.hour
    df['day_of_week'] = df['date_time'].dt.dayofweek
    df['month'] = df['date_time'].dt.month
    df['season'] = df['date_time'].dt.month % 12 // 3 + 1

    units = df['unitname'].unique()
    time_periods = ['hour', 'day_of_week', 'month', 'season']
    pdf_filename = f"{district_name}_crime_occurrence.pdf"

    with PdfPages(pdf_filename) as pdf_pages:
        for unit in units:
            unit_data = df[df['unitname'] == unit]
            for time_period in time_periods:
                plt.figure(figsize=(10, 6))
                sns.countplot(x=time_period, data=unit_data, palette='viridis')
                plt.title(f'Crime Occurrence by {time_period.capitalize()} in {district_name.title()}, Unit: {unit}')
                plt.xlabel(time_period.capitalize())
                plt.ylabel('Number of Crimes')
                plt.tight_layout()

    # Convert the plot to bytes
    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='pdf')
    plt.close()

    return img_bytes.getvalue()

# Route for downloading the PDF file
@app.route('/download/<district>', methods=['GET'])
def download_pdf(district):
    pdf_bytes = plot_crime_occurrence(district)
    if pdf_bytes:
        return Response(pdf_bytes, mimetype='application/pdf',
                        headers={'Content-Disposition': f'attachment;filename={district}_crime_distribution.pdf'})
    else:
        return jsonify({"error": "No data available or invalid district"}), 404
