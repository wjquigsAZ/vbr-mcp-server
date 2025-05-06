#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP, Context
import os
import requests
import json
import sys
import logging
from time import sleep
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Set up logging
from datetime import datetime
now = datetime.now()
current_time = now.strftime("%Y-%m-%d_%H-%M-%S")
os.makedirs('logs', exist_ok=True)
logfile = f'logs/vbr_tools_{current_time}.log'
logging.basicConfig(
    filename=logfile,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("vbr")

# Get environment variables
VBR_API_URL = os.getenv('VBR_API_URL', 'https://10.1.1.1:9419')
VBR_USERNAME = os.getenv('VBR_USERNAME')
VBR_PASSWORD = os.getenv('VBR_PASSWORD')

def get_vbr_session():
    """Create a session with the VBR API"""
    logger.info("Creating VBR API session")
    session = requests.Session()
    session.verify = False  # Disable SSL verification
    
    # Check if credentials are provided
    if not VBR_USERNAME or not VBR_PASSWORD:
        logger.warning("VBR credentials not provided. Some operations may fail.")
        return session
    
    # Authenticate with the VBR API
    try:
        auth_url = f"{VBR_API_URL}/api/oauth2/token"
        auth_data = {
            "grant_type": "password",
            "username": VBR_USERNAME,
            "password": VBR_PASSWORD
        }
        headers = {
            "x-api-version": "1.2-rev0",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = session.post(auth_url, headers=headers, data=auth_data)
        response.raise_for_status()
        
        token_data = response.json()
        session.headers.update({
            "Authorization": f"Bearer {token_data['access_token']}"
        })
        logger.info("Successfully authenticated with VBR API")
    except Exception as e:
        logger.error(f"Error authenticating with VBR API: {str(e)}")
    
    return session

@mcp.tool()
def list_vbr_repositories() -> str:
    """Lists all repositories in the VBR system.
    
    Returns:
        str: JSON string containing the list of repositories
    """
    logger.info("Listing VBR repositories")
    try:
        session = get_vbr_session()
        
        # Add required API version header
        headers = {
            "x-api-version": "1.2-rev0"  # Required header as per API documentation
        }
        
        # Try different repository endpoints
        repository_endpoints = [
            "/api/v1/backupInfrastructure/repositories",
            "/api/v1/repositories",
            "/api/repositories"
        ]
        
        for endpoint in repository_endpoints:
            url = f"{VBR_API_URL}{endpoint}"
            logger.info(f"Trying repository endpoint: {url}")
            
            try:
                response = session.get(url, headers=headers)
                if response.status_code == 200:
                    repositories = response.json()
                    logger.info(f"Found {len(repositories)} repositories")
                    return json.dumps(repositories, indent=2)
                else:
                    logger.warning(f"Endpoint {endpoint} returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Error with endpoint {endpoint}: {str(e)}")
                continue
        
        error_msg = "No valid repository endpoint found"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error listing repositories: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def get_repository_details(id: str) -> str:
    """Gets detailed information about a specific repository.
    
    Args:
        id: The ID of the repository to get details for
        
    Returns:
        str: JSON string containing repository details
    """
    logger.info(f"Getting details for repository ID: {id}")
    try:
        session = get_vbr_session()
        
        # Add required API version header
        headers = {
            "x-api-version": "1.2-rev0"  # Required header as per API documentation
        }
        
        # Try different repository endpoints
        repository_endpoints = [
            f"/api/v1/backupInfrastructure/repositories/{id}",
            f"/api/v1/repositories/{id}",
            f"/api/repositories/{id}"
        ]
        
        for endpoint in repository_endpoints:
            url = f"{VBR_API_URL}{endpoint}"
            logger.info(f"Trying repository details endpoint: {url}")
            
            try:
                response = session.get(url, headers=headers)
                if response.status_code == 200:
                    repository = response.json()
                    logger.info(f"Successfully retrieved details for repository {id}")
                    return json.dumps(repository, indent=2)
                else:
                    logger.warning(f"Endpoint {endpoint} returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Error with endpoint {endpoint}: {str(e)}")
                continue
        
        error_msg = f"No valid repository details endpoint found for ID {id}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error getting repository details: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def list_backup_jobs(repository_id: str = None) -> str:
    """Lists backup jobs, optionally filtered by repository ID.
    
    Args:
        repository_id: Optional repository ID to filter jobs
        
    Returns:
        str: JSON string containing the list of backup jobs
    """
    logger.info(f"Listing backup jobs" + (f" for repository {repository_id}" if repository_id else ""))
    try:
        session = get_vbr_session()
        
        # Add required API version header
        headers = {
            "x-api-version": "1.2-rev0"  # Required header as per API documentation
        }
        
        # Try different job endpoints
        job_endpoints = [
            "/api/v1/jobs",
            "/api/v1/backupInfrastructure/jobs",
            "/api/jobs"
        ]
        
        for endpoint in job_endpoints:
            url = f"{VBR_API_URL}{endpoint}"
            logger.info(f"Trying jobs endpoint: {url}")
            
            params = {}
            if repository_id:
                params['repositoryId'] = repository_id
                
            try:
                response = session.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    jobs = response.json()
                    logger.info(f"Found {len(jobs)} backup jobs")
                    return json.dumps(jobs, indent=2)
                else:
                    logger.warning(f"Endpoint {endpoint} returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Error with endpoint {endpoint}: {str(e)}")
                continue
        
        error_msg = "No valid jobs endpoint found"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error listing backup jobs: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    logger.info("Starting VBR tools server")
    # Initialize and run the server
    mcp.run(transport='stdio')
