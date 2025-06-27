# Therapy Assistant Agent

An AI-powered diagnostic and treatment support tool for mental health professionals.

## Overview

This project helps licensed therapists and psychiatrists identify mental health disorders and suggest evidence-based treatment options using advanced AI, RAG (Retrieval-Augmented Generation), and OpenAI integration. Built with React frontend and FastAPI backend, deployable via Docker Compose with PostgreSQL.

## Features

- **Diagnostic Support**: DSM-5-TR and ICD-11 based disorder identification
- **Treatment Recommendations**: Evidence-based therapy and intervention suggestions  
- **AI Integration**: OpenAI GPT-4 powered clinical assistance
- **Mobile Ready**: Cross-platform support with Capacitor for Android/iOS
- **Production Ready**: Complete Docker deployment with PostgreSQL
- **Synthetic Data Testing**: Comprehensive test data for development and validation

## Project Structure

```
therapy-assistant-agent/
├── backend/                    # FastAPI backend service
│   ├── app/                   # Application code
│   │   ├── api/              # API endpoints (auth, diagnostic, treatment)
│   │   ├── core/             # Core functionality (auth, config, database)
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic (OpenAI, vector DB, knowledge base)
│   │   └── utils/            # Utility functions
│   ├── alembic/              # Database migrations
│   ├── data/                 # Backend data storage
│   ├── tests/                # Backend tests
│   ├── Dockerfile            # Production Docker image
│   └── requirements.txt      # Python dependencies
├── frontend/                   # React frontend application
│   ├── src/                  # Source code
│   │   ├── components/       # React components
│   │   ├── contexts/         # React Context (auth, state)
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Utility functions
│   ├── public/               # Static assets
│   ├── tests/                # Frontend tests
│   ├── Dockerfile.prod       # Production Docker image
│   ├── nginx.conf            # Nginx configuration
│   ├── capacitor.config.ts   # Mobile app configuration
│   └── package.json          # Node.js dependencies
├── migrations/                 # Root-level Alembic migrations
├── nginx/                     # Nginx reverse proxy configs
├── data/                      # Data storage
│   ├── synthetic/            # Generated test data
│   ├── raw/                  # Raw datasets
│   └── processed/            # Processed datasets
├── scripts/                   # Utility scripts
├── docs/                     # Documentation
├── docker-compose.yml        # Production deployment
├── .env.production          # Environment variables template
├── README-production.md     # Production deployment guide
└── init-db.sql             # Database initialization
```

## Quick Start

### Production Deployment (Recommended)
```bash
# 1. Set up environment variables
cp .env.production .env
# Edit .env with your actual production values

# 2. Generate secure keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# 3. Start all services
docker-compose up -d

# 4. Initialize database
docker-compose exec backend alembic upgrade head
```

### Development Setup

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# Set environment variables
export OPENAI_API_KEY=your_key_here
export DATABASE_URL=postgresql://therapy_user:therapy_pass@localhost:5432/therapy_assistant_db

# Run development server
uvicorn app.main_auth:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install

# Run development server
npm start

# For mobile development
npm run cap:add:android
npm run cap:add:ios
```

### Generate Test Data
```bash
python scripts/synthetic_data_generator.py
```

## Key Technologies

- **Frontend**: React with TypeScript, Tailwind CSS, React Router
- **Backend**: FastAPI with Python, JWT authentication, OpenAI integration
- **Database**: PostgreSQL with Alembic migrations
- **Deployment**: Docker Compose, Nginx reverse proxy
- **Mobile**: Capacitor for Android/iOS cross-platform deployment
- **AI**: OpenAI GPT-4, RAG with vector databases
- **Security**: bcrypt password hashing, rate limiting, CORS protection

## Development Phases

1. **Phase 1 (Complete)**: React migration, authentication, OpenAI integration
2. **Phase 2 (Complete)**: Production deployment with Docker and PostgreSQL
3. **Phase 3 (Future)**: Mobile app deployment and advanced AI features
4. **Phase 4 (Future)**: Advanced analytics and international deployment

## Documentation

- [Product Requirements Document](docs/PRD_Therapy_Assistant_Agent.md)
- [Development Tasks](docs/DEVELOPMENT_TASKS.md)
- [Data Validation Report](docs/data_validation_report.md)
- [Production Deployment Guide](README-production.md)

## Security & Compliance

- All sensitive data is externalized to environment variables
- Non-root containers for enhanced security
- Rate limiting and CORS protection
- Secure password hashing with bcrypt
- JWT token-based authentication
- Production-ready security headers

## Default Accounts

For development and testing:
- **Email**: demo.therapist@example.com
- **Password**: DemoTherapist123!
- **Role**: Therapist

## Contributing

This project is focused on defensive security and clinical decision support only. All contributions must follow ethical AI guidelines and clinical best practices.

## License

This project is intended for educational and research purposes in mental health technology.