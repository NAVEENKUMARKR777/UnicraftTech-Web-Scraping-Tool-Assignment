import os
from typing import Dict, List, Optional

class Config:
    """Configuration settings for the web scraping tool"""
    
    # Rate limiting settings
    DEFAULT_DELAY = 2  # seconds between requests
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    
    # Selenium settings
    SELENIUM_TIMEOUT = 10
    HEADLESS_MODE = True
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    
    # Search engines configuration
    SEARCH_ENGINES = {
        'google': 'https://www.google.com/search?q={}',
        'bing': 'https://www.bing.com/search?q={}',
        'duckduckgo': 'https://duckduckgo.com/?q={}'
    }
    
    # Common selectors for different data types
    SELECTORS = {
        'title': ['title', 'h1', '.title', '#title'],
        'email': ['a[href^="mailto:"]', '.email', '.contact-email'],
        'phone': ['.phone', '.contact-phone', 'a[href^="tel:"]'],
        'address': ['.address', '.contact-address', '.location'],
        'social': {
            'linkedin': 'a[href*="linkedin.com"]',
            'twitter': 'a[href*="twitter.com"]',
            'facebook': 'a[href*="facebook.com"]',
            'instagram': 'a[href*="instagram.com"]'
        },
        'description': ['meta[name="description"]', '.description', '.about', '.company-info'],
        'contact_page': ['a[href*="contact"]', 'a[href*="about"]', 'a[href*="team"]']
    }
    
    # Technology stack patterns
    TECH_PATTERNS = {
        'javascript': ['react', 'angular', 'vue', 'node.js', 'javascript', 'js'],
        'python': ['django', 'flask', 'python', 'fastapi', 'pyramid'],
        'java': ['spring', 'hibernate', 'java', 'jsp', 'struts'],
        'php': ['laravel', 'symfony', 'php', 'wordpress', 'drupal'],
        'ruby': ['rails', 'ruby', 'sinatra'],
        'css': ['bootstrap', 'tailwind', 'sass', 'less', 'css'],
        'databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'sqlite'],
        'cloud': ['aws', 'azure', 'gcp', 'digital ocean', 'heroku'],
        'analytics': ['google analytics', 'mixpanel', 'amplitude', 'hotjar']
    }
    
    # Output formats
    OUTPUT_FORMATS = ['json', 'csv', 'xlsx']
    
    # Default output structure
    DEFAULT_OUTPUT_FIELDS = [
        'company_name', 'website_url', 'email', 'phone', 'address',
        'description', 'industry', 'founded_year', 'social_media',
        'tech_stack', 'competitors', 'projects', 'contact_info'
    ]
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Get default headers for requests"""
        return {
            'User-Agent': cls.USER_AGENTS[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    @classmethod
    def get_selenium_options(cls):
        """Get Chrome options for Selenium"""
        from selenium.webdriver.chrome.options import Options
        options = Options()
        if cls.HEADLESS_MODE:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-agent={cls.USER_AGENTS[0]}')
        return options 