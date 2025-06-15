import json
import os
from typing import Dict, List, TypedDict, Annotated
from .bedrock_llm import invoke_claude_v2 # Assuming bedrock_llm.py is in the same directory

# --- Define TypedDicts for Agent State ---
class Task(TypedDict):
    id: str # Changed to str for flexibility, can be "1" or "1.1"
    title: str
    description: str
    details: str | None
    testStrategy: str | None
    priority: str
    dependencies: List[str]
    status: str
    subtasks: List['Task'] # Recursive Task definition for subtasks

class AgentState(TypedDict):
    prd_content: str
    tasks: List[Task]
    current_task_to_expand: Task | None # Task currently being processed by expansion node
    expanded_tasks_hierarchy: List[Task] # Final hierarchical list of tasks
    error_message: str | None

# --- Prompt Loading Utility ---
PROMPT_DIR = os.path.join(os.path.dirname(__file__), '..', 'prompts')

def load_prompt_template(filename: str) -> str:
    """Loads a prompt template from the prompts directory."""
    try:
        with open(os.path.join(PROMPT_DIR, filename), 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Prompt file {filename} not found in {PROMPT_DIR}")
        return "" # Return empty string or raise error
    except Exception as e:
        print(f"ERROR: Could not read prompt file {filename}: {e}")
        return ""

# --- Node 1: PRD Parse Node ---
def prd_parse_node(state: AgentState) -> AgentState:
    """
    Parses the PRD content to generate top-level tasks.
    """
    print("--- Entering PRD Parse Node ---")
    prd_content = state.get("prd_content")
    if not prd_content:
        return {**state, "error_message": "PRD content is missing."}

    # Load the core PRD parsing prompt (simplified, actual has more sections)
    # For this example, we'll assume the core_prd_parsing_prompt.md's main system prompt part
    # and a simplified user prompt structure.
    # A more robust solution would parse the Markdown and use specific sections.

    # Simplified system prompt extraction (example, real parsing would be more robust)
    # This is a placeholder for actual prompt template parsing logic
    raw_system_prompt_template = load_prompt_template("core_prd_parsing_prompt.md")
    # Crude extraction of system prompt - this needs to be improved for real use
    # For now, let's assume the first major block of text is the system prompt.
    # In a real scenario, you'd parse the markdown or have dedicated .txt prompt files.

    # Placeholder for actual system prompt extraction
    # This is a simplified example. A real implementation would parse the .md file.
    system_prompt_lines = [
        "You are an AI assistant specialized in analyzing Product Requirements Documents (PRDs) and generating a structured, logically ordered, dependency-aware and sequenced list of development tasks in JSON format.",
        "Analyze the provided PRD content and generate approximately [numTasks] top-level development tasks.",
        "Respond ONLY with a valid JSON object containing a single key \"tasks\", where the value is an array of task objects."
        # ... (other key parts of the system prompt)
    ]
    system_prompt = "\n".join(system_prompt_lines).replace("[numTasks]", "5") # Default to 5 tasks for now

    user_prompt = f"Here is the Product Requirements Document (PRD) to break down:\n\n{prd_content}\n\n" \
                  f"Please generate approximately 5 top-level tasks. Ensure IDs are strings."


    print(f"System Prompt for PRD Parse:\n{system_prompt[:200]}...") # Log snippet
    print(f"User Prompt for PRD Parse:\n{user_prompt[:200]}...")   # Log snippet

    try:
        response_text = invoke_claude_v2(prompt=user_prompt, system_prompt=system_prompt, max_tokens=4000)
        print(f"Raw LLM response for PRD Parse:\n{response_text[:500]}...") # Log snippet

        # Attempt to parse the JSON (Claude often wraps in ```json ... ```)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.strip().startswith("{") and response_text.strip().endswith("}"):
            json_str = response_text.strip()
        else: # Fallback: try to find the first '{' and last '}'
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = response_text[first_brace:last_brace+1]
            else:
                raise ValueError("No clear JSON object found in LLM response.")

        parsed_response = json.loads(json_str)

        generated_tasks = parsed_response.get("tasks", [])

        # Ensure tasks have string IDs and an empty subtasks list
        processed_tasks = []
        for i, task_data in enumerate(generated_tasks):
            processed_tasks.append(Task(
                id=str(task_data.get("id", str(i + 1))), # Ensure ID is string
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description", ""),
                details=task_data.get("details"),
                testStrategy=task_data.get("testStrategy"),
                priority=task_data.get("priority", "medium"),
                dependencies=task_data.get("dependencies", []),
                status=task_data.get("status", "pending"),
                subtasks=[] # Initialize with empty subtasks
            ))

        print(f"Successfully parsed {len(processed_tasks)} top-level tasks.")
        return {**state, "tasks": processed_tasks, "expanded_tasks_hierarchy": list(processed_tasks), "error_message": None}

    except Exception as e:
        error_msg = f"PRD Parse Node Error: {e}\nRaw response was: {response_text[:500]}..."
        print(f"ERROR in prd_parse_node: {error_msg}")
        return {**state, "error_message": error_msg}

# --- Node 2: Task Expansion Node ---
def task_expansion_node(state: AgentState) -> AgentState:
    """
    Expands a single task into subtasks.
    The task to expand should be in state["current_task_to_expand"].
    Subtasks are added to this task within the state["expanded_tasks_hierarchy"].
    """
    print("--- Entering Task Expansion Node ---")
    parent_task_obj = state.get("current_task_to_expand")

    if not parent_task_obj:
        return {**state, "error_message": "No current task to expand."}

    # Convert TypedDict to a plain dict for modification if necessary, though we're finding it in a list
    # This node will modify a task within the 'expanded_tasks_hierarchy' list.

    # Find the parent task in the hierarchy to update it directly
    # This is crucial for recursive expansion.

    # Helper to find and update task in a nested list
    def find_and_get_task_for_expansion(task_id: str, task_list: List[Task]) -> Task | None:
        for task_item in task_list:
            if task_item["id"] == task_id:
                return task_item
            if task_item.get("subtasks"):
                found_in_subtasks = find_and_get_task_for_expansion(task_id, task_item["subtasks"])
                if found_in_subtasks:
                    return found_in_subtasks
        return None

    # Get a reference to the task object within the hierarchy
    parent_task_ref = find_and_get_task_for_expansion(parent_task_obj["id"], state["expanded_tasks_hierarchy"])

    if not parent_task_ref:
        return {**state, "error_message": f"Task {parent_task_obj['id']} not found in hierarchy for expansion."}


    # Simplified prompt loading and formatting for task expansion
    # In a real system, you'd parse the markdown file more robustly.
    # For now, using a simplified version of the main expansion prompt.
    num_subtasks = 3 # Default number of subtasks
    next_subtask_id_start_num = len(parent_task_ref.get("subtasks", [])) + 1

    # Placeholder for actual system prompt extraction from task_expansion_prompts.md
    system_prompt_expansion = (
        f"You are an AI assistant helping with task breakdown. "
        f"You need to break down a high-level task into {num_subtasks} specific subtasks. "
        "Respond ONLY with a valid JSON object containing a single key \"subtasks\" whose value is an array."
    )

    user_prompt_expansion = (
        f"Break down this parent task into exactly {num_subtasks} specific subtasks:\n\n"
        f"Parent Task ID: {parent_task_ref['id']}\n"
        f"Parent Title: {parent_task_ref['title']}\n"
        f"Parent Description: {parent_task_ref['description']}\n"
        f"Parent Current details: {parent_task_ref.get('details') or 'None'}\n\n"
        f"Assign sequential subtask IDs starting from numerically {next_subtask_id_start_num} "
        f"(e.g., if parent is '1', first subtask is '1.1' if next_subtask_id_start_num is 1). " # Clarify subtask ID format
        f"Return ONLY the JSON object containing the \"subtasks\" array."
    )

    print(f"System Prompt for Task Expansion:\n{system_prompt_expansion[:200]}...")
    print(f"User Prompt for Task Expansion (Task ID {parent_task_ref['id']}):\n{user_prompt_expansion[:200]}...")

    try:
        response_text = invoke_claude_v2(prompt=user_prompt_expansion, system_prompt=system_prompt_expansion, max_tokens=3000)
        print(f"Raw LLM response for Task Expansion (Task ID {parent_task_ref['id']}):\n{response_text[:500]}...")

        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif response_text.strip().startswith("{") and response_text.strip().endswith("}"):
            json_str = response_text.strip()
        else: # Fallback
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                json_str = response_text[first_brace:last_brace+1]
            else:
                raise ValueError("No clear JSON object found in LLM response for task expansion.")

        parsed_response = json.loads(json_str)
        generated_subtasks_data = parsed_response.get("subtasks", [])

        processed_subtasks = []
        for i, sub_data in enumerate(generated_subtasks_data):
            # Create hierarchical subtask IDs like "parent_id.sub_index"
            new_subtask_id = f"{parent_task_ref['id']}.{next_subtask_id_start_num + i}"
            processed_subtasks.append(Task(
                id=new_subtask_id,
                title=sub_data.get("title", "Untitled Subtask"),
                description=sub_data.get("description", ""),
                details=sub_data.get("details"),
                testStrategy=sub_data.get("testStrategy"),
                priority=sub_data.get("priority", "medium"),
                dependencies=sub_data.get("dependencies", []), # Dependencies would be like "1.1", "1.2"
                status=sub_data.get("status", "pending"),
                subtasks=[] # Initialize with empty subtasks for further expansion
            ))

        # Append to the referenced parent task's subtasks list
        if not parent_task_ref.get("subtasks"): # Ensure subtasks list exists
            parent_task_ref["subtasks"] = []
        parent_task_ref["subtasks"].extend(processed_subtasks)

        print(f"Successfully parsed and added {len(processed_subtasks)} subtasks to Task ID {parent_task_ref['id']}.")
        return {**state, "current_task_to_expand": None, "error_message": None} # Clear current task after expansion

    except Exception as e:
        error_msg = f"Task Expansion Node Error for Task ID {parent_task_ref['id']}: {e}\nRaw response was: {response_text[:500]}..."
        print(f"ERROR in task_expansion_node: {error_msg}")
        # Clear current task to avoid retrying the same failed expansion, or implement retry logic
        return {**state, "current_task_to_expand": None, "error_message": error_msg}

if __name__ == '__main__':
    # Example of how these nodes might be manually tested (not part of the graph yet)

    # Test PRD Parse Node
    initial_state_prd = AgentState(
        prd_content="Feature: User Authentication. Users should be able to sign up with email and password, log in, and log out. Password should be securely hashed. Add password recovery via email.",
        tasks=[],
        current_task_to_expand=None,
        expanded_tasks_hierarchy=[],
        error_message=None
    )
    print("\n--- Testing PRD Parse Node ---")
    # Create dummy .env if it doesn't exist for bedrock_llm example part
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# AWS_REGION=us-east-1\n")
    print("Ensure AWS credentials and Bedrock access are configured for this test.")

    parsed_state = prd_parse_node(initial_state_prd)
    print("\nPRD Parse Node Output:")
    if parsed_state.get("error_message"):
        print(f"Error: {parsed_state['error_message']}")
    else:
        print(json.dumps(parsed_state["tasks"], indent=2))

    # Test Task Expansion Node (if PRD parse was successful)
    if parsed_state.get("tasks") and not parsed_state.get("error_message"):
        task_to_expand = parsed_state["tasks"][0] # Expand the first task
        initial_state_expand = AgentState(
            prd_content=initial_state_prd["prd_content"], # carry over
            tasks=parsed_state["tasks"], # from previous step
            current_task_to_expand=task_to_expand,
            expanded_tasks_hierarchy=list(parsed_state["tasks"]), # Initialize hierarchy
            error_message=None
        )
        print(f"\n--- Testing Task Expansion Node (for Task ID: {task_to_expand['id']}) ---")
        expanded_state = task_expansion_node(initial_state_expand)
        print("\nTask Expansion Node Output (Full Hierarchy):")
        if expanded_state.get("error_message"):
            print(f"Error: {expanded_state['error_message']}")
        else:
            print(json.dumps(expanded_state["expanded_tasks_hierarchy"], indent=2))
