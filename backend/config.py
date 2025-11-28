"""
EmotiSense Configuration
Centralized configuration for all application settings
"""

import os
from pathlib import Path
from typing import Optional

class Config:
    """Application configuration"""
    
    # Application Settings
    APP_NAME = "EmotiSense"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server Settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    RELOAD = os.getenv("RELOAD", "True").lower() == "true"
    
    # CORS Settings
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000"
    ).split(",")
    
    # File Storage
    BASE_DIR = Path(__file__).parent
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
    PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", BASE_DIR / "processed"))
    
    # Create directories
    UPLOAD_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)
    
    # File Upload Limits
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", 100))
    MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    MAX_VIDEO_DURATION_SECONDS = int(os.getenv("MAX_VIDEO_DURATION", 600))  # 10 minutes
    
    ALLOWED_VIDEO_FORMATS = [
        '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'
    ]
    
    # Video Processing Settings
    FRAME_EXTRACTION_RATE = int(os.getenv("FRAME_RATE", 5))  # Frames per second
    MAX_FRAMES_TO_PROCESS = int(os.getenv("MAX_FRAMES", 1500))  # Max frames to analyze
    
    # Audio Processing Settings
    AUDIO_SAMPLE_RATE = 16000  # Hz
    AUDIO_CHANNELS = 1  # Mono
    
    # Database Settings
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'emotisense.db'}"
    )
    
    # MediaPipe Settings
    MP_MIN_DETECTION_CONFIDENCE = 0.5
    MP_MIN_TRACKING_CONFIDENCE = 0.5
    MP_MAX_NUM_FACES = 1
    
    # Analysis Thresholds
    EYE_CONTACT_THRESHOLD = 15  # degrees from center
    SMILE_AUTHENTICITY_THRESHOLD = 0.7
    ENGAGEMENT_THRESHOLD = 0.6
    
    # Speaking Rate Thresholds (words per minute)
    SPEAKING_RATE_SLOW = 120
    SPEAKING_RATE_OPTIMAL_MIN = 120
    SPEAKING_RATE_OPTIMAL_MAX = 160
    SPEAKING_RATE_FAST = 200
    
    # Performance Score Weights
    FACIAL_SCORE_WEIGHT = 0.4
    VOICE_SCORE_WEIGHT = 0.6
    
    # Facial Analysis Weights
    EYE_CONTACT_WEIGHT = 0.375
    SMILE_AUTHENTICITY_WEIGHT = 0.25
    ENGAGEMENT_WEIGHT = 0.25
    EMOTION_APPROPRIATENESS_WEIGHT = 0.125
    
    # Voice Analysis Weights
    CLARITY_WEIGHT = 0.3
    CONFIDENCE_WEIGHT = 0.4
    VOICE_ENGAGEMENT_WEIGHT = 0.3
    
    # Background Processing
    BACKGROUND_TASK_TIMEOUT = 600  # 10 minutes
    STATUS_CHECK_INTERVAL = 2  # seconds
    
    # Cleanup Settings
    AUTO_CLEANUP_ENABLED = os.getenv("AUTO_CLEANUP", "True").lower() == "true"
    CLEANUP_AGE_DAYS = int(os.getenv("CLEANUP_AGE_DAYS", 7))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", BASE_DIR / "emotisense.log")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT", "False").lower() == "true"
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", 10))
    
    # Feature Flags
    ENABLE_REAL_TIME_ANALYSIS = False  # Future feature
    ENABLE_MULTI_FACE_DETECTION = False  # Future feature
    ENABLE_SPEECH_TRANSCRIPTION = False  # Requires additional API
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check required directories
        if not cls.UPLOAD_DIR.exists():
            errors.append(f"Upload directory does not exist: {cls.UPLOAD_DIR}")
        
        # Check FFmpeg
        try:
            import subprocess
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, 
                         check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            errors.append("FFmpeg is not installed or not in PATH")
        
        # Check MediaPipe
        try:
            import mediapipe
        except ImportError:
            errors.append("MediaPipe is not installed")
        
        # Check librosa
        try:
            import librosa
        except ImportError:
            errors.append("librosa is not installed")
        
        if errors:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ Configuration validated successfully")
        return True
    
    @classmethod
    def print_config(cls):
        """Print current configuration"""
        print("\n" + "="*60)
        print(f"{cls.APP_NAME} v{cls.APP_VERSION} Configuration")
        print("="*60)
        print(f"Host: {cls.HOST}:{cls.PORT}")
        print(f"Debug: {cls.DEBUG}")
        print(f"Upload Directory: {cls.UPLOAD_DIR}")
        print(f"Max Upload Size: {cls.MAX_UPLOAD_SIZE_MB} MB")
        print(f"Max Video Duration: {cls.MAX_VIDEO_DURATION_SECONDS}s")
        print(f"Frame Extraction Rate: {cls.FRAME_EXTRACTION_RATE} FPS")
        print(f"Database: {cls.DATABASE_URL}")
        print("="*60 + "\n")


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    RELOAD = True


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    RELOAD = False
    RATE_LIMIT_ENABLED = True
    AUTO_CLEANUP_ENABLED = True
    
    # Use environment variables for sensitive data
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Stricter limits in production
    MAX_UPLOAD_SIZE_MB = 50
    MAX_VIDEO_DURATION_SECONDS = 300  # 5 minutes


class TestConfig(Config):
    """Test environment configuration"""
    DEBUG = True
    DATABASE_URL = "sqlite:///:memory:"
    UPLOAD_DIR = Path("/tmp/emotisense_test/uploads")
    PROCESSED_DIR = Path("/tmp/emotisense_test/processed")


# Environment-based configuration
ENV = os.getenv("ENVIRONMENT", "development").lower()

if ENV == "production":
    config = ProductionConfig
elif ENV == "test":
    config = TestConfig
else:
    config = DevelopmentConfig


# Export the active configuration
__all__ = ["config", "Config", "DevelopmentConfig", "ProductionConfig", "TestConfig"]