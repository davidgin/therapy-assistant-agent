# Therapy Assistant - Production Deployment

This directory contains the production configuration for the Therapy Assistant application with PostgreSQL database and Docker Compose.

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.production .env
   # Edit .env with your actual production values
   ```

2. **Generate secure keys:**
   ```bash
   # Generate SECRET_KEY (32+ characters)
   openssl rand -hex 32

   # Generate JWT_SECRET_KEY (32+ characters)  
   openssl rand -hex 32
   ```

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database:**
   ```bash
   # Run migrations
   docker-compose exec backend alembic upgrade head
   ```

## Services

- **Frontend**: React app served by Nginx on port 80
- **Backend**: FastAPI with authentication on port 8000  
- **PostgreSQL**: Database on port 5432
- **Redis**: Session storage on port 6379
- **Nginx Proxy**: Alternative reverse proxy on port 8080

## Environment Variables

Copy `.env.production` to `.env` and update:

- `POSTGRES_PASSWORD`: Secure database password
- `SECRET_KEY`: Application secret key (32+ chars)
- `JWT_SECRET_KEY`: JWT signing key (32+ chars)  
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `FRONTEND_URL`: Your domain URL
- `BACKEND_URL`: API domain URL

## Database Management

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"

# Database backup
docker-compose exec postgres pg_dump -U therapy_user therapy_assistant_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U therapy_user therapy_assistant_db < backup.sql
```

## Monitoring

- Frontend health: `http://localhost/health`
- Backend health: `http://localhost:8000/health`  
- Database status: `docker-compose exec postgres pg_isready`

## Security Notes

- All secrets are externalized to environment variables
- Non-root users in containers
- Security headers configured
- Rate limiting enabled
- SSL/TLS ready (configure certificates in nginx volume)

## Scaling

To scale backend services:
```bash
docker-compose up -d --scale backend=3
```