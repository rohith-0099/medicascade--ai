# Known Limitations
- ICD-10 local lookup covers ~130 diagnoses only
- Imaging agent requires HF_API_TOKEN for actual vision
- Ollama fallback requires manual installation
- FDA rate limit: 40 req/min (handled with backoff)
- MRI speedup is theoretical; actual time varies by hardware
- FHIR export is JSON-formatted, not schema-validated
