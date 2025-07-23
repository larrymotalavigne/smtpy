"""CSRF protection utilities for SMTPy."""

import secrets
from typing import Optional
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException
from config import SETTINGS


class CSRFProtect:
    """CSRF protection utility class."""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or SETTINGS.SECRET_KEY
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        self.token_max_age = 3600  # 1 hour
    
    def generate_csrf_token(self, session_id: str = None) -> str:
        """Generate a CSRF token for the given session."""
        if not session_id:
            session_id = secrets.token_urlsafe(16)
        
        # Create a token that includes session info
        token_data = {
            'session_id': session_id,
            'nonce': secrets.token_urlsafe(16)
        }
        
        return self.serializer.dumps(token_data)
    
    def validate_csrf_token(self, token: str, session_id: str = None) -> bool:
        """Validate a CSRF token."""
        if not token:
            return False
        
        try:
            token_data = self.serializer.loads(token, max_age=self.token_max_age)
            
            # If session_id is provided, validate it matches
            if session_id and token_data.get('session_id') != session_id:
                return False
            
            return True
        except (BadSignature, SignatureExpired):
            return False
    
    def get_csrf_token_from_request(self, request: Request) -> Optional[str]:
        """Extract CSRF token from request (form data or headers)."""
        # Try to get from form data first
        if hasattr(request, '_form'):
            form_data = request._form
            if 'csrf_token' in form_data:
                return form_data['csrf_token']
        
        # Try to get from headers
        return request.headers.get('X-CSRF-Token')
    
    def require_csrf_token(self, request: Request, token: str = None) -> None:
        """Require and validate CSRF token, raise HTTPException if invalid."""
        if not token:
            token = self.get_csrf_token_from_request(request)
        
        if not token:
            raise HTTPException(status_code=403, detail="CSRF token missing")
        
        # Get session ID from request session
        session_id = request.session.get('csrf_session_id')
        
        if not self.validate_csrf_token(token, session_id):
            raise HTTPException(status_code=403, detail="CSRF token invalid")


# Global CSRF protection instance
csrf_protect = CSRFProtect()


def get_csrf_token(request: Request) -> str:
    """Get or generate CSRF token for the current session."""
    # Get or create session ID for CSRF
    if 'csrf_session_id' not in request.session:
        request.session['csrf_session_id'] = secrets.token_urlsafe(16)
    
    session_id = request.session['csrf_session_id']
    return csrf_protect.generate_csrf_token(session_id)


def validate_csrf(request: Request, token: str = None) -> None:
    """Validate CSRF token from request."""
    csrf_protect.require_csrf_token(request, token)