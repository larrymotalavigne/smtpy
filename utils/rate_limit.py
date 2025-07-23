"""Rate limiting utilities for SMTPy."""

import time
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException
import threading


class RateLimiter:
    """Simple in-memory rate limiter using sliding window."""
    
    def __init__(self):
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit."""
        current_time = time.time()
        
        with self._lock:
            # Clean old requests outside the window
            request_times = self._requests[key]
            while request_times and request_times[0] <= current_time - window_seconds:
                request_times.popleft()
            
            # Check if we're under the limit
            if len(request_times) < max_requests:
                request_times.append(current_time)
                return True
            
            return False
    
    def get_remaining_requests(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get number of remaining requests in the current window."""
        current_time = time.time()
        
        with self._lock:
            request_times = self._requests[key]
            # Clean old requests
            while request_times and request_times[0] <= current_time - window_seconds:
                request_times.popleft()
            
            return max(0, max_requests - len(request_times))
    
    def get_reset_time(self, key: str, window_seconds: int) -> Optional[float]:
        """Get the time when the rate limit will reset."""
        with self._lock:
            request_times = self._requests[key]
            if not request_times:
                return None
            
            return request_times[0] + window_seconds


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded headers first (for reverse proxy setups)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in case of multiple proxies
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


def rate_limit_auth(max_requests: int = 5, window_seconds: int = 300):
    """
    Rate limit decorator for authentication endpoints.
    Default: 5 requests per 5 minutes per IP.
    """
    def decorator(func):
        def wrapper(request: Request, *args, **kwargs):
            client_ip = get_client_ip(request)
            key = f"auth:{client_ip}"
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                remaining = rate_limiter.get_remaining_requests(key, max_requests, window_seconds)
                reset_time = rate_limiter.get_reset_time(key, window_seconds)
                
                # Calculate seconds until reset
                retry_after = int(reset_time - time.time()) if reset_time else window_seconds
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Too many authentication attempts. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit_general(max_requests: int = 100, window_seconds: int = 60):
    """
    General rate limit decorator.
    Default: 100 requests per minute per IP.
    """
    def decorator(func):
        def wrapper(request: Request, *args, **kwargs):
            client_ip = get_client_ip(request)
            key = f"general:{client_ip}"
            
            if not rate_limiter.is_allowed(key, max_requests, window_seconds):
                remaining = rate_limiter.get_remaining_requests(key, max_requests, window_seconds)
                reset_time = rate_limiter.get_reset_time(key, window_seconds)
                
                retry_after = int(reset_time - time.time()) if reset_time else window_seconds
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def check_rate_limit(request: Request, key_prefix: str, max_requests: int, window_seconds: int) -> None:
    """
    Check rate limit and raise HTTPException if exceeded.
    """
    client_ip = get_client_ip(request)
    key = f"{key_prefix}:{client_ip}"
    
    if not rate_limiter.is_allowed(key, max_requests, window_seconds):
        remaining = rate_limiter.get_remaining_requests(key, max_requests, window_seconds)
        reset_time = rate_limiter.get_reset_time(key, window_seconds)
        
        retry_after = int(reset_time - time.time()) if reset_time else window_seconds
        
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )