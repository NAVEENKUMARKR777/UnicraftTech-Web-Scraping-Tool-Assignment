#!/usr/bin/env python3
"""
Demo script showing how to use the Web Scraping Tool
"""

import sys
import os
import json
from main import WebScrapingTool

def run_demo():
    """Run a comprehensive demo of the web scraping tool"""
    
    print("🎬 Web Scraping Tool Demo")
    print("=" * 50)
    
    # Initialize the tool
    print("🚀 Initializing Web Scraping Tool...")
    tool = WebScrapingTool(use_selenium=False, output_dir="demo_output")
    
    try:
        # Demo 1: Search and scrape companies
        print("\n📍 Demo 1: Search-based Company Discovery")
        print("-" * 40)
        
        query = "cloud computing startups in California"
        print(f"🔍 Searching for: '{query}'")
        
        # Search for companies (limited to 3 for demo)
        urls = tool.search_discovery.search_and_discover(
            query=query,
            max_results=3,
            search_engines=['google']
        )
        
        if urls:
            print(f"✅ Found {len(urls)} companies:")
            for i, url in enumerate(urls, 1):
                print(f"   {i}. {url}")
            
            # Scrape the first 2 companies
            print(f"\n📊 Scraping first 2 companies with basic extraction...")
            result = tool.scrape_from_urls(
                urls=urls[:2],
                extraction_level="basic",
                output_format="json",
                output_filename="demo_search_results"
            )
            
            if result.get('success'):
                print(f"✅ Search demo completed successfully!")
                print(f"   📄 Results saved to: {result['saved_file']}")
                print(f"   📊 Companies scraped: {len(result['results'])}")
            else:
                print("❌ Search demo failed")
        else:
            print("❌ No companies found for search demo")
        
        # Demo 2: Scrape specific URLs
        print("\n📍 Demo 2: Direct URL Scraping")
        print("-" * 40)
        
        # Use sample URLs from file
        sample_urls = [
            "https://example.com",
            "https://github.com",
            "https://python.org"
        ]
        
        print(f"🎯 Scraping {len(sample_urls)} specific URLs:")
        for i, url in enumerate(sample_urls, 1):
            print(f"   {i}. {url}")
        
        print(f"\n📊 Scraping with medium extraction level...")
        result = tool.scrape_from_urls(
            urls=sample_urls,
            extraction_level="medium",
            output_format="json",
            output_filename="demo_url_results"
        )
        
        if result.get('success'):
            print(f"✅ URL demo completed successfully!")
            print(f"   📄 Results saved to: {result['saved_file']}")
            print(f"   📊 Companies scraped: {len(result['results'])}")
            
            # Show sample data
            print(f"\n📋 Sample extracted data:")
            if result['results']:
                sample_company = result['results'][0]
                print(f"   Company: {sample_company.get('company_name', 'N/A')}")
                print(f"   Website: {sample_company.get('website_url', 'N/A')}")
                print(f"   Email: {sample_company.get('email', 'N/A')}")
                print(f"   Phone: {sample_company.get('phone', 'N/A')}")
        else:
            print("❌ URL demo failed")
        
        # Demo 3: Data format conversion
        print("\n📍 Demo 3: Data Format Conversion")
        print("-" * 40)
        
        if result.get('success'):
            print("📊 Converting JSON data to CSV and Excel...")
            
            # Convert to CSV
            csv_file = tool.data_output.save_data(
                data=result['results'],
                filename="demo_converted",
                format_type="csv"
            )
            print(f"✅ CSV file created: {csv_file}")
            
            # Convert to Excel
            excel_file = tool.data_output.save_data(
                data=result['results'],
                filename="demo_converted",
                format_type="xlsx"
            )
            print(f"✅ Excel file created: {excel_file}")
            
            # Generate statistics
            print(f"\n📈 Data Statistics:")
            stats = tool.data_output.get_output_stats(result['results'])
            print(f"   Total companies: {stats['total_companies']}")
            
            if 'data_completeness' in stats:
                for field, info in stats['data_completeness'].items():
                    print(f"   {field.title()}: {info['count']} ({info['percentage']:.1f}%)")
        
        # Demo 4: Show all output files
        print("\n📍 Demo 4: Generated Output Files")
        print("-" * 40)
        
        output_dir = "demo_output"
        if os.path.exists(output_dir):
            print(f"📁 Files created in '{output_dir}':")
            files = os.listdir(output_dir)
            for file in sorted(files):
                file_path = os.path.join(output_dir, file)
                size = os.path.getsize(file_path)
                print(f"   📄 {file} ({size} bytes)")
        
        print(f"\n🎉 Demo completed successfully!")
        print(f"🔍 Check the '{output_dir}' directory for all generated files.")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        return False
    
    finally:
        # Clean up
        tool.close()
    
    return True

def show_cli_examples():
    """Show examples of CLI usage"""
    print("\n🖥️  CLI Usage Examples")
    print("=" * 50)
    
    examples = [
        {
            "title": "Search for companies",
            "command": 'python main.py search --query "AI startups in Silicon Valley" --max-results 10 --level medium --format json'
        },
        {
            "title": "Scrape specific URLs",
            "command": 'python main.py scrape --file sample_urls.txt --level advanced --format xlsx'
        },
        {
            "title": "Convert data formats",
            "command": 'python main.py convert --input output/data.json --format csv'
        },
        {
            "title": "Show statistics",
            "command": 'python main.py stats --input output/data.json'
        },
        {
            "title": "Generate samples",
            "command": 'python main.py sample --input output/data.json --size 5'
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}:")
        print(f"   {example['command']}")
        print()

if __name__ == "__main__":
    print("🚀 Web Scraping Tool - Complete Demo")
    print("=" * 60)
    
    # Run the demo
    success = run_demo()
    
    # Show CLI examples
    show_cli_examples()
    
    print("💡 Tips:")
    print("   • Use --no-selenium for faster scraping")
    print("   • Use --verbose for detailed logging")
    print("   • Check scraper.log for detailed logs")
    print("   • Run 'python test_scraper.py' to test the installation")
    
    print("\n👋 Demo completed!")
    sys.exit(0 if success else 1) 