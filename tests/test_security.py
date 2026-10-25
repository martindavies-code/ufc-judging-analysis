"""Unit tests for security, sanitization, and path traversal protection."""

import pytest

from src.security import (
    escape_html,
    safe_json_embed,
    safe_resolve_path,
    sanitize_filename,
    sanitize_judge_name,
    sanitize_text,
    validate_numeric_id,
    validate_safe_url,
)


class TestValidateNumericId:
    def test_valid_integer(self):
        assert validate_numeric_id(1516) == 1516
        assert validate_numeric_id(0) == 0

    def test_valid_numeric_string(self):
        assert validate_numeric_id("1516") == 1516
        assert validate_numeric_id(" 42 ") == 42

    def test_negative_integer_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            validate_numeric_id(-1)

    def test_negative_string_raises(self):
        with pytest.raises(ValueError, match="numeric digits"):
            validate_numeric_id("-5")

    def test_non_numeric_string_raises(self):
        with pytest.raises(ValueError, match="numeric digits"):
            validate_numeric_id("1516a")
        with pytest.raises(ValueError, match="numeric digits"):
            validate_numeric_id("../../1516")

    def test_invalid_types_raise(self):
        with pytest.raises(TypeError):
            validate_numeric_id(None)
        with pytest.raises(TypeError):
            validate_numeric_id([123])
        with pytest.raises(TypeError):
            validate_numeric_id(12.34)


class TestSanitizeFilename:
    def test_clean_name(self):
        assert sanitize_filename("ufc_event_1516.html") == "ufc_event_1516.html"

    def test_path_traversal_characters_removed(self):
        sanitized = sanitize_filename("../../etc/passwd")
        assert "/" not in sanitized
        assert ".." not in sanitized or "_" in sanitized
        assert "\\" not in sanitized

    def test_windows_reserved_characters(self):
        sanitized = sanitize_filename('event<1516>:name"file|test?*.html')
        for bad_char in ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]:
            assert bad_char not in sanitized

    def test_null_bytes_and_control_chars(self):
        raw = "test\x00file\x1f\x7f.html"
        assert "\x00" not in sanitize_filename(raw)
        assert "\x1f" not in sanitize_filename(raw)

    def test_empty_filename_raises(self):
        with pytest.raises(ValueError):
            sanitize_filename("")
        with pytest.raises(ValueError):
            sanitize_filename("   ...   ")


class TestSafeResolvePath:
    def test_valid_child_resolution(self, tmp_path):
        resolved = safe_resolve_path(tmp_path, "subfolder/file.txt")
        assert resolved == (tmp_path / "subfolder" / "file.txt").resolve()

    def test_path_traversal_attempt_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_resolve_path(tmp_path, "../outside.txt")
        with pytest.raises(ValueError, match="Path traversal detected"):
            safe_resolve_path(tmp_path, "sub/../../outside.txt")


class TestSanitizeText:
    def test_none_handling(self):
        assert sanitize_text(None) == ""

    def test_non_string_handling(self):
        assert sanitize_text(12345) == "12345"

    def test_control_character_stripping(self):
        raw = "Hello\x00World\x07!"
        assert sanitize_text(raw) == "HelloWorld!"

    def test_unicode_normalization(self):
        # Non-breaking space \xa0
        raw = "Rakhmonov\xa0def.\xa0Garry"
        assert sanitize_text(raw) == "Rakhmonov def. Garry"


class TestEscapeHtml:
    def test_script_tag_escaping(self):
        xss_input = "<script>alert('XSS')</script>"
        escaped = escape_html(xss_input)
        assert "<script>" not in escaped
        assert "&lt;script&gt;" in escaped
        assert "&#x27;" in escaped or "&#39;" in escaped or "'" not in escaped

    def test_attribute_quote_escaping(self):
        raw = 'name" onmouseover="alert(1)'
        escaped = escape_html(raw)
        assert '"' not in escaped
        assert "&quot;" in escaped

    def test_ampersand_escaping(self):
        raw = "Johnson & Johnson"
        assert escape_html(raw) == "Johnson &amp; Johnson"

    def test_none_value(self):
        assert escape_html(None) == ""

    def test_numeric_value(self):
        assert escape_html(42) == "42"


class TestValidateSafeUrl:
    def test_valid_mmadecisions_https(self):
        url = "https://mmadecisions.com/decision/1516/Jon-Jones-def-Mauricio-Rua"
        assert validate_safe_url(url) == url

    def test_valid_mmadecisions_http_with_allowed_flag(self):
        url = "http://www.mmadecisions.com/event/751/UFC-310"
        assert validate_safe_url(url, allow_http=True) == url

    def test_ssrf_localhost_rejected(self):
        with pytest.raises(ValueError, match="Prohibited target host"):
            validate_safe_url("http://localhost:8080/admin")
        with pytest.raises(ValueError, match="Prohibited target host"):
            validate_safe_url("http://127.0.0.1/secrets")

    def test_ssrf_cloud_metadata_rejected(self):
        with pytest.raises(ValueError, match="Prohibited target host"):
            validate_safe_url("http://169.254.169.254/latest/meta-data/")

    def test_untrusted_domain_rejected(self):
        with pytest.raises(ValueError, match="Untrusted host"):
            validate_safe_url("https://malicious-site.com/payload")

    def test_disallowed_schemes_rejected(self):
        with pytest.raises(ValueError, match="Disallowed URL scheme"):
            validate_safe_url("file:///etc/passwd")
        with pytest.raises(ValueError, match="Disallowed URL scheme"):
            validate_safe_url("ftp://mmadecisions.com/data")

    def test_empty_or_invalid_type_rejected(self):
        with pytest.raises(ValueError):
            validate_safe_url("")
        with pytest.raises(ValueError):
            validate_safe_url(None)  # type: ignore


class TestSafeJsonEmbed:
    def test_prevents_script_breakout(self):
        data = {"comment": "</script><script>alert('pwned')</script>"}
        embedded = safe_json_embed(data)
        assert "</script>" not in embedded
        assert "\\u003c/script\\u003e" in embedded

    def test_escapes_html_and_line_separators(self):
        data = {"text": "A & B < C > D \u2028 \u2029"}
        embedded = safe_json_embed(data)
        assert "<" not in embedded
        assert ">" not in embedded
        assert "&" not in embedded
        assert "\\u0026" in embedded
        assert "\\u2028" in embedded
        assert "\\u2029" in embedded


class TestSanitizeJudgeName:
    def test_clean_name(self):
        assert sanitize_judge_name("Sal D'Amato") == "Sal D'Amato"

    def test_strips_html_tags(self):
        assert sanitize_judge_name("<script>alert(1)</script>Derek Cleary") == "alert(1)Derek Cleary"

    def test_strips_control_characters(self):
        assert sanitize_judge_name("Chris\x00Lee\x07") == "ChrisLee"

    def test_empty_name_defaults(self):
        assert sanitize_judge_name("") == "Unknown Judge"
        assert sanitize_judge_name(None) == "Unknown Judge"

    def test_truncates_oversized_name(self):
        long_name = "Judge " * 50
        sanitized = sanitize_judge_name(long_name, max_length=30)
        assert len(sanitized) <= 30
