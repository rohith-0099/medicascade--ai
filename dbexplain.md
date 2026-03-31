# Database Overview for MediCascade AI

This document explains what databases are used in this project and how they work.

## Databases Used
The project exclusively uses **SQLite**, a lightweight, serverless relational database built into Python's standard library (`sqlite3`). No external database servers like PostgreSQL, MySQL, or MongoDB are configured or required. 

The database file is created and managed locally by the application itself. Its storage path is dictated by the environment variable `DB_PATH`, which safely defaults to `outputs/medicascade.db` inside the backend directory.

## Architecture & How It Works

### Database Schema & Tables
The database maintains all of the application's historical and evaluative data using three primary SQL tables:

1. **`cases`**: This is the core table. Every single clinical case processed by the application is recorded here. It stores:
   - Identifiers & metadata: `case_id`, `source_pdf`, `pdf_path`
   - Clinical outcomes: `primary_diagnosis`, `icd10_code`, `icd10_description`
   - Pipeline metrics: `confidence`, `processing_time`
   - Payload logic (stored as JSON strings): `layer1_json` (specialist findings), `layer2_json` (final assessment), and `drug_warnings`.
   - Timestamps: `ingested_at`, `created_at` (indexed for faster chronologic queries).
   
2. **`feedback`**: Collects clinician feedback on the application's diagnostic accuracy. It uses a foreign key referencing the `cases` table (`case_id`), and stores an integer `rating` (bounded from 1 to 5), an optional textual `comment`, and a timestamp.

3. **`audit_log`**: A simple event-logging and auditing table used to sequentially record internal system actions, such as when an initial case is saved (`case_saved`) or when user feedback is successfully stored (`feedback_submitted`).

### Application Flow & Mechanism
The data logic is entirely encapsulated inside `backend/database.py`, which is imported and utilized by the `backend/main.py` routing layer.

1. **Automatic Initialization**: 
   When the FastAPI application initializes (`backend/main.py`), it automatically calls `init_db()`. This guarantees the underlying SQLite `.db` file exists and safely creates the required schemas identically every time the app starts.

2. **Storing AI Diagnostic Results**: 
   When a user submits a PDF to the `/api/diagnose` endpoint, the document securely moves through the 3-Layer internal AI pipeline. Right before returning the HTTP response, `save_case()` is invoked. This explicitly inserts or replaces a `cases` table record consolidating all the data from the layers (like intermediate JSONs, processing times, and ICD-10 codes) into a single row, whilst concurrently leaving a breadcrumb in the `audit_log`.

3. **API Retrieval & Metrics Engine**:
   - **History**: The frontend table is fed by `/api/history`, which calls `get_case_history()` to perform bulk SQL `SELECT` operations across the `cases` table to present chronological summaries.
   - **Aggregated Statistics**: Endpoints like `/api/stats` directly run statistical SQL statements over the database (`get_stats()`). They fetch real-time operational metrics across all tables, including total record counts (`COUNT`), averages (`AVG` for confidence and times), and calculating the top 5 diagnoses using `GROUP BY`.
   - **FHIR Export (`/api/fhir/{case_id}`)**: Pulls case data directly from the sqlite table using `get_case()` and maps it into standard FHIR R4 JSON schemas.

4. **Clinician Feedback Routing**:
   The `/api/feedback/{case_id}` endpoint receives user validations, passing them to `save_feedback()`. This function inserts the user rating against the unique `case_id` directly into the `feedback` table while logging the action into the `audit_log`.
