"""
Model Context Protocol (MCP) Server for Therapy Assistant
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class MCPMessageType(Enum):
    """MCP message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"

@dataclass
class MCPRequest:
    """MCP request structure"""
    id: str
    method: str
    params: Dict[str, Any]
    jsonrpc: str = "2.0"

@dataclass
class MCPResponse:
    """MCP response structure"""
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    jsonrpc: str = "2.0"

@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]

class TherapyMCPServer:
    """MCP Server for therapy assistant clinical tools"""
    
    def __init__(self):
        self.tools = self._initialize_tools()
        self.handlers = self._initialize_handlers()
    
    def _initialize_tools(self) -> List[MCPTool]:
        """Initialize available MCP tools"""
        return [
            MCPTool(
                name="search_clinical_guidelines",
                description="Search for clinical practice guidelines for specific conditions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "condition": {
                            "type": "string",
                            "description": "Mental health condition or disorder name"
                        },
                        "organization": {
                            "type": "string",
                            "description": "Specific organization guidelines (APA, WHO, NICE, etc.)",
                            "enum": ["APA", "WHO", "NICE", "SAMHSA", "any"]
                        },
                        "evidence_level": {
                            "type": "string",
                            "description": "Minimum evidence level required",
                            "enum": ["high", "moderate", "low", "any"]
                        }
                    },
                    "required": ["condition"]
                }
            ),
            
            MCPTool(
                name="get_diagnostic_criteria",
                description="Retrieve diagnostic criteria for mental health conditions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "disorder": {
                            "type": "string",
                            "description": "Name of the mental health disorder"
                        },
                        "classification_system": {
                            "type": "string",
                            "description": "Diagnostic classification system",
                            "enum": ["DSM-5-TR", "ICD-11", "both"]
                        }
                    },
                    "required": ["disorder"]
                }
            ),
            
            MCPTool(
                name="find_treatment_protocols",
                description="Find evidence-based treatment protocols for specific conditions",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "diagnosis": {
                            "type": "string",
                            "description": "Primary diagnosis or condition"
                        },
                        "modality": {
                            "type": "string",
                            "description": "Treatment modality preference",
                            "enum": ["CBT", "DBT", "psychodynamic", "medication", "combined", "any"]
                        },
                        "population": {
                            "type": "string",
                            "description": "Target population",
                            "enum": ["adult", "adolescent", "child", "elderly", "any"]
                        }
                    },
                    "required": ["diagnosis"]
                }
            ),
            
            MCPTool(
                name="validate_assessment_tool",
                description="Validate and get information about psychological assessment tools",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Name of the assessment tool or questionnaire"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Assessment purpose",
                            "enum": ["screening", "diagnosis", "symptom_tracking", "outcome_measurement"]
                        }
                    },
                    "required": ["tool_name"]
                }
            ),
            
            MCPTool(
                name="check_drug_interactions",
                description="Check for psychiatric medication interactions and contraindications",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "medications": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of current medications"
                        },
                        "new_medication": {
                            "type": "string",
                            "description": "New medication to check for interactions"
                        },
                        "medical_conditions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Relevant medical conditions"
                        }
                    },
                    "required": ["new_medication"]
                }
            ),
            
            MCPTool(
                name="get_crisis_resources",
                description="Get crisis intervention resources and protocols",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "crisis_type": {
                            "type": "string",
                            "description": "Type of crisis",
                            "enum": ["suicidal", "self_harm", "psychosis", "substance_abuse", "domestic_violence"]
                        },
                        "location": {
                            "type": "string",
                            "description": "Geographic location for local resources"
                        },
                        "immediate": {
                            "type": "boolean",
                            "description": "Whether this is an immediate crisis requiring emergency response"
                        }
                    },
                    "required": ["crisis_type"]
                }
            )
        ]
    
    def _initialize_handlers(self) -> Dict[str, callable]:
        """Initialize request handlers"""
        return {
            "tools/list": self._handle_list_tools,
            "tools/call": self._handle_call_tool,
            "resources/list": self._handle_list_resources,
            "resources/read": self._handle_read_resource,
            "prompts/list": self._handle_list_prompts,
            "prompts/get": self._handle_get_prompt
        }
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle incoming MCP request"""
        try:
            handler = self.handlers.get(request.method)
            if not handler:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                )
            
            result = await handler(request.params)
            return MCPResponse(id=request.id, result=result)
            
        except Exception as e:
            logger.error(f"Error handling MCP request {request.id}: {e}")
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [asdict(tool) for tool in self.tools]
        }
    
    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "search_clinical_guidelines":
            return await self._search_clinical_guidelines(arguments)
        elif tool_name == "get_diagnostic_criteria":
            return await self._get_diagnostic_criteria(arguments)
        elif tool_name == "find_treatment_protocols":
            return await self._find_treatment_protocols(arguments)
        elif tool_name == "validate_assessment_tool":
            return await self._validate_assessment_tool(arguments)
        elif tool_name == "check_drug_interactions":
            return await self._check_drug_interactions(arguments)
        elif tool_name == "get_crisis_resources":
            return await self._get_crisis_resources(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _search_clinical_guidelines(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search for clinical guidelines"""
        condition = args.get("condition")
        organization = args.get("organization", "any")
        evidence_level = args.get("evidence_level", "any")
        
        # Mock implementation - in real scenario, would query knowledge base
        guidelines = [
            {
                "title": f"Clinical Practice Guidelines for {condition}",
                "organization": "APA",
                "year": 2023,
                "evidence_level": "high",
                "url": f"https://www.apa.org/practice/guidelines/{condition.lower().replace(' ', '-')}",
                "summary": f"Evidence-based treatment recommendations for {condition}",
                "recommendations": [
                    "First-line treatment approaches",
                    "Assessment protocols",
                    "Monitoring guidelines"
                ]
            }
        ]
        
        return {
            "guidelines": guidelines,
            "total_found": len(guidelines),
            "search_criteria": {
                "condition": condition,
                "organization": organization,
                "evidence_level": evidence_level
            }
        }
    
    async def _get_diagnostic_criteria(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get diagnostic criteria for a disorder"""
        disorder = args.get("disorder")
        classification = args.get("classification_system", "DSM-5-TR")
        
        # Mock implementation
        criteria = {
            "disorder": disorder,
            "classification_system": classification,
            "criteria": [
                "Criterion A: Primary symptom cluster",
                "Criterion B: Duration requirements",
                "Criterion C: Functional impairment",
                "Criterion D: Exclusion criteria"
            ],
            "specifiers": ["Mild", "Moderate", "Severe"],
            "differential_diagnosis": [
                "Related disorder 1",
                "Related disorder 2"
            ]
        }
        
        return criteria
    
    async def _find_treatment_protocols(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Find treatment protocols"""
        diagnosis = args.get("diagnosis")
        modality = args.get("modality", "any")
        population = args.get("population", "adult")
        
        # Mock implementation
        protocols = [
            {
                "name": f"Cognitive Behavioral Therapy for {diagnosis}",
                "modality": "CBT",
                "duration": "12-16 sessions",
                "frequency": "Weekly",
                "evidence_level": "Strong",
                "population": population,
                "key_components": [
                    "Psychoeducation",
                    "Cognitive restructuring",
                    "Behavioral activation",
                    "Relapse prevention"
                ]
            }
        ]
        
        return {
            "protocols": protocols,
            "total_found": len(protocols)
        }
    
    async def _validate_assessment_tool(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate assessment tool"""
        tool_name = args.get("tool_name")
        purpose = args.get("purpose", "screening")
        
        # Mock implementation
        validation = {
            "tool_name": tool_name,
            "validated": True,
            "purpose": purpose,
            "psychometric_properties": {
                "reliability": 0.85,
                "validity": "Well-established",
                "sensitivity": 0.80,
                "specificity": 0.75
            },
            "administration": {
                "time_required": "5-10 minutes",
                "training_required": "Minimal",
                "scoring": "Automated"
            },
            "populations": ["Adult", "Adolescent"],
            "languages": ["English", "Spanish"]
        }
        
        return validation
    
    async def _check_drug_interactions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check drug interactions"""
        medications = args.get("medications", [])
        new_medication = args.get("new_medication")
        conditions = args.get("medical_conditions", [])
        
        # Mock implementation
        interactions = {
            "new_medication": new_medication,
            "current_medications": medications,
            "interactions": [
                {
                    "medication": "Example Drug",
                    "severity": "Moderate",
                    "mechanism": "CYP450 inhibition",
                    "clinical_effect": "Increased plasma levels",
                    "management": "Monitor for side effects, consider dose adjustment"
                }
            ],
            "contraindications": [],
            "monitoring_recommendations": [
                "Monitor liver function",
                "Watch for sedation",
                "Check drug levels if indicated"
            ]
        }
        
        return interactions
    
    async def _get_crisis_resources(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get crisis resources"""
        crisis_type = args.get("crisis_type")
        location = args.get("location", "National")
        immediate = args.get("immediate", False)
        
        resources = {
            "crisis_type": crisis_type,
            "immediate_response": immediate,
            "emergency_numbers": [
                {"name": "National Suicide Prevention Lifeline", "number": "988"},
                {"name": "Crisis Text Line", "number": "Text HOME to 741741"},
                {"name": "Emergency Services", "number": "911"}
            ],
            "local_resources": [
                {
                    "name": "Local Crisis Center",
                    "phone": "555-CRISIS",
                    "services": ["24/7 hotline", "Mobile crisis team", "Walk-in services"]
                }
            ],
            "safety_protocols": [
                "Immediate safety assessment",
                "Remove means of self-harm",
                "Develop safety plan",
                "Arrange follow-up care"
            ]
        }
        
        return resources
    
    async def _handle_list_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available resources"""
        return {
            "resources": [
                {
                    "uri": "therapy://clinical-guidelines",
                    "name": "Clinical Practice Guidelines",
                    "description": "Evidence-based clinical practice guidelines"
                },
                {
                    "uri": "therapy://diagnostic-criteria", 
                    "name": "Diagnostic Criteria",
                    "description": "DSM-5-TR and ICD-11 diagnostic criteria"
                },
                {
                    "uri": "therapy://treatment-protocols",
                    "name": "Treatment Protocols",
                    "description": "Evidence-based treatment protocols"
                }
            ]
        }
    
    async def _handle_read_resource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a specific resource"""
        uri = params.get("uri")
        
        # Mock implementation
        return {
            "uri": uri,
            "contents": [
                {
                    "type": "text",
                    "text": f"Resource content for {uri}"
                }
            ]
        }
    
    async def _handle_list_prompts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List available prompts"""
        return {
            "prompts": [
                {
                    "name": "diagnostic_assessment",
                    "description": "Structured diagnostic assessment prompt"
                },
                {
                    "name": "treatment_planning", 
                    "description": "Treatment planning prompt template"
                },
                {
                    "name": "crisis_intervention",
                    "description": "Crisis intervention protocol prompt"
                }
            ]
        }
    
    async def _handle_get_prompt(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific prompt"""
        name = params.get("name")
        
        prompts = {
            "diagnostic_assessment": {
                "name": "diagnostic_assessment",
                "description": "Structured diagnostic assessment",
                "arguments": [
                    {
                        "name": "symptoms",
                        "description": "Patient symptoms",
                        "required": True
                    },
                    {
                        "name": "history",
                        "description": "Clinical history",
                        "required": False
                    }
                ]
            }
        }
        
        return prompts.get(name, {"error": "Prompt not found"})

# Example MCP client integration
class MCPClient:
    """Simple MCP client for testing"""
    
    def __init__(self, server: TherapyMCPServer):
        self.server = server
        self.request_id = 0
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool via MCP"""
        self.request_id += 1
        
        request = MCPRequest(
            id=str(self.request_id),
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        response = await self.server.handle_request(request)
        return response.result

# Example usage
if __name__ == "__main__":
    async def main():
        server = TherapyMCPServer()
        client = MCPClient(server)
        
        # Test clinical guidelines search
        result = await client.call_tool(
            "search_clinical_guidelines",
            {"condition": "Major Depressive Disorder", "organization": "APA"}
        )
        
        print("Clinical Guidelines Search Result:")
        print(json.dumps(result, indent=2))
        
        # Test diagnostic criteria
        result = await client.call_tool(
            "get_diagnostic_criteria",
            {"disorder": "Generalized Anxiety Disorder"}
        )
        
        print("\nDiagnostic Criteria Result:")
        print(json.dumps(result, indent=2))
    
    asyncio.run(main())