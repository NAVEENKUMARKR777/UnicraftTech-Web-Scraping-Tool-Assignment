#!/usr/bin/env python3
"""
Proxy Manager for IP Rotation and Enhanced Anonymity
Supports multiple proxy providers and rotation strategies
"""

import requests
import random
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
import json
import os
from urllib.parse import urlparse
from dataclasses import dataclass
from enum import Enum
import threading
from collections import deque
import itertools

logger = logging.getLogger(__name__)

class ProxyType(Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"

@dataclass
class ProxyInfo:
    """Proxy information container"""
    host: str
    port: int
    proxy_type: ProxyType
    username: Optional[str] = None
    password: Optional[str] = None
    country: Optional[str] = None
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[float] = None
    response_time: Optional[float] = None
    is_working: bool = True

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total

    @property
    def proxy_url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.proxy_type.value}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, str]:
        """Convert to requests-compatible proxy dict"""
        proxy_url = self.proxy_url
        return {
            'http': proxy_url,
            'https': proxy_url
        }

class ProxyRotationStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    BEST_PERFORMANCE = "best_performance"
    WEIGHTED_RANDOM = "weighted_random"

class ProxyManager:
    """Advanced proxy management with rotation and health monitoring"""
    
    def __init__(self, rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.ROUND_ROBIN):
        self.proxies: List[ProxyInfo] = []
        self.rotation_strategy = rotation_strategy
        self.current_index = 0
        self.lock = threading.Lock()
        self.test_timeout = 10
        self.max_failures = 3
        
        # Load proxies from various sources
        self._load_free_proxies()
        self._load_user_proxies()
        
        # Performance tracking
        self.usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxy_failures': 0
        }
    
    def _load_free_proxies(self):
        """Load free proxies from public sources"""
        try:
            # Load from free proxy APIs
            free_proxy_sources = [
                self._get_proxy_list_free_proxies,
                self._get_free_proxy_list_net,
                self._get_gimmeproxy_proxies
            ]
            
            for source in free_proxy_sources:
                try:
                    proxies = source()
                    self.proxies.extend(proxies)
                    logger.info(f"Loaded {len(proxies)} proxies from {source.__name__}")
                except Exception as e:
                    logger.warning(f"Failed to load proxies from {source.__name__}: {e}")
                    
        except Exception as e:
            logger.error(f"Error loading free proxies: {e}")
    
    def _load_user_proxies(self):
        """Load user-configured proxies from file"""
        try:
            proxy_file = 'proxy_list.json'
            if os.path.exists(proxy_file):
                with open(proxy_file, 'r') as f:
                    proxy_configs = json.load(f)
                
                for config in proxy_configs:
                    proxy = ProxyInfo(
                        host=config['host'],
                        port=config['port'],
                        proxy_type=ProxyType(config['type']),
                        username=config.get('username'),
                        password=config.get('password'),
                        country=config.get('country')
                    )
                    self.proxies.append(proxy)
                
                logger.info(f"Loaded {len(proxy_configs)} user-configured proxies")
        except Exception as e:
            logger.warning(f"Error loading user proxies: {e}")
    
    def _get_proxy_list_free_proxies(self) -> List[ProxyInfo]:
        """Get proxies from proxy-list.download"""
        proxies = []
        try:
            # HTTP proxies
            response = requests.get(
                'https://www.proxy-list.download/api/v1/get?type=http',
                timeout=10
            )
            if response.status_code == 200:
                proxy_lines = response.text.strip().split('\n')
                for line in proxy_lines[:20]:  # Limit to 20 proxies
                    if ':' in line:
                        host, port = line.split(':')
                        proxy = ProxyInfo(
                            host=host.strip(),
                            port=int(port.strip()),
                            proxy_type=ProxyType.HTTP
                        )
                        proxies.append(proxy)
        except Exception as e:
            logger.warning(f"Error fetching from proxy-list.download: {e}")
        
        return proxies
    
    def _get_free_proxy_list_net(self) -> List[ProxyInfo]:
        """Get proxies from free-proxy-list.net"""
        proxies = []
        try:
            # Use requests to get proxy list
            response = requests.get(
                'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
                timeout=10
            )
            if response.status_code == 200:
                proxy_lines = response.text.strip().split('\n')
                for line in proxy_lines[:15]:  # Limit to 15 proxies
                    if ':' in line:
                        try:
                            host, port = line.split(':')
                            proxy = ProxyInfo(
                                host=host.strip(),
                                port=int(port.strip()),
                                proxy_type=ProxyType.HTTP
                            )
                            proxies.append(proxy)
                        except ValueError:
                            continue
        except Exception as e:
            logger.warning(f"Error fetching from free-proxy-list.net: {e}")
        
        return proxies
    
    def _get_gimmeproxy_proxies(self) -> List[ProxyInfo]:
        """Get proxies from gimmeproxy.com"""
        proxies = []
        try:
            for _ in range(5):  # Get 5 proxies
                response = requests.get(
                    'https://gimmeproxy.com/api/getProxy?format=json&protocol=http',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    proxy = ProxyInfo(
                        host=data['ip'],
                        port=int(data['port']),
                        proxy_type=ProxyType.HTTP,
                        country=data.get('country')
                    )
                    proxies.append(proxy)
                time.sleep(1)  # Rate limiting
        except Exception as e:
            logger.warning(f"Error fetching from gimmeproxy.com: {e}")
        
        return proxies
    
    def add_proxy(self, host: str, port: int, proxy_type: ProxyType,
                  username: str = None, password: str = None, country: str = None):
        """Add a proxy manually"""
        proxy = ProxyInfo(
            host=host,
            port=port,
            proxy_type=proxy_type,
            username=username,
            password=password,
            country=country
        )
        
        with self.lock:
            self.proxies.append(proxy)
        
        logger.info(f"Added proxy: {host}:{port}")
    
    def test_proxy(self, proxy: ProxyInfo, test_url: str = "http://httpbin.org/ip") -> bool:
        """Test if a proxy is working"""
        try:
            start_time = time.time()
            
            response = requests.get(
                test_url,
                proxies=proxy.to_dict(),
                timeout=self.test_timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            if response.status_code == 200:
                proxy.response_time = response_time
                proxy.success_count += 1
                proxy.is_working = True
                proxy.last_used = time.time()
                
                # Verify IP is different
                try:
                    data = response.json()
                    proxy_ip = data.get('origin', '').split(',')[0].strip()
                    logger.debug(f"Proxy {proxy.host}:{proxy.port} working, IP: {proxy_ip}")
                except:
                    pass
                
                return True
            else:
                proxy.failure_count += 1
                return False
                
        except Exception as e:
            proxy.failure_count += 1
            logger.debug(f"Proxy test failed for {proxy.host}:{proxy.port}: {e}")
            
            if proxy.failure_count >= self.max_failures:
                proxy.is_working = False
            
            return False
    
    def test_all_proxies(self) -> Dict[str, Any]:
        """Test all proxies and return results"""
        results = {
            'total_proxies': len(self.proxies),
            'working_proxies': 0,
            'failed_proxies': 0,
            'test_results': []
        }
        
        logger.info(f"Testing {len(self.proxies)} proxies...")
        
        for i, proxy in enumerate(self.proxies):
            logger.info(f"Testing proxy {i+1}/{len(self.proxies)}: {proxy.host}:{proxy.port}")
            
            is_working = self.test_proxy(proxy)
            
            result = {
                'proxy': f"{proxy.host}:{proxy.port}",
                'type': proxy.proxy_type.value,
                'working': is_working,
                'response_time': proxy.response_time,
                'country': proxy.country
            }
            
            results['test_results'].append(result)
            
            if is_working:
                results['working_proxies'] += 1
            else:
                results['failed_proxies'] += 1
        
        # Remove non-working proxies
        working_proxies = [p for p in self.proxies if p.is_working]
        self.proxies = working_proxies
        
        logger.info(f"Proxy testing complete: {results['working_proxies']} working, {results['failed_proxies']} failed")
        
        return results
    
    def get_next_proxy(self) -> Optional[ProxyInfo]:
        """Get next proxy based on rotation strategy"""
        with self.lock:
            working_proxies = [p for p in self.proxies if p.is_working]
            
            if not working_proxies:
                logger.warning("No working proxies available")
                return None
            
            if self.rotation_strategy == ProxyRotationStrategy.ROUND_ROBIN:
                proxy = working_proxies[self.current_index % len(working_proxies)]
                self.current_index = (self.current_index + 1) % len(working_proxies)
                
            elif self.rotation_strategy == ProxyRotationStrategy.RANDOM:
                proxy = random.choice(working_proxies)
                
            elif self.rotation_strategy == ProxyRotationStrategy.BEST_PERFORMANCE:
                # Sort by success rate and response time
                sorted_proxies = sorted(
                    working_proxies,
                    key=lambda p: (p.success_rate, -p.response_time if p.response_time else 0),
                    reverse=True
                )
                proxy = sorted_proxies[0]
                
            elif self.rotation_strategy == ProxyRotationStrategy.WEIGHTED_RANDOM:
                # Weight by success rate
                weights = [p.success_rate for p in working_proxies]
                proxy = random.choices(working_proxies, weights=weights)[0]
                
            else:
                proxy = working_proxies[0]
            
            proxy.last_used = time.time()
            return proxy
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """Make a request using proxy rotation"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            proxy = self.get_next_proxy()
            
            if not proxy:
                logger.error("No working proxies available")
                return None
            
            try:
                # Add proxy to kwargs
                if 'proxies' not in kwargs:
                    kwargs['proxies'] = proxy.to_dict()
                
                # Set default timeout
                if 'timeout' not in kwargs:
                    kwargs['timeout'] = 30
                
                # Make request
                response = requests.request(method, url, **kwargs)
                
                # Update proxy stats
                proxy.success_count += 1
                self.usage_stats['total_requests'] += 1
                self.usage_stats['successful_requests'] += 1
                
                return response
                
            except Exception as e:
                logger.warning(f"Request failed with proxy {proxy.host}:{proxy.port}: {e}")
                
                # Update proxy stats
                proxy.failure_count += 1
                self.usage_stats['total_requests'] += 1
                self.usage_stats['failed_requests'] += 1
                self.usage_stats['proxy_failures'] += 1
                
                # Mark proxy as non-working if too many failures
                if proxy.failure_count >= self.max_failures:
                    proxy.is_working = False
                    logger.info(f"Marking proxy {proxy.host}:{proxy.port} as non-working")
                
                retry_count += 1
                
                if retry_count < max_retries:
                    time.sleep(1)  # Brief delay before retry
        
        logger.error(f"Failed to make request to {url} after {max_retries} retries")
        return None
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        working_proxies = [p for p in self.proxies if p.is_working]
        
        stats = {
            'total_proxies': len(self.proxies),
            'working_proxies': len(working_proxies),
            'failed_proxies': len(self.proxies) - len(working_proxies),
            'rotation_strategy': self.rotation_strategy.value,
            'usage_stats': self.usage_stats.copy()
        }
        
        if working_proxies:
            response_times = [p.response_time for p in working_proxies if p.response_time]
            if response_times:
                stats['avg_response_time'] = sum(response_times) / len(response_times)
                stats['min_response_time'] = min(response_times)
                stats['max_response_time'] = max(response_times)
            
            success_rates = [p.success_rate for p in working_proxies]
            stats['avg_success_rate'] = sum(success_rates) / len(success_rates)
            
            # Country distribution
            countries = {}
            for proxy in working_proxies:
                country = proxy.country or 'Unknown'
                countries[country] = countries.get(country, 0) + 1
            stats['country_distribution'] = countries
            
            # Proxy type distribution
            types = {}
            for proxy in working_proxies:
                proxy_type = proxy.proxy_type.value
                types[proxy_type] = types.get(proxy_type, 0) + 1
            stats['type_distribution'] = types
        
        return stats
    
    def save_working_proxies(self, filename: str = 'working_proxies.json'):
        """Save working proxies to file"""
        working_proxies = [p for p in self.proxies if p.is_working]
        
        proxy_data = []
        for proxy in working_proxies:
            data = {
                'host': proxy.host,
                'port': proxy.port,
                'type': proxy.proxy_type.value,
                'username': proxy.username,
                'password': proxy.password,
                'country': proxy.country,
                'success_rate': proxy.success_rate,
                'response_time': proxy.response_time
            }
            proxy_data.append(data)
        
        with open(filename, 'w') as f:
            json.dump(proxy_data, f, indent=2)
        
        logger.info(f"Saved {len(proxy_data)} working proxies to {filename}")
    
    def load_working_proxies(self, filename: str = 'working_proxies.json'):
        """Load working proxies from file"""
        try:
            with open(filename, 'r') as f:
                proxy_data = json.load(f)
            
            loaded_proxies = []
            for data in proxy_data:
                proxy = ProxyInfo(
                    host=data['host'],
                    port=data['port'],
                    proxy_type=ProxyType(data['type']),
                    username=data.get('username'),
                    password=data.get('password'),
                    country=data.get('country')
                )
                # Restore stats
                if 'success_rate' in data and data['success_rate'] > 0:
                    proxy.success_count = 10  # Approximate
                    proxy.failure_count = int(10 * (1 - data['success_rate']))
                
                if 'response_time' in data:
                    proxy.response_time = data['response_time']
                
                loaded_proxies.append(proxy)
            
            self.proxies = loaded_proxies
            logger.info(f"Loaded {len(loaded_proxies)} proxies from {filename}")
            
        except Exception as e:
            logger.error(f"Error loading proxies from {filename}: {e}")
    
    def cleanup_failed_proxies(self):
        """Remove failed proxies from the list"""
        before_count = len(self.proxies)
        self.proxies = [p for p in self.proxies if p.is_working]
        after_count = len(self.proxies)
        
        removed = before_count - after_count
        if removed > 0:
            logger.info(f"Removed {removed} failed proxies")
    
    def reset_proxy_stats(self):
        """Reset proxy statistics"""
        for proxy in self.proxies:
            proxy.success_count = 0
            proxy.failure_count = 0
            proxy.is_working = True
        
        self.usage_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxy_failures': 0
        }
        
        logger.info("Reset all proxy statistics")

def create_sample_proxy_config():
    """Create a sample proxy configuration file"""
    sample_proxies = [
        {
            "host": "proxy1.example.com",
            "port": 8080,
            "type": "http",
            "username": "user1",
            "password": "pass1",
            "country": "US"
        },
        {
            "host": "proxy2.example.com",
            "port": 1080,
            "type": "socks5",
            "username": "user2",
            "password": "pass2",
            "country": "UK"
        }
    ]
    
    with open('proxy_list_sample.json', 'w') as f:
        json.dump(sample_proxies, f, indent=2)
    
    print("Created sample proxy configuration: proxy_list_sample.json")

# Example usage and testing
if __name__ == "__main__":
    # Create proxy manager
    print("🔄 Initializing Proxy Manager...")
    manager = ProxyManager(ProxyRotationStrategy.BEST_PERFORMANCE)
    
    print(f"📊 Loaded {len(manager.proxies)} proxies")
    
    # Test all proxies
    print("🧪 Testing all proxies...")
    test_results = manager.test_all_proxies()
    
    print(f"✅ Working proxies: {test_results['working_proxies']}")
    print(f"❌ Failed proxies: {test_results['failed_proxies']}")
    
    # Show statistics
    stats = manager.get_proxy_stats()
    print(f"\n📈 Proxy Statistics:")
    print(f"  Total: {stats['total_proxies']}")
    print(f"  Working: {stats['working_proxies']}")
    print(f"  Strategy: {stats['rotation_strategy']}")
    
    if stats['working_proxies'] > 0:
        print(f"  Avg Response Time: {stats.get('avg_response_time', 0):.2f}s")
        print(f"  Avg Success Rate: {stats.get('avg_success_rate', 0):.1%}")
    
    # Save working proxies
    manager.save_working_proxies()
    
    # Create sample config
    create_sample_proxy_config() 