# MediDash - Medical Dashboard for Disease Prediction

MediDash is a comprehensive medical dashboard application designed for public health surveillance and disease prediction. The system analyzes health records, environmental data, and demographic information to provide insights into disease trends and predict potential outbreaks.

## Features

- **Dashboard Overview**: Summary of key health metrics and recent records
- **Disease Prediction**: ML-powered forecasting of disease trends based on historical data

## Technology Stack

- **Backend**: Django 5.0.3
- **Database**: PostgreSQL 14
- **Data Analysis**: Pandas, NumPy, Scikit-learn
- **Frontend**: Bootstrap 5, Chart.js, Leaflet.js
- **Containerization**: Docker, Docker Compose

## Data Models

The system uses a comprehensive data model to track health metrics:

- **Location**: Geographic locations with coordinates and population data
- **Demographics**: Population demographic information including age, gender, and socioeconomic status
- **Person**: Individual records linked to demographics and locations
- **MedicalHistory**: Individual medical history including chronic conditions and allergies
- **Disease**: Disease information including contagion rates and symptoms
- **EnvironmentalFactor**: Environmental metrics like air quality, temperature, and humidity
- **HealthcareResource**: Healthcare availability metrics like hospital beds and medical personnel
- **HealthRecord**: Core health event tracking with disease severity, risk levels, and outcomes

## Project Structure

```
MediDash/
├── dashboard/                # Main Django application
│   ├── models.py             # Data models for health records
│   ├── views.py              # View controllers
│   ├── urls.py               # URL routing
│   ├── management/
│   │   ├── commands/         # Custom management commands
│   │       ├── import_data.py        # CSV data import command
│   │       ├── import_sample_data.py # Generate sample data
├── templates/                # HTML templates
│   ├── base.html             # Base template with navigation
│   ├── dashboard/            # Dashboard-specific templates
├── static/                   # Static assets (JS, CSS)
├── MediDash/                 # Django project settings
├── entrypoint.sh             # Docker entrypoint script
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker services configuration
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management script
└── public_health_surveillance_dataset.csv  # Sample dataset
```

## Setup Instructions

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MediDash.git
   cd MediDash
   ```

2. Build and start the containers:
   ```bash
   docker compose up --build
   ```

3. Apply migrations and create initial database structure:
   ```bash
   docker compose exec web python manage.py migrate
   ```

4. Populate the database with sample data:
   ```bash
   docker compose exec web python manage.py import_sample_data
   ```

5. Alternatively, import data from the CSV file:
   ```bash
   docker compose exec web python manage.py import_data /app/public_health_surveillance_dataset.csv
   ```

6. Access the application at http://localhost:8000

### Manual Setup

1. Clone the repository and create a virtual environment:
   ```bash
   git clone https://github.com/yourusername/MediDash.git
   cd MediDash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure PostgreSQL database and set environment variables:
   ```
   DATABASE=postgres
   SQL_ENGINE=django.db.backends.postgresql
   SQL_DATABASE=medidash
   SQL_USER=postgres
   SQL_PASSWORD=your_password
   SQL_HOST=localhost
   SQL_PORT=5432
   ```

4. Apply migrations and run the server:
   ```bash
   python manage.py migrate
   python manage.py import_sample_data  # Generate sample data
   python manage.py runserver
   ```

5. Access the application at http://localhost:8000

## Data Processing

The system processes several types of data:

- **Health Records**: Patient health data including symptoms and diagnosis
- **Environmental Factors**: Air quality, temperature, humidity, etc.
- **Demographics**: Population information by location
- **Healthcare Resources**: Availability of medical resources

## Data Import Options

MediDash provides two methods for data import:

1. **Sample Data Generation**: Use the `import_sample_data` command to generate synthetic data for testing and demonstration
   ```bash
   python manage.py import_sample_data
   ```

2. **CSV Import**: Import real data from a CSV file using the `import_data` command
   ```bash
   python manage.py import_data /path/to/your/data.csv
   ```


## Dashboard Sections

- **Overview**: High-level summary of key health metrics
- **Disease Prediction**: Machine learning models to forecast disease trends

## Development

### Running Tests

```bash
python manage.py test
# or using pytest
pytest
```

### Code Style

This project follows PEP 8 style guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
