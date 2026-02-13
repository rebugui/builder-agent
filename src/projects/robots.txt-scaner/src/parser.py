"""Robots.txt parsing logic."""
import re
from typing import List, Tuple
from .models import UserAgentGroupModel, DirectiveModel


class RobotsParser:
    """Parses robots.txt content into structured data."""
    
    def __init__(self, content: str):
        self.content = content
        self.groups: List[UserAgentGroupModel] = []
        self.sitemaps: List[str] = []
        
    def parse(self) -> Tuple[List[UserAgentGroupModel], List[str]]:
        """Main entry point for parsing."""
        lines = self.content.splitlines()
        
        current_group = None
        
        for line in lines:
            # Remove comments and trim whitespace
            line = re.split(r'#', line)[0].strip()
            if not line:
                continue
                
            parts = line.split(':', 1)
            if len(parts) != 2:
                continue
                
            key = parts[0].strip().lower()
            value = parts[1].strip()
            
            if key == 'user-agent':
                # Save previous group if exists
                if current_group:
                    self.groups.append(current_group)
                # Start new group
                current_group = UserAgentGroupModel(user_agent=value)
                
            elif key == 'disallow':
                if current_group:
                    current_group.directives.append(DirectiveModel(type='Disallow', path=value))
                else:
                    # Rules without a user-agent usually apply to *
                    # For simplicity, we create a generic group if we encounter orphaned directives
                    # or skip them. Here we assume they belong to the last implicit group.
                    pass 
                    
            elif key == 'allow':
                if current_group:
                    current_group.directives.append(DirectiveModel(type='Allow', path=value))
                    
            elif key == 'crawl-delay':
                if current_group:
                    try:
                        current_group.crawl_delay = int(value)
                    except ValueError:
                        pass
                        
            elif key == 'sitemap':
                self.sitemaps.append(value)
        
        # Append the last group
        if current_group:
            self.groups.append(current_group)
            
        return self.groups, self.sitemaps