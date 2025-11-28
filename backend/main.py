from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from datetime import datetime
from pathlib import Path
import asyncio

# Initialize FastAPI app
app = FastAPI(
    title="EmotiSense API",
    description="Real-time emotion and performance analytics for video content",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
PROCESSED_DIR = Path("processed")
UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("🚀 EmotiSense Backend Starting...")
print("=" * 60)

# Import analysis modules with error handling
try:
    from modules.video_processor import VideoProcessor
    from modules.emotion_analyzer import EmotionAnalyzer
    from modules.audio_analyzer import AudioAnalyzer
    from modules.report_generator import ReportGenerator
    from database.db_handler import DatabaseHandler
    
    print("✅ All modules imported successfully")
    
    # Initialize components
    video_processor = VideoProcessor()
    emotion_analyzer = EmotionAnalyzer()
    audio_analyzer = AudioAnalyzer()
    report_generator = ReportGenerator()
    db = DatabaseHandler()
    
    print("✅ All components initialized")
    
except Exception as e:
    print(f"❌ Error importing modules: {e}")
    print("   Please check that all module files exist and are correct")
    raise

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "message": "EmotiSense API - Video Emotion Analytics",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "upload": "/api/upload",
            "status": "/api/status/{session_id}",
            "results": "/api/results/{session_id}",
            "sessions": "/api/sessions",
            "health": "/health"
        }
    }

@app.post("/api/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload video for analysis"""
    
    print(f"\n📹 Received upload request: {file.filename}")
    
    # Validate file
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=400, 
            detail=f"File must be a video. Received: {file.content_type}"
        )
    
    # Generate unique ID
    session_id = str(uuid.uuid4())
    file_extension = Path(file.filename).suffix
    file_path = UPLOAD_DIR / f"{session_id}{file_extension}"
    
    # Save uploaded file
    try:
        print(f"💾 Saving file to: {file_path}")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"✅ File saved successfully ({len(content)} bytes)")
    except Exception as e:
        print(f"❌ Failed to save file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create database entry
    db.create_session(session_id, str(file_path), file.filename)
    print(f"✅ Database session created: {session_id}")
    
    # Start background processing
    background_tasks.add_task(process_video_pipeline, session_id, file_path)
    print(f"🔄 Background processing started for session: {session_id}")
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "status": "processing",
        "message": "Video uploaded successfully. Processing started."
    }

async def process_video_pipeline(session_id: str, file_path: Path):
    """Background task to process video through entire pipeline"""
    
    print(f"\n{'='*60}")
    print(f"🎬 Starting analysis for session: {session_id}")
    print(f"{'='*60}")
    
    try:
        # Update status
        db.update_status(session_id, "processing")
        
        # Step 1: Extract frames and audio
        print("📹 Step 1: Processing video...")
        frames, audio_path, metadata = video_processor.process_video(str(file_path))
        print(f"✅ Extracted {len(frames)} frames and audio")
        db.update_session(session_id, {"metadata": metadata})
        
        # Step 2: Analyze emotions from frames
        print("😊 Step 2: Analyzing facial expressions...")
        emotion_data = emotion_analyzer.analyze_frames(frames)
        print(f"✅ Emotion analysis complete")
        
        # Step 3: Analyze audio
        print("🎤 Step 3: Analyzing voice...")
        audio_data = audio_analyzer.analyze_audio(audio_path)
        print(f"✅ Audio analysis complete")
        
        # Step 4: Generate comprehensive report
        print("📊 Step 4: Generating report...")
        report = report_generator.generate_report(
            emotion_data=emotion_data,
            audio_data=audio_data,
            metadata=metadata
        )
        print(f"✅ Report generated")
        
        # Step 5: Save results
        print("💾 Step 5: Saving results...")
        db.save_analysis_results(session_id, {
            "emotion_analysis": emotion_data,
            "audio_analysis": audio_data,
            "report": report,
            "processed_at": datetime.now().isoformat()
        })
        
        db.update_status(session_id, "completed")
        print(f"{'='*60}")
        print(f"✅ Analysis completed for session: {session_id}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Error processing video: {e}")
        import traceback
        traceback.print_exc()
        db.update_status(session_id, "failed")
        db.update_session(session_id, {"error": str(e)})

@app.get("/api/status/{session_id}")
async def get_status(session_id: str):
    """Get processing status"""
    session = db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "status": session.get("status"),
        "progress": session.get("progress", 0),
        "created_at": session.get("created_at")
    }

@app.get("/api/results/{session_id}")
async def get_results(session_id: str):
    """Get analysis results"""
    results = db.get_results(session_id)
    
    if not results:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        elif session.get("status") == "processing":
            raise HTTPException(status_code=202, detail="Analysis still in progress")
        elif session.get("status") == "failed":
            raise HTTPException(status_code=500, detail="Analysis failed")
        else:
            raise HTTPException(status_code=404, detail="Results not found")
    
    return results

@app.get("/api/sessions")
async def list_sessions(limit: int = 10):
    """List recent sessions"""
    sessions = db.list_sessions(limit)
    return {"sessions": sessions}

@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session and associated files"""
    session = db.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Delete files
    file_path = Path(session.get("file_path"))
    if file_path.exists():
        file_path.unlink()
    
    # Delete from database
    db.delete_session(session_id)
    
    return {"message": "Session deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting EmotiSense Backend Server")
    print("=" * 60)
    print("📍 Server will be available at: http://localhost:8000")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 Health Check: http://localhost:8000/health")
    print("=" * 60 + "\n")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )