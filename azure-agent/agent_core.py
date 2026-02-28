import os
import json
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse, parse_qs
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
EXCEL_BRIDGE_URL = os.getenv("EXCEL_BRIDGE_URL", "http://localhost:8001")
CALCSLIVE_API_URL = os.getenv("CALCSLIVE_API_URL", "https://calcslive.com/api/v1")
CALCSLIVE_API_KEY = os.getenv("CALCSLIVE_API_KEY", "")

def _normalize_inference_base_url(endpoint: str) -> str:
    """Normalize Azure serverless inference endpoint to OpenAI SDK base_url."""
    base_url = endpoint.strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
            base_url = base_url[:-len("/chat/completions")]
    if not base_url.endswith("/v1"):
            if base_url.endswith("/v1/"):
                base_url = base_url[:-1]
            else:
                base_url = f"{base_url}/v1"
    return base_url

def _parse_azure_openai_deployment_endpoint(endpoint: str) -> dict:
    """Parse Azure OpenAI deployment chat-completions endpoint."""
    parsed = urlparse(endpoint.strip())
    path_parts = [p for p in parsed.path.split("/") if p]

    deployment_name = None
    if "deployments" in path_parts:
            idx = path_parts.index("deployments")
            if idx + 1 < len(path_parts):
                deployment_name = path_parts[idx + 1]

    query = parse_qs(parsed.query)
    api_version = query.get("api-version", [None])[0]

    return {
            "azure_endpoint": f"{parsed.scheme}://{parsed.netloc}",
            "deployment": deployment_name,
            "api_version": api_version,
    }


def _post_json(url: str, payload: dict, timeout: float, headers: dict | None = None) -> dict:
    """POST JSON and return standardized dict response."""
    try:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code >= 400:
                try:
                    error_body = response.json()
                except Exception:
                    error_body = response.text
                return {
                    "success": False,
                    "statusCode": response.status_code,
                    "error": "HTTP request failed",
                    "details": error_body,
                }

            return {"success": True, "data": response.json()}

    except httpx.ConnectError:
            return {"success": False, "error": f"Connection failed to {url}"}
    except Exception as e:
            return {"success": False, "error": str(e)}

def _extract_calc_outputs(calc_result: dict) -> dict:
    """Extract outputs map from normalized CalcsLive response."""
    if not calc_result.get("success"):
            return {}
    data = calc_result.get("data")
    if not isinstance(data, dict):
            return {}
    if isinstance(data.get("outputs"), dict):
            return data["outputs"]
    nested = data.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("outputs"), dict):
            return nested["outputs"]
    return {}


# ============ Excel Bridge Functions ============

def read_excel_pq_table() -> dict:
    """Read the PQ table from Excel via the bridge."""
    try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{EXCEL_BRIDGE_URL}/excel/pq-for-calcslive")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
            return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
            return {"success": False, "error": str(e)}

def write_excel_results(results: dict) -> dict:
    """Write calculated results back to Excel."""
    try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    f"{EXCEL_BRIDGE_URL}/excel/write-pq-results",
                    json={"results": results}
                )
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
            return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
            return {"success": False, "error": str(e)}

def get_excel_health() -> dict:
    """Check Excel connection health."""
    try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{EXCEL_BRIDGE_URL}/excel/health")
                response.raise_for_status()
                return response.json()
    except httpx.ConnectError:
            return {"success": False, "error": f"Cannot connect to Excel Bridge at {EXCEL_BRIDGE_URL}"}
    except Exception as e:
            return {"success": False, "error": str(e)}


# ============ CalcsLive Functions ============

def calculate_with_calcslive(pqs: list, inputs: dict, outputs: dict = None) -> dict:
    """
    Perform a unit-aware calculation using CalcsLive run_script API.
    """
    payload = {"pqs": pqs}
    if inputs:
            payload["inputs"] = inputs
    if outputs:
            payload["outputs"] = outputs

    headers = {"Content-Type": "application/json"}
    if CALCSLIVE_API_KEY:
            headers["Authorization"] = f"Bearer {CALCSLIVE_API_KEY}"

    result = _post_json(
            f"{CALCSLIVE_API_URL}/run-script",
            payload,
            timeout=30.0,
            headers=headers,
    )

    if not result.get("success"):
            if result.get("statusCode") == 401:
                return {
                    "success": False,
                    "error": "CalcsLive API requires authentication",
                    "details": result.get("details"),
                }
            return result

    data = result.get("data")
    if isinstance(data, dict) and data.get("success") is False:
            return data

    return {"success": True, "data": data}


# ============ Agent Core Class ============

