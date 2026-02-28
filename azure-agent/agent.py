"""
CalcsLive Agent for Excel - CLI fallback
Microsoft AI Dev Days Hackathon 2026
"""

import sys
import json
from agent_core import CalcsLiveAgent, get_excel_health, read_excel_pq_table, calculate_with_calcslive, write_excel_results, _extract_calc_outputs

def run_agent_cli():
    """Run the CalcsLive Agent via Terminal."""
    print("=" * 60)
    print("CalcsLive Agent for Excel - CLI Mode")
    print("=" * 60)

    try:
        agent = CalcsLiveAgent()
        print(f"Connected to Azure AI (Mode: {agent.mode})")
    except ValueError as e:
        print(f"Error initializing Agent: {e}")
        return

    print("Type 'quit' to exit.")
    print("Try: 'Check Excel' or 'Calculate the values'")
    print()

    # Initialize history
    messages = [
        {"role": "system", "content": agent.system_message}
    ]

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
            
            print("  [Agent is reasoning...]")
            
            # Delegate loop to core loop
            messages, executed_tools = agent.chat_interact(messages)
            
            for tool_name, result in executed_tools:
                 print(f"  [Tool run: {tool_name}] -> Success: {result.get('success', True)}")

            # Find latest assistant response to print
            if messages:
                 last_msg = messages[-1]
                 if last_msg.get("role") == "assistant" and "tool_calls" not in last_msg:
                      print(f"\\nAgent: {last_msg.get('content')}\\n")

    except KeyboardInterrupt:
        print("\\nGoodbye!")

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
        pq_data.get("inputs", {}),
        pq_data.get("outputs", {}),
    )

    if not calc_result.get("success"):
        print(f"   Error: {calc_result.get('error')}")
        print("   (CalcsLive API may require authentication)")
        # Use dummy values for demo
        print("   Using demo values instead...")
        results = {"V": 0.0965, "m": 212.75}
    else:
        outputs = _extract_calc_outputs(calc_result)
        results = {sym: info.get("value") for sym, info in outputs.items()}
        print(f"   Results: {results if results else 'No outputs returned'}")

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
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            run_demo_local()
        elif sys.argv[1] == "--help":
            print("Usage:")
            print("  python agent.py        - Run with Azure AI")
            print("  python agent.py --demo - Run local demo (no Azure)")
    else:
        run_agent_cli()
