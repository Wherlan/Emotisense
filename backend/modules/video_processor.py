import cv2
import numpy as np
from pathlib import Path
import subprocess
import json
from typing import Tuple, List, Dict

class VideoProcessor:
    """Handles video processing, frame extraction, and audio separation"""
    
    def __init__(self, frame_rate: int = 5):
        """
        Initialize video processor
        
        Args:
            frame_rate: Number of frames to extract per second
        """
        self.frame_rate = frame_rate
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    def process_video(self, video_path: str) -> Tuple[List[np.ndarray], str, Dict]:
        """
        Process video: extract frames and audio
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (frames, audio_path, metadata)
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if video_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported video format: {video_path.suffix}")
        
        # Extract metadata
        metadata = self._get_video_metadata(video_path)
        
        # Extract frames
        frames = self._extract_frames(video_path, metadata)
        
        # Extract audio
        audio_path = self._extract_audio(video_path)
        
        return frames, audio_path, metadata
    
    def _get_video_metadata(self, video_path: Path) -> Dict:
        """Extract video metadata using OpenCV"""
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError("Failed to open video file")
        
        metadata = {
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "duration_seconds": 0
        }
        
        if metadata["fps"] > 0:
            metadata["duration_seconds"] = metadata["frame_count"] / metadata["fps"]
        
        cap.release()
        return metadata
    
    def _extract_frames(self, video_path: Path, metadata: Dict) -> List[np.ndarray]:
        """Extract frames at specified frame rate"""
        cap = cv2.VideoCapture(str(video_path))
        frames = []
        
        fps = metadata["fps"]
        frame_interval = int(fps / self.frame_rate) if fps > self.frame_rate else 1
        
        frame_idx = 0
        extracted = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Extract frame at intervals
            if frame_idx % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                extracted += 1
                
                # Limit to prevent memory issues (max 5 minutes * frame_rate)
                if extracted >= (300 * self.frame_rate):
                    break
            
            frame_idx += 1
        
        cap.release()
        
        print(f"Extracted {len(frames)} frames from video")
        return frames
    
    def _extract_audio(self, video_path: Path) -> str:
        """Extract audio from video using FFmpeg"""
        audio_path = video_path.parent / f"{video_path.stem}_audio.wav"
        
        # FFmpeg command to extract audio
        command = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # WAV format
            '-ar', '16000',  # 16kHz sample rate
            '-ac', '1',  # Mono
            '-y',  # Overwrite output
            str(audio_path)
        ]
        
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            print(f"Audio extracted to: {audio_path}")
            return str(audio_path)
            
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr.decode()}")
            raise RuntimeError("Failed to extract audio from video")
        except FileNotFoundError:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg.")
    
    def validate_video(self, video_path: str, max_duration: int = 600) -> Dict:
        """
        Validate video file
        
        Args:
            video_path: Path to video
            max_duration: Maximum duration in seconds (default 10 minutes)
            
        Returns:
            Validation result dictionary
        """
        try:
            metadata = self._get_video_metadata(Path(video_path))
            
            if metadata["duration_seconds"] > max_duration:
                return {
                    "valid": False,
                    "error": f"Video exceeds maximum duration of {max_duration}s"
                }
            
            if metadata["duration_seconds"] < 1:
                return {
                    "valid": False,
                    "error": "Video is too short (minimum 1 second)"
                }
            
            return {
                "valid": True,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def create_thumbnail(self, video_path: str, output_path: str, timestamp: float = 1.0):
        """Create thumbnail from video at specified timestamp"""
        cap = cv2.VideoCapture(video_path)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_number = int(timestamp * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        
        if ret:
            cv2.imwrite(output_path, frame)
        
        cap.release()
        return output_path if ret else None