class CalcsLiveAgent:
    def __init__(self):
            # Check for serverless inference endpoint first (Models-as-a-Service)
            inference_endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
            inference_key = os.getenv("AZURE_AI_INFERENCE_KEY")

            # Fall back to project SDK
            project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
            self.model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "grok-3-mini")
            inference_model = os.getenv("AZURE_AI_INFERENCE_MODEL", self.model_deployment)

            self.openai_client = None
            self.mode = "Unknown"

            if inference_endpoint and inference_key:
                self.mode = "Serverless Inference"
                if "/openai/deployments/" in inference_endpoint:
                    from openai import AzureOpenAI

                    parsed = _parse_azure_openai_deployment_endpoint(inference_endpoint)
                    api_version = os.getenv("AZURE_AI_INFERENCE_API_VERSION") or parsed.get("api_version") or "2024-05-01-preview"
                    deployment_from_url = parsed.get("deployment")

                    if deployment_from_url:
                            self.model_deployment = deployment_from_url

                    self.openai_client = AzureOpenAI(
                            api_key=inference_key,
                            azure_endpoint=parsed["azure_endpoint"],
                            api_version=api_version,
                    )
                else:
                    from openai import OpenAI
                    base_url = _normalize_inference_base_url(inference_endpoint)
                    self.openai_client = OpenAI(
                            base_url=base_url,
                            api_key=inference_key,
                    )
                    self.model_deployment = inference_model

            elif project_endpoint:
                self.mode = "Azure AI Projects"
                from azure.ai.projects import AIProjectClient
                from azure.identity import DefaultAzureCredential
                
                credential = DefaultAzureCredential()
                project_client = AIProjectClient(
                    endpoint=project_endpoint,
                    credential=credential
                )
                self.openai_client = project_client.get_openai_client()
            else:
                raise ValueError("No Azure endpoint configured. Set AZURE_AI_INFERENCE_ENDPOINT or AZURE_AI_PROJECT_ENDPOINT")

            self.tools = [
                {
                    "type": "function",
                    "function": {
                            "name": "get_excel_health",
                            "description": "Check if Excel is connected and has a workbook open",
                            "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "read_excel_pq_table",
                            "description": "Read the PQ (Physical Quantity) table from Excel including inputs, outputs, and their values/units",
                            "parameters": {"type": "object", "properties": {}, "required": []}
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "write_excel_results",
                            "description": "Write calculated results back to Excel",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "results": {
                                            "type": "object",
                                            "description": "Dict mapping symbol names to values, e.g., {\"V\": 0.0965, \"m\": 212.75}"
                                    }
                                },
                                "required": ["results"]
                            }
                    }
                },
                {
                    "type": "function",
                    "function": {
                            "name": "calculate_with_calcslive",
                            "description": "Perform unit-aware calculation using CalcsLive API",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "pqs": {
                                            "type": "array",
                                            "description": "List of PQ definitions with sym, unit, value (for inputs) or expression (for outputs)"
                                    },
                                    "inputs": {
                                            "type": "object",
                                            "description": "Dict of input values, e.g., {\"D\": {\"value\": 2, \"unit\": \"in\"}}"
                                    },
                                    "outputs": {
                                            "type": "object",
                                            "description": "Optional requested outputs with unit preferences, e.g., {\"V\": {\"unit\": \"L\"}}"
                                    }
                                },
                                "required": ["pqs", "inputs"]
                            }
                    }
                }
            ]

            self.system_message = """You are the CalcsLive Agent, helping users perform unit-aware calculations in Excel.

Your workflow:
1. First, check Excel health to ensure connection
2. Read the PQ (Physical Quantity) table from Excel to get inputs and output definitions
3. Use CalcsLive to calculate the outputs with proper unit conversions
4. Write the calculated results back to Excel

Key concepts:
- PQ = Physical Quantity (value + unit, e.g., "2 inches", "3 cm")
- Inputs = PQs where user provides values (no expression)
- Outputs = PQs with expressions that need calculation

When asked to calculate, follow this sequence:
1. Call get_excel_health to verify connection
2. Call read_excel_pq_table to get the data
3. Call calculate_with_calcslive with the PQs and inputs
4. Call write_excel_results with the calculated values

Always explain what you're doing. Show your tool results to the user as they happen if it takes multiple steps.
"""

    def execute_tool(self, func_name: str, func_args: dict) -> dict:
            """Execute a tool and return the result."""
            if func_name == "get_excel_health":
                return get_excel_health()
            elif func_name == "read_excel_pq_table":
                return read_excel_pq_table()
            elif func_name == "write_excel_results":
                return write_excel_results(func_args.get("results", {}))
            elif func_name == "calculate_with_calcslive":
                return calculate_with_calcslive(
                    func_args.get("pqs", []),
                    func_args.get("inputs", {}),
                    func_args.get("outputs", {}),
                )
            else:
                return {"error": f"Unknown function: {func_name}"}

    def chat_interact(self, messages: List[Dict]) -> Tuple[List[Dict], List[tuple]]:
            """
            Process an agent turn given existing chat history.
            Returns the updated conversation history, and an optional list of executed (tool_name: result) tuples
            for the UI to optionally display.
            """
            
            tool_round = 0
            executed_tools = []
            
            while True:
                tool_round += 1
                if tool_round > 8:
                    messages.append({"role": "assistant", "content": "Stopped after too many tool rounds for one prompt."})
                    return messages, executed_tools

                try:
                    response = self.openai_client.chat.completions.create(
                            model=self.model_deployment,
                            messages=messages,
                            tools=self.tools
                    )
                except Exception as e:
                    messages.append({"role": "assistant", "content": f"Error calling model - {e}"})
                    return messages, executed_tools

                assistant_message = response.choices[0].message

                if assistant_message.tool_calls:
                    messages.append({
                            "role": "assistant",
                            "content": assistant_message.content,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                            "name": tc.function.name,
                                            "arguments": tc.function.arguments
                                    }
                                }
                                for tc in assistant_message.tool_calls
                            ]
                    })

                    for tool_call in assistant_message.tool_calls:
                            func_name = tool_call.function.name
                            try:
                                func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                            except json.JSONDecodeError:
                                func_args = {}

                            result = self.execute_tool(func_name, func_args)
                            executed_tools.append((func_name, result))
                            
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })

                    # Continue loop to allow model to observe tool outputs
                    continue
                else:
                    if assistant_message.content:
                            messages.append({
                                "role": "assistant",
                                "content": assistant_message.content
                            })
                    return messages, executed_tools
