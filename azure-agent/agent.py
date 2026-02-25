"""
CalcsLive Agent for Excel
Microsoft AI Dev Days Hackathon 2026

This agent orchestrates unit-aware calculations between Excel and CalcsLive:
1. Reads PQ (Physical Quantity) data from Excel via local bridge
2. Calls CalcsLive API for unit-aware calculations
3. Writes results back to Excel

Uses Azure AI Projects SDK with OpenAI Assistants API.
"""

import os
import json
from typing import Any
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
EXCEL_BRIDGE_URL = os.getenv("EXCEL_BRIDGE_URL", "http://localhost:8001")
CALCSLIVE_API_URL = "https://calcslive.com/api/v1"


# ============ Excel Bridge Functions ============

def read_excel_pq_table() -> dict:
    """Read the PQ table from Excel via the bridge."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{EXCEL_BRIDGE_URL}/excel/pq-for-calcslive")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to Excel Bridge at localhost:8001"}
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
        return {"success": False, "error": "Cannot connect to Excel Bridge"}
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
        return {"success": False, "error": "Cannot connect to Excel Bridge at localhost:8001"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ CalcsLive Functions ============

def calculate_with_calcslive(pqs: list, inputs: dict, outputs: dict = None) -> dict:
    """
    Perform a unit-aware calculation using CalcsLive run_script API.
    """
    try:
        payload = {"pqs": pqs}
        if inputs:
            payload["inputs"] = inputs
        if outputs:
            payload["outputs"] = outputs

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{CALCSLIVE_API_URL}/run-script",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 401:
                return {"success": False, "error": "CalcsLive API requires authentication"}

            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        return {"success": False, "error": "Cannot connect to CalcsLive API"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ Agent using Azure AI with Chat Completions API ============

def run_agent_with_azure():
    """Run the CalcsLive Agent using Azure AI with Chat Completions API."""

    # Check for serverless inference endpoint first (Models-as-a-Service)
    inference_endpoint = os.getenv("AZURE_AI_INFERENCE_ENDPOINT")
    inference_key = os.getenv("AZURE_AI_INFERENCE_KEY")

    # Fall back to project SDK
    project_endpoint = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
    model_deployment = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "grok-3-mini")

    print("=" * 60)
    print("CalcsLive Agent for Excel")
    print("=" * 60)

    # Determine which client to use
    openai_client = None

    if inference_endpoint and inference_key:
        # Use direct inference endpoint (serverless deployment)
        print(f"Mode: Serverless Inference")
        print(f"Endpoint: {inference_endpoint}")

        from openai import OpenAI
        # For serverless, the base_url should be the endpoint without /chat/completions
        base_url = inference_endpoint.replace("/chat/completions", "").replace("/v1/", "/v1")
        if not base_url.endswith("/v1"):
            base_url = base_url.rstrip("/") + "/v1"

        openai_client = OpenAI(
            base_url=base_url,
            api_key=inference_key
        )
        model_deployment = "grok-3-mini"  # Model name for serverless

    elif project_endpoint:
        # Use Azure AI Projects SDK
        print(f"Mode: Azure AI Projects")
        print(f"Project: {project_endpoint}")
        print(f"Model: {model_deployment}")

        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=project_endpoint,
            credential=credential
        )
        openai_client = project_client.get_openai_client()
    else:
        print("Error: No Azure endpoint configured.")
        print("Set either:")
        print("  - AZURE_AI_INFERENCE_ENDPOINT + AZURE_AI_INFERENCE_KEY (for serverless)")
        print("  - AZURE_AI_PROJECT_ENDPOINT (for project SDK)")
        return

    print()

    # Define tools for function calling
    tools = [
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
                        }
                    },
                    "required": ["pqs", "inputs"]
                }
            }
        }
    ]

    system_message = """You are the CalcsLive Agent, helping users perform unit-aware calculations in Excel.

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

