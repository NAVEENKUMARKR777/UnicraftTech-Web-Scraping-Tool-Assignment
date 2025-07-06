# 🛠️ Troubleshooting Guide

## 🔧 Installation Issues

### Issue 1: Clearbit Package Installation Error
**Error**: `error in clearbit setup command: use_2to3 is invalid`

**Solution**: 
1. **Use the safe requirements file**: `pip install -r requirements-safe.txt`
2. **Or use the automated installer**: `python install_dependencies.py`
3. **The Clearbit functionality still works** - we use direct API calls instead

### Issue 2: General Package Installation Failures
**Solution**: 
```bash
# Option 1: Use the automated installer (recommended)
python install_dependencies.py

# Option 2: Install manually with flexible versions
pip install requests beautifulsoup4 selenium pandas lxml fake-useragent python-dotenv click tqdm webdriver-manager nltk textblob validators python-dateutil openpyxl

# Option 3: Install core packages only
pip install -r requirements-safe.txt
```

## 🌐 WebDriver/Selenium Issues

### Issue 1: WebDriver Initialization Error
**Error**: `WebDriver.__init__() got multiple values for argument 'options'`

**Fix Applied**: Updated `scraper.py` to use proper Selenium 4.x syntax:
```python
from selenium.webdriver.chrome.service import Service
service = Service(ChromeDriverManager().install())
self.driver = webdriver.Chrome(service=service, options=options)
```

**Testing**: Run `python test_fixes.py` to verify the fix

### Issue 2: Chrome Driver Download Issues
**Error**: Could not reach host / Driver downloading issues

**Solutions**:
1. **Check internet connection**: Ensure you can access Google's servers
2. **Use offline mode**: `python main.py search "query" --no-selenium`
3. **Manual Chrome installation**: Install Google Chrome browser
4. **Corporate network**: May need proxy configuration

## 🔍 Search Discovery Issues

### Issue 1: No Companies Found
**Error**: `No companies found for the given query`

**Fix Applied**: Added improved search discovery with multiple fallback strategies:

1. **Sample company database** for common queries
2. **Multiple search engines** (DuckDuckGo, Bing)
3. **GitHub organization search** for tech companies
4. **Better error handling** and fallbacks

**Testing**:
```bash
# Test the improved search
python search_discovery_improved.py

# Or test through main CLI
python main.py search --query "cloud computing" --max-results 5
```

### Issue 2: 403 Forbidden Errors
**Cause**: Websites blocking requests due to bot detection

**Solutions**:
1. **Improved user agents**: Better browser simulation
2. **Request delays**: Human-like timing
3. **Rotate requests**: Use different search strategies
4. **Try different queries**: Use more specific keywords

## 🔧 Configuration Issues

### Issue 1: Missing Environment Variables
**Error**: API keys not found

**Solution**:
```bash
# Copy the example environment file
cp .env.example .env

# Edit with your API keys
# Get keys from:
# - Clearbit: https://clearbit.com/
# - Hunter.io: https://hunter.io/
# - Crunchbase: https://data.crunchbase.com/
```

### Issue 2: Output Directory Issues
**Error**: Cannot create output directory

**Solution**:
```bash
# Create directory manually
mkdir output

# Or specify different directory
python main.py search "query" --output-dir /path/to/writable/directory
```

## 🐍 Python/Environment Issues

### Issue 1: Python Version Compatibility
**Requirement**: Python 3.8+ recommended

**Check version**:
```bash
python --version

# If using older Python, upgrade or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Issue 2: Import Errors
**Error**: ModuleNotFoundError

**Solutions**:
1. **Install in virtual environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements-safe.txt
   ```

2. **Check Python path**: Ensure you're in the correct directory

3. **Reinstall packages**: `pip install --force-reinstall package_name`

## 🌐 Network/Connectivity Issues

### Issue 1: Request Timeouts
**Symptoms**: Scraping takes very long or times out

**Solutions**:
1. **Check internet connection**
2. **Use shorter timeout**: Modify `Config.REQUEST_TIMEOUT`
3. **Try fewer results**: Use `--max-results 5`
4. **Use no-selenium mode**: `--no-selenium` flag

### Issue 2: Rate Limiting
**Symptoms**: Getting blocked by websites

**Solutions**:
1. **Increase delays**: Modify `Config.REQUEST_DELAY`
2. **Use proxy support**: `python proxy_manager.py`
3. **Try smaller batches**: Process fewer URLs at once

## 📊 Data Extraction Issues

### Issue 1: No Data Extracted
**Symptoms**: Empty results or minimal data

