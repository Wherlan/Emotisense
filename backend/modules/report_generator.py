from typing import Dict, List
import numpy as np
from datetime import datetime

class ReportGenerator:
    """Generates comprehensive analysis reports with actionable insights"""
    
    def __init__(self):
        self.performance_thresholds = {
            "excellent": 0.8,
            "good": 0.6,
            "needs_improvement": 0.4
        }
    
    def generate_report(
        self,
        emotion_data: Dict,
        audio_data: Dict,
        metadata: Dict
    ) -> Dict:
        """
        Generate comprehensive performance report
        
        Args:
            emotion_data: Results from emotion analysis
            audio_data: Results from audio analysis
            metadata: Video metadata
            
        Returns:
            Complete report dictionary
        """
        
        # Calculate performance score
        performance_score = self._calculate_performance_score(
            emotion_data, audio_data
        )
        
        # Generate insights
        insights = self._generate_insights(emotion_data, audio_data)
        
        # Create improvement plan
        improvement_plan = self._create_improvement_plan(
            emotion_data, audio_data, performance_score
        )
        
        # Identify strengths and weaknesses
        strengths = self._identify_strengths(emotion_data, audio_data, performance_score)
        weaknesses = self._identify_weaknesses(emotion_data, audio_data, performance_score)
        
        # Generate timestamps for key moments
        key_moments = self._identify_key_moments(emotion_data, audio_data)
        
        return {
            "performance_score": performance_score,
            "rating": self._get_rating(performance_score["overall"]),
            "summary": self._generate_summary(emotion_data, audio_data, metadata),
            "insights": insights,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improvement_plan": improvement_plan,
            "key_moments": key_moments,
            "detailed_metrics": {
                "facial_analysis": self._format_facial_metrics(emotion_data),
                "voice_analysis": self._format_voice_metrics(audio_data)
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def _calculate_performance_score(
        self,
        emotion_data: Dict,
        audio_data: Dict
    ) -> Dict:
        """Calculate overall performance score from all metrics"""
        
        # Facial performance (40% weight)
        facial_score = 0.0
        emotion_summary = emotion_data.get("summary", {})
        
        if emotion_summary:
            # Eye contact (15%)
            eye_contact_pct = emotion_summary.get("eye_contact_percentage", 0)
            eye_contact_score = min(1.0, eye_contact_pct / 80.0)
            
            # Smile authenticity (10%)
            smile_score = emotion_summary.get("average_smile_authenticity", 0)
            
            # Engagement (10%)
            engagement_score = emotion_summary.get("average_engagement_level", 0)
            
            # Emotional appropriateness (5%)
            emotion_dist = emotion_summary.get("emotion_distribution", {})
            positive_emotions = sum(
                emotion_dist.get(e, 0) for e in ["happy", "confident", "neutral"]
            )
            emotion_score = min(1.0, positive_emotions / 70.0)
            
            facial_score = (
                eye_contact_score * 0.375 +
                smile_score * 0.25 +
                engagement_score * 0.25 +
                emotion_score * 0.125
            )
        
        # Voice performance (60% weight)
        voice_score = 0.0
        quality_scores = audio_data.get("quality_scores", {})
        
        if quality_scores:
            clarity = quality_scores.get("clarity", 0)
            confidence = quality_scores.get("confidence", 0)
            engagement = quality_scores.get("engagement", 0)
            
            voice_score = (
                clarity * 0.3 +
                confidence * 0.4 +
                engagement * 0.3
            )
        
        # Combined score
        overall = (facial_score * 0.4 + voice_score * 0.6)
        
        return {
            "overall": round(overall, 3),
            "facial_score": round(facial_score, 3),
            "voice_score": round(voice_score, 3),
            "breakdown": {
                "eye_contact": round(eye_contact_score if emotion_summary else 0, 3),
                "smile_authenticity": round(smile_score if emotion_summary else 0, 3),
                "engagement": round(engagement_score if emotion_summary else 0, 3),
                "voice_clarity": round(clarity if quality_scores else 0, 3),
                "voice_confidence": round(confidence if quality_scores else 0, 3),
                "voice_engagement": round(engagement if quality_scores else 0, 3)
            }
        }
    
    def _get_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _generate_summary(
        self,
        emotion_data: Dict,
        audio_data: Dict,
        metadata: Dict
    ) -> str:
        """Generate natural language summary"""
        
        emotion_summary = emotion_data.get("summary", {})
        quality_scores = audio_data.get("quality_scores", {})
        
        duration = metadata.get("duration_seconds", 0)
        duration_str = f"{int(duration // 60)}m {int(duration % 60)}s"
        
        dominant_emotion = emotion_summary.get("dominant_emotion", "neutral")
        eye_contact = emotion_summary.get("eye_contact_percentage", 0)
        
        overall_voice = quality_scores.get("overall", 0)
        
        summary = f"Analyzed {duration_str} of video content. "
        summary += f"Your dominant emotion was {dominant_emotion} with {eye_contact:.0f}% eye contact maintained. "
        
        if overall_voice >= 0.7:
            summary += "Your voice delivery was strong with good clarity and confidence. "
        elif overall_voice >= 0.5:
            summary += "Your voice delivery was adequate but has room for improvement. "
        else:
            summary += "Your voice delivery needs significant improvement in clarity and confidence. "
        
        return summary
    
    def _generate_insights(self, emotion_data: Dict, audio_data: Dict) -> List[str]:
        """Generate key insights from the analysis"""
        
        insights = []
        emotion_summary = emotion_data.get("summary", {})
        
        # Eye contact insights
        eye_contact = emotion_summary.get("eye_contact_percentage", 0)
        if eye_contact >= 70:
            insights.append(f"Strong eye contact maintained at {eye_contact:.0f}%. This conveys confidence and engagement.")
        elif eye_contact < 50:
            insights.append(f"Eye contact at {eye_contact:.0f}% is below optimal. Aim for 60-80% to appear more confident.")
        
        # Smile authenticity
        smile = emotion_summary.get("average_smile_authenticity", 0)
        if smile >= 0.7:
            insights.append("Your smiles appear genuine and authentic, which builds rapport.")
        elif smile < 0.4 and smile > 0:
            insights.append("Smiles detected but may appear forced. Practice natural, relaxed expressions.")
        
        # Voice insights
        speaking_rate = audio_data.get("speaking_rate", {})
        wpm = speaking_rate.get("words_per_minute", 0)
        if wpm > 0:
            if 120 <= wpm <= 160:
                insights.append(f"Speaking pace at {wpm:.0f} WPM is optimal for clarity and engagement.")
            elif wpm > 180:
                insights.append(f"Speaking pace at {wpm:.0f} WPM is too fast. Slow down for better comprehension.")
            elif wpm < 100:
                insights.append(f"Speaking pace at {wpm:.0f} WPM is too slow. Increase tempo to maintain engagement.")
        
        # Energy insights
        energy = audio_data.get("energy_analysis", {})
        confidence_indicator = energy.get("confidence_indicator", 0)
        if confidence_indicator >= 0.7:
            insights.append("Voice energy conveys strong confidence and authority.")
        elif confidence_indicator < 0.5:
            insights.append("Voice energy is low. Project more to convey confidence and enthusiasm.")
        
        return insights
    
    def _identify_strengths(
        self,
        emotion_data: Dict,
        audio_data: Dict,
        performance_score: Dict
    ) -> List[str]:
        """Identify top strengths"""
        
        strengths = []
        breakdown = performance_score.get("breakdown", {})
        
        # Check each metric
        if breakdown.get("eye_contact", 0) >= 0.7:
            strengths.append("Excellent eye contact - maintains connection with audience")
        
        if breakdown.get("smile_authenticity", 0) >= 0.7:
            strengths.append("Authentic, warm facial expressions")
        
        if breakdown.get("voice_clarity", 0) >= 0.7:
            strengths.append("Clear and well-paced speech delivery")
        
        if breakdown.get("voice_confidence", 0) >= 0.7:
            strengths.append("Confident vocal presence with good energy")
        
        if breakdown.get("voice_engagement", 0) >= 0.7:
            strengths.append("Engaging voice with good pitch variation")
        
        if breakdown.get("engagement", 0) >= 0.7:
            strengths.append("High overall engagement and presence")
        
        if not strengths:
            strengths.append("Baseline performance established - focus on improvement areas below")
        
        return strengths[:5]  # Top 5 strengths
    
    def _identify_weaknesses(
        self,
        emotion_data: Dict,
        audio_data: Dict,
        performance_score: Dict
    ) -> List[str]:
        """Identify areas for improvement"""
        
        weaknesses = []
        breakdown = performance_score.get("breakdown", {})
        
        # Check each metric
        if breakdown.get("eye_contact", 0) < 0.5:
            weaknesses.append("Eye contact needs improvement - look at camera more often")
        
        if breakdown.get("smile_authenticity", 0) < 0.4:
            weaknesses.append("Work on natural, authentic facial expressions")
        
        if breakdown.get("voice_clarity", 0) < 0.5:
            weaknesses.append("Speech clarity - adjust pace and enunciation")
        
        if breakdown.get("voice_confidence", 0) < 0.5:
            weaknesses.append("Vocal confidence - increase volume and reduce pauses")
        
        if breakdown.get("voice_engagement", 0) < 0.5:
            weaknesses.append("Voice monotony - add more pitch variation and enthusiasm")
        
        # Audio specific issues
        prosody = audio_data.get("prosody", {})
        if prosody.get("monotone_score", 0) > 0.7:
            weaknesses.append("Voice is too monotone - vary your pitch more")
        
        speaking_rate = audio_data.get("speaking_rate", {})
        if speaking_rate.get("words_per_minute", 0) > 200:
            weaknesses.append("Speaking too fast - slow down for better clarity")
        
        return weaknesses[:5]  # Top 5 areas to improve
    
    def _create_improvement_plan(
        self,
        emotion_data: Dict,
        audio_data: Dict,
        performance_score: Dict
    ) -> List[Dict]:
        """Create actionable improvement plan"""
        
        plan = []
        breakdown = performance_score.get("breakdown", {})
        
        # Prioritize by lowest scores
        metrics = [
            ("eye_contact", "Eye Contact", "Practice looking directly at the camera lens. Imagine you're talking to a friend."),
            ("smile_authenticity", "Facial Expressions", "Practice genuine smiles in the mirror. Think of something pleasant before speaking."),
            ("voice_clarity", "Speech Clarity", "Slow down by 10-20%. Enunciate clearly. Practice tongue twisters."),
            ("voice_confidence", "Vocal Confidence", "Breathe deeply. Project from your diaphragm. Record yourself daily."),
            ("voice_engagement", "Voice Variation", "Practice emphasizing key words. Vary your pitch when telling stories."),
        ]
        
        for metric_key, title, action in metrics:
            score = breakdown.get(metric_key, 0)
            if score < 0.6:
                plan.append({
                    "area": title,
                    "current_score": round(score, 2),
                    "priority": "high" if score < 0.4 else "medium",
                    "action": action,
                    "target_score": 0.7
                })
        
        # Sort by priority and score
        plan.sort(key=lambda x: (x["priority"] == "high", x["current_score"]))
        
        return plan[:5]  # Top 5 priorities
    
    def _identify_key_moments(self, emotion_data: Dict, audio_data: Dict) -> List[Dict]:
        """Identify key moments in the video with timestamps"""
        
        moments = []
        timeline = emotion_data.get("timeline", [])
        
        # Find peak engagement moments
        engagement_scores = [
            (f.get("timestamp", 0), f.get("engagement_level", 0))
            for f in timeline if f.get("face_detected")
        ]
        
        if engagement_scores:
            # Top 3 engagement moments
            top_engagement = sorted(engagement_scores, key=lambda x: x[1], reverse=True)[:3]
            for timestamp, score in top_engagement:
                moments.append({
                    "timestamp": timestamp,
                    "type": "peak_engagement",
                    "description": f"High engagement (score: {score:.2f})",
                    "timestamp_formatted": f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"
                })
        
        # Find moments with poor eye contact
        poor_eye_contact = [
            f for f in timeline 
            if f.get("face_detected") and not f.get("eye_contact", True)
        ]
        
        if len(poor_eye_contact) > 5:
            # Sample a few moments
            sample_moments = poor_eye_contact[::len(poor_eye_contact)//3][:3]
            for moment in sample_moments:
                timestamp = moment.get("timestamp", 0)
                moments.append({
                    "timestamp": timestamp,
                    "type": "improvement_opportunity",
                    "description": "Eye contact break - practice maintaining camera focus",
                    "timestamp_formatted": f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"
                })
        
        # Sort by timestamp
        moments.sort(key=lambda x: x["timestamp"])
        
        return moments[:10]  # Top 10 key moments
    
    def _format_facial_metrics(self, emotion_data: Dict) -> Dict:
        """Format facial analysis metrics for report"""
        summary = emotion_data.get("summary", {})
        return {
            "face_detection_rate": f"{summary.get('face_detection_rate', 0) * 100:.1f}%",
            "eye_contact_percentage": f"{summary.get('eye_contact_percentage', 0):.1f}%",
            "smile_authenticity": f"{summary.get('average_smile_authenticity', 0) * 100:.0f}/100",
            "engagement_level": f"{summary.get('average_engagement_level', 0) * 100:.0f}/100",
            "dominant_emotion": summary.get("dominant_emotion", "unknown"),
            "emotion_distribution": summary.get("emotion_distribution", {}),
            "emotional_range": f"{summary.get('emotional_variability', 0) * 100:.0f}/100"
        }
    
    def _format_voice_metrics(self, audio_data: Dict) -> Dict:
        """Format voice analysis metrics for report"""
        return {
            "duration": f"{audio_data.get('duration_seconds', 0):.1f}s",
            "speaking_rate": audio_data.get("speaking_rate", {}).get("pace", "unknown"),
            "words_per_minute": audio_data.get("speaking_rate", {}).get("words_per_minute", 0),
            "voice_clarity": f"{audio_data.get('quality_scores', {}).get('clarity', 0) * 100:.0f}/100",
            "voice_confidence": f"{audio_data.get('quality_scores', {}).get('confidence', 0) * 100:.0f}/100",
            "voice_engagement": f"{audio_data.get('quality_scores', {}).get('engagement', 0) * 100:.0f}/100",
            "pause_quality": audio_data.get("pause_analysis", {}).get("pause_quality", "unknown"),
            "pitch_variation": f"{audio_data.get('prosody', {}).get('variation_score', 0) * 100:.0f}/100"
        }