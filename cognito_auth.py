import os
import json
import requests
import jwt
from functools import wraps
from flask import request, jsonify, session, redirect, url_for
import boto3
from botocore.exceptions import ClientError

# Cognito configuration
COGNITO_USER_POOL_ID = 'ap-southeast-2_nE3GDTq9a'
COGNITO_CLIENT_ID = '5cbftujsn7j6vbmtfv6corljbj'
COGNITO_DOMAIN = 'legal-rag-auth'
COGNITO_REGION = 'ap-southeast-2'

# Cognito endpoints
COGNITO_DOMAIN_URL = f'https://{COGNITO_DOMAIN}.auth.{COGNITO_REGION}.amazoncognito.com'
AUTHORIZATION_ENDPOINT = f'{COGNITO_DOMAIN_URL}/oauth2/authorize'
TOKEN_ENDPOINT = f'{COGNITO_DOMAIN_URL}/oauth2/token'
USERINFO_ENDPOINT = f'{COGNITO_DOMAIN_URL}/oauth2/userInfo'
LOGOUT_ENDPOINT = f'{COGNITO_DOMAIN_URL}/logout'

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)

def get_cognito_public_keys():
    """Get Cognito public keys for JWT verification"""
    try:
        response = requests.get(f'{COGNITO_DOMAIN_URL}/.well-known/jwks.json')
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Cognito public keys: {e}")
        return None

def verify_jwt_token(token):
    """Verify JWT token from Cognito"""
    try:
        # Decode token without verification first to get the key ID
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get('kid')
        
        # Get public keys
        public_keys = get_cognito_public_keys()
        if not public_keys:
            return None
        
        # Find the correct public key
        public_key = None
        for key in public_keys['keys']:
            if key['kid'] == key_id:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
                break
        
        if not public_key:
            return None
        
        # Verify and decode the token
        decoded = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=COGNITO_CLIENT_ID,
            issuer=f'https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}'
        )
        
        return decoded
    except Exception as e:
        print(f"Error verifying JWT token: {e}")
        return None

def get_user_info(access_token):
    """Get user information from Cognito"""
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(USERINFO_ENDPOINT, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error getting user info: {e}")
        return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if authentication is disabled for local development
        if os.getenv('DISABLE_AUTH', 'false').lower() == 'true':
            return f(*args, **kwargs)
        
        # Check if user is authenticated via session
        if 'user_info' in session:
            return f(*args, **kwargs)
        
        # Check for authorization header (for API calls)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_info = verify_jwt_token(token)
            if user_info:
                return f(*args, **kwargs)
        
        # Redirect to login for web requests
        # Check if it's a web request (not an API request)
        is_web_request = (
            request.headers.get('Accept', '').startswith('text/html') or
            'text/html' in request.headers.get('Accept', '') or
            request.headers.get('User-Agent', '').startswith('Mozilla') or
            request.headers.get('User-Agent', '').startswith('Chrome') or
            request.headers.get('User-Agent', '').startswith('Safari') or
            request.headers.get('User-Agent', '').startswith('Firefox')
        )
        
        if is_web_request:
            return redirect(url_for('login'))
        
        # Return 401 for API requests
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function

def get_login_url(redirect_uri=None):
    """Generate Cognito login URL"""
    if not redirect_uri:
        redirect_uri = f"{request.url_root.rstrip('/')}/callback"
    
    params = {
        'response_type': 'code',
        'client_id': COGNITO_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'state': 'state'  # You might want to generate a random state
    }
    
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    return f'{AUTHORIZATION_ENDPOINT}?{query_string}'

def get_logout_url(redirect_uri=None):
    """Generate Cognito logout URL"""
    if not redirect_uri:
        redirect_uri = request.url_root.rstrip('/')
    
    params = {
        'client_id': COGNITO_CLIENT_ID,
        'logout_uri': redirect_uri
    }
    
    query_string = '&'.join([f'{k}={v}' for k, v in params.items()])
    return f'{LOGOUT_ENDPOINT}?{query_string}'

def exchange_code_for_tokens(authorization_code, redirect_uri):
    """Exchange authorization code for tokens"""
    try:
        data = {
            'grant_type': 'authorization_code',
            'client_id': COGNITO_CLIENT_ID,
            'code': authorization_code,
            'redirect_uri': redirect_uri
        }
        
        response = requests.post(TOKEN_ENDPOINT, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error exchanging code for tokens: {e}")
        return None

def refresh_access_token(refresh_token):
    """Refresh access token using refresh token"""
    try:
        data = {
            'grant_type': 'refresh_token',
            'client_id': COGNITO_CLIENT_ID,
            'refresh_token': refresh_token
        }
        
        response = requests.post(TOKEN_ENDPOINT, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error refreshing access token: {e}")
        return None 