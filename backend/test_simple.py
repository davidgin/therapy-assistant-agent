#!/usr/bin/env python3
"""
Simple test validation script to check individual components
without full database setup
"""

def test_password_utilities():
    """Test password utilities independently."""
    from app.main_auth_async import hash_password, verify_password
    
    password = "testpassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False
    
    print("✅ Password utilities working correctly")


def test_jwt_utilities():
    """Test JWT utilities independently."""
    from app.main_auth_async import create_access_token, decode_token
    
    data = {"sub": "test@example.com", "role": "therapist"}
    token = create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == "test@example.com"
    assert payload["role"] == "therapist"
    
    print("✅ JWT utilities working correctly")


def test_audio_analysis_models():
    """Test audio analysis models independently."""
    from app.services.audio_analysis import AudioFeatures, VoiceAnalysis
    
    # Test AudioFeatures
    features = AudioFeatures(
        mean_pitch=150.0,
        pitch_variance=100.0,
        mean_energy=0.02,
        duration=5.0
    )
    
    assert features.mean_pitch == 150.0
    assert features.duration == 5.0
    
    # Test VoiceAnalysis
    analysis = VoiceAnalysis(
        transcription="Test transcription",
        sentiment="positive",
        emotion="happy",
        confidence=0.85
    )
    
    assert analysis.transcription == "Test transcription"
    assert analysis.sentiment == "positive"
    assert analysis.confidence == 0.85
    
    print("✅ Audio analysis models working correctly")


def test_settings_configuration():
    """Test settings configuration independently."""
    import os
    from unittest.mock import patch
    
    # Test with environment variables
    with patch.dict(os.environ, {
        'SECRET_KEY': 'test-secret-key',
        'ALGORITHM': 'HS256',
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30'
    }):
        from app.core.config import Settings
        
        settings = Settings()
        assert settings.SECRET_KEY == 'test-secret-key'
        assert settings.ALGORITHM == 'HS256'
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    
    print("✅ Settings configuration working correctly")


def test_file_operations():
    """Test file operations independently."""
    import tempfile
    import asyncio
    import os
    
    async def run_file_tests():
        from app.services.async_file_service import AsyncFileService
        
        service = AsyncFileService()
        test_content = "This is test content"
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Test file operations
            content = await service.read_text(temp_path)
            assert content == test_content
            
            exists = await service.file_exists(temp_path)
            assert exists is True
            
            size = await service.get_file_size(temp_path)
            assert size == len(test_content)
            
        finally:
            os.unlink(temp_path)
    
    asyncio.run(run_file_tests())
    print("✅ File operations working correctly")


def main():
    """Run all simple tests."""
    print("🧪 Running Simple Component Tests")
    print("=" * 50)
    
    try:
        test_password_utilities()
        test_jwt_utilities()
        test_audio_analysis_models()
        test_settings_configuration()
        test_file_operations()
        
        print("\n🎉 All component tests passed!")
        print("The testing framework components are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)