Always explain what you're doing."""

    print("Connected to Azure AI")
    print("Type 'quit' to exit.")
    print("Try: 'Check Excel' or 'Calculate the values'")
    print()

    def execute_tool(func_name: str, func_args: dict) -> dict:
        """Execute a tool and return the result."""
        print(f"  [Calling {func_name}...]")

        if func_name == "get_excel_health":
            return get_excel_health()
        elif func_name == "read_excel_pq_table":
            return read_excel_pq_table()
        elif func_name == "write_excel_results":
            return write_excel_results(func_args.get("results", {}))
        elif func_name == "calculate_with_calcslive":
            return calculate_with_calcslive(
                func_args.get("pqs", []),
                func_args.get("inputs", {})
            )
        else:
            return {"error": f"Unknown function: {func_name}"}

    # Conversation history
    messages = [{"role": "system", "content": system_message}]

    try:
        while True:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            # Add user message
            messages.append({"role": "user", "content": user_input})

            # Loop to handle tool calls
            while True:
                try:
                    response = openai_client.chat.completions.create(
                        model=model_deployment,
                        messages=messages,
                        tools=tools
                    )
                except Exception as e:
                    print(f"\nAgent: Error calling model - {e}\n")
                    # Remove the last user message since we couldn't process it
                    messages.pop()
                    break

                assistant_message = response.choices[0].message

                # Check if the model wants to use tools
                if assistant_message.tool_calls:
                    # Add assistant message with tool calls to history
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

                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}

                        result = execute_tool(func_name, func_args)

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })

                    # Continue the loop to get the next response
                    continue
                else:
                    # No more tool calls, print the response
                    if assistant_message.content:
                        print(f"\nAgent: {assistant_message.content}\n")
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message.content
                        })
                    break

    except KeyboardInterrupt:
        print("\nGoodbye!")

    print("Session ended.")


# ============ Simple Demo Mode (no Azure) ============

def run_demo_local():
    """Run a demo calculation locally without Azure (for testing)."""
    print("=" * 60)
    print("CalcsLive Agent - Local Demo Mode")
    print("=" * 60)
    print()

    # Step 1: Check Excel
    print("1. Checking Excel connection...")
    health = get_excel_health()
    if not health.get("success", False) and health.get("status") != "connected":
        print(f"   Error: {health.get('error', health)}")
        return
    print(f"   Connected: {health.get('workbookName', 'Unknown')}")
    print()

    # Step 2: Read PQ table
    print("2. Reading PQ table from Excel...")
    pq_data = read_excel_pq_table()
    if not pq_data.get("success"):
        print(f"   Error: {pq_data.get('error')}")
        return

    print(f"   ArticleID: {pq_data.get('articleId')}")
    print(f"   Inputs: {pq_data.get('inputs')}")
    print(f"   Outputs: {pq_data.get('outputs')}")
    print()

    # Step 3: Calculate
    print("3. Calculating with CalcsLive...")
    calc_result = calculate_with_calcslive(
        pq_data.get("pqs", []),
        pq_data.get("inputs", {})
    )

    if not calc_result.get("success"):
        print(f"   Error: {calc_result.get('error')}")
        print("   (CalcsLive API may require authentication)")
        # Use dummy values for demo
        print("   Using demo values instead...")
        results = {"V": 0.0965, "m": 212.75}
    else:
        outputs = calc_result.get("data", {}).get("outputs", {})
        results = {sym: info.get("value") for sym, info in outputs.items()}
        print(f"   Results: {results}")

    print()

    # Step 4: Write back
    print("4. Writing results to Excel...")
    write_result = write_excel_results(results)
    if write_result.get("success"):
        print(f"   Written {write_result.get('valuesWritten')} values")
        for detail in write_result.get("details", []):
            print(f"   - {detail['sym']} = {detail['value']} -> {detail['cell']}")
    else:
        print(f"   Error: {write_result.get('error')}")

    print()
    print("Done!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            # Local demo without Azure
            run_demo_local()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python agent.py        - Run with Azure AI")
            print("  python agent.py --demo - Run local demo (no Azure)")
    else:
        # Run with Azure
        run_agent_with_azure()