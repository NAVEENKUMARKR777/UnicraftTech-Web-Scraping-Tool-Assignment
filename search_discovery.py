import requests
import time
import random
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote_plus
from typing import List, Dict, Optional, Set
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import validators

from config import Config
from scraper import WebScraper

logger = logging.getLogger(__name__)

class SearchDiscovery:
    """Company discovery through search engines"""
    
    def __init__(self, use_selenium: bool = True):
        self.use_selenium = use_selenium
        self.scraper = WebScraper(use_selenium=use_selenium)
        self.discovered_urls = set()
        
    def search_companies(self, query: str, max_results: int = 20, search_engine: str = 'google') -> List[str]:
        """Search for companies based on query"""
        logger.info(f"Searching for companies with query: '{query}' using {search_engine}")
        
        if search_engine == 'google':
            return self._search_google(query, max_results)
        elif search_engine == 'bing':
            return self._search_bing(query, max_results)
        elif search_engine == 'duckduckgo':
            return self._search_duckduckgo(query, max_results)
        else:
            logger.error(f"Unsupported search engine: {search_engine}")
            return []
    
    def _search_google(self, query: str, max_results: int) -> List[str]:
        """Search Google for company URLs"""
        company_urls = []
        
        # Format query for better company results
        formatted_query = f"{query} company website"
        search_url = f"https://www.google.com/search?q={quote_plus(formatted_query)}&num={min(max_results, 100)}"
        
        try:
            if self.use_selenium and self.scraper.driver:
                soup = self._get_search_results_selenium(search_url)
            else:
                soup = self._get_search_results_requests(search_url)
            
            if not soup:
                logger.error("Failed to get search results")
                return []
            
            # Extract URLs from search results
            urls = self._extract_google_urls(soup)
            company_urls.extend(urls)
            
            # Try additional pages if needed
            if len(company_urls) < max_results:
                for page in range(2, 4):  # Pages 2-3
                    start = (page - 1) * 10
                    page_url = f"{search_url}&start={start}"
                    
                    soup = self._get_search_results_requests(page_url)
                    if soup:
                        urls = self._extract_google_urls(soup)
                        company_urls.extend(urls)
                        
                        if len(company_urls) >= max_results:
                            break
                    
                    time.sleep(random.uniform(2, 4))  # Random delay
            
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
        
        return self._filter_company_urls(company_urls[:max_results])
    
    def _search_bing(self, query: str, max_results: int) -> List[str]:
        """Search Bing for company URLs"""
        company_urls = []
        
        formatted_query = f"{query} company website"
        search_url = f"https://www.bing.com/search?q={quote_plus(formatted_query)}&count={min(max_results, 50)}"
        
        try:
            soup = self._get_search_results_requests(search_url)
            if soup:
                urls = self._extract_bing_urls(soup)
                company_urls.extend(urls)
            
        except Exception as e:
            logger.error(f"Error searching Bing: {e}")
        
        return self._filter_company_urls(company_urls[:max_results])
    
    def _search_duckduckgo(self, query: str, max_results: int) -> List[str]:
        """Search DuckDuckGo for company URLs"""
        company_urls = []
        
        formatted_query = f"{query} company website"
        search_url = f"https://duckduckgo.com/html?q={quote_plus(formatted_query)}"
        
        try:
            soup = self._get_search_results_requests(search_url)
            if soup:
                urls = self._extract_duckduckgo_urls(soup)
                company_urls.extend(urls)
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
        
        return self._filter_company_urls(company_urls[:max_results])
    
    def _get_search_results_selenium(self, url: str) -> Optional[BeautifulSoup]:
        """Get search results using Selenium"""
        try:
            self.scraper.driver.get(url)
            
            # Wait for results to load
            WebDriverWait(self.scraper.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.result"))
            )
            
            # Handle potential CAPTCHA or consent forms
            time.sleep(random.uniform(3, 5))
            
            return BeautifulSoup(self.scraper.driver.page_source, 'html.parser')
            
        except TimeoutException:
            logger.error(f"Timeout waiting for search results: {url}")
            return None
        except Exception as e:
            logger.error(f"Error getting search results with Selenium: {e}")
            return None
    
    def _get_search_results_requests(self, url: str) -> Optional[BeautifulSoup]:
        """Get search results using requests"""
        try:
            headers = {
                'User-Agent': random.choice(Config.USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
            
        except Exception as e:
            logger.error(f"Error getting search results with requests: {e}")
            return None
    
    def _extract_google_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs from Google search results"""
        urls = []
        
        # Google search result selectors
        selectors = [
            'div.g a[href]',
            'div.yuRUbf a[href]',
            'h3 a[href]',
            'a[href^="http"]:not([href*="google.com"])'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and href.startswith('http'):
                    # Clean Google redirect URLs
                    if '/url?q=' in href:
                        try:
                            actual_url = href.split('/url?q=')[1].split('&')[0]
                            urls.append(actual_url)
                        except:
                            continue
                    else:
                        urls.append(href)
        
        return urls
    
    def _extract_bing_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs from Bing search results"""
        urls = []
        
        # Bing search result selectors
        selectors = [
            'li.b_algo a[href]',
            'h2 a[href]',
            'a[href^="http"]:not([href*="bing.com"])'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and href.startswith('http'):
                    urls.append(href)
        
        return urls
    
    def _extract_duckduckgo_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract URLs from DuckDuckGo search results"""
        urls = []
        
        # DuckDuckGo search result selectors
        selectors = [
            'a.result__a[href]',
            'h2 a[href]',
            'a[href^="http"]:not([href*="duckduckgo.com"])'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and href.startswith('http'):
                    urls.append(href)
        
        return urls
    
    def _filter_company_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to keep only company websites"""
        filtered_urls = []
        
        # URLs to exclude
        exclude_patterns = [
            r'facebook\.com',
            r'twitter\.com',
            r'linkedin\.com',
            r'instagram\.com',
            r'youtube\.com',
            r'google\.com',
            r'bing\.com',
            r'yahoo\.com',
            r'wikipedia\.org',
            r'reddit\.com',
            r'pinterest\.com',
            r'amazon\.com',
            r'ebay\.com',
            r'crunchbase\.com',
            r'glassdoor\.com',
            r'indeed\.com',
            r'job.*\.com',
            r'career.*\.com',
            r'news\.',
            r'blog\.',
            r'forum\.',
            r'\.pdf$',
            r'\.doc$',
            r'\.docx$'
        ]
        
        exclude_regex = re.compile('|'.join(exclude_patterns), re.IGNORECASE)
        
        for url in urls:
            try:
                # Validate URL
                if not validators.url(url):
                    continue
                
                # Check if URL should be excluded
                if exclude_regex.search(url):
                    continue
                
                # Check if already discovered
                if url in self.discovered_urls:
                    continue
                
                # Check domain structure (should look like a company website)
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Skip if domain looks like a subdomain of a platform
                if any(platform in domain for platform in ['blogspot', 'wordpress', 'medium', 'substack']):
                    continue
                
                # Skip if path suggests it's not a main company site
                if any(path in parsed.path.lower() for path in ['/jobs', '/careers', '/news', '/blog', '/forum']):
                    continue
                
                filtered_urls.append(url)
                self.discovered_urls.add(url)
                
            except Exception as e:
                logger.debug(f"Error filtering URL {url}: {e}")
                continue
        
        return filtered_urls
    
    def discover_from_seed_urls(self, seed_urls: List[str], max_depth: int = 2) -> List[str]:
        """Discover additional company URLs from seed URLs"""
        discovered_urls = set(seed_urls)
        
        for depth in range(max_depth):
            current_urls = list(discovered_urls)
            
            for url in current_urls:
                try:
                    # Get page content
                    soup = self.scraper._get_page_content(url)
                    if not soup:
                        continue
                    
                    # Find related company links
                    related_urls = self._extract_related_company_urls(soup, url)
                    
                    for related_url in related_urls:
                        if related_url not in discovered_urls:
                            discovered_urls.add(related_url)
                    
                    time.sleep(random.uniform(1, 3))  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error discovering from {url}: {e}")
                    continue
        
        return list(discovered_urls)
    
    def _extract_related_company_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract URLs of related companies from a page"""
        related_urls = []
        
        # Look for partner, client, or competitor links
        link_patterns = [
            r'partner',
            r'client',
            r'customer',
            r'competitor',
            r'similar',
            r'related',
            r'alternative'
        ]
        
        pattern_regex = re.compile('|'.join(link_patterns), re.IGNORECASE)
        
        # Find sections that might contain related companies
        relevant_sections = soup.find_all(['div', 'section'], string=pattern_regex)
        
        for section in relevant_sections:
            links = section.find_all('a', href=True)
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if validators.url(full_url):
                        related_urls.append(full_url)
        
        # Also look for any external links that might be companies
        external_links = soup.find_all('a', href=re.compile(r'^https?://'))
        for link in external_links[:20]:  # Limit to avoid noise
            href = link.get('href')
            if href and href != base_url:
                parsed_base = urlparse(base_url)
                parsed_href = urlparse(href)
                
                # Skip if same domain
                if parsed_base.netloc == parsed_href.netloc:
                    continue
                
                related_urls.append(href)
        
        return self._filter_company_urls(related_urls)
    
    def search_and_discover(self, query: str, max_results: int = 20, 
                           search_engines: List[str] = None, 
                           use_seed_discovery: bool = True) -> List[str]:
        """Combined search and discovery method"""
        if search_engines is None:
            search_engines = ['google', 'bing']
        
        all_urls = []
        
        # Search each engine
        for engine in search_engines:
            urls = self.search_companies(query, max_results // len(search_engines), engine)
            all_urls.extend(urls)
            time.sleep(random.uniform(2, 4))  # Rate limiting between engines
        
        # Remove duplicates
        unique_urls = list(dict.fromkeys(all_urls))
        
        # Optionally discover more URLs from seed URLs
        if use_seed_discovery and len(unique_urls) > 0:
            seed_urls = unique_urls[:5]  # Use first 5 as seeds
            additional_urls = self.discover_from_seed_urls(seed_urls, max_depth=1)
            unique_urls.extend(additional_urls)
        
        # Final filtering and limiting
        filtered_urls = self._filter_company_urls(unique_urls)
        
        logger.info(f"Discovered {len(filtered_urls)} company URLs for query: '{query}'")
        return filtered_urls[:max_results]
    
    def close(self):
        """Close scraper resources"""
        if self.scraper:
            self.scraper.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 