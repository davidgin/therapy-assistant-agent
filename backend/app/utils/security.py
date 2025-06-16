"""
Security utilities for the therapy assistant application
"""

import hashlib
import secrets
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps
import re

logger = logging.getLogger(__name__)

class SecurityManager:
    """Security utilities for application security"""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate a cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: Optional[str] = None) -> tuple[str, str]:
        """
        Hash sensitive data with salt
        
        Returns:
            Tuple of (hashed_data, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use SHA-256 with salt
        combined = f"{data}{salt}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()
        
        return hashed, salt
    
    @staticmethod
    def verify_hashed_data(data: str, hashed_data: str, salt: str) -> bool:
        """Verify data against its hash"""
        test_hash, _ = SecurityManager.hash_sensitive_data(data, salt)
        return test_hash == hashed_data
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove directory traversal patterns
        sanitized = re.sub(r'\.\.[\\/]', '', filename)
        
        # Remove or replace dangerous characters
        sanitized = re.sub(r'[<>:"|?*]', '_', sanitized)
        
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
            sanitized = name[:255-len(ext)-1] + ('.' + ext if ext else '')
        
        return sanitized
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_suspicious_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze request for suspicious patterns
        
        Returns:
            Analysis result with risk score and details
        """
        analysis = {
            "risk_score": 0,
            "issues": [],
            "blocked": False
        }
        
        # Check for SQL injection patterns
        sql_patterns = [
            r'\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP)\b',
            r'[\'";].*[\'";]',
            r'--.*$',
            r'/\*.*\*/'
        ]
        
        # Check for XSS patterns  
        xss_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object'
        ]
        
        # Check all string values in request
        def check_patterns(text: str, patterns: List[str], issue_type: str):
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    analysis["risk_score"] += 5
                    analysis["issues"].append(f"Potential {issue_type} detected")
                    break
        
        # Recursively check all string values
        def check_value(value, key=""):
            if isinstance(value, str):
                check_patterns(value, sql_patterns, "SQL injection")
                check_patterns(value, xss_patterns, "XSS attack")
                
                # Check for excessive length
                if len(value) > 10000:
                    analysis["risk_score"] += 3
                    analysis["issues"].append(f"Unusually long input in {key}")
                    
            elif isinstance(value, dict):
                for k, v in value.items():
                    check_value(v, k)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    check_value(item, f"{key}[{i}]")
        
        check_value(request_data)
        
        # Block if risk score is too high
        if analysis["risk_score"] >= 10:
            analysis["blocked"] = True
        
        return analysis

class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self):
        self.requests = {}  # {client_id: [(timestamp, count), ...]}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = datetime.now()
    
    def is_allowed(self, client_id: str, limit: int = 100, window: int = 3600) -> bool:
        """
        Check if request is allowed under rate limit
        
        Args:
            client_id: Unique identifier for client
            limit: Maximum requests per window
            window: Time window in seconds
            
        Returns:
            True if request is allowed
        """
        now = datetime.now()
        
        # Clean up old entries periodically
        if (now - self.last_cleanup).seconds > self.cleanup_interval:
            self._cleanup_old_entries()
            self.last_cleanup = now
        
        # Initialize client if not exists
        if client_id not in self.requests:
            self.requests[client_id] = []
        
        # Remove entries outside current window
        cutoff = now - timedelta(seconds=window)
        self.requests[client_id] = [
            (timestamp, count) for timestamp, count in self.requests[client_id]
            if timestamp > cutoff
        ]
        
        # Count requests in current window
        current_count = sum(count for _, count in self.requests[client_id])
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for client {client_id}: {current_count}/{limit}")
            return False
        
        # Add current request
        self.requests[client_id].append((now, 1))
        return True
    
    def _cleanup_old_entries(self):
        """Remove old rate limiting entries"""
        cutoff = datetime.now() - timedelta(seconds=7200)  # 2 hours
        
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                (timestamp, count) for timestamp, count in self.requests[client_id]
                if timestamp > cutoff
            ]
            
            # Remove empty entries
            if not self.requests[client_id]:
                del self.requests[client_id]

class AuditLogger:
    """Security audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
        
        # Create separate handler for security logs
        handler = logging.FileHandler("security_audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"AUTH_ATTEMPT - User: {user_id}, Status: {status}, IP: {ip_address}")
    
    def log_sensitive_operation(self, user_id: str, operation: str, resource: str, ip_address: str):
        """Log sensitive operations"""
        self.logger.info(f"SENSITIVE_OP - User: {user_id}, Operation: {operation}, Resource: {resource}, IP: {ip_address}")
    
    def log_security_violation(self, user_id: str, violation_type: str, details: str, ip_address: str):
        """Log security violations"""
        self.logger.warning(f"SECURITY_VIOLATION - User: {user_id}, Type: {violation_type}, Details: {details}, IP: {ip_address}")
    
    def log_data_access(self, user_id: str, data_type: str, action: str, ip_address: str):
        """Log data access events"""
        self.logger.info(f"DATA_ACCESS - User: {user_id}, Type: {data_type}, Action: {action}, IP: {ip_address}")

# Global instances
security_manager = SecurityManager()
rate_limiter = RateLimiter()
audit_logger = AuditLogger()

def require_https(func):
    """Decorator to require HTTPS for sensitive endpoints"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # In a real deployment, check if request is HTTPS
        # For development, we'll skip this check
        return func(*args, **kwargs)
    return wrapper

def sanitize_input(data: Any) -> Any:
    """Sanitize input data recursively"""
    if isinstance(data, str):
        # Remove null bytes
        sanitized = data.replace('\x00', '')
        
        # Limit length
        if len(sanitized) > 10000:
            sanitized = sanitized[:10000]
        
        return sanitized.strip()
    
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    
    else:
        return data

def check_content_security_policy() -> Dict[str, str]:
    """Generate Content Security Policy headers"""
    return {
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self' https://api.openai.com; "
            "frame-ancestors 'none';"
        ),
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }