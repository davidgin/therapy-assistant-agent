#!/usr/bin/env python3
"""
Database setup script for the therapy assistant application
Creates database, tables, and populates initial data
"""

import os
import sys
import json
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the backend directory to Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import Base, engine
from app.models.user import User, UserRole, LicenseType
from app.models.clinical_case import ClinicalCase
from app.core.auth import AuthService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Database setup and initialization"""
    
    def __init__(self):
        self.engine = engine
        
    def create_database_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("✅ Database tables created successfully")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Error creating tables: {e}")
            return False
    
    def create_demo_users(self):
        """Create demo users for testing"""
        logger.info("Creating demo users...")
        
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        db = SessionLocal()
        
        try:
            demo_users = [
                {
                    "email": "demo.therapist@example.com",
                    "username": "demo_therapist",
                    "password": "demo123",
                    "first_name": "Dr. Sarah",
                    "last_name": "Johnson",
                    "role": UserRole.THERAPIST,
                    "license_type": LicenseType.LMFT,
                    "license_number": "LMFT123456",
                    "license_state": "CA",
                    "organization": "Demo Mental Health Clinic"
                },
                {
                    "email": "demo.psychiatrist@example.com", 
                    "username": "demo_psychiatrist",
                    "password": "demo123",
                    "first_name": "Dr. Michael",
                    "last_name": "Chen",
                    "role": UserRole.PSYCHIATRIST,
                    "license_type": LicenseType.MD,
                    "license_number": "MD789012",
                    "license_state": "CA",
                    "organization": "Demo Mental Health Clinic"
                },
                {
                    "email": "demo.student@example.com",
                    "username": "demo_student", 
                    "password": "demo123",
                    "first_name": "Emily",
                    "last_name": "Davis",
                    "role": UserRole.STUDENT,
                    "license_type": LicenseType.STUDENT,
                    "organization": "University Psychology Program"
                },
                {
                    "email": "admin@therapyassistant.ai",
                    "username": "admin",
                    "password": "admin123!",
                    "first_name": "System",
                    "last_name": "Administrator",
                    "role": UserRole.ADMIN,
                    "is_superuser": True
                }
            ]
            
            created_count = 0
            for user_data in demo_users:
                # Check if user already exists
                existing_user = db.query(User).filter(
                    User.email == user_data["email"]
                ).first()
                
                if existing_user:
                    logger.info(f"User {user_data['email']} already exists, skipping...")
                    continue
                
                # Hash password
                hashed_password = AuthService.get_password_hash(user_data.pop("password"))
                
                # Create user
                user = User(
                    hashed_password=hashed_password,
                    is_active=True,
                    is_verified=True,
                    **user_data
                )
                
                db.add(user)
                created_count += 1
                logger.info(f"Created user: {user.email}")
            
            db.commit()
            logger.info(f"✅ Created {created_count} demo users")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Error creating demo users: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def load_synthetic_cases(self):
        """Load synthetic clinical cases into database"""
        logger.info("Loading synthetic clinical cases...")
        
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        db = SessionLocal()
        
        try:
            # Load synthetic cases from JSON
            cases_file = backend_path / "data" / "synthetic" / "synthetic_clinical_cases.json"
            
            if not cases_file.exists():
                logger.warning(f"Synthetic cases file not found: {cases_file}")
                return False
            
            with open(cases_file, 'r') as f:
                cases_data = json.load(f)
            
            created_count = 0
            for case_data in cases_data:
                # Check if case already exists
                existing_case = db.query(ClinicalCase).filter(
                    ClinicalCase.case_id == case_data["case_id"]
                ).first()
                
                if existing_case:
                    logger.info(f"Case {case_data['case_id']} already exists, skipping...")
                    continue
                
                # Extract demographics
                demographics = case_data.get("patient_demographics", {})
                
                # Create clinical case
                clinical_case = ClinicalCase(
                    case_id=case_data["case_id"],
                    patient_age=demographics.get("age"),
                    patient_gender=demographics.get("gender"),
                    occupation=demographics.get("occupation"),
                    presenting_complaint=", ".join(case_data.get("presenting_symptoms", [])),
                    history_present_illness=case_data.get("clinical_history", ""),
                    past_psychiatric_history=case_data.get("assessment_notes", ""),
                    primary_diagnosis=case_data.get("suggested_diagnosis", {}).get("primary"),
                    dsm5_criteria_met=case_data.get("presenting_symptoms", []),
                    icd11_code=case_data.get("suggested_diagnosis", {}).get("icd11_code"),
                    severity=case_data.get("severity"),
                    treatment_recommendations=case_data.get("treatment_recommendations", []),
                    is_synthetic="true",
                    source_description="Generated synthetic case for testing"
                )
                
                db.add(clinical_case)
                created_count += 1
                logger.info(f"Created case: {clinical_case.case_id}")
            
            db.commit()
            logger.info(f"✅ Loaded {created_count} synthetic clinical cases")
            return True
            
        except (SQLAlchemyError, FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"❌ Error loading synthetic cases: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def verify_database_setup(self):
        """Verify database setup is correct"""
        logger.info("Verifying database setup...")
        
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        db = SessionLocal()
        
        try:
            # Check users
            user_count = db.query(User).count()
            logger.info(f"Users in database: {user_count}")
            
            # Check clinical cases
            case_count = db.query(ClinicalCase).count()
            logger.info(f"Clinical cases in database: {case_count}")
            
            # Check if demo accounts work
            demo_user = db.query(User).filter(
                User.email == "demo.therapist@example.com"
            ).first()
            
            if demo_user:
                logger.info(f"✅ Demo therapist account verified: {demo_user.full_name}")
            else:
                logger.warning("❌ Demo therapist account not found")
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Error verifying database: {e}")
            return False
        finally:
            db.close()
    
    def reset_database(self):
        """Reset database (drop and recreate all tables)"""
        logger.warning("⚠️  Resetting database - this will delete all data!")
        
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Dropped all tables")
            
            Base.metadata.create_all(bind=self.engine)
            logger.info("Recreated all tables")
            
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Error resetting database: {e}")
            return False

def main():
    """Main setup function"""
    logger.info("🚀 Starting database setup for Therapy Assistant Agent...")
    
    setup = DatabaseSetup()
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        logger.info("Reset mode requested")
        if not setup.reset_database():
            return 1
    
    # Create tables
    if not setup.create_database_tables():
        return 1
    
    # Create demo users
    if not setup.create_demo_users():
        return 1
    
    # Load synthetic cases
    if not setup.load_synthetic_cases():
        return 1
    
    # Verify setup
    if not setup.verify_database_setup():
        return 1
    
    logger.info("🎉 Database setup completed successfully!")
    logger.info("\n📋 Demo Accounts Created:")
    logger.info("  👨‍⚕️ Therapist: demo.therapist@example.com / demo123")
    logger.info("  👩‍⚕️ Psychiatrist: demo.psychiatrist@example.com / demo123")  
    logger.info("  🎓 Student: demo.student@example.com / demo123")
    logger.info("  👤 Admin: admin@therapyassistant.ai / admin123!")
    
    return 0

if __name__ == "__main__":
    exit(main())