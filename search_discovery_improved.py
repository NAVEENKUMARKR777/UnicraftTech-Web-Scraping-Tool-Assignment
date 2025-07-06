#!/usr/bin/env python3
"""
Improved Search Discovery Module
Enhanced company discovery with multiple fallback strategies
"""

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
import json

from config import Config

logger = logging.getLogger(__name__)

class ImprovedSearchDiscovery:
    """Enhanced company discovery with multiple strategies"""
    
    def __init__(self, use_selenium: bool = True):
        self.use_selenium = use_selenium
        self.discovered_urls = set()
        self.session = requests.Session()
        self._setup_session()
        
        # Sample company URLs for different industries (fallback)
        self.sample_companies = {
            "cloud computing": [
                "https://aws.amazon.com",
                "https://cloud.google.com",
                "https://azure.microsoft.com",
                "https://www.digitalocean.com",
                "https://www.linode.com",
                "https://vultr.com",
                "https://www.scaleway.com",
                "https://www.hetzner.com"
            ],
            "ai": [
                "https://openai.com",
                "https://www.anthropic.com",
                "https://stability.ai",
                "https://www.midjourney.com",
                "https://huggingface.co",
                "https://replicate.com",
                "https://www.perplexity.ai",
                "https://claude.ai"
            ],
            "fintech": [
                "https://stripe.com",
                "https://square.com",
                "https://www.paypal.com",
                "https://www.coinbase.com",
                "https://plaid.com",
                "https://www.affirm.com",
                "https://www.klarna.com",
                "https://www.robinhood.com"
            ],
            "saas": [
                "https://slack.com",
                "https://zoom.us",
                "https://www.salesforce.com",
                "https://www.hubspot.com",
                "https://www.zendesk.com",
                "https://www.atlassian.com",
                "https://monday.com",
                "https://www.notion.so"
            ]
        }
        
    def _setup_session(self):
        """Setup requests session with proper headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def search_companies(self, query: str, max_results: int = 20) -> List[str]:
        """Multi-strategy company search"""
        logger.info(f"Searching for companies with query: '{query}'")
        
        all_urls = []
        
        # Strategy 1: Try sample companies first (for demo purposes)
        sample_urls = self._get_sample_companies(query)
        if sample_urls:
            all_urls.extend(sample_urls)
            logger.info(f"Found {len(sample_urls)} sample companies")
        
        # Strategy 2: Search engines with improved approach
        search_urls = self._search_engines(query, max_results)
        all_urls.extend(search_urls)
        
        # Strategy 3: Company directories
        directory_urls = self._search_directories(query, max_results)
        all_urls.extend(directory_urls)
        
        # Strategy 4: GitHub organizations (for tech companies)
        if any(tech_word in query.lower() for tech_word in ['tech', 'software', 'app', 'platform', 'cloud', 'ai']):
            github_urls = self._search_github_orgs(query)
            all_urls.extend(github_urls)
        
        # Remove duplicates and filter
        unique_urls = list(dict.fromkeys(all_urls))
        filtered_urls = self._filter_company_urls(unique_urls)
        
        result = filtered_urls[:max_results]
        logger.info(f"Discovered {len(result)} company URLs for query: '{query}'")
        
        return result
    
    def _get_sample_companies(self, query: str) -> List[str]:
        """Get sample companies based on query keywords"""
        sample_urls = []
        query_lower = query.lower()
        
        for category, urls in self.sample_companies.items():
            if any(keyword in query_lower for keyword in category.split()):
                sample_urls.extend(urls[:4])  # Take first 4 from each matching category
        
        # If no specific category matches, take some from each
        if not sample_urls:
            for category, urls in self.sample_companies.items():
                sample_urls.extend(urls[:2])  # Take 2 from each category
        
        return sample_urls
    
    def _search_engines(self, query: str, max_results: int) -> List[str]:
        """Search multiple engines with improved techniques"""
        urls = []
        
        # Try different search approaches
        search_variants = [
            f"{query} company website",
            f"{query} startup",
            f"{query} business",
            f'"{query}" company',
            f"{query} site:com"
        ]
        
        for search_query in search_variants[:2]:  # Limit to avoid rate limiting
            try:
                # Try DuckDuckGo first (less blocking)
                ddg_urls = self._search_duckduckgo_improved(search_query, max_results // 4)
                urls.extend(ddg_urls)
                
                time.sleep(random.uniform(2, 4))
                
                # Try Bing
                bing_urls = self._search_bing_improved(search_query, max_results // 4)
                urls.extend(bing_urls)
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.warning(f"Search engine error: {e}")
                continue
        
        return urls
    
    def _search_duckduckgo_improved(self, query: str, max_results: int) -> List[str]:
        """Improved DuckDuckGo search"""
        urls = []
        
        try:
            # DuckDuckGo instant answers API
            search_url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&t=webscraper"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Extract URLs from results
                for result in data.get('Results', []):
                    first_url = result.get('FirstURL')
                    if first_url:
                        urls.append(first_url)
                
                # Also check related topics
                for topic in data.get('RelatedTopics', []):
                    if isinstance(topic, dict):
                        first_url = topic.get('FirstURL')
                        if first_url:
                            urls.append(first_url)
            
            # Fallback to HTML search
            if len(urls) < max_results:
                html_urls = self._search_duckduckgo_html(query, max_results)
                urls.extend(html_urls)
                
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
        
        return urls[:max_results]
    
    def _search_duckduckgo_html(self, query: str, max_results: int) -> List[str]:
        """DuckDuckGo HTML search fallback"""
        urls = []
        
        try:
            search_url = f"https://duckduckgo.com/html?q={quote_plus(query)}"
            
            response = self.session.get(search_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract URLs from search results
                for link in soup.find_all('a', {'class': 'result__a'}):
                    href = link.get('href')
                    if href and href.startswith('http'):
                        urls.append(href)
                
                # Also try general result links
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.startswith('http') and 'duckduckgo.com' not in href:
                        urls.append(href)
                        
        except Exception as e:
            logger.warning(f"DuckDuckGo HTML search error: {e}")
        
        return urls[:max_results]
    
    def _search_bing_improved(self, query: str, max_results: int) -> List[str]:
        """Improved Bing search"""
        urls = []
        
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}&count={min(max_results, 50)}"
            
            # Use different user agent for Bing
            headers = self.session.headers.copy()
            headers['User-Agent'] = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Bing result selectors
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and href.startswith('http') and 'bing.com' not in href:
                        urls.append(href)
                        
        except Exception as e:
            logger.warning(f"Bing search error: {e}")
        
        return urls[:max_results]
    
    def _search_directories(self, query: str, max_results: int) -> List[str]:
        """Search company directories and databases"""
        urls = []
        
        # Company directory sources
        directories = [
            {
                'name': 'Product Hunt',
                'search': lambda q: self._search_producthunt(q),
            },
            {
                'name': 'AngelList',
                'search': lambda q: self._search_angellist(q),
            },
            {
                'name': 'Built In',
                'search': lambda q: self._search_builtin(q),
            }
        ]
        
        for directory in directories:
            try:
                dir_urls = directory['search'](query)
                urls.extend(dir_urls)
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.warning(f"Error searching {directory['name']}: {e}")
                continue
        
        return urls[:max_results]
    
    def _search_producthunt(self, query: str) -> List[str]:
        """Search Product Hunt for companies"""
        urls = []
        
        try:
            search_url = f"https://www.producthunt.com/search?q={quote_plus(query)}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for product links that might lead to company websites
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and '/posts/' in href:
                        # This would need to be crawled further to get actual company URLs
                        # For now, we'll skip this complex extraction
                        pass
                        
        except Exception as e:
            logger.debug(f"Product Hunt search error: {e}")
        
        return urls
    
    def _search_angellist(self, query: str) -> List[str]:
        """Search AngelList for startups"""
        urls = []
        
        try:
            # AngelList search is complex and requires authentication
            # For demo purposes, we'll return empty
            pass
                        
        except Exception as e:
            logger.debug(f"AngelList search error: {e}")
        
        return urls
    
    def _search_builtin(self, query: str) -> List[str]:
        """Search Built In for tech companies"""
        urls = []
        
        try:
            search_url = f"https://builtin.com/companies?search={quote_plus(query)}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract company profile links
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and '/company/' in href:
                        # This would lead to company profiles, not direct websites
                        # Would need additional crawling
                        pass
                        
        except Exception as e:
            logger.debug(f"Built In search error: {e}")
        
        return urls
    
    def _search_github_orgs(self, query: str) -> List[str]:
        """Search GitHub organizations for tech companies"""
        urls = []
        
        try:
            # GitHub search API
            search_url = f"https://api.github.com/search/users?q={quote_plus(query)}+type:org&sort=repositories&order=desc"
            
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for org in data.get('items', [])[:10]:  # Top 10 organizations
                    org_url = org.get('html_url')
                    if org_url:
                        # Try to find the organization's website
                        org_response = self.session.get(f"https://api.github.com/orgs/{org['login']}", timeout=5)
                        if org_response.status_code == 200:
                            org_data = org_response.json()
                            blog_url = org_data.get('blog')
                            if blog_url and validators.url(blog_url):
                                urls.append(blog_url)
                    
                    time.sleep(0.5)  # Rate limiting for GitHub API
                        
        except Exception as e:
            logger.debug(f"GitHub search error: {e}")
        
        return urls
    
    def _filter_company_urls(self, urls: List[str]) -> List[str]:
        """Filter URLs to keep only likely company websites"""
        filtered_urls = []
        
        # URLs to exclude (less restrictive than before)
        exclude_patterns = [
            r'facebook\.com',
            r'twitter\.com',
            r'instagram\.com',
            r'youtube\.com',
            r'google\.com',
            r'bing\.com',
            r'yahoo\.com',
            r'wikipedia\.org',
            r'reddit\.com',
            r'pinterest\.com',
            r'amazon\.com/(?!s3)', # Allow S3 but not main Amazon
            r'ebay\.com',
            r'news\.',
            r'\.pdf$',
            r'\.doc$',
            r'\.docx$'
        ]
        
        exclude_regex = re.compile('|'.join(exclude_patterns), re.IGNORECASE)
        
        for url in urls:
            try:
                # Basic URL validation
                if not url or not isinstance(url, str):
                    continue
                    
                # Fix URL if needed
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Validate URL
                if not validators.url(url):
                    continue
                
                # Check if URL should be excluded
                if exclude_regex.search(url):
                    continue
                
                # Check if already discovered
                if url in self.discovered_urls:
                    continue
                
                # Check domain structure
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Skip obviously non-company domains
                if any(platform in domain for platform in ['blogspot', 'wordpress.com', 'medium.com']):
                    continue
                
                # Must have a reasonable domain
                if len(domain.split('.')) < 2:
                    continue
                
                filtered_urls.append(url)
                self.discovered_urls.add(url)
                
            except Exception as e:
                logger.debug(f"Error filtering URL {url}: {e}")
                continue
        
        return filtered_urls
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'session'):
            self.session.close()

# Example usage and testing
if __name__ == "__main__":
    print("🔍 Testing Improved Search Discovery...")
    
    discovery = ImprovedSearchDiscovery(use_selenium=False)
    
    # Test queries
    test_queries = [
        "cloud computing startups",
        "AI companies",
        "fintech startups",
        "SaaS companies"
    ]
    
    for query in test_queries:
        print(f"\n🔎 Searching for: {query}")
        urls = discovery.search_companies(query, max_results=10)
        print(f"Found {len(urls)} companies:")
        for i, url in enumerate(urls, 1):
            print(f"  {i}. {url}")
    
    discovery.close()
    print("✅ Search discovery test completed") 