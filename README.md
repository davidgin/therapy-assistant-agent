# Therapy Assistant Agent

An AI-powered diagnostic and treatment support tool for mental health professionals.

## Overview

This project helps licensed therapists and psychiatrists identify mental health disorders and suggest evidence-based treatment options using advanced AI, RAG (Retrieval-Augmented Generation), voice analysis, and OpenAI integration. Built with FastAPI backend providing both web interface and mobile app support, featuring comprehensive speech pattern analysis for enhanced diagnostic accuracy, deployable via Docker Compose with PostgreSQL.

## Features

- **Diagnostic Support**: DSM-5-TR and ICD-11 based disorder identification
- **Treatment Recommendations**: Evidence-based therapy and intervention suggestions  
- **AI Integration**: OpenAI GPT-4 powered clinical assistance
- **Voice Analysis**: Advanced speech pattern, tone, and emotion recognition
- **Mobile App**: Native React Native app for Android/iOS with full feature parity
- **Web Interface**: Server-side rendered FastAPI web application
- **Production Ready**: Complete Docker deployment with PostgreSQL
- **Synthetic Data Testing**: Comprehensive test data for development and validation

## Project Structure

```
therapy-assistant-agent/
├── backend/                    # FastAPI backend service
│   ├── app/                   # Application code
│   │   ├── api/              # API endpoints (auth, diagnostic, treatment)
│   │   ├── config/           # Configuration (data sources, settings)
│   │   ├── core/             # Core functionality (auth, config, database)
│   │   ├── mcp/              # Model Context Protocol integration
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic (OpenAI, vector DB, knowledge base, data acquisition, audio analysis)
│   │   ├── templates/        # Jinja2 templates for web interface
│   │   ├── static/           # Static files for web interface (includes voice-recorder.js)
│   │   └── utils/            # Utility functions
│   ├── alembic/              # Database migrations
│   ├── data/                 # Backend data storage (acquired clinical data)
│   ├── tests/                # Backend tests
│   ├── Dockerfile            # Production Docker image
│   └── requirements.txt      # Python dependencies
├── mobile/                     # React Native mobile application
│   ├── src/                  # Source code
│   │   ├── components/       # React Native components (includes VoiceRecorder.tsx)
│   │   ├── contexts/         # React Context (auth, state)
│   │   ├── screens/          # Screen components
│   │   ├── services/         # API services (includes voiceService.ts)
│   │   ├── navigation/       # Navigation configuration
│   │   ├── types/            # TypeScript types
│   │   └── theme/            # Theme configuration
│   ├── android/              # Android platform code
│   ├── ios/                  # iOS platform code
│   ├── build-android.sh      # Android build script
│   ├── build-ios.sh          # iOS build script
│   └── package.json          # Node.js dependencies
├── migrations/                 # Root-level Alembic migrations
├── nginx/                     # Nginx reverse proxy configs
├── data/                      # Data storage
│   ├── synthetic/            # Generated test data
│   ├── raw/                  # Raw datasets
│   └── processed/            # Processed datasets
├── scripts/                   # Utility scripts (data download, setup)
│   ├── download_clinical_data.py  # Clinical data acquisition script
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

# 3. Start web application
docker-compose up -d

# 4. Initialize database
docker-compose exec web alembic upgrade head
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

# Run web development server
uvicorn app.main_web:app --reload

# Or run API-only server
uvicorn app.main_auth_async:app --reload
```

#### Mobile App Setup
```bash
cd mobile
npm install

# Start Metro bundler
npm start

# Run on Android
npm run android

# Run on iOS
npm run ios

# Build for production
./build-android.sh    # Android APK/AAB
./build-ios.sh        # iOS IPA
```

### Generate Test Data
```bash
python scripts/synthetic_data_generator.py
```

## Key Technologies

- **Web Interface**: FastAPI with Jinja2 templates, server-side rendering
- **Mobile App**: React Native with TypeScript, React Navigation, React Native Paper
- **Backend**: FastAPI with Python, JWT authentication, OpenAI integration
- **Database**: PostgreSQL with Alembic migrations, AsyncSession for concurrent operations
- **Deployment**: Docker Compose, single container deployment
- **Mobile Build**: Android APK/AAB and iOS IPA generation scripts
- **AI**: OpenAI GPT-4, RAG with vector databases
- **Voice Analysis**: Speech recognition, librosa audio processing, tone/emotion detection
- **Security**: bcrypt password hashing, rate limiting, CORS protection
- **Performance**: Async I/O for database, OpenAI API, and file operations

## Development Phases

1. **Phase 1 (Complete)**: React migration, authentication, OpenAI integration
2. **Phase 2 (Complete)**: Production deployment with Docker and PostgreSQL
3. **Phase 3 (Complete)**: Async I/O performance optimizations for concurrent users
4. **Phase 4 (Complete)**: Enhanced vector database and RAG system implementation
5. **Phase 5 (Future)**: Free clinical data integration and MCP protocol
   - Download and integrate freely available clinical datasets
   - Enhance vector database with DSM-5-TR, ICD-11, and clinical guidelines
   - Implement Model Context Protocol (MCP) for external data sources
   - Add real-time knowledge base updates and validation
6. **Phase 6 (Complete)**: React Native mobile app with Android/iOS build scripts
7. **Phase 7 (Complete)**: Voice analysis and speech pattern recognition
   - Advanced speech-to-text transcription with Google Speech Recognition
   - Real-time tone analysis (calm, anxious, depressed, agitated, neutral)
   - Emotion detection and sentiment analysis from speech patterns
   - Speech metrics calculation (rate, pause frequency, confidence scoring)
   - Audio feature extraction using librosa (pitch, energy, spectral analysis)
   - Mobile app voice recording with React Native integration
   - Web interface voice recording with MediaRecorder API
   - Clinical-grade audio analysis for diagnostic augmentation
8. **Phase 8 (Ongoing)**: LLM and RAG optimization and tuning
   - Fine-tuning OpenAI GPT models for clinical psychology domain
   - Optimizing RAG (Retrieval-Augmented Generation) pipeline performance
   - Improving vector database query accuracy and relevance
   - Enhancing prompt engineering for better diagnostic accuracy
   - Implementing domain-specific knowledge base refinement
   - Adding contextual memory for multi-turn conversations
   - Optimizing embedding models for clinical terminology
   - Performance benchmarking and continuous improvement
9. **Phase 9 (Future)**: Advanced analytics and international deployment

## Documentation

- [Product Requirements Document](docs/PRD_Therapy_Assistant_Agent.md)
- [Development Tasks](docs/DEVELOPMENT_TASKS.md)
- [Data Validation Report](docs/data_validation_report.md)
- [Production Deployment Guide](README-production.md)
- [Async Performance Improvements](ASYNC_IMPROVEMENTS.md)
- [Phase 5: Data Integration Plan](docs/PHASE5_DATA_INTEGRATION_PLAN.md)
- [Phase 7: Voice Analysis Implementation](docs/PHASE7_VOICE_ANALYSIS.md)
- [Phase 8: LLM and RAG Optimization](docs/PHASE8_LLM_RAG_OPTIMIZATION.md)

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