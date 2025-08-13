#!/usr/bin/env python3
"""
AWS Secrets Manager Utility Module

This module provides functions to securely retrieve secrets from AWS Secrets Manager.
"""

import boto3
import json
import logging
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, region_name: str = 'ap-southeast-2') -> Optional[str]:
    """
    Retrieve a secret from AWS Secrets Manager
    
    Args:
        secret_name: The name of the secret in AWS Secrets Manager
        region_name: The AWS region where the secret is stored
        
    Returns:
        The secret value as a string, or None if retrieval fails
    """
    try:
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        # Get the secret
        response = client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret
        if 'SecretString' in response:
            secret = response['SecretString']
            # If the secret is JSON, parse it
            try:
                secret_dict = json.loads(secret)
                # If it's a dictionary, return the first value or the whole dict
                if isinstance(secret_dict, dict):
                    # For simple key-value secrets, return the first value
                    if len(secret_dict) == 1:
                        return list(secret_dict.values())[0]
                    # For complex secrets, return the whole dict as JSON string
                    return json.dumps(secret_dict)
                else:
                    return secret
            except json.JSONDecodeError:
                # If it's not JSON, return as-is
                return secret
        else:
            # Binary secret
            import base64
            decoded_binary_secret = base64.b64decode(response['SecretBinary'])
            return decoded_binary_secret.decode('utf-8')
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DecryptionFailureException':
            logger.error(f"Secrets Manager can't decrypt the protected secret text using the provided KMS key: {e}")
        elif error_code == 'InternalServiceErrorException':
            logger.error(f"An error occurred on the server side: {e}")
        elif error_code == 'InvalidParameterException':
            logger.error(f"You provided an invalid value for a parameter: {e}")
        elif error_code == 'InvalidRequestException':
            logger.error(f"You provided a parameter value that is not valid for the current state of the resource: {e}")
        elif error_code == 'ResourceNotFoundException':
            logger.error(f"Secret {secret_name} not found in AWS Secrets Manager: {e}")
        else:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
        return None
    except NoCredentialsError:
        logger.error("AWS credentials not found. Make sure you have configured AWS credentials.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
        return None

def get_private_gpt4_api_key() -> Optional[str]:
    """
    Retrieve the Private GPT-4 API key from AWS Secrets Manager
    
    Returns:
        The Private GPT-4 API key as a string, or None if retrieval fails
    """
    return get_secret('legal-rag/private-gpt4-api-key')

def get_anthropic_api_key() -> Optional[str]:
    """
    Retrieve the Anthropic API key from AWS Secrets Manager
    
    Returns:
        The Anthropic API key as a string, or None if retrieval fails
    """
    return get_secret('legal-rag/anthropic-api-key')

def get_openai_api_key() -> Optional[str]:
    """
    Retrieve the OpenAI API key from AWS Secrets Manager
    
    Returns:
        The OpenAI API key as a string, or None if retrieval fails
    """
    return get_secret('legal-rag/openai-api-key')

def get_google_api_key() -> Optional[str]:
    """
    Retrieve the Google API key from AWS Secrets Manager
    
    Returns:
        The Google API key as a string, or None if retrieval fails
    """
    return get_secret('legal-rag/google-api-key')

def get_secret_key() -> Optional[str]:
    """
    Retrieve the Flask secret key from AWS Secrets Manager
    
    Returns:
        The Flask secret key as a string, or None if retrieval fails
    """
    return get_secret('legal-rag/secret-key')
