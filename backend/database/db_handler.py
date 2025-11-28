import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
import threading

class DatabaseHandler:
    """Handles all database operations for storing sessions and results"""
    
    def __init__(self, db_path: str = "emotisense.db"):
        self.db_path = db_path
        self.local = threading.local()
        self._init_database()
    
    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.local.connection.row_factory = sqlite3.Row
        return self.local.connection
    
    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                metadata TEXT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                emotion_analysis TEXT,
                audio_analysis TEXT,
                report TEXT,
                processed_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # User sessions tracking (for analytics)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        
        # Create indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_status 
            ON sessions(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_created 
            ON sessions(created_at DESC)
        """)
        
        conn.commit()
    
    def create_session(
        self,
        session_id: str,
        file_path: str,
        filename: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Create a new session"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions (session_id, filename, file_path, status)
                VALUES (?, ?, ?, 'pending')
            """, (session_id, filename, file_path))
            
            if user_id:
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_id)
                    VALUES (?, ?)
                """, (user_id, session_id))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            print(f"Database error creating session: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "session_id": row["session_id"],
                    "filename": row["filename"],
                    "file_path": row["file_path"],
                    "status": row["status"],
                    "progress": row["progress"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else None,
                    "error": row["error"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
            
            return None
            
        except sqlite3.Error as e:
            print(f"Database error getting session: {e}")
            return None
    
    def update_status(self, session_id: str, status: str, progress: int = None):
        """Update session status"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if progress is not None:
                cursor.execute("""
                    UPDATE sessions 
                    SET status = ?, progress = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, progress, session_id))
            else:
                cursor.execute("""
                    UPDATE sessions 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (status, session_id))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Database error updating status: {e}")
    
    def update_session(self, session_id: str, updates: Dict):
        """Update session with arbitrary data"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Handle metadata updates
            if "metadata" in updates:
                updates["metadata"] = json.dumps(updates["metadata"])
            
            # Build dynamic UPDATE query
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [session_id]
            
            cursor.execute(f"""
                UPDATE sessions 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
            """, values)
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Database error updating session: {e}")

    def save_analysis_results(self, session_id: str, results: Dict):
        """Save analysis results"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Helper function to convert numpy types to Python types
            def convert_to_serializable(obj):
                """Convert numpy types to native Python types"""
                import numpy as np
                
                if isinstance(obj, dict):
                    return {key: convert_to_serializable(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_serializable(item) for item in obj]
                elif isinstance(obj, (np.integer, np.int64, np.int32)):
                    return int(obj)
                elif isinstance(obj, (np.floating, np.float64, np.float32)):
                    return float(obj)
                elif isinstance(obj, (np.bool_, bool)):
                    return bool(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                else:
                    return obj
                # Convert all data to serializable format
            emotion_data = convert_to_serializable(results.get("emotion_analysis", {}))
            audio_data = convert_to_serializable(results.get("audio_analysis", {}))
            report_data = convert_to_serializable(results.get("report", {}))
            cursor.execute("""
                INSERT INTO analysis_results 
                (session_id, emotion_analysis, audio_analysis, report, processed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session_id,
                json.dumps(emotion_data),
                json.dumps(audio_data),
                json.dumps(report_data),
                results.get("processed_at")
                ))
            conn.commit()
                
        except sqlite3.Error as e:
            print(f"Database error saving results: {e}")
        except Exception as e:
            print(f"Error converting data: {e}")   
    
    def get_results(self, session_id: str) -> Optional[Dict]:
        """Get analysis results for a session"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # First check if session is completed
            session = self.get_session(session_id)
            if not session or session["status"] != "completed":
                return None
            
            cursor.execute("""
                SELECT * FROM analysis_results 
                WHERE session_id = ?
                ORDER BY processed_at DESC
                LIMIT 1
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "session_id": session_id,
                    "emotion_analysis": json.loads(row["emotion_analysis"]),
                    "audio_analysis": json.loads(row["audio_analysis"]),
                    "report": json.loads(row["report"]),
                    "processed_at": row["processed_at"]
                }
            
            return None
            
        except sqlite3.Error as e:
            print(f"Database error getting results: {e}")
            return None
    
    def list_sessions(
        self,
        limit: int = 10,
        status: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict]:
        """List sessions with optional filtering"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT s.* FROM sessions s"
            params = []
            
            if user_id:
                query += " INNER JOIN user_sessions us ON s.session_id = us.session_id"
                query += " WHERE us.user_id = ?"
                params.append(user_id)
            
            if status:
                query += " WHERE s.status = ?" if "WHERE" not in query else " AND s.status = ?"
                params.append(status)
            
            query += " ORDER BY s.created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            
            sessions = []
            for row in rows:
                sessions.append({
                    "session_id": row["session_id"],
                    "filename": row["filename"],
                    "status": row["status"],
                    "progress": row["progress"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                })
            
            return sessions
            
        except sqlite3.Error as e:
            print(f"Database error listing sessions: {e}")
            return []
    
    def delete_session(self, session_id: str):
        """Delete a session and its results"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete results first (foreign key constraint)
            cursor.execute("""
                DELETE FROM analysis_results WHERE session_id = ?
            """, (session_id,))
            
            # Delete user session tracking
            cursor.execute("""
                DELETE FROM user_sessions WHERE session_id = ?
            """, (session_id,))
            
            # Delete session
            cursor.execute("""
                DELETE FROM sessions WHERE session_id = ?
            """, (session_id,))
            
            conn.commit()
            
        except sqlite3.Error as e:
            print(f"Database error deleting session: {e}")
    
    def get_statistics(self) -> Dict:
        """Get platform statistics"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) as total FROM sessions")
            total_sessions = cursor.fetchone()["total"]
            
            # Completed sessions
            cursor.execute("SELECT COUNT(*) as completed FROM sessions WHERE status = 'completed'")
            completed = cursor.fetchone()["completed"]
            
            # Failed sessions
            cursor.execute("SELECT COUNT(*) as failed FROM sessions WHERE status = 'failed'")
            failed = cursor.fetchone()["failed"]
            
            # Average processing time (if we track it)
            cursor.execute("""
                SELECT AVG(
                    JULIANDAY(updated_at) - JULIANDAY(created_at)
                ) * 24 * 60 as avg_minutes
                FROM sessions
                WHERE status = 'completed'
            """)
            result = cursor.fetchone()
            avg_processing_time = result["avg_minutes"] if result["avg_minutes"] else 0
            
            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed,
                "failed_sessions": failed,
                "success_rate": (completed / total_sessions * 100) if total_sessions > 0 else 0,
                "average_processing_time_minutes": round(avg_processing_time, 2)
            }
            
        except sqlite3.Error as e:
            print(f"Database error getting statistics: {e}")
            return {}
    
    def cleanup_old_sessions(self, days: int = 30):
        """Clean up sessions older than specified days"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM sessions 
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted
            
        except sqlite3.Error as e:
            print(f"Database error cleaning up: {e}")
            return 0