import cv2
import numpy as np
from typing import List, Dict, Tuple
from collections import Counter

class EmotionAnalyzer:
    """Analyzes facial expressions using OpenCV's Haar Cascades"""
    
    def __init__(self):
        # Load OpenCV's pre-trained face and eye detectors
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_smile.xml'
        )
        
    def analyze_frames(self, frames: List[np.ndarray]) -> Dict:
        """Analyze all frames for emotions and facial features"""
        
        results = {
            "timeline": [],
            "summary": {},
            "facial_features": {
                "eye_contact": [],
                "smile_authenticity": [],
                "micro_expressions": []
            }
        }
        
        for idx, frame in enumerate(frames):
            frame_analysis = self._analyze_single_frame(frame, idx)
            results["timeline"].append(frame_analysis)
            
            if frame_analysis.get("eye_contact") is not None:
                results["facial_features"]["eye_contact"].append(
                    frame_analysis["eye_contact"]
                )
            
            if frame_analysis.get("smile_score") is not None:
                results["facial_features"]["smile_authenticity"].append(
                    frame_analysis["smile_score"]
                )
        
        results["summary"] = self._generate_summary(results["timeline"])
        
        return results
    
    def _analyze_single_frame(self, frame: np.ndarray, frame_idx: int) -> Dict:
        """Analyze a single frame for facial features"""
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        
        if len(faces) == 0:
            return {
                "frame_index": frame_idx,
                "face_detected": False,
                "timestamp": frame_idx / 5.0
            }
        
        # Use the largest face
        face = max(faces, key=lambda f: f[2] * f[3])
        x, y, w, h = face
        
        # Extract face region
        face_roi_gray = gray[y:y+h, x:x+w]
        face_roi_color = frame[y:y+h, x:x+w]
        
        # Detect eyes
        eyes = self.eye_cascade.detectMultiScale(
            face_roi_gray, scaleFactor=1.1, minNeighbors=10, minSize=(15, 15)
        )
        
        # Detect smile
        smiles = self.smile_cascade.detectMultiScale(
            face_roi_gray, scaleFactor=1.8, minNeighbors=20, minSize=(25, 25)
        )
        
        # Calculate metrics
        has_eyes = len(eyes) >= 2
        has_smile = len(smiles) > 0
        
        # Determine eye contact (face centered in frame)
        frame_center_x = frame.shape[1] / 2
        frame_center_y = frame.shape[0] / 2
        face_center_x = x + w / 2
        face_center_y = y + h / 2
        
        distance_from_center = np.sqrt(
            (face_center_x - frame_center_x)**2 + 
            (face_center_y - frame_center_y)**2
        )
        
        max_distance = np.sqrt(frame.shape[0]**2 + frame.shape[1]**2) / 4
        eye_contact = distance_from_center < max_distance * 0.5
        
        # Estimate emotion
        emotion = self._estimate_emotion(has_eyes, has_smile, len(eyes), len(smiles))
        
        # Calculate smile authenticity
        smile_score = self._calculate_smile_score(has_smile, has_eyes, len(smiles))
        
        # Calculate engagement
        engagement = self._calculate_engagement(has_eyes, eye_contact, has_smile)
        
        return {
            "frame_index": frame_idx,
            "timestamp": frame_idx / 5.0,
            "face_detected": True,
            "emotion": emotion["primary"],
            "emotion_confidence": emotion["confidence"],
            "secondary_emotions": emotion["secondary"],
            "eye_contact": eye_contact,
            "smile_score": smile_score,
            "engagement_level": engagement,
            "metrics": {
                "eyes_detected": len(eyes),
                "smile_detected": has_smile,
                "face_size": w * h,
                "face_position": {
                    "x": face_center_x,
                    "y": face_center_y
                }
            }
        }
    
    def _estimate_emotion(self, has_eyes: bool, has_smile: bool, 
                         eye_count: int, smile_count: int) -> Dict:
        """Estimate emotion based on detected features"""
        
        emotions = []
        
        if has_smile and eye_count >= 2:
            # Happy: smile with visible eyes
            emotions.append(("happy", 0.8))
        elif has_smile and eye_count < 2:
            # Possible forced smile
            emotions.append(("happy", 0.5))
            emotions.append(("nervous", 0.4))
        elif not has_smile and eye_count >= 2:
            # Neutral or thoughtful
            emotions.append(("neutral", 0.6))
            emotions.append(("confident", 0.5))
        elif not has_smile and eye_count < 2:
            # Eyes partially closed
            emotions.append(("thoughtful", 0.5))
            emotions.append(("nervous", 0.4))
        else:
            emotions.append(("neutral", 0.5))
        
        # Add confidence as a base emotion
        if has_eyes and not has_smile:
            emotions.append(("confident", 0.6))
        
        emotions.sort(key=lambda x: x[1], reverse=True)
        
        return {
            "primary": emotions[0][0] if emotions else "neutral",
            "confidence": emotions[0][1] if emotions else 0.5,
            "secondary": [e[0] for e in emotions[1:3]]
        }
    
    def _calculate_smile_score(self, has_smile: bool, has_eyes: bool, 
                               smile_count: int) -> float:
        """Calculate smile authenticity score"""
        
        if not has_smile:
            return 0.0
        
        # Genuine smiles typically have visible eyes
        base_score = 0.5
        
        if has_eyes:
            base_score += 0.3
        
        # Multiple smile detections indicate stronger smile
        if smile_count > 1:
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _calculate_engagement(self, has_eyes: bool, eye_contact: bool, 
                             has_smile: bool) -> float:
        """Calculate engagement level"""
        
        engagement = 0.0
        
        if has_eyes:
            engagement += 0.3
        
        if eye_contact:
            engagement += 0.4
        
        if has_smile:
            engagement += 0.3
        
        return min(1.0, engagement)
    
    def _generate_summary(self, timeline: List[Dict]) -> Dict:
        """Generate summary statistics from timeline"""
        
        valid_frames = [f for f in timeline if f.get("face_detected")]
        
        if not valid_frames:
            return {"error": "No faces detected in video"}
        
        emotions = [f["emotion"] for f in valid_frames]
        eye_contact_frames = sum(1 for f in valid_frames if f.get("eye_contact", False))
        avg_smile = np.mean([f.get("smile_score", 0) for f in valid_frames])
        avg_engagement = np.mean([f.get("engagement_level", 0) for f in valid_frames])
        
        emotion_distribution = Counter(emotions)
        total_emotions = len(emotions)
        
        return {
            "total_frames_analyzed": len(timeline),
            "frames_with_face": len(valid_frames),
            "face_detection_rate": len(valid_frames) / len(timeline),
            "eye_contact_percentage": (eye_contact_frames / len(valid_frames)) * 100,
            "average_smile_authenticity": round(avg_smile, 2),
            "average_engagement_level": round(avg_engagement, 2),
            "emotion_distribution": {
                emotion: round((count / total_emotions) * 100, 1)
                for emotion, count in emotion_distribution.items()
            },
            "dominant_emotion": emotion_distribution.most_common(1)[0][0],
            "emotional_variability": len(set(emotions)) / 7
        }