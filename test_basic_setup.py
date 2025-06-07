#!/usr/bin/env python3
"""
Basic test script to verify the core setup without heavy dependencies
"""

import sys
import os
sys.path.append('backend')

def test_database_models():
    """Test database model imports"""
    print("Testing database models...")
    try:
        from backend.app.core.database import Base, get_db
        from backend.app.models.user import User, UserRole, LicenseType
        from backend.app.models.clinical_case import ClinicalCase
        from backend.app.models.diagnostic_session import DiagnosticSession
        from backend.app.models.treatment_plan import TreatmentPlan
        print("✅ Database models imported successfully")
        return True
    except Exception as e:
        print(f"❌ Database models import failed: {e}")
        return False

def test_auth_system():
    """Test authentication system"""
    print("\nTesting authentication system...")
    try:
        from backend.app.core.auth import AuthService
        
        # Test password hashing
        password = "test_password_123"
        hashed = AuthService.get_password_hash(password)
        print(f"✅ Password hashing works: {hashed[:20]}...")
        
        # Test password verification
        is_valid = AuthService.verify_password(password, hashed)
        print(f"✅ Password verification works: {is_valid}")
        
        # Test token creation
        token = AuthService.create_access_token({"sub": "test@example.com"})
        print(f"✅ JWT token creation works: {token[:30]}...")
        
        return True
    except Exception as e:
        print(f"❌ Authentication system test failed: {e}")
        return False

def test_synthetic_data():
    """Test synthetic data generation"""
    print("\nTesting synthetic data generation...")
    try:
        sys.path.append('scripts')
        from synthetic_data_generator import SyntheticDataGenerator
        
        generator = SyntheticDataGenerator()
        case = generator.generate_case("major_depressive_disorder", 1)
        
        print(f"✅ Generated case: {case.case_id}")
        print(f"✅ Diagnosis: {case.primary_diagnosis}")
        print(f"✅ Demographics: {case.patient_demographics.age}yo {case.patient_demographics.gender}")
        
        return True
    except Exception as e:
        print(f"❌ Synthetic data generation test failed: {e}")
        return False

def test_clinical_data():
    """Test clinical data loading"""
    print("\nTesting clinical data...")
    try:
        # Test synthetic data file exists
        data_file = "data/synthetic/synthetic_clinical_cases.json"
        if os.path.exists(data_file):
            import json
            with open(data_file, 'r') as f:
                cases = json.load(f)
            print(f"✅ Found {len(cases)} clinical cases in {data_file}")
            
            # Show sample case
            if cases:
                sample = cases[0]
                print(f"✅ Sample case: {sample['case_id']} - {sample['primary_diagnosis']}")
            return True
        else:
            print(f"❌ Clinical data file not found: {data_file}")
            return False
    except Exception as e:
        print(f"❌ Clinical data test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Therapy Assistant Agent Setup")
    print("=" * 50)
    
    tests = [
        test_database_models,
        test_auth_system,
        test_synthetic_data,
        test_clinical_data
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All core components working correctly!")
        print("\nNext steps:")
        print("1. Install ML dependencies: pip install faiss-cpu sentence-transformers")
        print("2. Run: docker-compose up --build")
        print("3. Test endpoints: http://localhost:8000/health")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)