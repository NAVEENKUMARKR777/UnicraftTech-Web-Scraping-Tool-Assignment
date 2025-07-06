# Web Scraping Tool for Company Discovery and Data Extraction

A comprehensive web scraping tool that discovers companies and extracts detailed information based on search queries or seed URLs. Built with Python, this tool provides multi-level data extraction capabilities from basic contact information to advanced competitive intelligence.

## 🚀 Features

### ✅ **Implemented Features**

#### **Core Features (Minimal Requirements)**
- ✅ **Input Handling**: Accepts search queries or seed URLs with validation
- ✅ **Basic Data Extraction (Level 1)**:
  - Company name
  - Website URL
  - Email addresses
  - Phone numbers
- ✅ **Multiple Output Formats**: JSON, CSV, Excel (XLSX)
- ✅ **Comprehensive Error Handling**: Graceful handling of network errors, invalid URLs, and missing data
- ✅ **Detailed Logging**: Complete logging of operations and errors

#### **Advanced Features (Optional Enhancements)**
- ✅ **Medium Data Extraction (Level 2)**:
  - Social media profiles (LinkedIn, Twitter, Facebook, Instagram)
  - Physical addresses
  - Company descriptions
  - Founded year
  - Industry classification
  - Services offered
- ✅ **Advanced Data Extraction (Level 3)**:
  - Technology stack detection
  - Current projects and focus areas
  - Competitor analysis
  - Market positioning insights
  - Company size estimation
  - Funding information
  - Recent news mentions
- ✅ **Dynamic Content Handling**: Selenium WebDriver for JavaScript-rendered pages
- ✅ **Company Discovery**: Search engine integration (Google, Bing, DuckDuckGo)
- ✅ **Smart URL Filtering**: Automatic filtering of social media and irrelevant pages
- ✅ **Rate Limiting**: Configurable delays and anti-detection measures
- ✅ **User Agent Rotation**: Multiple user agents to avoid detection
- ✅ **CLI Interface**: Comprehensive command-line interface
- ✅ **Data Analysis**: Statistics and completeness reporting
- ✅ **Testing Suite**: Comprehensive unit and integration tests

## 📋 Requirements

### System Requirements
- Python 3.8 or higher
- Chrome browser (for Selenium functionality)
- Internet connection

### Python Dependencies
All dependencies are listed in `requirements.txt`:
```
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
pandas==2.1.3
lxml==4.9.3
fake-useragent==1.4.0
python-dotenv==1.0.0
click==8.1.7
tqdm==4.66.1
scrapy==2.11.0
webdriver-manager==4.0.1
nltk==3.8.1
textblob==0.17.1
validators==0.22.0
aiohttp==3.9.1
asyncio==3.4.3
python-dateutil==2.8.2
openpyxl==3.1.2
```

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd web-scraping-tool
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Installation
```bash
python main.py --help
```

## 🎯 Usage

### Command Line Interface

The tool provides a comprehensive CLI with multiple commands:

#### **1. Search and Scrape Companies**
```bash
python main.py search --query "cloud computing startups in Silicon Valley" --max-results 20 --level advanced --format json
```

**Options:**
- `--query, -q`: Search query (required)
- `--max-results, -n`: Maximum number of companies (default: 20)
- `--level, -l`: Extraction level (basic/medium/advanced, default: basic)
- `--engines, -e`: Search engines (google/bing/duckduckgo, default: google,bing)
- `--format, -f`: Output format (json/csv/xlsx, default: json)
- `--output, -o`: Output filename (optional)

#### **2. Scrape Specific URLs**
```bash
python main.py scrape --urls https://example.com https://company.com --level advanced --format xlsx
```

**Options:**
- `--urls, -u`: Individual URLs to scrape
- `--file, -f`: File containing URLs (one per line)
- `--level, -l`: Extraction level
- `--format, -fmt`: Output format
- `--output, -o`: Output filename

#### **3. Convert Data Formats**
```bash
python main.py convert --input output/data.json --format csv --output converted_data
```

#### **4. Generate Statistics**
```bash
python main.py stats --input output/data.json
```

#### **5. Create Sample Data**
```bash
python main.py sample --input output/data.json --size 5
```

#### **6. Run Demo**
```bash
python main.py demo
```

### Global Options
- `--verbose, -v`: Enable verbose logging
- `--no-selenium`: Disable Selenium (faster but limited)
- `--output-dir`: Custom output directory

## 📊 Data Extraction Levels

### Level 1: Basic Extraction
- Company name
- Website URL
- Email addresses
- Phone numbers

### Level 2: Medium Extraction
**Includes Level 1 plus:**
- Social media profiles
- Physical addresses
- Company descriptions
- Founded year
- Industry classification
- Services offered

### Level 3: Advanced Extraction
**Includes Level 1 & 2 plus:**
- Technology stack analysis
- Current projects
- Competitor identification
- Market positioning
- Company size estimation
- Funding information
- Recent news mentions

## 📁 Project Structure

