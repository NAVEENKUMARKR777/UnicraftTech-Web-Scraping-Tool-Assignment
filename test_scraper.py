#!/usr/bin/env python3
"""
Comprehensive tests for the Web Scraping Tool
"""

import unittest
import tempfile
import json
import os
from unittest.mock import Mock, patch, MagicMock
import sys
import logging

# Import our modules
from scraper import WebScraper
from search_discovery import SearchDiscovery
from data_output import DataOutput
from config import Config
from main import WebScrapingTool

# Disable logging during tests
logging.disable(logging.CRITICAL)

class TestWebScraper(unittest.TestCase):
    """Test cases for WebScraper class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = WebScraper(use_selenium=False)
        
    def tearDown(self):
        """Clean up after tests"""
        if self.scraper:
            self.scraper.close()
    
    def test_init_without_selenium(self):
        """Test scraper initialization without Selenium"""
        scraper = WebScraper(use_selenium=False)
        self.assertIsNone(scraper.driver)
        self.assertIsNotNone(scraper.session)
        scraper.close()
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs"""
        result = self.scraper.scrape_url("invalid-url")
        self.assertIn("error", result)
        self.assertIn("Invalid URL", result["error"])
    
    def test_basic_data_extraction_structure(self):
        """Test that basic data extraction returns correct structure"""
        # Mock the page content
        mock_soup = Mock()
        mock_soup.find.return_value = Mock()
        mock_soup.find.return_value.text = "Test Company"
        mock_soup.find_all.return_value = []
        mock_soup.select.return_value = []
        mock_soup.get_text.return_value = "Test content"
        
        with patch.object(self.scraper, '_get_page_content', return_value=mock_soup):
            result = self.scraper.extract_basic_data("https://example.com")
            
            # Check required fields
            required_fields = ["url", "company_name", "website_url", "email", "phone", "extraction_level"]
            for field in required_fields:
                self.assertIn(field, result)
            
            self.assertEqual(result["extraction_level"], "basic")
    
    def test_email_extraction(self):
        """Test email extraction functionality"""
        # Mock BeautifulSoup with email content
        mock_soup = Mock()
        mock_link = Mock()
        mock_link.get.return_value = "mailto:test@example.com"
        mock_link.__getitem__ = Mock(return_value="mailto:test@example.com")
        mock_soup.find_all.return_value = [mock_link]
        mock_soup.get_text.return_value = "Contact us at contact@example.com"
        
        emails = self.scraper._extract_emails(mock_soup)
        self.assertIsInstance(emails, list)
    
    def test_phone_extraction(self):
        """Test phone number extraction"""
        mock_soup = Mock()
        mock_link = Mock()
        mock_link.get.return_value = "tel:+1234567890"
        mock_link.__getitem__ = Mock(return_value="tel:+1234567890")
        mock_soup.find_all.return_value = [mock_link]
        mock_soup.get_text.return_value = "Call us at +1 (234) 567-8900"
        
        phones = self.scraper._extract_phones(mock_soup)
        self.assertIsInstance(phones, list)
    
    def test_company_name_extraction(self):
        """Test company name extraction"""
        mock_soup = Mock()
        mock_title = Mock()
        mock_title.text = "Test Company - Homepage"
        mock_soup.find.return_value = mock_title
        
        name = self.scraper._extract_company_name(mock_soup, "https://example.com")
        self.assertIsInstance(name, str)
        self.assertGreater(len(name), 0)