**Solutions**:
1. **Try different extraction levels**: `--level medium` or `--level advanced`
2. **Check URL accessibility**: Ensure websites are reachable
3. **Try with Selenium**: Remove `--no-selenium` flag
4. **Use different queries**: Try more specific keywords

### Issue 2: Incomplete Data
**Symptoms**: Missing emails, phones, or other details

**Solutions**:
1. **Use advanced extraction**: `--level advanced`
2. **Enable API integration**: Set up API keys
3. **Try different websites**: Some sites have better structured data

## 🖥️ Dashboard Issues

### Issue 1: Dashboard Won't Start
**Error**: Flask import errors or port conflicts

**Solutions**:
```bash
# Install Flask dependencies
pip install Flask Flask-SocketIO

# Try different port
python web_dashboard.py --port 8080

# Check if port is in use
netstat -an | grep :5000
```

### Issue 2: Dashboard Connection Issues
**Symptoms**: Can't access dashboard in browser

**Solutions**:
1. **Check firewall**: Ensure port 5000 is open
2. **Try localhost**: Access `http://localhost:5000`
3. **Check logs**: Look for error messages in console

## 🤖 API Integration Issues

### Issue 1: API Key Errors
**Error**: Authentication failed or quota exceeded

**Solutions**:
1. **Verify API keys**: Check .env file configuration
2. **Check quotas**: Ensure you haven't exceeded API limits
3. **Test APIs individually**: `python api_integration.py`

### Issue 2: Rate Limiting from APIs
**Symptoms**: API calls being rejected

**Solutions**:
1. **Check rate limits**: Each API has different limits
2. **Increase delays**: APIs have built-in rate limiting
3. **Use free tier wisely**: Monitor usage

## 🧪 Testing and Verification

### Run Comprehensive Tests
```bash
# Test all components
python test_fixes.py

# Test individual components
python scraper.py          # Test scraping
python search_discovery_improved.py  # Test search
python web_dashboard.py     # Test dashboard
python proxy_manager.py     # Test proxies
```

### Quick Verification Commands
```bash
# Basic functionality
python main.py demo

# Search with improved discovery
python main.py search --query "tech startups" --max-results 3

# Test specific URL
python main.py scrape --urls https://example.com --level basic

# Test output formats
python main.py search --query "AI companies" --format csv --max-results 2
```

## 🚨 Emergency Fallbacks

### If Nothing Works
1. **Use sample data**: The tool includes sample companies for testing
2. **Manual URL list**: Create a file with URLs and use `--file` option
3. **Basic scraping only**: Use `--no-selenium --level basic`
4. **Minimal dependencies**: Install only core packages

### Minimal Working Setup
```bash
# Absolute minimum installation
pip install requests beautifulsoup4 click pandas

# Run with minimal features
python main.py scrape --urls https://example.com --no-selenium --level basic
```

## 📞 Getting Help

### Debugging Steps
1. **Check Python version**: `python --version`
2. **Run tests**: `python test_fixes.py`
3. **Check logs**: Look for ERROR messages
4. **Try minimal setup**: Use basic features first
5. **Check internet**: Verify connectivity

### Log Analysis
```bash
# Enable verbose logging
python main.py search "query" --verbose

# Check specific component logs
grep "ERROR" *.log
```

### Common Log Messages
- **"Failed to initialize Selenium"**: Chrome/WebDriver issue → Use `--no-selenium`
- **"No companies found"**: Search issue → Try different keywords
- **"Request timeout"**: Network issue → Check connectivity
- **"Import error"**: Missing dependency → Reinstall packages

## ✅ Verification Checklist

After applying fixes, verify:
- [ ] Dependencies install without errors
- [ ] Selenium WebDriver initializes (or gracefully falls back)
- [ ] Search discovery finds companies
- [ ] Basic scraping extracts data
- [ ] Output files are created
- [ ] Dashboard starts (if using advanced features)

## 🎯 Performance Optimization

### For Better Results
1. **Use specific queries**: "fintech startups in NYC" vs "companies"
2. **Enable API integration**: Set up external API keys
3. **Use appropriate extraction level**: Basic for speed, Advanced for completeness
4. **Monitor resource usage**: Close unused browsers/applications

### For Faster Performance
1. **Disable Selenium**: Use `--no-selenium` flag
2. **Reduce results**: Use `--max-results 5`
3. **Use JSON output**: Fastest format for processing
4. **Enable caching**: Set `ENABLE_CACHING=true` in .env

---

**Need more help?** All fixes have been applied and tested. The tool should now work reliably with proper fallbacks for any issues. 🎉 