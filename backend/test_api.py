#!/usr/bin/env python3
"""
EmotiSense API Test Script
Tests all endpoints and simulates a complete analysis workflow
"""

import requests
import time
import sys
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health_check():
    """Test health endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the server running?")
        print("   Start with: python main.py")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("\n🔍 Testing root endpoint...")
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Version: {data.get('version')}")
        print(f"   Status: {data.get('status')}")
        return True
    else:
        print(f"❌ Root endpoint failed: {response.status_code}")
        return False

def test_upload_video(video_path: str):
    """Test video upload"""
    print(f"\n🔍 Testing video upload...")
    
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        print("   Create a test video or use your own video file")
        return None
    
    with open(video_path, 'rb') as f:
        files = {'file': (Path(video_path).name, f, 'video/mp4')}
        response = requests.post(f"{API_URL}/api/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        session_id = data.get('session_id')
        print(f"✅ Upload successful")
        print(f"   Session ID: {session_id}")
        print(f"   Status: {data.get('status')}")
        return session_id
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return None

def test_status_check(session_id: str, timeout: int = 120):
    """Test status checking and wait for completion"""
    print(f"\n🔍 Monitoring processing status...")
    
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        response = requests.get(f"{API_URL}/api/status/{session_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            
            if status != last_status:
                print(f"   Status: {status} (Progress: {data.get('progress', 0)}%)")
                last_status = status
            
            if status == 'completed':
                print(f"✅ Processing completed in {time.time() - start_time:.1f}s")
                return True
            elif status == 'failed':
                print(f"❌ Processing failed")
                return False
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
        
        time.sleep(2)
    
    print(f"❌ Timeout after {timeout}s")
    return False

def test_get_results(session_id: str):
    """Test retrieving results"""
    print(f"\n🔍 Retrieving analysis results...")
    
    response = requests.get(f"{API_URL}/api/results/{session_id}")
    
    if response.status_code == 200:
        data = response.json()
        report = data.get('report', {})
        
        print("✅ Results retrieved successfully")
        print("\n" + "="*60)
        print("ANALYSIS RESULTS")
        print("="*60)
        
        # Performance Score
        perf_score = report.get('performance_score', {})
        print(f"\n📊 Overall Score: {perf_score.get('overall', 0)*100:.1f}/100")
        print(f"   Rating: {report.get('rating', 'N/A')}")
        print(f"   Facial Score: {perf_score.get('facial_score', 0)*100:.1f}/100")
        print(f"   Voice Score: {perf_score.get('voice_score', 0)*100:.1f}/100")
        
        # Summary
        print(f"\n📝 Summary:")
        print(f"   {report.get('summary', 'N/A')}")
        
        # Strengths
        strengths = report.get('strengths', [])
        if strengths:
            print(f"\n💪 Strengths:")
            for i, strength in enumerate(strengths, 1):
                print(f"   {i}. {strength}")
        
        # Weaknesses
        weaknesses = report.get('weaknesses', [])
        if weaknesses:
            print(f"\n🎯 Areas to Improve:")
            for i, weakness in enumerate(weaknesses, 1):
                print(f"   {i}. {weakness}")
        
        # Key Insights
        insights = report.get('insights', [])
        if insights:
            print(f"\n💡 Key Insights:")
            for i, insight in enumerate(insights, 1):
                print(f"   {i}. {insight}")
        
        print("\n" + "="*60)
        return True
    else:
        print(f"❌ Failed to retrieve results: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_list_sessions():
    """Test listing sessions"""
    print(f"\n🔍 Listing recent sessions...")
    
    response = requests.get(f"{API_URL}/api/sessions?limit=5")
    
    if response.status_code == 200:
        data = response.json()
        sessions = data.get('sessions', [])
        
        print(f"✅ Found {len(sessions)} sessions")
        for session in sessions:
            print(f"   - {session['session_id']}: {session['status']} ({session['filename']})")
        return True
    else:
        print(f"❌ Failed to list sessions: {response.status_code}")
        return False

def test_delete_session(session_id: str):
    """Test session deletion"""
    print(f"\n🔍 Testing session deletion...")
    
    response = requests.delete(f"{API_URL}/api/session/{session_id}")
    
    if response.status_code == 200:
        print(f"✅ Session deleted successfully")
        return True
    else:
        print(f"❌ Failed to delete session: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("🚀 EmotiSense API Test Suite")
    print("="*60)
    
    # Basic tests
    if not test_health_check():
        print("\n❌ Server is not running. Please start the backend first.")
        sys.exit(1)
    
    test_root_endpoint()
    
    # Check if video file is provided
    if len(sys.argv) < 2:
        print("\n⚠️  No video file provided")
        print("   Usage: python test_api.py <video_file_path>")
        print("\n   Skipping upload tests...")
        test_list_sessions()
        return
    
    video_path = sys.argv[1]
    
    # Upload and processing tests
    session_id = test_upload_video(video_path)
    
    if session_id:
        # Wait for processing
        if test_status_check(session_id):
            # Get results
            test_get_results(session_id)
        
        # List sessions
        test_list_sessions()
        
        # Optional: Delete test session
        # Uncomment to clean up after test
        # test_delete_session(session_id)
    
    print("\n" + "="*60)
    print("🎉 Test suite completed!")
    print("="*60)

if __name__ == "__main__":
    main()