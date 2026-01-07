"""
Streamlit 실행 스크립트
"""
import subprocess
import sys

if __name__ == "__main__":
    # Streamlit 설치 확인
    try:
        import streamlit
    except ImportError:
        print("📦 Streamlit 설치 중...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    
    # 앱 실행
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
