import re
import time
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Any
import json
import random
from fake_useragent import UserAgent
import validators

from config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebScraper:
    """Main web scraping class with multi-level data extraction"""
    
    def __init__(self, use_selenium: bool = True, delay: float = None):
        self.use_selenium = use_selenium
        self.delay = delay or Config.DEFAULT_DELAY
        self.session = requests.Session()
        self.session.headers.update(Config.get_headers())
        self.ua = UserAgent()
        self.driver = None
        
        if use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Initialize Selenium WebDriver"""
        try:
            from selenium.webdriver.chrome.service import Service
            
            options = Config.get_selenium_options()
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        try:
            new_agent = self.ua.random
            self.session.headers.update({'User-Agent': new_agent})
            if self.driver:
                self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": new_agent})
        except Exception as e:
            logger.warning(f"Failed to rotate user agent: {e}")
    
    def _get_page_content(self, url: str, use_selenium: bool = False) -> Optional[BeautifulSoup]:
        """Get page content using requests or Selenium"""
        try:
            if use_selenium and self.driver:
                return self._get_selenium_content(url)
            else:
                return self._get_requests_content(url)
        except Exception as e:
            logger.error(f"Error getting page content for {url}: {e}")
            return None
    
    def _get_requests_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content using requests"""
        try:
            self._rotate_user_agent()
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Requests error for {url}: {e}")
            return None
    
    def _get_selenium_content(self, url: str) -> Optional[BeautifulSoup]:
        """Get page content using Selenium"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, Config.SELENIUM_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for potential JavaScript content
            time.sleep(2)
            
            return BeautifulSoup(self.driver.page_source, 'html.parser')
        except (TimeoutException, WebDriverException) as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None
    
    def extract_basic_data(self, url: str) -> Dict[str, Any]:
        """Level 1 - Basic Data Extraction"""
        logger.info(f"Extracting basic data from {url}")
        
        soup = self._get_page_content(url)
        if not soup:
            return {"error": "Failed to fetch page content"}
        
        data = {
            "url": url,
            "company_name": self._extract_company_name(soup, url),
            "website_url": url,
            "email": self._extract_emails(soup),
            "phone": self._extract_phones(soup),
            "extraction_level": "basic"
        }
        
        time.sleep(self.delay)
        return data
    
    def extract_medium_data(self, url: str) -> Dict[str, Any]:
        """Level 2 - Medium Data Extraction with Enhanced Details"""
        logger.info(f"Extracting medium data from {url}")
        
        # Get basic data first
        data = self.extract_basic_data(url)
        if "error" in data:
            return data
        
        soup = self._get_page_content(url)
        if not soup:
            return data
        
        # Enhanced contact information
        data.update({
            "social_media": self._extract_social_media(soup),
            "address": self._extract_address(soup),
            "description": self._extract_description(soup),
            "year_founded": self._extract_founded_year(soup),
            "industry": self._extract_industry(soup),
            "services": self._extract_services(soup),
            "extraction_level": "medium"
        })
        
        # Try to get additional info from contact/about pages
        contact_urls = self._find_contact_pages(soup, url)
        for contact_url in contact_urls[:2]:  # Limit to 2 additional pages
            self._extract_contact_page_info(contact_url, data)
        
        return data
    
    def extract_advanced_data(self, url: str) -> Dict[str, Any]:
        """Level 3 - Advanced Data Extraction with Comprehensive Insights"""
        logger.info(f"Extracting advanced data from {url}")
        
        # Get medium data first
        data = self.extract_medium_data(url)
        if "error" in data:
            return data
        
        soup = self._get_page_content(url, use_selenium=True)  # Use Selenium for advanced
        if not soup:
            return data
        
        # Advanced insights
        data.update({
            "tech_stack": self._extract_tech_stack(soup),
            "current_projects": self._extract_current_projects(soup),
            "competitors": self._extract_competitors(soup),
            "market_position": self._extract_market_position(soup),
            "company_size": self._extract_company_size(soup),
            "funding_info": self._extract_funding_info(soup),
            "news_mentions": self._extract_news_mentions(soup),
            "extraction_level": "advanced"
        })
        
        return data
    
    def _extract_company_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract company name from various sources"""
        # Try different approaches
        approaches = [
            lambda: soup.find('title').text.split('|')[0].strip() if soup.find('title') else '',
            lambda: soup.find('h1').text.strip() if soup.find('h1') else '',
            lambda: soup.find('meta', {'property': 'og:site_name'})['content'] if soup.find('meta', {'property': 'og:site_name'}) else '',
            lambda: soup.find('meta', {'name': 'application-name'})['content'] if soup.find('meta', {'name': 'application-name'}) else '',
            lambda: urlparse(url).netloc.replace('www.', '').split('.')[0].capitalize()
        ]
        
        for approach in approaches:
            try:
                name = approach()
                if name and len(name) > 0:
                    return name
            except:
                continue
        
        return urlparse(url).netloc.replace('www.', '')
    
    def _extract_emails(self, soup: BeautifulSoup) -> List[str]:
        """Extract email addresses"""
        emails = set()
        
        # Look for mailto links
        for link in soup.find_all('a', href=re.compile(r'^mailto:')):
            email = link['href'].replace('mailto:', '').split('?')[0]
            if validators.email(email):
                emails.add(email)
        
        # Look for email patterns in text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        text_content = soup.get_text()
        found_emails = re.findall(email_pattern, text_content)
        
        for email in found_emails:
            if validators.email(email) and not email.endswith('.png') and not email.endswith('.jpg'):
                emails.add(email)
        
        return list(emails)
    
    def _extract_phones(self, soup: BeautifulSoup) -> List[str]:
        """Extract phone numbers"""
        phones = set()
        
        # Look for tel links
        for link in soup.find_all('a', href=re.compile(r'^tel:')):
            phone = link['href'].replace('tel:', '').strip()
            phones.add(phone)
        
        # Look for phone patterns in text
        phone_patterns = [
            r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US format
            r'\+?[\d\s\-\(\)]{10,}',  # International format
        ]
        
        text_content = soup.get_text()
        for pattern in phone_patterns:
            found_phones = re.findall(pattern, text_content)
            for phone in found_phones:
                clean_phone = re.sub(r'[^\d\+]', '', phone)
                if len(clean_phone) >= 10:
                    phones.add(phone.strip())
        
        return list(phones)
    
    def _extract_social_media(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract social media links"""
        social_media = {}
        
        for platform, selector in Config.SELECTORS['social'].items():
            links = soup.select(selector)
            if links:
                social_media[platform] = links[0]['href']
        
        return social_media
    
    def _extract_address(self, soup: BeautifulSoup) -> str:
        """Extract physical address"""
        selectors = Config.SELECTORS['address']
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements[0].get_text(strip=True)
        
        # Look for address patterns in text
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl)',
            r'\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Za-z]{2}\s+\d{5}'
        ]
        
        text_content = soup.get_text()
        for pattern in address_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract company description"""
        selectors = Config.SELECTORS['description']
        
        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', '')
            else:
                elements = soup.select(selector)
                if elements:
                    return elements[0].get_text(strip=True)
        
        # Fallback to first paragraph
        paragraphs = soup.find_all('p')
        if paragraphs:
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 50:  # Reasonable description length
                    return text
        
        return ""
    
    def _extract_founded_year(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract founding year"""
        text_content = soup.get_text()
        
        # Look for patterns like "Founded in 2020", "Since 1995", etc.
        year_patterns = [
            r'founded\s+in\s+(\d{4})',
            r'since\s+(\d{4})',
            r'established\s+in\s+(\d{4})',
            r'©\s*(\d{4})',
            r'copyright\s+(\d{4})'
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                try:
                    year = int(matches[0])
                    if 1900 <= year <= 2024:
                        return year
                except ValueError:
                    continue
        
        return None
    
    def _extract_industry(self, soup: BeautifulSoup) -> str:
        """Extract industry/sector information"""
        # Look for industry keywords
        industry_keywords = [
            'technology', 'software', 'healthcare', 'finance', 'education',
            'retail', 'manufacturing', 'consulting', 'marketing', 'design',
            'development', 'services', 'solutions', 'platform', 'cloud',
            'ai', 'machine learning', 'blockchain', 'fintech', 'saas'
        ]
        
        text_content = soup.get_text().lower()
        
        for keyword in industry_keywords:
            if keyword in text_content:
                return keyword.title()
        
        return ""
    
    def _extract_services(self, soup: BeautifulSoup) -> List[str]:
        """Extract services offered"""
        services = []
        
        # Look for service/product lists
        service_selectors = [
            'ul li', 'ol li', '.service', '.product', '.offering'
        ]
        
        for selector in service_selectors:
            elements = soup.select(selector)
            for element in elements[:5]:  # Limit to avoid noise
                text = element.get_text(strip=True)
                if 20 < len(text) < 100:  # Reasonable service description length
                    services.append(text)
        
        return services[:10]  # Return top 10 services
    
    def _extract_tech_stack(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract technology stack information"""
        tech_stack = {}
        text_content = soup.get_text().lower()
        
        for category, technologies in Config.TECH_PATTERNS.items():
            found_tech = []
            for tech in technologies:
                if tech.lower() in text_content:
                    found_tech.append(tech)
            
            if found_tech:
                tech_stack[category] = found_tech
        
        # Also check script tags for JavaScript frameworks
        scripts = soup.find_all('script')
        js_frameworks = []
        for script in scripts:
            if script.string:
                script_text = script.string.lower()
                for framework in ['react', 'angular', 'vue', 'jquery']:
                    if framework in script_text:
                        js_frameworks.append(framework)
        
        if js_frameworks:
            tech_stack['frontend_frameworks'] = js_frameworks
        
        return tech_stack
    
    def _extract_current_projects(self, soup: BeautifulSoup) -> List[str]:
        """Extract current projects or initiatives"""
        projects = []
        
        # Look for project/news/blog sections
        project_selectors = [
            '.project', '.case-study', '.portfolio', '.news', '.blog-post'
        ]
        
        for selector in project_selectors:
            elements = soup.select(selector)
            for element in elements[:3]:  # Limit to 3 projects
                title = element.find(['h1', 'h2', 'h3', 'h4'])
                if title:
                    projects.append(title.get_text(strip=True))
        
        return projects
    
    def _extract_competitors(self, soup: BeautifulSoup) -> List[str]:
        """Extract competitor information"""
        competitors = []
        text_content = soup.get_text().lower()
        
        # Look for competitor mentions
        competitor_patterns = [
            r'competitor[s]?[:\s]+([^.]+)',
            r'vs\.?\s+([A-Z][a-z]+)',
            r'alternative to\s+([A-Z][a-z]+)'
        ]
        
        for pattern in competitor_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                if isinstance(match, str) and len(match.strip()) > 0:
                    competitors.append(match.strip())
        
        return competitors[:5]  # Return top 5 competitors
    
    def _extract_market_position(self, soup: BeautifulSoup) -> str:
        """Extract market positioning information"""
        text_content = soup.get_text().lower()
        
        position_keywords = {
            'leader': ['leader', 'leading', 'market leader', 'industry leader'],
            'challenger': ['challenger', 'innovative', 'disruptive', 'game changer'],
            'niche': ['specialized', 'niche', 'boutique', 'focused'],
            'startup': ['startup', 'emerging', 'new', 'founded recently']
        }
        
        for position, keywords in position_keywords.items():
            for keyword in keywords:
                if keyword in text_content:
                    return position
        
        return ""
    
    def _extract_company_size(self, soup: BeautifulSoup) -> str:
        """Extract company size information"""
        text_content = soup.get_text().lower()
        
        size_patterns = [
            r'(\d+)\s*(?:to|[-–])\s*(\d+)\s*employees',
            r'(\d+)\+?\s*employees',
            r'team\s+of\s+(\d+)',
            r'(\d+)\s*people'
        ]
        
        for pattern in size_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                return f"{matches[0]} employees" if isinstance(matches[0], str) else f"{matches[0][0]}-{matches[0][1]} employees"
        
        return ""
    
    def _extract_funding_info(self, soup: BeautifulSoup) -> str:
        """Extract funding information"""
        text_content = soup.get_text().lower()
        
        funding_patterns = [
            r'raised\s+\$([0-9,]+\s*(?:million|m|billion|b|thousand|k))',
            r'funding\s+of\s+\$([0-9,]+\s*(?:million|m|billion|b|thousand|k))',
            r'series\s+[a-z]\s+\$([0-9,]+\s*(?:million|m|billion|b|thousand|k))'
        ]
        
        for pattern in funding_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                return f"${matches[0]}"
        
        return ""
    
    def _extract_news_mentions(self, soup: BeautifulSoup) -> List[str]:
        """Extract recent news mentions"""
        news_mentions = []
        
        # Look for news/press sections
        news_selectors = [
            '.news', '.press', '.media', '.article', '.blog'
        ]
        
        for selector in news_selectors:
            elements = soup.select(selector)
            for element in elements[:3]:  # Limit to 3 news items
                title = element.find(['h1', 'h2', 'h3', 'h4'])
                if title:
                    news_mentions.append(title.get_text(strip=True))
        
        return news_mentions
    
    def _find_contact_pages(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find contact/about page URLs"""
        contact_urls = []
        
        for selector in Config.SELECTORS['contact_page']:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in contact_urls:
                        contact_urls.append(full_url)
        
        return contact_urls
    
    def _extract_contact_page_info(self, url: str, data: Dict[str, Any]):
        """Extract additional info from contact/about pages"""
        try:
            soup = self._get_page_content(url)
            if not soup:
                return
            
            # Try to get additional emails and phones
            emails = self._extract_emails(soup)
            phones = self._extract_phones(soup)
            
            # Merge with existing data
            if emails:
                existing_emails = data.get('email', [])
                if isinstance(existing_emails, str):
                    existing_emails = [existing_emails]
                data['email'] = list(set(existing_emails + emails))
            
            if phones:
                existing_phones = data.get('phone', [])
                if isinstance(existing_phones, str):
                    existing_phones = [existing_phones]
                data['phone'] = list(set(existing_phones + phones))
            
            # Get address if not already found
            if not data.get('address'):
                address = self._extract_address(soup)
                if address:
                    data['address'] = address
            
            time.sleep(self.delay)
        except Exception as e:
            logger.error(f"Error extracting contact page info from {url}: {e}")
    
    def scrape_url(self, url: str, level: str = "basic") -> Dict[str, Any]:
        """Main scraping method"""
        if not validators.url(url):
            return {"error": f"Invalid URL: {url}"}
        
        try:
            if level == "basic":
                return self.extract_basic_data(url)
            elif level == "medium":
                return self.extract_medium_data(url)
            elif level == "advanced":
                return self.extract_advanced_data(url)
            else:
                return {"error": f"Invalid extraction level: {level}"}
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {"error": str(e)}
    
    def scrape_multiple_urls(self, urls: List[str], level: str = "basic") -> List[Dict[str, Any]]:
        """Scrape multiple URLs"""
        results = []
        
        for url in urls:
            logger.info(f"Scraping {url} ({len(results)+1}/{len(urls)})")
            result = self.scrape_url(url, level)
            results.append(result)
            
            # Add delay between requests
            time.sleep(self.delay)
        
        return results
    
    def close(self):
        """Close browser and clean up resources"""
        if self.driver:
            self.driver.quit()
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 