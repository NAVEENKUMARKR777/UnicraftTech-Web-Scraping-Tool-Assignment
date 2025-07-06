#!/usr/bin/env python3
"""
Setup script for Web Scraping Tool
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        # Install dependencies
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print("❌ Failed to install dependencies")
            print(f"Error: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_chrome_browser():
    """Check if Chrome browser is available"""
    print("🌐 Checking Chrome browser...")
    
    try:
        # Try to import webdriver_manager
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Try to get Chrome driver
        ChromeDriverManager().install()
        print("✅ Chrome browser and driver available")
        return True
        
    except Exception as e:
        print("⚠️  Chrome browser not found or not accessible")
        print("   Selenium features will not work")
        print("   You can still use the tool with --no-selenium flag")
        return False

def run_basic_tests():
    """Run basic tests to verify installation"""
    print("🧪 Running basic tests...")
    
    try:
        # Test imports
        from config import Config
        from scraper import WebScraper
        from data_output import DataOutput
        from main import WebScrapingTool
        
        print("✅ All modules imported successfully")
        
        # Test basic functionality
        scraper = WebScraper(use_selenium=False)
        scraper.close()
        
        print("✅ Basic functionality test passed")
        return True
        
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = ["output", "demo_output"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory already exists: {directory}")

def show_usage_examples():
    """Show usage examples"""
    print("\n🎯 Usage Examples:")
    print("=" * 50)
    
    examples = [
        "# Search for companies",
        'python main.py search --query "AI startups" --max-results 10',
        "",
        "# Scrape specific URLs",
        'python main.py scrape --file sample_urls.txt --level basic',
        "",
        "# Run demo",
        'python main.py demo',
        "",
        "# Run tests",
        'python test_scraper.py',
        "",
        "# Get help",
        'python main.py --help'
    ]
    
    for example in examples:
        print(f"  {example}")

def main():
    """Main setup function"""
    print("🚀 Web Scraping Tool Setup")
    print("=" * 60)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        success = False
    
    # Install dependencies
    if success and not install_dependencies():
        success = False
    
    # Check Chrome browser
    chrome_available = check_chrome_browser()
    
    # Run basic tests
    if success and not run_basic_tests():
        success = False
    
    # Create directories
    if success:
        create_directories()
    
    # Show results
    print("\n" + "=" * 60)
    if success:
        print("🎉 Setup completed successfully!")
        
        if chrome_available:
            print("✅ Full functionality available (with Selenium)")
        else:
            print("⚠️  Limited functionality (no Selenium)")
            print("   Use --no-selenium flag for faster scraping")
        
        print("\n📚 Next steps:")
        print("1. Run the demo: python demo.py")
        print("2. Try the CLI: python main.py --help")
        print("3. Run tests: python test_scraper.py")
        
        show_usage_examples()
        
    else:
        print("❌ Setup failed!")
        print("Please check the errors above and try again.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 