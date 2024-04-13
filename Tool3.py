import io
from flask import Flask, Response, jsonify
from flask_cors import CORS
import pandas as pd
from sqlalchemy import create_engine
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import seaborn as sns

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

# Function to plot crime occurrence for a specific district and unit
def plot_crime_occurrence(district, unit):
    # Query to fetch data for the specified district and unit
    query = f"SELECT * FROM tool3 WHERE district_name = '{district}' AND unitname = '{unit}'"
    df = pd.read_sql_query(query, engine)

    if df.empty:
        return None

    # Convert date_time to datetime format
    df['date_time'] = pd.to_datetime(df['date_time'])

    # Extract time periods
    df['hour'] = df['date_time'].dt.hour
    df['day_of_week'] = df['date_time'].dt.dayofweek
    df['month'] = df['date_time'].dt.month
    df['season'] = (df['month'] - 1) // 3 + 1

    # Define time periods to plot
    time_periods = ['hour', 'day_of_week', 'month', 'season']

    # Create PDF filename
    pdf_filename = f"{district}_{unit}_crime_occurrence.pdf"

    # Create PDF file
    with PdfPages(pdf_filename) as pdf_pages:
        for time_period in time_periods:
            plt.figure(figsize=(10, 6))
            sns.countplot(x=time_period, data=df, palette='viridis')
            plt.title(f'Crime Occurrence by {time_period.capitalize()} in {district.title()}, Unit: {unit}')
            plt.xlabel(time_period.capitalize())
            plt.ylabel('Number of Crimes')
            plt.tight_layout()
            pdf_pages.savefig()
            plt.close()

    # Read the saved PDF file and return it as a byte stream
    with open(pdf_filename, 'rb') as f:
        pdf_bytes = f.read()

    return pdf_bytes

# Route for downloading the PDF file for a specified district and unit
@app.route('/download/<district>/<unit>', methods=['GET'])
def download_pdf(district, unit):
    pdf_bytes = plot_crime_occurrence(district, unit)
    if pdf_bytes:
        response = Response(pdf_bytes, mimetype='application/pdf',
                            headers={'Content-Disposition': f'attachment;filename={district}_{unit}_crime_occurrence.pdf'})
        return response
    else:
        return jsonify({"error": "No data available or invalid district/unit"}), 404

# Route to get the list of districts
@app.route('/get_districts', methods=['GET'])
def get_districts():
    query = "SELECT DISTINCT district_name FROM tool3"
    districts_df = pd.read_sql_query(query, engine)
    districts = districts_df['district_name'].tolist()
    return jsonify(districts)

# Route to get the list of units based on the selected district
@app.route('/get_units/<district>', methods=['GET'])
def get_units(district):
    query = f"SELECT DISTINCT unitname FROM tool3 WHERE district_name = '{district}'"
    units_df = pd.read_sql_query(query, engine)
    units = units_df['unitname'].tolist()
    return jsonify(units)

if __name__ == '__main__':
    app.run(debug=True)
