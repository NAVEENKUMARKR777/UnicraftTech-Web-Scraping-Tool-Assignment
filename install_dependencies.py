#!/usr/bin/env python3
"""
Dependency Installation Script
Safely installs all required dependencies for the web scraping tool
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success!")
            return True
        else:
            print(f"❌ {description} - Failed!")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def install_dependencies():
    """Install all dependencies safely"""
    print("🚀 Installing Web Scraping Tool Dependencies")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version_info
    print(f"📍 Python Version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("⚠️  Warning: Python 3.8+ is recommended for best compatibility")
    
    # Upgrade pip first
    print("\n🔧 Upgrading pip...")
    upgrade_pip = run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")
    
    # Install core dependencies first
    core_deps = [
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "selenium==4.15.2",
        "pandas==2.1.3",
        "lxml==4.9.3",
        "fake-useragent==1.4.0",
        "python-dotenv==1.0.0",
        "click==8.1.7",
        "tqdm==4.66.1",
        "webdriver-manager==4.0.1",
        "nltk==3.8.1",
        "textblob==0.17.1",
        "validators==0.22.0",
        "python-dateutil==2.8.2",
        "openpyxl==3.1.2"
    ]
    
    print("\n📦 Installing core dependencies...")
    for dep in core_deps:
        success = run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}")
        if not success:
            print(f"⚠️  Failed to install {dep}, trying without version pin...")
            package_name = dep.split("==")[0]
            run_command(f"{sys.executable} -m pip install {package_name}", f"Installing {package_name} (latest)")
    
    # Install optional dependencies
    optional_deps = [
        "scrapy==2.11.0",
        "aiohttp==3.9.1",
        "asyncio==3.4.3",
        "requests-oauthlib==1.3.1",
        "PySocks==1.7.1",
        "Flask==3.0.0",
        "Flask-SocketIO==5.3.6",
        "gunicorn==21.2.0",
        "APScheduler==3.10.4",
        "SQLAlchemy==2.0.23",
        "psutil==5.9.6",
        "colorama==0.4.6",
        "rich==13.7.0",
        "urllib3==2.1.0"
    ]
    
    print("\n🔧 Installing optional dependencies...")
    for dep in optional_deps:
        success = run_command(f"{sys.executable} -m pip install {dep}", f"Installing {dep}")
        if not success:
            print(f"⚠️  Failed to install {dep}, trying without version pin...")
            package_name = dep.split("==")[0]
            run_command(f"{sys.executable} -m pip install {package_name}", f"Installing {package_name} (latest)")
    
    # Download NLTK data
    print("\n📚 Downloading NLTK data...")
    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        print("✅ NLTK data downloaded successfully")
    except Exception as e:
        print(f"⚠️  NLTK data download failed: {e}")
    
    # Test basic imports
    print("\n🧪 Testing critical imports...")
    critical_imports = [
        ("requests", "HTTP requests"),
        ("bs4", "BeautifulSoup"),
        ("selenium", "Selenium webdriver"),
        ("pandas", "Data processing"),
        ("click", "CLI interface"),
        ("flask", "Web dashboard"),
        ("apscheduler", "Job scheduling")
    ]
    
    for module, description in critical_imports:
        try:
            __import__(module)
            print(f"✅ {description} - OK")
        except ImportError as e:
            print(f"❌ {description} - Failed: {e}")
    
    print("\n🎉 Installation complete!")
    print("\n📋 Next steps:")
    print("1. Copy .env.example to .env and configure API keys")
    print("2. Run: python main.py --help to see available commands")
    print("3. Try: python main.py demo to run a demonstration")
    print("4. For web dashboard: python web_dashboard.py")

if __name__ == "__main__":
    install_dependencies() 