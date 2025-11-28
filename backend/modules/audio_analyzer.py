import librosa
import numpy as np
from typing import Dict, List, Tuple
import re
from collections import Counter

class AudioAnalyzer:
    """Analyzes audio for voice sentiment, speaking patterns, and filler words"""
    
    def __init__(self):
        self.filler_words = [
            'um', 'uh', 'like', 'you know', 'so', 'actually',
            'basically', 'literally', 'kind of', 'sort of',
            'i mean', 'right', 'okay', 'well'
        ]
        
    def analyze_audio(self, audio_path: str) -> Dict:
        """
        Complete audio analysis pipeline
        
        Args:
            audio_path: Path to audio file (WAV)
            
        Returns:
            Dictionary containing audio analysis results
        """
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Perform various analyses
            prosody = self._analyze_prosody(y, sr)
            speaking_rate = self._analyze_speaking_rate(y, sr)
            energy = self._analyze_energy(y, sr)
            pauses = self._analyze_pauses(y, sr)
            pitch = self._analyze_pitch(y, sr)
            
            # Calculate overall speaking quality scores
            quality_scores = self._calculate_quality_scores(
                prosody, speaking_rate, energy, pauses, pitch
            )
            
            # Transcription would go here (using faster-whisper)
            # For now, we'll simulate filler word detection
            filler_analysis = self._analyze_fillers_from_audio(y, sr)
            
            return {
                "duration_seconds": len(y) / sr,
                "prosody": prosody,
                "speaking_rate": speaking_rate,
                "energy_analysis": energy,
                "pause_analysis": pauses,
                "pitch_analysis": pitch,
                "filler_words": filler_analysis,
                "quality_scores": quality_scores,
                "recommendations": self._generate_recommendations(quality_scores)
            }
            
        except Exception as e:
            return {
                "error": f"Audio analysis failed: {str(e)}",
                "duration_seconds": 0
            }
    
    def _analyze_prosody(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze prosodic features (pitch variation, rhythm)"""
        
        # Extract pitch using librosa
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        # Get pitch values over time
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if not pitch_values:
            return {"variation": 0, "range_hz": 0, "monotone_score": 1.0}
        
        pitch_values = np.array(pitch_values)
        
        # Calculate variation metrics
        pitch_std = np.std(pitch_values)
        pitch_range = np.max(pitch_values) - np.min(pitch_values)
        
        # Monotone score (lower is better, means more variation)
        monotone_score = 1.0 / (1.0 + pitch_std / 50.0)
        
        return {
            "mean_pitch_hz": float(np.mean(pitch_values)),
            "pitch_std": float(pitch_std),
            "range_hz": float(pitch_range),
            "variation_score": min(1.0, pitch_std / 100.0),  # Normalized
            "monotone_score": float(monotone_score)
        }
    
    def _analyze_speaking_rate(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze speaking rate and rhythm"""
        
        # Detect onset events (syllables/words)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        onsets = librosa.onset.onset_detect(
            onset_envelope=onset_env,
            sr=sr,
            units='time'
        )
        
        duration = len(y) / sr
        
        if duration == 0:
            return {"words_per_minute": 0, "pace": "unknown"}
        
        # Estimate words (rough approximation: 1 onset ≈ 0.7 words)
        estimated_words = len(onsets) * 0.7
        wpm = (estimated_words / duration) * 60
        
        # Classify pace
        if wpm < 120:
            pace = "slow"
            pace_score = 0.6
        elif 120 <= wpm <= 160:
            pace = "optimal"
            pace_score = 1.0
        elif 160 < wpm <= 200:
            pace = "fast"
            pace_score = 0.7
        else:
            pace = "very_fast"
            pace_score = 0.4
        
        return {
            "words_per_minute": round(wpm, 1),
            "pace": pace,
            "pace_score": pace_score,
            "total_speech_segments": len(onsets),
            "avg_segment_duration": duration / len(onsets) if onsets.size > 0 else 0
        }
    
    def _analyze_energy(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze voice energy and dynamics"""
        
        # Calculate RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Calculate energy statistics
        mean_energy = np.mean(rms)
        energy_std = np.std(rms)
        
        # Detect low energy segments (potential nervousness or lack of confidence)
        low_energy_threshold = mean_energy * 0.5
        low_energy_ratio = np.sum(rms < low_energy_threshold) / len(rms)
        
        # Dynamic range
        dynamic_range = np.max(rms) - np.min(rms)
        
        # Energy consistency score (lower is more consistent)
        consistency = 1.0 - min(1.0, energy_std / mean_energy)
        
        return {
            "mean_energy": float(mean_energy),
            "energy_variation": float(energy_std),
            "dynamic_range": float(dynamic_range),
            "consistency_score": float(consistency),
            "low_energy_ratio": float(low_energy_ratio),
            "confidence_indicator": float(1.0 - low_energy_ratio)
        }
    
    def _analyze_pauses(self, y: np.ndarray, sr: int) -> Dict:
        """Analyze speaking pauses and silence"""
        
        # Detect silent segments
        intervals = librosa.effects.split(y, top_db=20)
        
        if len(intervals) == 0:
            return {
                "total_pauses": 0,
                "avg_pause_duration": 0,
                "speaking_time_ratio": 0
            }
        
        # Calculate pause durations
        pauses = []
        for i in range(len(intervals) - 1):
            pause_start = intervals[i][1] / sr
            pause_end = intervals[i + 1][0] / sr
            pause_duration = pause_end - pause_start
            pauses.append(pause_duration)
        
        # Speaking time
        speaking_frames = sum(end - start for start, end in intervals)
        total_frames = len(y)
        speaking_ratio = speaking_frames / total_frames
        
        # Classify pause patterns
        if pauses:
            avg_pause = np.mean(pauses)
            if avg_pause < 0.3:
                pause_quality = "minimal_pauses"
            elif 0.3 <= avg_pause <= 0.8:
                pause_quality = "natural_pauses"
            else:
                pause_quality = "long_pauses"
        else:
            avg_pause = 0
            pause_quality = "continuous"
        
        return {
            "total_pauses": len(pauses),
            "avg_pause_duration": float(avg_pause),
            "max_pause_duration": float(max(pauses)) if pauses else 0,
            "speaking_time_ratio": float(speaking_ratio),
            "pause_quality": pause_quality,
            "naturalness_score": self._calculate_pause_naturalness(pauses)
        }
    
    def _calculate_pause_naturalness(self, pauses: List[float]) -> float:
        """Calculate how natural the pause pattern is"""
        if not pauses:
            return 0.5
        
        # Natural pauses are typically 0.3-0.8 seconds
        natural_pauses = [p for p in pauses if 0.3 <= p <= 0.8]
        naturalness = len(natural_pauses) / len(pauses)
        
        return float(naturalness)
    
    def _analyze_pitch(self, y: np.ndarray, sr: int) -> Dict:
        """Detailed pitch analysis"""
        
        # Extract pitch contour
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        
        pitch_values = []
        for t in range(pitches.shape[1]):
            index = magnitudes[:, t].argmax()
            pitch = pitches[index, t]
            if pitch > 0:
                pitch_values.append(pitch)
        
        if not pitch_values:
            return {
                "average_pitch": 0,
                "pitch_stability": 0,
                "expressiveness": 0
            }
        
        pitch_values = np.array(pitch_values)
        
        # Calculate stability (inverse of variance)
        stability = 1.0 / (1.0 + np.var(pitch_values) / 1000.0)
        
        # Expressiveness (good variation without being erratic)
        pitch_std = np.std(pitch_values)
        expressiveness = min(1.0, pitch_std / 80.0) * (1.0 - abs(pitch_std - 50) / 100.0)
        
        return {
            "average_pitch_hz": float(np.mean(pitch_values)),
            "pitch_stability": float(stability),
            "pitch_range_hz": float(np.max(pitch_values) - np.min(pitch_values)),
            "expressiveness": float(max(0, expressiveness))
        }
    
    def _analyze_fillers_from_audio(self, y: np.ndarray, sr: int) -> Dict:
        """
        Detect filler words from audio characteristics
        Note: This is a simplified version. Full implementation would use speech recognition.
        """
        
        # Detect very short utterances (often fillers)
        intervals = librosa.effects.split(y, top_db=25)
        
        short_segments = 0
        for start, end in intervals:
            duration = (end - start) / sr
            if 0.1 <= duration <= 0.5:  # Typical filler word duration
                short_segments += 1
        
        total_segments = len(intervals)
        estimated_filler_rate = (short_segments / total_segments) if total_segments > 0 else 0
        
        return {
            "estimated_filler_count": short_segments,
            "filler_rate": round(estimated_filler_rate * 100, 1),
            "note": "Filler detection requires speech transcription for accuracy"
        }
    
    def _calculate_quality_scores(
        self,
        prosody: Dict,
        speaking_rate: Dict,
        energy: Dict,
        pauses: Dict,
        pitch: Dict
    ) -> Dict:
        """Calculate overall speaking quality scores"""
        
        # Clarity score (based on pace and energy)
        clarity = (
            speaking_rate.get("pace_score", 0.5) * 0.6 +
            energy.get("consistency_score", 0.5) * 0.4
        )
        
        # Confidence score (based on energy and pauses)
        confidence = (
            energy.get("confidence_indicator", 0.5) * 0.5 +
            (1.0 - prosody.get("monotone_score", 0.5)) * 0.3 +
            pauses.get("naturalness_score", 0.5) * 0.2
        )
        
        # Engagement score (based on variation and expressiveness)
        engagement = (
            prosody.get("variation_score", 0.5) * 0.4 +
            pitch.get("expressiveness", 0.5) * 0.4 +
            (1.0 - prosody.get("monotone_score", 0.5)) * 0.2
        )
        
        # Overall score
        overall = (clarity * 0.3 + confidence * 0.4 + engagement * 0.3)
        
        return {
            "clarity": round(clarity, 2),
            "confidence": round(confidence, 2),
            "engagement": round(engagement, 2),
            "overall": round(overall, 2)
        }
    
    def _generate_recommendations(self, quality_scores: Dict) -> List[str]:
        """Generate actionable recommendations based on scores"""
        
        recommendations = []
        
        if quality_scores["clarity"] < 0.6:
            recommendations.append(
                "Improve clarity by speaking at a moderate pace (120-160 words/minute) "
                "and maintaining consistent volume."
            )
        
        if quality_scores["confidence"] < 0.6:
            recommendations.append(
                "Boost confidence by increasing voice energy and reducing long pauses. "
                "Practice breathing techniques to maintain steady delivery."
            )
        
        if quality_scores["engagement"] < 0.6:
            recommendations.append(
                "Enhance engagement by varying your pitch and tone. Avoid monotone delivery "
                "by emphasizing key points and showing enthusiasm."
            )
        
        if quality_scores["overall"] >= 0.8:
            recommendations.append(
                "Excellent speaking quality! Your voice clarity, confidence, and "
                "engagement are all strong."
            )
        
        if not recommendations:
            recommendations.append(
                "Good speaking quality overall. Continue practicing to maintain consistency."
            )
        
        return recommendations