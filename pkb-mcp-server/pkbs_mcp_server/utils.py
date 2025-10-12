"""Utility functions for the PKB MCP Server."""

import re
from typing import List


def extract_links(content: str) -> List[str]:
    """
    Extract potential note links from content.
    Looks for patterns like [[Note Title]] or [[note-id]].
    """
    link_pattern = r'\[\[(.*?)\]\]'
    matches = re.findall(link_pattern, content)
    return matches
