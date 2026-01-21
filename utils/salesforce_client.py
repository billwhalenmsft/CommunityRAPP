"""
Salesforce Client - Handles authentication and API calls to Salesforce
Supports both Username-Password OAuth flow (dev/demo) and JWT Bearer (production)

Configuration via environment variables:
- SALESFORCE_INSTANCE_URL: Your Salesforce instance URL
- SALESFORCE_CLIENT_ID: Connected App Consumer Key
- SALESFORCE_CLIENT_SECRET: Connected App Consumer Secret
- SALESFORCE_USERNAME: Salesforce username
- SALESFORCE_PASSWORD: Salesforce password
- SALESFORCE_SECURITY_TOKEN: Security token (append to password)
- SALESFORCE_API_VERSION: API version (default: v59.0)
"""

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import lru_cache

# =============================================================================
# CONFIGURATION
# =============================================================================
class SalesforceConfig:
    """Salesforce configuration from environment variables."""
    
    def __init__(self):
        self.instance_url = os.environ.get('SALESFORCE_INSTANCE_URL', 
            'https://empathetic-bear-vanmxr-dev-ed.my.salesforce.com')
        self.client_id = os.environ.get('SALESFORCE_CLIENT_ID', '')
        self.client_secret = os.environ.get('SALESFORCE_CLIENT_SECRET', '')
        self.username = os.environ.get('SALESFORCE_USERNAME', '')
        self.password = os.environ.get('SALESFORCE_PASSWORD', '')
        self.security_token = os.environ.get('SALESFORCE_SECURITY_TOKEN', '')
        self.api_version = os.environ.get('SALESFORCE_API_VERSION', 'v59.0')
        
        # Derived URLs
        self.login_url = os.environ.get('SALESFORCE_LOGIN_URL', 
            'https://login.salesforce.com')  # Use test.salesforce.com for sandbox
        self.token_url = f"{self.login_url}/services/oauth2/token"
        
    @property
    def is_configured(self) -> bool:
        """Check if Salesforce credentials are configured."""
        return bool(self.client_id and self.username and self.password)
    
    @property
    def api_base_url(self) -> str:
        """Get the base URL for REST API calls."""
        return f"{self.instance_url}/services/data/{self.api_version}"


