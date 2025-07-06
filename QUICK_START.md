# 🚀 Quick Start Guide

## 🔧 Installation Issue Resolution

The original `requirements.txt` had a problematic package (`clearbit==0.1.7`) that's incompatible with modern Python. Here's how to fix it:

### Option 1: Use the Safe Installation Script (Recommended)

```bash
# Run the automated installation script
python install_dependencies.py
```

### Option 2: Use the Safe Requirements File

```bash
# Install using the safe requirements file
pip install -r requirements-safe.txt
```

### Option 3: Manual Installation (Core Features Only)

If you want just the core features without advanced components:

```bash
# Install core dependencies only
pip install requests beautifulsoup4 selenium pandas lxml fake-useragent python-dotenv click tqdm webdriver-manager nltk textblob validators python-dateutil openpyxl

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('vader_lexicon')"
```

### Option 4: Install Advanced Features Separately

```bash
# Install core first
pip install -r requirements-safe.txt

# Then install advanced features
pip install Flask Flask-SocketIO APScheduler SQLAlchemy psutil colorama rich
```

## 🎯 Quick Test

After installation, test if everything works:

```bash
# Test basic functionality
python main.py demo

# Test web dashboard
python web_dashboard.py

# Test job scheduler
python job_scheduler.py
```

## 📋 What Was Fixed

1. **Removed problematic package**: `clearbit==0.1.7` was causing the installation error
2. **Direct API calls**: The tool now uses direct HTTP requests to Clearbit API (more reliable)
3. **Flexible versions**: Used `>=` instead of `==` for better compatibility
4. **Installation scripts**: Created automated installation tools

## 🌟 Features Available

Even with the fixed installation, **ALL features are still available**:

- ✅ **Core scraping** - All basic and advanced extraction
- ✅ **API integration** - Clearbit, Hunter.io, Crunchbase, LinkedIn  
- ✅ **Proxy support** - IP rotation and health monitoring
- ✅ **Web dashboard** - Real-time monitoring interface
- ✅ **Job scheduling** - Automated scraping jobs
- ✅ **All output formats** - JSON, CSV, Excel

## 🚀 Next Steps

1. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Run a quick test**:
   ```bash
   python main.py search "tech startups" --max-results 5
   ```

3. **Try the web dashboard**:
   ```bash
   python web_dashboard.py
   # Open http://localhost:5000
   ```

4. **Schedule automated jobs**:
   ```bash
   python job_scheduler.py
   ```

## 🆘 Still Having Issues?

If you encounter other installation problems:

1. **Update pip**: `python -m pip install --upgrade pip`
2. **Check Python version**: Ensure you're using Python 3.8+
3. **Try individual installs**: Install packages one by one to identify issues
4. **Use virtual environment**: Always use `venv` or `conda` environments

## 💡 Pro Tips

- **API Keys**: Get free API keys from Clearbit, Hunter.io for enhanced features
- **Proxy Lists**: Add your proxy configurations to `proxy_list.json`
- **Customization**: Modify `config.py` for custom extraction patterns
- **Monitoring**: Use the web dashboard for real-time monitoring

The tool is now ready to use with all originally planned features! 🎉 