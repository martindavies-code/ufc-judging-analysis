"""Security, path sanitization, URL validation, and input protection utilities.

Implements protections against:
- CWE-22 (Improper Limitation of a Pathname to a Restricted Directory / Path Traversal)
- CWE-79 (Improper Neutralization of Input During Web Page Generation / Cross-site Scripting)
- CWE-918 (Server-Side Request Forgery / SSRF)
- CWE-89 (Improper Neutralization of Special Elements used in an SQL Command)
"""

import html
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Container, Optional, Set, Union
from urllib.parse import urlparse

ALLOWED_SCRAPING_HOSTS: Set[str] = {
    "mmadecisions.com",
    "www.mmadecisions.com",
}


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


def sanitize_judge_name(name: Optional[str], max_length: int = 100) -> str:
    """Strictly sanitize judge name against script injection, control chars, and HTML."""
    if not name:
        return "Unknown Judge"
    clean = sanitize_text(name)
    # Strip any residual HTML tags
    clean = re.sub(r"<[^>]*>", "", clean)
    # Standardize whitespace
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:max_length] if clean else "Unknown Judge"


def escape_html(val: Optional[Union[str, int, float]]) -> str:
    """Escape text for safe HTML embedding (CWE-79 / Stored XSS prevention)."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)


def safe_json_embed(obj: Any) -> str:
    """Serialize object to JSON safely embedded inside HTML <script> tags.
    
    Escapes <, >, &, and Unicode line/paragraph separators (U+2028, U+2029)
    to prevent script tag breakouts and JS syntax errors.
    """
    raw_json = json.dumps(obj)
    return (
        raw_json
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def validate_safe_url(
    url: str,
    allowed_domains: Optional[Container[str]] = None,
    allow_http: bool = False
) -> str:
    """Validate URL against SSRF (CWE-918) and protocol attacks.
    
    Ensures URL uses safe schemes (https, or http if allow_http=True)
    and strictly targets allowed destination hosts.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
        
    clean_url = url.strip()
    parsed = urlparse(clean_url)
    
    allowed_schemes = {"https", "http"} if allow_http else {"https", "http"}
    if parsed.scheme.lower() not in allowed_schemes:
        raise ValueError(f"Disallowed URL scheme: '{parsed.scheme}'. Only {allowed_schemes} allowed.")
        
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"URL missing valid hostname: '{clean_url}'")
        
    # Check for localhost and private IP ranges
    if host in {"localhost", "127.0.0.1", "::1"} or host.startswith("169.254."):
        raise ValueError(f"Prohibited target host (SSRF protection): '{host}'")
        
    domains = allowed_domains if allowed_domains is not None else ALLOWED_SCRAPING_HOSTS
    if host not in domains:
        raise ValueError(f"Untrusted host: '{host}'. Allowed domains: {domains}")
        
    return clean_url
