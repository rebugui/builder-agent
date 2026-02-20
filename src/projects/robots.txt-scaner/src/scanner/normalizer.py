"""
URL Normalizer Module

Handles URL validation and normalization for robots.txt scanning.
"""

import re
from typing import Optional
from urllib.parse import urlparse, urlunparse


class URLNormalizer:
    """
    Normalizes URLs and constructs robots.txt URLs.
    
    Handles:
    - URL validation
    - Protocol scheme addition
    - robots.txt URL construction
    """
    
    # Regex for domain validation
    DOMAIN_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
    )
    
    # Maximum URL length
    MAX_URL_LENGTH = 2048
    
    def normalize_to_robots_url(self, url: str) -> str:
        """
        Convert a URL or domain to a robots.txt URL.
        
        Args:
            url: Input URL or domain.
            
        Returns:
            Full robots.txt URL.
            
        Examples:
            >>> normalizer.normalize_to_robots_url("example.com")
            'https://example.com/robots.txt'
            >>> normalizer.normalize_to_robots_url("http://example.com/path")
            'http://example.com/robots.txt'
        """
        url = url.strip()
        
        if not url:
            return ""
        
        # Limit length for security
        if len(url) > self.MAX_URL_LENGTH:
            url = url[:self.MAX_URL_LENGTH]
        
        # Remove common prefixes that users might accidentally include
        for prefix in ['www.', 'http://www.', 'https://www.']:
            if url.lower().startswith(prefix):
                # Keep the scheme if present
                if prefix.startswith('http'):
                    scheme = prefix.split(':')[0]
                    url = f"{scheme}://{url[len(prefix):]}"
                    break
                else:
                    url = url[len(prefix):]
                    break
        
        # Parse the URL
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                # No scheme, add https
                if '//' not in url:
                    url = f'https://{url}'
                else:
                    url = f'https:{url}'
                parsed = urlparse(url)
            
            # Construct robots.txt URL
            scheme = parsed.scheme if parsed.scheme in ('http', 'https') else 'https'
            netloc = parsed.netloc
            
            if not netloc:
                # Handle case where input was just a domain
                netloc = url.split('/')[0].split('?')[0].split('#')[0]
            
            # Remove port from netloc for checking, but keep it in URL
            domain = netloc.split(':')[0]
            
            # Validate domain
            if not self._is_valid_domain(domain):
                return ""
            
            return f"{scheme}://{netloc}/robots.txt"
            
        except Exception:
            return ""
    
    def get_base_url(self, url: str) -> str:
        """
        Get the base URL (scheme + domain) from a URL.
        
        Args:
            url: Input URL.
            
        Returns:
            Base URL (e.g., "https://example.com").
        """
        url = url.strip()
        
        if not url:
            return ""
        
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'
        
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme if parsed.scheme in ('http', 'https') else 'https'
            netloc = parsed.netloc
            
            if not netloc:
                return ""
            
            return f"{scheme}://{netloc}"
        except Exception:
            return ""
    
    def is_valid_url(self, url: str) -> bool:
        """
        Validate a URL string.
        
        Args:
            url: URL to validate.
            
        Returns:
            True if URL is valid, False otherwise.
        """
        if not url:
            return False
        
        url = url.strip()
        
        # Check length
        if len(url) > self.MAX_URL_LENGTH:
            return False
        
        # Try to parse and validate
        try:
            # Add scheme if missing for validation
            test_url = url
            if not url.startswith(('http://', 'https://')):
                test_url = f'https://{url}'
            
            parsed = urlparse(test_url)
            
            # Must have a valid scheme and netloc
            if parsed.scheme not in ('http', 'https', ''):
                return False
            
            domain = parsed.netloc.split(':')[0] if parsed.netloc else url.split('/')[0]
            
            return self._is_valid_domain(domain)
            
        except Exception:
            return False
    
    def _is_valid_domain(self, domain: str) -> bool:
        """
        Validate a domain name.
        
        Args:
            domain: Domain to validate.
            
        Returns:
            True if domain is valid.
        """
        if not domain:
            return False
        
        # Check length
        if len(domain) > 253:
            return False
        
        # Remove brackets for IPv6
        if domain.startswith('[') and domain.endswith(']'):
            return True  # IPv6 address
        
        # Check for IP address
        if self._is_valid_ipv4(domain):
            return True
        
        # Validate domain format
        if not self.DOMAIN_PATTERN.match(domain):
            return False
        
        # Check for valid TLD
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        
        tld = parts[-1]
        if len(tld) < 2 or not tld.isalpha():
            return False
        
        return True
    
    def _is_valid_ipv4(self, ip: str) -> bool:
        """
        Validate an IPv4 address.
        
        Args:
            ip: IP address string.
            
        Returns:
            True if valid IPv4.
        """
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False
