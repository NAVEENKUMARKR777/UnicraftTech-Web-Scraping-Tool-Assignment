#!/usr/bin/env python3
"""
Web Scraping Tool for Company Discovery and Data Extraction
"""

import click
import logging
import sys
import time
import json
from typing import List, Dict, Any, Optional
from tqdm import tqdm
import validators

from config import Config
from scraper import WebScraper
from search_discovery import SearchDiscovery
from search_discovery_improved import ImprovedSearchDiscovery
from data_output import DataOutput

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WebScrapingTool:
    """Main web scraping tool class"""
    
    def __init__(self, use_selenium: bool = True, output_dir: str = "output"):
        self.scraper = WebScraper(use_selenium=use_selenium)
        self.search_discovery = SearchDiscovery(use_selenium=use_selenium)
        self.data_output = DataOutput(output_dir=output_dir)
        
    def scrape_from_query(self, query: str, max_results: int = 20, 
                         extraction_level: str = "basic",
                         search_engines: List[str] = None,
                         output_format: str = "json",
                         output_filename: str = None) -> Dict[str, Any]:
        """Scrape companies from search query"""
        
        logger.info(f"Starting scraping process for query: '{query}'")
        
        # Discover companies - Try original method first
        click.echo(f"🔍 Discovering companies for query: '{query}'")
        try:
            urls = self.search_discovery.search_and_discover(
                query=query,
                max_results=max_results,
                search_engines=search_engines or ['google', 'bing']
            )
        except Exception as e:
            logger.warning(f"Original search failed: {e}")
            urls = []
        
        # If no results, try improved search discovery
        if not urls:
            click.echo("🔄 Trying improved search methods...")
            try:
                improved_discovery = ImprovedSearchDiscovery(use_selenium=False)
                urls = improved_discovery.search_companies(query, max_results)
                improved_discovery.close()
                
                if urls:
                    click.echo(f"✅ Found {len(urls)} companies using improved search")
                    
            except Exception as e:
                logger.warning(f"Improved search also failed: {e}")
                urls = []
        
        if not urls:
            click.echo("❌ No companies found for the given query.")
            click.echo("💡 Try different keywords or check your internet connection.")
            return {"error": "No companies found", "query": query}
        
        click.echo(f"✅ Found {len(urls)} companies to scrape")
        
        # Scrape data
        return self.scrape_from_urls(
            urls=urls,
            extraction_level=extraction_level,
            output_format=output_format,
            output_filename=output_filename
        )
    
    def scrape_from_urls(self, urls: List[str], 
                        extraction_level: str = "basic",
                        output_format: str = "json",
                        output_filename: str = None) -> Dict[str, Any]:
        """Scrape companies from list of URLs"""
        
        logger.info(f"Starting scraping {len(urls)} URLs with {extraction_level} extraction")
        
        results = []
        failed_urls = []
        
        # Progress bar
        with tqdm(total=len(urls), desc="Scraping companies") as pbar:
            for i, url in enumerate(urls):
                try:
                    click.echo(f"📊 Scraping {i+1}/{len(urls)}: {url}")
                    
                    # Scrape single URL
                    result = self.scraper.scrape_url(url, level=extraction_level)
                    
                    if "error" in result:
                        failed_urls.append({"url": url, "error": result["error"]})
                        logger.warning(f"Failed to scrape {url}: {result['error']}")
                    else:
                        results.append(result)
                        logger.info(f"Successfully scraped {url}")
                    
                    pbar.update(1)
                    
                except Exception as e:
                    failed_urls.append({"url": url, "error": str(e)})
                    logger.error(f"Error scraping {url}: {e}")
                    pbar.update(1)
        
        # Save results
        if results:
            saved_file = self.data_output.save_data(
                data=results,
                filename=output_filename,
                format_type=output_format
            )
            
            # Generate statistics
            stats = self.data_output.get_output_stats(results)
            
            click.echo(f"\n✅ Scraping completed!")
            click.echo(f"📄 Data saved to: {saved_file}")
            click.echo(f"📊 Successfully scraped: {len(results)} companies")
            click.echo(f"❌ Failed to scrape: {len(failed_urls)} companies")
            
            return {
                "success": True,
                "results": results,
                "failed_urls": failed_urls,
                "saved_file": saved_file,
                "stats": stats
            }
        else:
            click.echo("❌ No data was successfully scraped.")
            return {
                "success": False,
                "error": "No data scraped",
                "failed_urls": failed_urls
            }
    
    def close(self):
        """Close all resources"""
        self.scraper.close()
        self.search_discovery.close()
    
    def __enter__(self):
        """Enter context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        self.close()

# CLI Interface
@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--no-selenium', is_flag=True, help='Disable Selenium (faster but limited)')
@click.option('--output-dir', default='output', help='Output directory for results')
@click.pass_context
def cli(ctx, verbose, no_selenium, output_dir):
    """Web Scraping Tool for Company Discovery and Data Extraction"""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize tool
    ctx.ensure_object(dict)
    ctx.obj['tool'] = WebScrapingTool(
        use_selenium=not no_selenium,
        output_dir=output_dir
    )
    
    click.echo("🚀 Web Scraping Tool initialized")


@cli.command()
@click.option('--query', '-q', required=True, help='Search query for companies')
@click.option('--max-results', '-n', default=20, help='Maximum number of companies to find')
@click.option('--level', '-l', 
              type=click.Choice(['basic', 'medium', 'advanced']), 
              default='basic', 
              help='Data extraction level')
@click.option('--engines', '-e', 
              multiple=True, 
              type=click.Choice(['google', 'bing', 'duckduckgo']),
              default=['google', 'bing'],
              help='Search engines to use')
@click.option('--format', '-f', 
              type=click.Choice(['json', 'csv', 'xlsx']), 
              default='json',
              help='Output format')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.pass_context
def search(ctx, query, max_results, level, engines, format, output):
    """Search for companies and extract data"""
    
    tool = ctx.obj['tool']
    
    try:
        result = tool.scrape_from_query(
            query=query,
            max_results=max_results,
            extraction_level=level,
            search_engines=list(engines),
            output_format=format,
            output_filename=output
        )
        
        if result.get('success'):
            click.echo(f"\n📈 Extraction Statistics:")
            stats = result['stats']
            click.echo(f"   Total companies: {stats['total_companies']}")
            
            if 'data_completeness' in stats:
                click.echo(f"   Email coverage: {stats['data_completeness']['email']['percentage']:.1f}%")
                click.echo(f"   Phone coverage: {stats['data_completeness']['phone']['percentage']:.1f}%")
    
    except KeyboardInterrupt:
        click.echo("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Error in search command: {e}")
    finally:
        tool.close()


@cli.command()
@click.option('--urls', '-u', multiple=True, help='Company URLs to scrape')
@click.option('--file', '-f', help='File containing URLs (one per line)')
@click.option('--level', '-l', 
              type=click.Choice(['basic', 'medium', 'advanced']), 
              default='basic', 
              help='Data extraction level')
@click.option('--format', '-fmt', 
              type=click.Choice(['json', 'csv', 'xlsx']), 
              default='json',
              help='Output format')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.pass_context
def scrape(ctx, urls, file, level, format, output):
    """Scrape specific company URLs"""
    
    tool = ctx.obj['tool']
    
    # Collect URLs
    url_list = list(urls)
    
    if file:
        try:
            with open(file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                url_list.extend(file_urls)
        except Exception as e:
            click.echo(f"❌ Error reading file {file}: {e}")
            return
    
    if not url_list:
        click.echo("❌ No URLs provided. Use --urls or --file option.")
        return
    
    # Validate URLs
    valid_urls = []
    for url in url_list:
        if validators.url(url):
            valid_urls.append(url)
        else:
            click.echo(f"⚠️  Invalid URL skipped: {url}")
    
    if not valid_urls:
        click.echo("❌ No valid URLs found.")
        return
    
    click.echo(f"🎯 Scraping {len(valid_urls)} URLs")
    
    try:
        result = tool.scrape_from_urls(
            urls=valid_urls,
            extraction_level=level,
            output_format=format,
            output_filename=output
        )
        
        if result.get('success'):
            click.echo(f"\n📈 Extraction Statistics:")
            stats = result['stats']
            click.echo(f"   Total companies: {stats['total_companies']}")
            
            if 'data_completeness' in stats:
                click.echo(f"   Email coverage: {stats['data_completeness']['email']['percentage']:.1f}%")
                click.echo(f"   Phone coverage: {stats['data_completeness']['phone']['percentage']:.1f}%")
    
    except KeyboardInterrupt:
        click.echo("\n⚠️  Scraping interrupted by user")
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Error in scrape command: {e}")
    finally:
        tool.close()


@cli.command()
@click.option('--input', '-i', required=True, help='Input file path')
@click.option('--format', '-f', 
              type=click.Choice(['json', 'csv', 'xlsx']), 
              default='json',
              help='Output format')
@click.option('--output', '-o', help='Output filename (without extension)')
@click.pass_context
def convert(ctx, input, format, output):
    """Convert data between formats"""
    
    tool = ctx.obj['tool']
    
    try:
        # Load data
        data = tool.data_output.load_data(input)
        
        # Save in new format
        saved_file = tool.data_output.save_data(
            data=data,
            filename=output,
            format_type=format
        )
        
        click.echo(f"✅ Data converted and saved to: {saved_file}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Error in convert command: {e}")


@cli.command()
@click.option('--input', '-i', required=True, help='Input file path')
@click.pass_context
def stats(ctx, input):
    """Show statistics about scraped data"""
    
    tool = ctx.obj['tool']
    
    try:
        # Load data
        data = tool.data_output.load_data(input)
        
        # Get statistics
        stats = tool.data_output.get_output_stats(data)
        
        # Display statistics
        click.echo(f"\n📊 Data Statistics for {input}")
        click.echo(f"=" * 50)
        click.echo(f"Total Companies: {stats['total_companies']}")
        
        if 'extraction_levels' in stats:
            click.echo(f"\nExtraction Levels:")
            for level, count in stats['extraction_levels'].items():
                click.echo(f"  {level.title()}: {count}")
        
        if 'data_completeness' in stats:
            click.echo(f"\nData Completeness:")
            for field, info in stats['data_completeness'].items():
                click.echo(f"  {field.title()}: {info['count']} ({info['percentage']:.1f}%)")
        
        if 'contact_info_availability' in stats:
            click.echo(f"\nContact Information:")
            for field, count in stats['contact_info_availability'].items():
                click.echo(f"  {field.title()}: {count}")
        
        click.echo(f"\nAdditional Data:")
        click.echo(f"  Social Media: {stats.get('social_media_presence', 0)}")
        click.echo(f"  Tech Stack Info: {stats.get('tech_stack_info', 0)}")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Error in stats command: {e}")


@cli.command()
@click.option('--input', '-i', required=True, help='Input file path')
@click.option('--size', '-s', default=5, help='Number of sample records')
@click.pass_context
def sample(ctx, input, size):
    """Generate sample output files"""
    
    tool = ctx.obj['tool']
    
    try:
        # Load data
        data = tool.data_output.load_data(input)
        
        # Save sample data
        saved_files = tool.data_output.save_sample_data(data, sample_size=size)
        
        click.echo(f"✅ Sample data generated:")
        for file in saved_files:
            click.echo(f"   {file}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")
        logger.error(f"Error in sample command: {e}")


@cli.command()
def demo():
    """Run a demonstration of the tool"""
    
    click.echo("🎬 Running Web Scraping Tool Demo")
    click.echo("=" * 50)
    
    # Demo query
    demo_query = "cloud computing startups in Silicon Valley"
    
    with WebScrapingTool(use_selenium=False) as tool:  # Use faster mode for demo
        try:
            click.echo(f"🔍 Searching for: '{demo_query}'")
            
            # Search for a few companies
            urls = tool.search_discovery.search_and_discover(
                query=demo_query,
                max_results=3,
                search_engines=['google']
            )
            
            if urls:
                click.echo(f"✅ Found {len(urls)} companies for demo")
                
                # Scrape basic data
                result = tool.scrape_from_urls(
                    urls=urls[:2],  # Just first 2 for demo
                    extraction_level="basic",
                    output_format="json",
                    output_filename="demo_results"
                )
                
                if result.get('success'):
                    click.echo("🎉 Demo completed successfully!")
                    click.echo(f"📄 Check output folder for demo results")
                else:
                    click.echo("⚠️  Demo completed with some issues")
            else:
                click.echo("❌ No companies found for demo")
                
        except Exception as e:
            click.echo(f"❌ Demo error: {e}")
            logger.error(f"Error in demo: {e}")


if __name__ == '__main__':
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 