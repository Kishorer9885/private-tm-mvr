from langgraph.graph import StateGraph, END
from typing import List, TypedDict, Annotated, Sequence, Dict
import operator # For AddableValues

# Import nodes and state definition from graph_nodes
from .graph_nodes import AgentState, Task, prd_parse_node, task_expansion_node

# --- Graph Construction ---
class TaskHierarchyGraph:
    def __init__(self):
        self.graph = StateGraph(AgentState)
        self._build_graph()
        self.app = self.graph.compile()
        self.max_expansion_depth = 1 # Controls how deep subtasks are expanded. 0 = top-level only. 1 = one level of subtasks.
        self.tasks_to_process_for_expansion: List[Task] = [] # Queue for tasks to expand

    def _build_graph(self):
        # Add nodes
        self.graph.add_node("prd_parser", prd_parse_node)
        self.graph.add_node("task_expander", task_expansion_node)

        # Placeholder for a final output node/step if needed
        # self.graph.add_node("output_results", self.output_results_node) # Example

        # Define edges
        self.graph.set_entry_point("prd_parser")

        # After PRD parsing, decide if we need to expand tasks
        self.graph.add_conditional_edges(
            "prd_parser",
            self.prepare_for_task_expansion_or_finish, # This will populate tasks_to_process_for_expansion
            {
                "expand_next_task": "task_expander", # If tasks to expand
                "finish_processing": END # If no (more) tasks to expand or error
            }
        )

        # After task expansion, loop back to decide on the next task or finish
        self.graph.add_conditional_edges(
            "task_expander",
            self.prepare_for_task_expansion_or_finish, # Decide next step
            {
                "expand_next_task": "task_expander",
                "finish_processing": END
            }
        )

    def get_task_depth(self, task_id: str) -> int:
        """Calculates the depth of a task based on its ID (e.g., '1' is 0, '1.1' is 1)."""
        return task_id.count('.')

    def _collect_tasks_for_expansion(self, tasks: List[Task], current_depth: int = 0):
        """
        Helper to collect tasks for expansion up to max_expansion_depth.
        This should be called after new tasks/subtasks are added.
        """
        for task in tasks:
            task_depth = self.get_task_depth(task["id"])
            if task_depth < self.max_expansion_depth:
                # Check if it's already expanded or in queue to avoid re-adding
                # For simplicity, we'll just add. A more robust check might be needed.
                if not task.get("subtasks"): # Only add if it has no subtasks yet
                     # Ensure not already in the queue to avoid duplicates from different calls
                    if not any(t["id"] == task["id"] for t in self.tasks_to_process_for_expansion):
                        self.tasks_to_process_for_expansion.append(task)

            # Recursively collect from subtasks if any exist (they might from a previous partial run)
            if task.get("subtasks"):
                self._collect_tasks_for_expansion(task["subtasks"], current_depth + 1)


    def prepare_for_task_expansion_or_finish(self, state: AgentState) -> str:
        """
        Routing function.
        Decides if there are more tasks to expand or if processing should end.
        Manages a queue of tasks to be expanded.
        """
        print("--- Router: Deciding next step ---")
        if state.get("error_message"):
            print(f"Router: Error detected: {state['error_message']}. Finishing.")
            return "finish_processing"

        # If this is the first time after prd_parser, or if task_expander just finished
        # we need to (re)populate the expansion queue.
        # The task_expander node itself adds subtasks to the hierarchy.
        # We collect tasks from the *current* hierarchy that need expansion.

        # Clear previous queue and rebuild based on current hierarchy and depth limits
        self.tasks_to_process_for_expansion = []
        if state.get("expanded_tasks_hierarchy"):
            self._collect_tasks_for_expansion(state["expanded_tasks_hierarchy"])

        print(f"Router: Found {len(self.tasks_to_process_for_expansion)} tasks in queue for potential expansion.")

        if self.tasks_to_process_for_expansion:
            next_task_to_expand = self.tasks_to_process_for_expansion.pop(0) # Get the next task (FIFO)
            state["current_task_to_expand"] = next_task_to_expand
            print(f"Router: Next task to expand: ID {next_task_to_expand['id']} - '{next_task_to_expand['title']}'")
            return "expand_next_task"
        else:
            print("Router: No more tasks to expand or max depth reached for all. Finishing.")
            state["current_task_to_expand"] = None # Clear it
            return "finish_processing"

    # Example of a final node if you want to do something with the results
    # def output_results_node(self, state: AgentState) -> AgentState:
    #     print("--- Final Results ---")
    #     print(json.dumps(state["expanded_tasks_hierarchy"], indent=2))
    #     return state

# Example of running the graph (will be moved to a main script later)
if __name__ == '__main__':
    import json
    import os

    # Create dummy .env if it doesn't exist for bedrock_llm example part
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# AWS_REGION=us-east-1\n")
    print("Ensure AWS credentials and Bedrock access are configured for this test.")

    graph_runner = TaskHierarchyGraph()
    graph_runner.max_expansion_depth = 1 # Expand one level of subtasks

    # Example PRD content
    sample_prd = ("Feature: User Login System.\n"
                  "Users must be able to register with a username, email, and password.\n"
                  "Passwords must be stored securely, using hashing and salting.\n"
                  "Users should be able to log in with their email and password.\n"
                  "A 'forgot password' functionality should allow users to reset their password via email.")

    initial_input = AgentState(
        prd_content=sample_prd,
        tasks=[], # Initial tasks from PRD parser
        current_task_to_expand=None,
        expanded_tasks_hierarchy=[], # This will be populated by prd_parser and updated by task_expander
        error_message=None
    )

    print("\n--- Invoking LangGraph Agent ---")
    # For streaming results:
    # for event in graph_runner.app.stream(initial_input, {"recursion_limit": 20}):
    #     for node_name, output_state in event.items():
    #         print(f"Output from node '{node_name}':")
    #         # print(json.dumps(output_state, indent=2, default=str)) # Print full state, careful with large states
    #         if output_state.get("error_message"):
    #             print(f"  ERROR: {output_state['error_message']}")
    #         if node_name == "prd_parser" and output_state.get("tasks"):
    #             print(f"  Parsed {len(output_state['tasks'])} top-level tasks.")
    #         if node_name == "task_expander" and output_state.get("expanded_tasks_hierarchy"):
    #             print(f"  Task expansion modified hierarchy.")
    #         print("---")
    # final_state = output_state # The last state after streaming

    # For non-streaming full invocation:
    final_state = graph_runner.app.invoke(initial_input, {"recursion_limit": 25})


    print("\n--- Agent Run Complete ---")
    if final_state.get("error_message"):
        print(f"Agent finished with an error: {final_state['error_message']}")

    print("\nFinal Task Hierarchy:")
    print(json.dumps(final_state.get("expanded_tasks_hierarchy", []), indent=2, default=str))

    # To see the graph structure:
    # from IPython.display import Image, display
    # try:
    #     img_bytes = graph_runner.app.get_graph().draw_mermaid_png()
    #     with open("graph.png", "wb") as f:
    #         f.write(img_bytes)
    #     print("\nGraph visualization saved to graph.png")
    # except Exception as e:
    #     print(f"Could not generate graph image: {e}")
