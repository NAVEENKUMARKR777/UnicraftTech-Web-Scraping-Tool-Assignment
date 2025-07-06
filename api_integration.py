#!/usr/bin/env python3
"""
API Integration Module for External Data Enrichment
Supports LinkedIn, Clearbit, and other external APIs
"""

import requests
import json
import logging
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class APIIntegration:
    """Handle external API integrations for data enrichment"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Web Scraping Tool/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # API credentials from environment variables
        self.clearbit_key = os.getenv('CLEARBIT_API_KEY')
        self.linkedin_key = os.getenv('LINKEDIN_API_KEY')
        self.hunter_key = os.getenv('HUNTER_API_KEY')
        self.crunchbase_key = os.getenv('CRUNCHBASE_API_KEY')
        
        # Rate limiting
        self.last_request_time = {}
        self.rate_limits = {
            'clearbit': 600,  # 10 requests per minute
            'linkedin': 500,  # 500 requests per hour
            'hunter': 100,    # 100 requests per month (free tier)
            'crunchbase': 200 # 200 requests per hour
        }
    
    def _rate_limit(self, service: str, requests_per_hour: int):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        service_key = f"{service}_rate_limit"
        
        if service_key in self.last_request_time:
            time_diff = current_time - self.last_request_time[service_key]
            min_interval = 3600 / requests_per_hour  # seconds between requests
            
            if time_diff < min_interval:
                sleep_time = min_interval - time_diff
                logger.info(f"Rate limiting {service}: sleeping {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time[service_key] = current_time
    
    def enrich_company_data(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich company data using multiple APIs"""
        enriched_data = company_data.copy()
        
        # Extract domain from website URL
        website_url = company_data.get('website_url', '')
        if not website_url:
            logger.warning("No website URL provided for enrichment")
            return enriched_data
        
        domain = self._extract_domain(website_url)
        company_name = company_data.get('company_name', '')
        
        # Enrich with Clearbit
        if self.clearbit_key:
            clearbit_data = self._enrich_with_clearbit(domain, company_name)
            if clearbit_data:
                enriched_data['clearbit_data'] = clearbit_data
                enriched_data.update(self._merge_clearbit_data(clearbit_data))
        
        # Enrich with Hunter.io for email information
        if self.hunter_key:
            hunter_data = self._enrich_with_hunter(domain)
            if hunter_data:
                enriched_data['hunter_data'] = hunter_data
                enriched_data.update(self._merge_hunter_data(hunter_data))
        
        # Enrich with Crunchbase
        if self.crunchbase_key:
            crunchbase_data = self._enrich_with_crunchbase(company_name, domain)
            if crunchbase_data:
                enriched_data['crunchbase_data'] = crunchbase_data
                enriched_data.update(self._merge_crunchbase_data(crunchbase_data))
        
        # LinkedIn enrichment (using public data)
        linkedin_data = self._enrich_with_linkedin_public(company_name, domain)
        if linkedin_data:
            enriched_data['linkedin_data'] = linkedin_data
            enriched_data.update(self._merge_linkedin_data(linkedin_data))
        
        return enriched_data
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower().replace('www.', '')
        except:
            return url
    
    def _enrich_with_clearbit(self, domain: str, company_name: str) -> Optional[Dict[str, Any]]:
        """Enrich data using Clearbit API"""
        try:
            self._rate_limit('clearbit', self.rate_limits['clearbit'])
            
            # Clearbit Enrichment API
            url = f"https://company.clearbit.com/v2/companies/find"
            params = {'domain': domain}
            
            response = self.session.get(
                url,
                params=params,
                auth=(self.clearbit_key, ''),
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully enriched {domain} with Clearbit")
                return data
            elif response.status_code == 404:
                logger.info(f"No Clearbit data found for {domain}")
                return None
            else:
                logger.warning(f"Clearbit API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error enriching with Clearbit: {e}")
            return None
    
    def _enrich_with_hunter(self, domain: str) -> Optional[Dict[str, Any]]:
        """Enrich data using Hunter.io API"""
        try:
            self._rate_limit('hunter', self.rate_limits['hunter'])
            
            # Hunter.io Domain Search API
            url = "https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'api_key': self.hunter_key,
                'limit': 10
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully enriched {domain} with Hunter.io")
                return data
            else:
                logger.warning(f"Hunter.io API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error enriching with Hunter.io: {e}")
            return None
    
    def _enrich_with_crunchbase(self, company_name: str, domain: str) -> Optional[Dict[str, Any]]:
        """Enrich data using Crunchbase API"""
        try:
            self._rate_limit('crunchbase', self.rate_limits['crunchbase'])
            
            # Crunchbase Search API
            url = "https://api.crunchbase.com/v4/searches/organizations"
            headers = {
                'X-cb-user-key': self.crunchbase_key,
                'Content-Type': 'application/json'
            }
            
            # Search by company name and domain
            payload = {
                'field_ids': [
                    'name', 'short_description', 'categories', 'founded_on',
                    'num_employees_enum', 'funding_total', 'website_url',
                    'headquarters_regions', 'investor_identifiers'
                ],
                'query': company_name,
                'limit': 5
            }
            
            response = self.session.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully enriched {company_name} with Crunchbase")
                return data
            else:
                logger.warning(f"Crunchbase API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error enriching with Crunchbase: {e}")
            return None
    
    def _enrich_with_linkedin_public(self, company_name: str, domain: str) -> Optional[Dict[str, Any]]:
        """Enrich data using LinkedIn public data (web scraping)"""
        try:
            # Search for LinkedIn company page
            search_query = f"{company_name} site:linkedin.com/company"
            
            # Use Google Search to find LinkedIn company page
            from search_discovery import SearchDiscovery
            
            discovery = SearchDiscovery(use_selenium=False)
            urls = discovery.search_companies(search_query, max_results=3, search_engine='google')
            
            linkedin_urls = [url for url in urls if 'linkedin.com/company' in url]
            
            if linkedin_urls:
                # Scrape LinkedIn company page
                from scraper import WebScraper
                
                scraper = WebScraper(use_selenium=True)
                linkedin_data = {}
                
                for url in linkedin_urls[:1]:  # Just first result
                    try:
                        soup = scraper._get_page_content(url, use_selenium=True)
                        if soup:
                            # Extract LinkedIn-specific data
                            linkedin_data = self._extract_linkedin_data(soup, url)
                            break
                    except Exception as e:
                        logger.warning(f"Error scraping LinkedIn page {url}: {e}")
                
                scraper.close()
                discovery.close()
                
                if linkedin_data:
                    logger.info(f"Successfully enriched {company_name} with LinkedIn data")
                    return linkedin_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error enriching with LinkedIn: {e}")
            return None
    
    def _extract_linkedin_data(self, soup, url: str) -> Dict[str, Any]:
        """Extract data from LinkedIn company page"""
        data = {'linkedin_url': url}
        
        try:
            # Company name
            name_selectors = ['h1', '.org-top-card-summary__title', '.company-name']
            for selector in name_selectors:
                element = soup.select_one(selector)
                if element:
                    data['linkedin_company_name'] = element.get_text(strip=True)
                    break
            
            # Description
            desc_selectors = ['.org-top-card-summary__description', '.company-description']
            for selector in desc_selectors:
                element = soup.select_one(selector)
                if element:
                    data['linkedin_description'] = element.get_text(strip=True)
                    break
            
            # Employee count
            employee_selectors = ['.org-top-card-summary__follower-count', '.company-employees']
            for selector in employee_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    data['linkedin_employees'] = text
                    break
            
            # Industry
            industry_selectors = ['.org-top-card-summary__industry', '.company-industry']
            for selector in industry_selectors:
                element = soup.select_one(selector)
                if element:
                    data['linkedin_industry'] = element.get_text(strip=True)
                    break
            
            # Location
            location_selectors = ['.org-top-card-summary__headquarter', '.company-location']
            for selector in location_selectors:
                element = soup.select_one(selector)
                if element:
                    data['linkedin_location'] = element.get_text(strip=True)
                    break
            
        except Exception as e:
            logger.warning(f"Error extracting LinkedIn data: {e}")
        
        return data
    
    def _merge_clearbit_data(self, clearbit_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge Clearbit data into company record"""
        merged = {}
        
        try:
            if 'name' in clearbit_data:
                merged['api_company_name'] = clearbit_data['name']
            
            if 'description' in clearbit_data:
                merged['api_description'] = clearbit_data['description']
            
            if 'foundedYear' in clearbit_data:
                merged['api_founded_year'] = clearbit_data['foundedYear']
            
            if 'employees' in clearbit_data:
                merged['api_employee_count'] = clearbit_data['employees']
            
            if 'employeesRange' in clearbit_data:
                merged['api_employee_range'] = clearbit_data['employeesRange']
            
            if 'category' in clearbit_data:
                merged['api_industry'] = clearbit_data['category']['industry']
                merged['api_sector'] = clearbit_data['category']['sector']
            
            if 'location' in clearbit_data:
                merged['api_location'] = clearbit_data['location']
            
            if 'tech' in clearbit_data:
                merged['api_tech_stack'] = clearbit_data['tech']
            
            if 'metrics' in clearbit_data:
                merged['api_metrics'] = clearbit_data['metrics']
            
            if 'funding' in clearbit_data:
                merged['api_funding'] = clearbit_data['funding']
            
        except Exception as e:
            logger.warning(f"Error merging Clearbit data: {e}")
        
        return merged
    
    def _merge_hunter_data(self, hunter_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge Hunter.io data into company record"""
        merged = {}
        
        try:
            if 'data' in hunter_data:
                data = hunter_data['data']
                
                if 'organization' in data:
                    merged['api_organization'] = data['organization']
                
                if 'emails' in data:
                    emails = [email['value'] for email in data['emails'] if 'value' in email]
                    if emails:
                        merged['api_emails'] = emails
                
                if 'pattern' in data:
                    merged['api_email_pattern'] = data['pattern']
                
                if 'country' in data:
                    merged['api_country'] = data['country']
                
        except Exception as e:
            logger.warning(f"Error merging Hunter.io data: {e}")
        
        return merged
    
    def _merge_crunchbase_data(self, crunchbase_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge Crunchbase data into company record"""
        merged = {}
        
        try:
            if 'entities' in crunchbase_data and crunchbase_data['entities']:
                entity = crunchbase_data['entities'][0]  # First result
                properties = entity.get('properties', {})
                
                if 'name' in properties:
                    merged['api_crunchbase_name'] = properties['name']
                
                if 'short_description' in properties:
                    merged['api_crunchbase_description'] = properties['short_description']
                
                if 'founded_on' in properties:
                    merged['api_crunchbase_founded'] = properties['founded_on']
                
                if 'num_employees_enum' in properties:
                    merged['api_crunchbase_employees'] = properties['num_employees_enum']
                
                if 'funding_total' in properties:
                    merged['api_crunchbase_funding'] = properties['funding_total']
                
                if 'categories' in properties:
                    merged['api_crunchbase_categories'] = properties['categories']
                
                if 'headquarters_regions' in properties:
                    merged['api_crunchbase_location'] = properties['headquarters_regions']
                
        except Exception as e:
            logger.warning(f"Error merging Crunchbase data: {e}")
        
        return merged
    
    def _merge_linkedin_data(self, linkedin_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge LinkedIn data into company record"""
        merged = {}
        
        try:
            for key, value in linkedin_data.items():
                if key.startswith('linkedin_'):
                    merged[f'api_{key}'] = value
                
        except Exception as e:
            logger.warning(f"Error merging LinkedIn data: {e}")
        
        return merged
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get status of all API integrations"""
        status = {
            'clearbit': {
                'available': bool(self.clearbit_key),
                'key_configured': bool(self.clearbit_key)
            },
            'hunter': {
                'available': bool(self.hunter_key),
                'key_configured': bool(self.hunter_key)
            },
            'crunchbase': {
                'available': bool(self.crunchbase_key),
                'key_configured': bool(self.crunchbase_key)
            },
            'linkedin': {
                'available': True,  # Uses web scraping
                'key_configured': True
            }
        }
        
        return status
    
    def test_api_connections(self) -> Dict[str, Any]:
        """Test API connections"""
        results = {}
        
        # Test Clearbit
        if self.clearbit_key:
            try:
                test_data = self._enrich_with_clearbit('google.com', 'Google')
                results['clearbit'] = {
                    'status': 'success' if test_data else 'no_data',
                    'message': 'API connection successful' if test_data else 'No data returned'
                }
            except Exception as e:
                results['clearbit'] = {
                    'status': 'error',
                    'message': str(e)
                }
        else:
            results['clearbit'] = {
                'status': 'not_configured',
                'message': 'API key not configured'
            }
        
        # Test Hunter
        if self.hunter_key:
            try:
                test_data = self._enrich_with_hunter('google.com')
                results['hunter'] = {
                    'status': 'success' if test_data else 'no_data',
                    'message': 'API connection successful' if test_data else 'No data returned'
                }
            except Exception as e:
                results['hunter'] = {
                    'status': 'error',
                    'message': str(e)
                }
        else:
            results['hunter'] = {
                'status': 'not_configured',
                'message': 'API key not configured'
            }
        
        # Test Crunchbase
        if self.crunchbase_key:
            try:
                test_data = self._enrich_with_crunchbase('Google', 'google.com')
                results['crunchbase'] = {
                    'status': 'success' if test_data else 'no_data',
                    'message': 'API connection successful' if test_data else 'No data returned'
                }
            except Exception as e:
                results['crunchbase'] = {
                    'status': 'error',
                    'message': str(e)
                }
        else:
            results['crunchbase'] = {
                'status': 'not_configured',
                'message': 'API key not configured'
            }
        
        # Test LinkedIn (always available)
        results['linkedin'] = {
            'status': 'available',
            'message': 'Web scraping based - always available'
        }
        
        return results

# Example usage and testing
if __name__ == "__main__":
    # Create API integration instance
    api = APIIntegration()
    
    # Test API status
    print("API Status:")
    status = api.get_api_status()
    for service, info in status.items():
        print(f"  {service}: {'✅' if info['available'] else '❌'} Available")
    
    # Test with sample company data
    sample_data = {
        'company_name': 'Example Corp',
        'website_url': 'https://example.com',
        'email': ['contact@example.com'],
        'phone': ['+1-555-123-4567']
    }
    
    print("\nEnriching sample company data...")
    enriched = api.enrich_company_data(sample_data)
    
    print(f"Original fields: {len(sample_data)}")
    print(f"Enriched fields: {len(enriched)}")
    print("New fields added:")
    for key in enriched:
        if key not in sample_data:
            print(f"  - {key}") 