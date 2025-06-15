import os
from typing import List
from .graph_nodes import Task # Assuming Task TypedDict is in graph_nodes

def read_markdown_prd(file_path: str) -> str:
    """
    Reads the content of a Markdown PRD file.

    Args:
        file_path (str): The path to the Markdown PRD file.

    Returns:
        str: The content of the file as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: For other reading errors.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Successfully read PRD file: {file_path}")
        return content
    except FileNotFoundError:
        print(f"Error: PRD file not found at {file_path}")
        raise
    except Exception as e:
        print(f"Error reading PRD file {file_path}: {e}")
        raise

def _format_task_to_markdown(task: Task, level: int = 1) -> str:
    """
    Recursively formats a single task and its subtasks into Markdown.
    """
    markdown_lines = []
    heading_prefix = "#" * level

    markdown_lines.append(f"{heading_prefix} Task: {task.get('title', 'N/A')} (ID: {task.get('id', 'N/A')})")
    markdown_lines.append(f"- **Description:** {task.get('description', 'N/A')}")
    markdown_lines.append(f"- **Priority:** {task.get('priority', 'medium')}")
    markdown_lines.append(f"- **Status:** {task.get('status', 'pending')}")

    details = task.get('details')
    if details:
        # Escape backticks within details for code block
        escaped_details = details.replace('`', '\\`')
        markdown_lines.append(f"- **Details:**\n  ```\n{escaped_details}\n  ```")
    else:
        markdown_lines.append("- **Details:** N/A")

    test_strategy = task.get('testStrategy')
    if test_strategy:
        escaped_test_strategy = test_strategy.replace('`', '\\`')
        markdown_lines.append(f"- **Test Strategy:**\n  ```\n{escaped_test_strategy}\n  ```")
    else:
        markdown_lines.append("- **Test Strategy:** N/A")

    dependencies = task.get('dependencies', [])
    if dependencies:
        markdown_lines.append(f"- **Dependencies:** {', '.join(map(str, dependencies))}")
    else:
        markdown_lines.append("- **Dependencies:** None")

    markdown_lines.append("") # Add a blank line for spacing

    subtasks = task.get('subtasks', [])
    if subtasks:
        markdown_lines.append(f"{heading_prefix}# Subtasks for {task.get('id', 'N/A')}:" ) # Note: this will create H3 for H1 parent's subtasks etc.
        markdown_lines.append("")
        for subtask in subtasks:
            markdown_lines.append(_format_task_to_markdown(subtask, level + 1)) # Correctly increment level for sub-subtasks

    return "\n".join(markdown_lines)

def write_markdown_task_hierarchy(task_hierarchy: List[Task], output_file_path: str) -> None:
    """
    Writes the hierarchical list of tasks to a Markdown file.

    Args:
        task_hierarchy (List[Task]): The list of top-level tasks, potentially with nested subtasks.
        output_file_path (str): The path to the output Markdown file.

    Raises:
        Exception: For file writing errors.
    """
    try:
        full_markdown_content = "# Project Task Hierarchy\n\n"
        if not task_hierarchy:
            full_markdown_content += "No tasks were generated or found.\n"
        else:
            for task in task_hierarchy:
                full_markdown_content += _format_task_to_markdown(task, level=2) # Start top-level tasks at H2
                full_markdown_content += "\n---\n\n" # Separator between top-level tasks

        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(full_markdown_content)
        print(f"Successfully wrote task hierarchy to Markdown file: {output_file_path}")

    except Exception as e:
        print(f"Error writing task hierarchy to Markdown file {output_file_path}: {e}")
        raise

if __name__ == '__main__':
    print("--- Testing file_utils.py ---")

    dummy_prd_path = "dummy_prd_for_file_utils_test.md"
    example_prd_content = """
# Project X - Feature Y

## Overview
This project aims to implement Feature Y for Project X.
This involves creating a new user interface and a backend API.
"""
    with open(dummy_prd_path, "w", encoding="utf-8") as f:
        f.write(example_prd_content)
    print(f"Created dummy PRD file: {dummy_prd_path}")

    try:
        prd_data = read_markdown_prd(dummy_prd_path)
        print(f"Read PRD content (first 50 chars): '{prd_data[:50]}...'")
        assert prd_data == example_prd_content
    except Exception as e:
        print(f"Error during read_markdown_prd test: {e}")

    example_tasks: List[Task] = [
        Task(id="1", title="Setup Backend API", description="Create the basic API structure",
             details="Use FastAPI framework. Setup basic CRUD endpoints for resources.",
             testStrategy="Unit tests for each endpoint. Integration test for basic flow.",
             priority="high", dependencies=[], status="pending", subtasks=[
                 Task(id="1.1", title="Define API Models", description="Define Pydantic models for API",
                      details="Models for User, Product.", testStrategy="Schema validation.",
                      priority="high", dependencies=[], status="pending", subtasks=[]),
                 Task(id="1.2", title="Implement User Auth", description="Implement JWT authentication",
                      details="Endpoints for login, register.", testStrategy="Test with valid/invalid tokens.",
                      priority="high", dependencies=["1.1"], status="pending", subtasks=[])
             ]),
        Task(id="2", title="Develop UI Components", description="Create reusable UI components",
             details="Use React and Material UI. Components for buttons, forms, tables.",
             testStrategy="Storybook for component testing.",
             priority="medium", dependencies=["1"], status="pending", subtasks=[])
    ]

    # Ensure the examples directory exists for the output file
    examples_dir = "langgraph_task_agent/examples/"
    if not os.path.exists(examples_dir):
        os.makedirs(examples_dir)
        print(f"Created examples directory: {examples_dir}")

    output_md_path = os.path.join(examples_dir, "generated_task_hierarchy.md")
    print(f"Attempting to write task hierarchy to: {output_md_path}")
    try:
        write_markdown_task_hierarchy(example_tasks, output_md_path)
        print(f"Task hierarchy Markdown file created at {output_md_path}. Please review its content.")
        assert os.path.exists(output_md_path)
        with open(output_md_path, "r", encoding="utf-8") as f:
            generated_md_content = f.read()
            assert "Task: Setup Backend API (ID: 1)" in generated_md_content
            assert "### Subtasks for 1:" in generated_md_content # Check if subtask section title is correct
            assert "#### Task: Define API Models (ID: 1.1)" in generated_md_content # Check subtask heading level
    except Exception as e:
        print(f"Error during write_markdown_task_hierarchy test: {e}")

    if os.path.exists(dummy_prd_path):
        os.remove(dummy_prd_path)
        print(f"Cleaned up dummy PRD file: {dummy_prd_path}")

    print("--- file_utils.py tests complete ---")
