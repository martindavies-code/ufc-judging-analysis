"""Security, path sanitization, and input validation utilities."""

import html
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional, Union


def validate_numeric_id(val: Union[str, int], name: str = "ID") -> int:
    """Validate that an ID is a strictly positive integer.
    
    Prevents path traversal and parameter injection via numeric identifiers.
    """
    if isinstance(val, int):
        if val < 0:
            raise ValueError(f"{name} must be a non-negative integer, got {val}")
        return val
    
    if not isinstance(val, str):
        raise TypeError(f"{name} must be string or int, got {type(val).__name__}")
        
    val_clean = val.strip()
    if not val_clean.isdigit():
        raise ValueError(f"{name} must be numeric digits only, got '{val}'")
        
    return int(val_clean)


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize arbitrary strings for safe filesystem usage.
    
    Strips directory separators, null bytes, and non-printable characters.
    Guards against CWE-22 (Path Traversal).
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
        
    # Normalize unicode to NFKC
    normalized = unicodedata.normalize("NFKC", str(filename))
    
    # Strip null bytes and control chars
    clean = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", normalized)
    
    # Replace path separators and Windows-reserved characters: < > : " / \ | ? *
    clean = re.sub(r'[<>:"/\\|?*]+', "_", clean)
    
    # Strip leading/trailing whitespace and dots (Windows reserved trailing dots)
    clean = clean.strip(". ")
    
    if not clean:
        raise ValueError("Filename sanitized to empty string")
        
    return clean[:max_length]


def safe_resolve_path(base_dir: Union[str, Path], relative_path: str) -> Path:
    """Safely resolve a child path within base_dir.
    
    Raises ValueError if the resolved path attempts to escape base_dir (Path Traversal).
    """
    base = Path(base_dir).resolve()
    target = (base / relative_path).resolve()
    
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Path traversal detected: '{relative_path}' escapes base directory '{base}'")
        
    return target


def sanitize_text(text: Optional[str]) -> str:
    """Clean arbitrary string input: normalize unicode, strip control characters."""
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
        
    # NFKC normalizes compatibility characters like &nbsp; (\xa0) and full-width chars
    normalized = unicodedata.normalize("NFKC", text)
    # Remove control characters except newline and tab
    clean = re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "", normalized)
    return clean.strip()


def escape_html(val: Optional[Union[str, int, float]]) -> str:
    """Escape text for safe HTML embedding (CWE-79 / Stored XSS prevention)."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)
