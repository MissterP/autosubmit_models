# Autosubmit Models API

API for obtaining statistics and data related to models used in Autosubmit experiments.

## Requirements

- Python 3.9 or higher
- SQLite (for development and testing)
- TimescaleDB (for production metrics storage)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd autosubmit_models
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp sample.env .env
# Edit .env with your configuration
```

## Architecture

The application follows a clean architecture pattern with the following components:

- **API Layer**: REST API built with FastAPI
- **Domain Layer**: Business logic, models, interfaces
- **Data Layer**: Data access controllers for different data sources
- **Workers**: Background workers for periodic data collection

### Data Sources

The system can work with two data sources:

1. **ECEARTH Database**: Direct access to experiment data (legacy mode)
2. **TimescaleDB**: Time-series database for storing historical metrics (recommended)

For production environments, the TimescaleDB integration offers several benefits:
- Historical metrics tracking
- Reduced coupling with the external ECEARTH service
- Better performance for API queries
- Ability to extend with additional metrics and statistics

## TimescaleDB Setup

1. Install TimescaleDB following the [official instructions](https://docs.timescale.com/install/)

2. Create a database for metrics:
```sql
CREATE DATABASE metrics;
```

3. Connect to the database and install the TimescaleDB extension:
```sql
\c metrics
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
```

4. The application will automatically create the required tables when started

## Execution

### API Server

Start the API server to handle requests:

```bash
./scripts/run_api.sh
```

The API will be available at: `http://localhost:8002`
Swagger UI Documentation: `http://localhost:8002/docs`

### API Workers

Start the background workers to collect metrics:

```bash
# Start all workers
./scripts/run_workers.sh

# Start a specific worker
./scripts/run_workers.sh popular_models
```

API workers will collect metrics from the source database at regular intervals and store them in TimescaleDB.

### Docker

You can also use Docker for both the API and workers:

```bash
# Development environment
docker-compose -f docker/compose.dev.yaml up

# Production environment
docker-compose -f docker/compose.prod.yaml up
```

## New Workflow

The system now follows this workflow:

1. **API Workers** periodically fetch data from the ECEARTH database, calculate metrics, and store them in TimescaleDB
2. **API Endpoints** fetch pre-calculated metrics from TimescaleDB when users make requests
3. Any filters provided in API requests are applied to the TimescaleDB data

This approach provides several benefits:
- Reduced load on the ECEARTH database
- Historical data tracking (metrics are stored with timestamps)
- Faster API responses
- Decoupling from the external service

## Adding New Metrics

The system is designed to be easily extensible with new metrics:

1. Create a new controller in `src/data/controllers/metrics/` following the pattern of existing controllers
2. Create a new worker in `src/workers/` that inherits from `BaseWorker`
3. Register the new worker in `src/workers/api_worker.py`

## Tests

The project implements TDD (Test-Driven Development) with unit and integration tests.

### Run all tests:
```bash
make test
```

### Run tests with coverage:
```bash
make test-cov
```

Coverage reports are generated in:
- Terminal: Coverage summary by file
- `htmlcov/`: Detailed HTML report
- `coverage.xml`: XML report for CI tools integration

## Linting with Flake8

The project uses Flake8 to validate code quality.

```bash
make lint
```

## Security Review

The project includes security analysis with Bandit and Safety:

```bash
make security
```

## Continuous Integration

The project includes GitHub Actions for:
- Automatic test execution
- Flake8 linting verification
- Security analysis
- Coverage report generation

### Run all validations:
```bash
make check
```

