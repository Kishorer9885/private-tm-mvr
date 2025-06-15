import argparse
import json
import os
from agent_logic.graph_nodes import AgentState # Assuming AgentState is in graph_nodes
from agent_logic.agent_graph import TaskHierarchyGraph
from agent_logic.file_utils import read_markdown_prd, write_markdown_task_hierarchy

# Ensure .env is loaded if bedrock_llm.py is used by graph indirectly
from dotenv import load_dotenv
load_dotenv() # Load from .env in the current directory or parent

def main():
    parser = argparse.ArgumentParser(description="Run the LangGraph Task Hierarchy Agent.")
    parser.add_argument(
        "-i", "--input-prd",
        required=True,
        help="Path to the input PRD Markdown file."
    )
    parser.add_argument(
        "-o", "--output-md",
        required=True,
        help="Path for the output Markdown file for the task hierarchy."
    )
    parser.add_argument(
        "-d", "--max-depth",
        type=int,
        default=1, # Default to expanding one level of subtasks
        help="Maximum depth for task expansion (0 for top-level only, 1 for one level of subtasks, etc.)."
    )
    parser.add_argument(
        "--recursion-limit",
        type=int,
        default=25, # Default LangGraph recursion limit
        help="Recursion limit for the LangGraph execution."
    )

    args = parser.parse_args()

    print(f"Starting agent with Input PRD: {args.input_prd}, Output MD: {args.output_md}, Max Expansion Depth: {args.max_depth}")

    # 1. Load PRD
    try:
        prd_content = read_markdown_prd(args.input_prd)
    except Exception as e:
        print(f"Failed to read PRD file: {e}")
        return

    # 2. Initialize AgentState
    initial_agent_state = AgentState(
        prd_content=prd_content,
        tasks=[],
        current_task_to_expand=None,
        expanded_tasks_hierarchy=[],
        error_message=None
    )

    # 3. Instantiate and Run Graph
    try:
        print("Initializing Task Hierarchy Graph...")
        graph_runner = TaskHierarchyGraph()
        graph_runner.max_expansion_depth = args.max_depth

        print(f"Invoking graph with recursion limit: {args.recursion_limit}...")
        # Configuration for the graph run, like recursion limit
        config = {"recursion_limit": args.recursion_limit}
        final_state = graph_runner.app.invoke(initial_agent_state, config=config)

        print("Graph invocation complete.")

    except Exception as e:
        print(f"An error occurred during graph execution: {e}")
        # Try to dump the state if available, even on error
        if 'final_state' in locals() and final_state:
             print("State at time of error (or last successful step):")
             print(json.dumps(final_state, indent=2, default=str)) # Use default=str for non-serializable
        return

    # 4. Handle Output
    if final_state:
        error_msg = final_state.get("error_message")
        if error_msg:
            print(f"Agent finished with an error: {error_msg}")
        else:
            print("Agent finished successfully.")

        task_hierarchy = final_state.get("expanded_tasks_hierarchy", [])
        if task_hierarchy:
            try:
                write_markdown_task_hierarchy(task_hierarchy, args.output_md)
                print(f"Task hierarchy written to {args.output_md}")
            except Exception as e:
                print(f"Failed to write output Markdown file: {e}")
        else:
            print("No task hierarchy was generated to write.")
            if not error_msg: # If no specific error, but also no output, mention it.
                 print("The agent completed, but the final task hierarchy is empty.")
                 print("Consider checking LLM responses or prompt configurations if this is unexpected.")


    else:
        print("Agent did not return a final state. This should not happen.")

if __name__ == "__main__":
    # This allows running the agent directly:
    # python langgraph_task_agent/run_agent.py -i path/to/prd.md -o path/to/output.md
    main()