class TestSearchDiscovery(unittest.TestCase):
    """Test cases for SearchDiscovery class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.search_discovery = SearchDiscovery(use_selenium=False)
        
    def tearDown(self):
        """Clean up after tests"""
        if self.search_discovery:
            self.search_discovery.close()
    
    def test_init(self):
        """Test SearchDiscovery initialization"""
        self.assertIsNotNone(self.search_discovery.scraper)
        self.assertIsInstance(self.search_discovery.discovered_urls, set)
    
    def test_filter_company_urls(self):
        """Test URL filtering functionality"""
        test_urls = [
            "https://example.com",
            "https://facebook.com/company",
            "https://linkedin.com/company",
            "https://company.com/careers",
            "https://validcompany.com"
        ]
        
        filtered = self.search_discovery._filter_company_urls(test_urls)
        
        # Should filter out social media and career pages
        self.assertNotIn("https://facebook.com/company", filtered)
        self.assertNotIn("https://linkedin.com/company", filtered)
        self.assertNotIn("https://company.com/careers", filtered)
        
        # Should keep valid company URLs
        self.assertIn("https://example.com", filtered)
        self.assertIn("https://validcompany.com", filtered)
    
    @patch('requests.get')
    def test_search_companies_mock(self, mock_get):
        """Test company search with mocked response"""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'<html><body><div class="g"><a href="https://example.com">Test Company</a></div></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        urls = self.search_discovery.search_companies("test query", max_results=5)
        self.assertIsInstance(urls, list)

class TestDataOutput(unittest.TestCase):
    """Test cases for DataOutput class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.data_output = DataOutput(output_dir=self.temp_dir)
        
        # Sample test data
        self.sample_data = [
            {
                "company_name": "Test Company 1",
                "website_url": "https://test1.com",
                "email": ["test@test1.com"],
                "phone": ["+1234567890"],
                "extraction_level": "basic"
            },
            {
                "company_name": "Test Company 2",
                "website_url": "https://test2.com",
                "email": ["info@test2.com"],
                "phone": [],
                "extraction_level": "medium",
                "social_media": {"linkedin": "https://linkedin.com/company/test2"}
            }
        ]
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_json(self):
        """Test JSON output functionality"""
        filepath = self.data_output.save_data(
            data=self.sample_data,
            filename="test_json",
            format_type="json"
        )
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.json'))
        
        # Verify content
        with open(filepath, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(len(loaded_data), 2)
        self.assertEqual(loaded_data[0]["company_name"], "Test Company 1")
    
    def test_save_csv(self):
        """Test CSV output functionality"""
        filepath = self.data_output.save_data(
            data=self.sample_data,
            filename="test_csv",
            format_type="csv"
        )
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.csv'))
        
        # Verify content
        with open(filepath, 'r') as f:
            content = f.read()
        
        self.assertIn("company_name", content)
        self.assertIn("Test Company 1", content)
    
    def test_save_excel(self):
        """Test Excel output functionality"""
        filepath = self.data_output.save_data(
            data=self.sample_data,
            filename="test_excel",
            format_type="xlsx"
        )
        
        self.assertTrue(os.path.exists(filepath))
        self.assertTrue(filepath.endswith('.xlsx'))
    
    def test_get_output_stats(self):
        """Test statistics generation"""
        stats = self.data_output.get_output_stats(self.sample_data)
        
        self.assertEqual(stats["total_companies"], 2)
        self.assertIn("extraction_levels", stats)
        self.assertIn("data_completeness", stats)
        self.assertIn("contact_info_availability", stats)
    
    def test_flatten_record(self):
        """Test record flattening for CSV export"""
        test_record = {
            "name": "Test",
            "contact": {"email": "test@test.com", "phone": "123"},
            "tags": ["tag1", "tag2"]
        }
        
        flattened = self.data_output._flatten_record(test_record)
        
        self.assertIn("name", flattened)
        self.assertIn("contact_email", flattened)
        self.assertIn("contact_phone", flattened)
        self.assertIn("tags", flattened)

class TestConfig(unittest.TestCase):
    """Test cases for Config class"""
    
    def test_config_values(self):
        """Test configuration values"""
        self.assertIsInstance(Config.DEFAULT_DELAY, (int, float))
        self.assertIsInstance(Config.USER_AGENTS, list)
        self.assertGreater(len(Config.USER_AGENTS), 0)
        self.assertIsInstance(Config.SELECTORS, dict)
        self.assertIsInstance(Config.TECH_PATTERNS, dict)
    
    def test_get_headers(self):
        """Test header generation"""
        headers = Config.get_headers()
        self.assertIsInstance(headers, dict)
        self.assertIn('User-Agent', headers)
        self.assertIn('Accept', headers)
    
    def test_selenium_options(self):
        """Test Selenium options"""
        options = Config.get_selenium_options()
        self.assertIsNotNone(options)

class TestWebScrapingTool(unittest.TestCase):
    """Test cases for the main WebScrapingTool class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.tool = WebScrapingTool(use_selenium=False, output_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.tool:
            self.tool.close()
        
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test WebScrapingTool initialization"""
        self.assertIsNotNone(self.tool.scraper)
        self.assertIsNotNone(self.tool.search_discovery)
        self.assertIsNotNone(self.tool.data_output)
    
    def test_scrape_from_urls_invalid(self):
        """Test scraping with invalid URLs"""
        result = self.tool.scrape_from_urls(["invalid-url"])
        self.assertFalse(result.get('success', True))
    
    def test_scrape_from_urls_empty(self):
        """Test scraping with empty URL list"""
        result = self.tool.scrape_from_urls([])
        self.assertFalse(result.get('success', True))

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up after integration tests"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_mock(self):
        """Test complete end-to-end workflow with mocked data"""
        # This test would require extensive mocking
        # For now, just test that components can be initialized together
        with WebScrapingTool(use_selenium=False, output_dir=self.temp_dir) as tool:
            self.assertIsNotNone(tool.scraper)
            self.assertIsNotNone(tool.search_discovery)
            self.assertIsNotNone(tool.data_output)

def run_tests():
    """Run all tests"""
    print("🧪 Running Web Scraping Tool Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestWebScraper,
        TestSearchDiscovery,
        TestDataOutput,
        TestConfig,
        TestWebScrapingTool,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 