```
web-scraping-tool/
├── main.py                 # CLI interface and main application
├── scraper.py             # Core scraping functionality
├── search_discovery.py    # Company discovery via search engines
├── data_output.py         # Data export and formatting
├── config.py              # Configuration and settings
├── test_scraper.py        # Comprehensive test suite
├── requirements.txt       # Python dependencies
├── README.md              # This file
├── output/                # Output directory (created automatically)
│   ├── *.json            # JSON output files
│   ├── *.csv             # CSV output files
│   └── *.xlsx            # Excel output files
└── scraper.log           # Application logs
```

## 🎨 Output Examples

### JSON Output
```json
[
  {
    "company_name": "Example Corp",
    "website_url": "https://example.com",
    "email": ["contact@example.com", "info@example.com"],
    "phone": ["+1-555-123-4567"],
    "address": "123 Main St, San Francisco, CA 94102",
    "description": "Leading cloud computing solutions provider",
    "social_media": {
      "linkedin": "https://linkedin.com/company/example",
      "twitter": "https://twitter.com/example"
    },
    "tech_stack": {
      "javascript": ["react", "node.js"],
      "cloud": ["aws", "azure"]
    },
    "extraction_level": "advanced"
  }
]
```

### CSV Output
Contains flattened data with columns like:
- `company_name`
- `website_url`
- `email`
- `phone`
- `social_media_linkedin`
- `tech_stack_javascript`
- etc.

### Excel Output
- **Company Data** sheet: Main data
- **Summary** sheet: Statistics and completeness metrics

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_scraper.py
```

The test suite includes:
- Unit tests for all components
- Integration tests
- Mock-based testing for external dependencies
- Error handling verification

## ⚙️ Configuration

### Custom Configuration
Modify `config.py` to customize:
- Rate limiting settings
- User agent rotation
- CSS selectors
- Technology detection patterns
- Output formats

### Environment Variables
Create a `.env` file for sensitive configuration:
```
SELENIUM_HEADLESS=True
DEFAULT_DELAY=2
MAX_RETRIES=3
```

## 🔧 Advanced Usage

### Programmatic Usage
```python
from main import WebScrapingTool

# Initialize tool
tool = WebScrapingTool(use_selenium=True, output_dir="custom_output")

# Search and scrape
result = tool.scrape_from_query(
    query="fintech startups in New York",
    max_results=10,
    extraction_level="advanced"
)

# Process results
if result.get('success'):
    print(f"Scraped {len(result['results'])} companies")
    print(f"Data saved to: {result['saved_file']}")

# Clean up
tool.close()
```

### Batch Processing
```python
# Process multiple queries
queries = [
    "AI startups in Silicon Valley",
    "blockchain companies in London",
    "fintech companies in Singapore"
]

for query in queries:
    result = tool.scrape_from_query(query, max_results=15)
    # Process each result
```

## 🚫 Limitations and Considerations

### Ethical Scraping
- Respects robots.txt files
- Implements rate limiting
- Uses proper User-Agent headers
- Avoids overwhelming target servers

### Technical Limitations
- Some sites may block automated requests
- JavaScript-heavy sites require Selenium (slower)
- Search engines may implement CAPTCHAs
- Some data may not be publicly available

### Legal Considerations
- Only scrapes publicly available information
- Respects website terms of service
- Implements appropriate delays
- Users responsible for compliance with applicable laws

## 📈 Performance

### Optimization Tips
1. **Use `--no-selenium`** for faster scraping when dynamic content isn't needed
2. **Adjust rate limiting** in `config.py` for your use case
3. **Use basic extraction level** for large datasets
4. **Batch process** URLs for efficiency

### Typical Performance
- **Basic extraction**: ~2-3 seconds per company
- **Advanced extraction**: ~5-10 seconds per company
- **Search discovery**: ~10-30 seconds per query (depending on results)

## 🛡️ Error Handling

The tool includes comprehensive error handling:
- Network timeouts and connection errors
- Invalid URL handling
- Missing data graceful handling
- Rate limiting and retry logic
- Detailed logging for debugging

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests before submitting
5. Follow existing code style

### Running Tests
```bash
# Run all tests
python test_scraper.py

# Run specific test class
python -m unittest test_scraper.TestWebScraper

# Run with verbose output
python test_scraper.py -v
```

## 📝 License

This project is provided as-is for educational and legitimate business purposes. Users are responsible for ensuring compliance with applicable laws and website terms of service.

## 🔗 Support

For questions or issues:
1. Check the logs in `scraper.log`
2. Run tests to verify installation
3. Review configuration settings
4. Contact: hr@unicraft.tech

## 🎯 Future Enhancements

Potential future features:
- [ ] Web dashboard interface
- [ ] Database integration
- [ ] Real-time monitoring
- [ ] Machine learning for better data extraction
- [ ] API integration (LinkedIn, Clearbit, etc.)
- [ ] Scheduled scraping jobs
- [ ] Email notifications
- [ ] Data validation and cleaning
- [ ] Export to CRM systems

---

**Note**: This tool is designed for legitimate business intelligence and lead generation purposes. Please ensure you comply with all applicable laws and respect website terms of service when using this tool. 