"""HubSpot Segment Manager Agent - Creates and manages contact segments."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import requests
from agents.base_agent import BaseAgent, AgentConfig, AgentContext


class SegmentManagerAgent(BaseAgent):
    """Agent for managing HubSpot contact segments and lists.
    
    Capabilities:
    - Create contact segments based on criteria
    - Update existing segments
    - Query segment membership
    - Manage segment filters
    - Create "Fecha de creación = Hoy" segments
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        context: Optional[AgentContext] = None
    ):
        """Initialize HubSpot Segment Manager Agent.
        
        Args:
            config: Agent configuration (uses default if not provided)
            context: Execution context
        """
        if config is None:
            config = AgentConfig(
                name="HubSpotSegmentManager",
                description="Manages HubSpot contact segments and lists",
                model="gpt-4",
                temperature=0.3
            )
        
        super().__init__(config, context)

        # Get HubSpot API key from environment
        self.api_key = os.getenv("HUBSPOT_API_KEY")
        self.base_url = "https://api.hubapi.com"

        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY environment variable not set")
    
    def get_system_prompt(self) -> str:
        """Return system prompt for HubSpot segment management.
        
        Returns:
            System prompt string
        """
        return (
            "You are a HubSpot Segment Manager agent specialized in "
            "creating and managing contact segments.\n"
            "Your capabilities:\n"
            "1. Create new contact segments with specific criteria\n"
            "2. Update existing segment filters\n"
            "3. Query contacts in segments\n"
            "4. Create date-based segments (e.g., 'Fecha de creación = Hoy')\n"
            "5. Manage segment membership\n"
            "When creating segments:\n"
            "- Use clear, descriptive names\n"
            "- Set appropriate filter criteria\n"
            "- Validate filter logic before creation\n"
            "- Handle API rate limits gracefully\n"
            "For 'Fecha de creación = Hoy' segments:\n"
            "- Use 'createdate' property\n"
            "- Set filter to 'TODAY' or current date\n"
            "- Name segment appropriately with date\n"
            "Always:\n"
            "- Verify segment creation was successful\n"
            "- Return segment IDs and URLs\n"
            "- Log all operations\n"
            "- Handle errors with clear messages\n"
        )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Return list of available HubSpot tools.
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "name": "create_segment",
                "description": "Create a new contact segment/list in HubSpot",
                "parameters": {
                    "name": "Segment name",
                    "filters": "Filter criteria (property, operator, value)"
                }
            },
            {
                "name": "create_today_segment",
                "description": "Create segment for contacts created today",
                "parameters": {
                    "name_suffix": "Optional suffix for segment name"
                }
            },
            {
                "name": "list_segments",
                "description": "List all contact segments",
                "parameters": {}
            },
            {
                "name": "get_segment_contacts",
                "description": "Get contacts in a specific segment",
                "parameters": {
                    "list_id": "Segment/list ID"
                }
            },
            {
                "name": "update_segment",
                "description": "Update segment filters or properties",
                "parameters": {
                    "list_id": "Segment/list ID",
                    "updates": "Updated properties"
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a HubSpot segment management tool.
        
        Args:
            tool_name: Name of tool to execute
            tool_input: Tool input parameters
            
        Returns:
            Tool execution result
        """
        try:
            if tool_name == "create_segment":
                return self._create_segment(
                    name=tool_input.get("name"),
                    filters=tool_input.get("filters", [])
                )
            
            elif tool_name == "create_today_segment":
                return self._create_today_segment(
                    name_suffix=tool_input.get("name_suffix", "")
                )
            
            elif tool_name == "list_segments":
                return self._list_segments()
            
            elif tool_name == "get_segment_contacts":
                return self._get_segment_contacts(
                    list_id=tool_input.get("list_id")
                )
            
            elif tool_name == "update_segment":
                return self._update_segment(
                    list_id=tool_input.get("list_id"),
                    updates=tool_input.get("updates", {})
                )
            
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        
        except Exception as e:
                return {"error": f"Tool execution failed: {str(e)}"}
    
    def _get_auth_headers_and_params(
        self
    ) -> tuple[Dict[str, str], Dict[str, str]]:
        """Get authentication headers and parameters based on API key type."""
        headers = {"Content-Type": "application/json"}
        params = {}
        
        if self.api_key.startswith("pat-"):
            # Private App Access Token
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            # Legacy API Key
            params["hapikey"] = self.api_key
            
        return headers, params

    def _create_segment(
        self,
        name: str,
        filters: List[Dict]
    ) -> Dict[str, Any]:
        """Create a new contact segment.
        
        Args:
            name: Segment name
            filters: List of filter criteria
            
        Returns:
            Created segment information
        """
        url = f"{self.base_url}/contacts/v1/lists"
        
        payload = {
            "name": name,
            "dynamic": True,  # Dynamic list (auto-updates)
            "filters": filters
        }
        
        headers, params = self._get_auth_headers_and_params()
        
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "list_id": data.get("listId"),
                "name": data.get("name"),
                "url": f"https://app.hubspot.com/contacts/lists/{data.get('listId')}",
                "filters": data.get("filters")
            }
        else:
            return {
                "success": False,
                "error": (
                    f"Failed to create segment: {response.status_code} - "
                    f"{response.text}"
                )
            }
    
    def _create_today_segment(self, name_suffix: str = "") -> Dict[str, Any]:
        """Create a segment for contacts created today.
        
        Args:
            name_suffix: Optional suffix for segment name
            
        Returns:
            Created segment information
        """
        today = datetime.now().strftime("%Y-%m-%d")
        segment_name = f"Fecha de creación = Hoy ({today})"
        if name_suffix:
            segment_name += f" - {name_suffix}"

        # Filter for contacts created today
        filters = [[{
            "property": "createdate",
            "operator": "EQ",
            "value": "TODAY"
        }]]

        return self._create_segment(name=segment_name, filters=filters)
    
    def _list_segments(self) -> Dict[str, Any]:
        """List all contact segments.
        
        Returns:
            List of segments
        """
        url = f"{self.base_url}/contacts/v1/lists"
        
        headers, params = self._get_auth_headers_and_params()
        
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            lists = data.get("lists", [])
            
            return {
                "success": True,
                "count": len(lists),
                "segments": [
                    {
                        "id": lst.get("listId"),
                        "name": lst.get("name"),
                        "size": lst.get("metaData", {}).get("size", 0),
                        "dynamic": lst.get("dynamic", False)
                    }
                    for lst in lists
                ]
            }
        else:
            return {
                "success": False,
                "error": f"Failed to list segments: {response.status_code}"
            }
    
    def _get_segment_contacts(self, list_id: str) -> Dict[str, Any]:
        """Get contacts in a specific segment.
        
        Args:
            list_id: Segment/list ID
            
        Returns:
            Segment contacts
        """
        url = f"{self.base_url}/contacts/v1/lists/{list_id}/contacts/all"

        headers, params = self._get_auth_headers_and_params()

        params["count"] = 100  # Max per page

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get("contacts", [])
            
            return {
                "success": True,
                "count": len(contacts),
                "has_more": data.get("has-more", False),
                "contacts": [
                    {
                        "id": contact.get("vid"),
                        "email": contact.get("identity-profiles", [{}])[0].get("identities", [{}])[0].get("value"),
                        "properties": contact.get("properties", {})
                    }
                    for contact in contacts
                ]
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get contacts: {response.status_code}"
            }
    
    def _update_segment(
        self,
        list_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update segment properties.
        
        Args:
            list_id: Segment/list ID
            updates: Properties to update
            
        Returns:
            Update result
        """
        url = f"{self.base_url}/contacts/v1/lists/{list_id}"
        
        headers, params = self._get_auth_headers_and_params()
        
        response = requests.post(url, json=updates, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "list_id": list_id,
                "message": "Segment updated successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to update segment: {response.status_code}"
            }