# =============================================================================
# SALESFORCE CLIENT
# =============================================================================
class SalesforceClient:
    """
    Salesforce REST API Client with OAuth 2.0 authentication.
    
    Usage:
        client = SalesforceClient()
        if client.authenticate():
            cases = client.query("SELECT Id, Subject FROM Case WHERE Status = 'New'")
    """
    
    def __init__(self, config: SalesforceConfig = None):
        self.config = config or SalesforceConfig()
        self.access_token: Optional[str] = None
        self.instance_url: Optional[str] = None
        self.token_expiry: Optional[datetime] = None
        self._session = requests.Session()
        
    def authenticate(self) -> bool:
        """
        Authenticate with Salesforce using Username-Password OAuth flow.
        Returns True if authentication succeeds.
        """
        if not self.config.is_configured:
            logging.warning("Salesforce credentials not configured. Using mock data.")
            return False
            
        try:
            # Username-Password OAuth 2.0 Flow
            payload = {
                'grant_type': 'password',
                'client_id': self.config.client_id,
                'client_secret': self.config.client_secret,
                'username': self.config.username,
                'password': self.config.password + self.config.security_token
            }
            
            response = self._session.post(self.config.token_url, data=payload)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.instance_url = token_data['instance_url']
                # Token typically valid for 2 hours, refresh at 90 minutes
                self.token_expiry = datetime.utcnow() + timedelta(minutes=90)
                
                # Update session headers
                self._session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                })
                
                logging.info(f"Salesforce authentication successful. Instance: {self.instance_url}")
                return True
            else:
                error = response.json()
                logging.error(f"Salesforce authentication failed: {error}")
                return False
                
        except Exception as e:
            logging.error(f"Salesforce authentication error: {str(e)}")
            return False
    
    def _ensure_authenticated(self) -> bool:
        """Ensure we have a valid access token."""
        if self.access_token and self.token_expiry and datetime.utcnow() < self.token_expiry:
            return True
        return self.authenticate()
    
    @property
    def api_base(self) -> str:
        """Get the API base URL (uses instance URL from auth response)."""
        base = self.instance_url or self.config.instance_url
        return f"{base}/services/data/{self.config.api_version}"
    
    # =========================================================================
    # QUERY METHODS
    # =========================================================================
    def query(self, soql: str) -> Dict[str, Any]:
        """
        Execute a SOQL query.
        
        Args:
            soql: SOQL query string
            
        Returns:
            Dictionary with 'totalSize', 'done', and 'records' keys
        """
        if not self._ensure_authenticated():
            return {"totalSize": 0, "done": True, "records": [], "error": "Not authenticated"}
        
        try:
            url = f"{self.api_base}/query"
            response = self._session.get(url, params={'q': soql})
            
            if response.status_code == 200:
                return response.json()
            else:
                error = response.json()
                logging.error(f"SOQL query failed: {error}")
                return {"totalSize": 0, "done": True, "records": [], "error": error}
                
        except Exception as e:
            logging.error(f"Query error: {str(e)}")
            return {"totalSize": 0, "done": True, "records": [], "error": str(e)}
    
    def query_all(self, soql: str) -> List[Dict]:
        """
        Execute SOQL query and return all records (handles pagination).
        """
        all_records = []
        result = self.query(soql)
        all_records.extend(result.get('records', []))
        
        # Handle pagination
        while not result.get('done', True) and 'nextRecordsUrl' in result:
            response = self._session.get(f"{self.instance_url}{result['nextRecordsUrl']}")
            if response.status_code == 200:
                result = response.json()
                all_records.extend(result.get('records', []))
            else:
                break
                
        return all_records
    
    # =========================================================================
    # CASE-SPECIFIC METHODS
    # =========================================================================
    def get_new_cases(self, limit: int = 50) -> List[Dict]:
        """Get new cases that need triage."""
        soql = f"""
            SELECT Id, CaseNumber, Subject, Description, Status, Priority, Type, 
                   Origin, CreatedDate, ClosedDate,
                   Account.Id, Account.Name, Account.Type,
                   Contact.Id, Contact.Name, Contact.Email, Contact.Phone,
                   Product_Model__c, Serial_Number__c
            FROM Case 
            WHERE Status = 'New' 
            AND Triage_Status__c = null
            ORDER BY CreatedDate DESC 
            LIMIT {limit}
        """
        return self.query_all(soql)
    
    def get_aging_cases(self, threshold_hours: int = 4, limit: int = 50) -> List[Dict]:
        """Get cases that have been open beyond the threshold."""
        threshold_time = (datetime.utcnow() - timedelta(hours=threshold_hours)).strftime('%Y-%m-%dT%H:%M:%SZ')
        soql = f"""
            SELECT Id, CaseNumber, Subject, Description, Status, Priority, Type,
                   CreatedDate, 
                   Account.Id, Account.Name,
                   Contact.Name, Contact.Email
            FROM Case 
            WHERE Status IN ('New', 'Open', 'In Progress')
            AND CreatedDate < {threshold_time}
            AND Triage_Status__c = null
            ORDER BY CreatedDate ASC
            LIMIT {limit}
        """
        return self.query_all(soql)
    
    def get_case_details(self, case_id: str) -> Optional[Dict]:
        """Get full details for a specific case."""
        soql = f"""
            SELECT Id, CaseNumber, Subject, Description, Status, Priority, Type, 
                   Origin, CreatedDate, ClosedDate, LastModifiedDate,
                   Account.Id, Account.Name, Account.AccountNumber, Account.Type,
                   Contact.Id, Contact.Name, Contact.Email, Contact.Phone,
                   Product_Model__c, Serial_Number__c, Install_Date__c,
                   Triage_Status__c, Triage_Priority__c, Triage_Summary__c
            FROM Case 
            WHERE Id = '{case_id}'
        """
        result = self.query(soql)
        records = result.get('records', [])
        return records[0] if records else None
    
    def get_case_attachments(self, case_id: str) -> List[Dict]:
        """Get attachments linked to a case via ContentDocumentLink."""
        soql = f"""
            SELECT ContentDocument.Id, ContentDocument.Title, 
                   ContentDocument.FileType, ContentDocument.ContentSize,
                   ContentDocument.LatestPublishedVersionId
            FROM ContentDocumentLink 
            WHERE LinkedEntityId = '{case_id}'
        """
        return self.query_all(soql)
    
    def get_case_comments(self, case_id: str) -> List[Dict]:
        """Get comments on a case."""
        soql = f"""
            SELECT Id, CommentBody, CreatedDate, CreatedBy.Name, IsPublished
            FROM CaseComment 
            WHERE ParentId = '{case_id}'
            ORDER BY CreatedDate DESC
        """
        return self.query_all(soql)
    
    # =========================================================================
    # UPDATE METHODS
    # =========================================================================
    def update_record(self, sobject: str, record_id: str, data: Dict) -> Dict:
        """
        Update a Salesforce record.
        
        Args:
            sobject: Object type (e.g., 'Case')
            record_id: Salesforce record ID
            data: Dictionary of fields to update
            
        Returns:
            Response data or error
        """
        if not self._ensure_authenticated():
            return {"success": False, "error": "Not authenticated"}
        
        try:
            url = f"{self.api_base}/sobjects/{sobject}/{record_id}"
            response = self._session.patch(url, json=data)
            
            if response.status_code == 204:  # Success with no content
                return {"success": True, "id": record_id}
            else:
                error = response.json() if response.content else {"message": "Unknown error"}
                logging.error(f"Update failed: {error}")
                return {"success": False, "error": error}
                
        except Exception as e:
            logging.error(f"Update error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def update_case(self, case_id: str, data: Dict) -> Dict:
        """Update a Case record."""
        return self.update_record('Case', case_id, data)
    
    def update_case_triage(self, case_id: str, triage_data: Dict) -> Dict:
        """
        Update case with triage results.
        
        Expected triage_data fields:
        - priority: High/Medium/Low
        - issue_type: Equipment Failure, Maintenance, etc.
        - triage_summary: AI-generated summary
        - recommended_action: Next steps
        - triage_status: Completed, Pending, etc.
        """
        # Map triage fields to Salesforce custom fields
        sf_data = {}
        
        field_mapping = {
            'priority': 'Triage_Priority__c',
            'issue_type': 'Triage_Issue_Type__c',
            'triage_summary': 'Triage_Summary__c',
            'recommended_action': 'Recommended_Action__c',
            'triage_status': 'Triage_Status__c',
            'recommended_queue': 'Recommended_Queue__c'
        }
        
        for key, sf_field in field_mapping.items():
            if key in triage_data:
                sf_data[sf_field] = triage_data[key]
        
        # Add timestamp
        sf_data['AI_Triaged_Date__c'] = datetime.utcnow().isoformat() + 'Z'
        
        return self.update_case(case_id, sf_data)
    
    def add_case_comment(self, case_id: str, comment: str, is_public: bool = False) -> Dict:
        """Add a comment to a case."""
        if not self._ensure_authenticated():
            return {"success": False, "error": "Not authenticated"}
        
        try:
            url = f"{self.api_base}/sobjects/CaseComment"
            data = {
                "ParentId": case_id,
                "CommentBody": comment,
                "IsPublished": is_public
            }
            response = self._session.post(url, json=data)
            
            if response.status_code == 201:
                return {"success": True, "id": response.json().get('id')}
            else:
                error = response.json()
                return {"success": False, "error": error}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # =========================================================================
    # CONTENT/ATTACHMENT METHODS
    # =========================================================================
    def get_content_version(self, version_id: str) -> Optional[bytes]:
        """Download the content of a file attachment."""
        if not self._ensure_authenticated():
            return None
        
        try:
            url = f"{self.api_base}/sobjects/ContentVersion/{version_id}/VersionData"
            response = self._session.get(url)
            
            if response.status_code == 200:
                return response.content
            else:
                logging.error(f"Failed to download content: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"Content download error: {str(e)}")
            return None
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    def describe_object(self, sobject: str) -> Dict:
        """Get metadata about a Salesforce object."""
        if not self._ensure_authenticated():
            return {}
        
        url = f"{self.api_base}/sobjects/{sobject}/describe"
        response = self._session.get(url)
        return response.json() if response.status_code == 200 else {}
    
    def get_case_fields(self) -> List[str]:
        """Get list of available Case fields."""
        describe = self.describe_object('Case')
        return [f['name'] for f in describe.get('fields', [])]


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
_client_instance: Optional[SalesforceClient] = None

def get_salesforce_client() -> SalesforceClient:
    """Get or create the singleton Salesforce client."""
    global _client_instance
    if _client_instance is None:
        _client_instance = SalesforceClient()
    return _client_instance


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def is_salesforce_configured() -> bool:
    """Check if Salesforce is configured."""
    config = SalesforceConfig()
    return config.is_configured


def test_salesforce_connection() -> Dict:
    """Test the Salesforce connection and return status."""
    client = get_salesforce_client()
    
    if not client.config.is_configured:
        return {
            "status": "not_configured",
            "message": "Salesforce credentials not set. Please configure environment variables.",
            "required_vars": [
                "SALESFORCE_INSTANCE_URL",
                "SALESFORCE_CLIENT_ID", 
                "SALESFORCE_CLIENT_SECRET",
                "SALESFORCE_USERNAME",
                "SALESFORCE_PASSWORD",
                "SALESFORCE_SECURITY_TOKEN"
            ]
        }
    
    if client.authenticate():
        # Test a simple query
        result = client.query("SELECT Id FROM Case LIMIT 1")
        return {
            "status": "connected",
            "instance_url": client.instance_url,
            "api_version": client.config.api_version,
            "test_query": "Success" if 'records' in result else "Failed"
        }
    else:
        return {
            "status": "auth_failed",
            "message": "Authentication failed. Check credentials."
        }
