# Therapy Assistant Agent

An AI-powered diagnostic and treatment support tool for mental health professionals.

## Overview

This project helps licensed therapists and psychiatrists identify mental health disorders and suggest evidence-based treatment options using advanced AI, RAG (Retrieval-Augmented Generation), and speech analysis capabilities.

## Features

- **Diagnostic Support**: DSM-5-TR and ICD-11 based disorder identification
- **Treatment Recommendations**: Evidence-based therapy and intervention suggestions  
- **Speech Analysis**: Voice pattern analysis and emotional tone detection
- **International Support**: Multi-language and cultural adaptation capabilities
- **Synthetic Data Testing**: Comprehensive test data for development and validation

## Project Structure

```
therapy-assistant-agent/
├── backend/                 # FastAPI backend service
│   ├── app/                # Application code
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core functionality
│   │   ├── models/        # Database models
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utility functions
│   ├── tests/             # Backend tests
│   └── requirements.txt   # Python dependencies
├── frontend/               # Vue.js frontend application
│   ├── src/               # Source code
│   │   ├── components/    # Vue components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
│   ├── tests/             # Frontend tests
│   └── package.json       # Node.js dependencies
├── data/                   # Data storage
│   ├── synthetic/         # Generated test data
│   ├── raw/              # Raw datasets
│   └── processed/        # Processed datasets
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── config/               # Configuration files
└── .github/workflows/    # CI/CD workflows
```

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Generate Test Data
```bash
python scripts/synthetic_data_generator.py
```

## Development Phases

1. **Phase 1 (MVP)**: Core diagnostic engine with synthetic data
2. **Phase 2**: Enhanced features and user management
3. **Phase 3**: Speech processing integration
4. **Phase 4**: Advanced analytics and international deployment

## Documentation

- [Product Requirements Document](docs/PRD_Therapy_Assistant_Agent.md)
- [Development Tasks](docs/DEVELOPMENT_TASKS.md)
- [Data Validation Report](docs/data_validation_report.md)

## Contributing

This project is focused on defensive security and clinical decision support only. All contributions must follow ethical AI guidelines and clinical best practices.

## License

This project is intended for educational and research purposes in mental health technology.