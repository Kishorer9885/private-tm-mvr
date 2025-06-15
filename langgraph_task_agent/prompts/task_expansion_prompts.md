# Prompts for Task Expansion (Subtask Generation)

Source: `scripts/modules/task-manager/expand-task.js`

These prompts are used to break down a parent task into detailed subtasks.

## 1. Main System Prompt (Standard Expansion)

Used with `generateMainUserPrompt`.

```text
You are an AI assistant helping with task breakdown for software development.
You need to break down a high-level task into [subtaskCount] specific subtasks that can be implemented one by one.

Subtasks should:
1. Be specific and actionable implementation steps
2. Follow a logical sequence
3. Each handle a distinct part of the parent task
4. Include clear guidance on implementation approach
5. Have appropriate dependency chains between subtasks (using the new sequential IDs)
6. Collectively cover all aspects of the parent task

For each subtask, provide:
- id: Sequential integer starting from the provided nextSubtaskId
- title: Clear, specific title
- description: Detailed description
- dependencies: Array of prerequisite subtask IDs (use the new sequential IDs)
- details: Implementation details
- testStrategy: Optional testing approach

Respond ONLY with a valid JSON object containing a single key "subtasks" whose value is an array matching the structure described. Do not include any explanatory text, markdown formatting, or code block markers.
```

**Dynamic Placeholders:**
*   `[subtaskCount]`: The target number of subtasks to generate.

## 2. Main User Prompt (Standard Expansion)

Used with `generateMainSystemPrompt`.

```text
Break down this task into exactly [subtaskCount] specific subtasks:

Task ID: [task.id]
Title: [task.title]
Description: [task.description]
Current details: [task.details_or_None]
[additionalContext_if_any]

Return ONLY the JSON object containing the "subtasks" array, matching this structure:
[schemaDescription_for_subtasks]
```

**Dynamic Placeholders:**
*   `[subtaskCount]`: The target number of subtasks.
*   `[task.id]`: ID of the parent task.
*   `[task.title]`: Title of the parent task.
*   `[task.description]`: Description of the parent task.
*   `[task.details_or_None]`: Current details of the parent task, or "None".
*   `[additionalContext_if_any]`: Optional additional context provided by the user, prepended with "Additional context: ".
*   `[schemaDescription_for_subtasks]`: A string describing the JSON structure for the subtasks array, including an example subtask with `id` starting from `[nextSubtaskId]`.
*   `[nextSubtaskId]`: The starting ID for the new subtasks.

## 3. Research User Prompt (Expansion with Research)

Used when `useResearch` is true. The system prompt for research is simpler: "You are an AI assistant that responds ONLY with valid JSON objects as requested. The object should contain a 'subtasks' array." (or similar, as the code uses a generic one for `generateTextService` with research role).

```text
Analyze the following task and break it down into exactly [subtaskCount] specific subtasks using your research capabilities. Assign sequential IDs starting from [nextSubtaskId].

Parent Task:
ID: [task.id]
Title: [task.title]
Description: [task.description]
Current details: [task.details_or_None]
[additionalContext_if_any_research]

CRITICAL: Respond ONLY with a valid JSON object containing a single key "subtasks". The value must be an array of the generated subtasks, strictly matching this structure:
[schemaDescription_for_subtasks_research]

Important: For the 'dependencies' field, if a subtask has no dependencies, you MUST use an empty array, for example: "dependencies": []. Do not use null or omit the field.

Do not include ANY explanatory text, markdown, or code block markers. Just the JSON object.
```

**Dynamic Placeholders:**
*   `[subtaskCount]`: The target number of subtasks.
*   `[nextSubtaskId]`: The starting ID for the new subtasks.
*   `[task.id]`: ID of the parent task.
*   `[task.title]`: Title of the parent task.
*   `[task.description]`: Description of the parent task.
*   `[task.details_or_None]`: Current details of the parent task, or "None".
*   `[additionalContext_if_any_research]`: Optional additional context, prepended with "Consider this context: ".
*   `[schemaDescription_for_subtasks_research]`: A string describing the JSON structure for the subtasks array, including an example subtask with `id` starting from `[nextSubtaskId]`.

## 4. Simplified System Prompt (When Using Complexity Report's `expansionPrompt`)

Used when an `expansionPrompt` is available from the complexity analysis report. The user prompt in this case *is* the `expansionPrompt` from the report, potentially augmented with `additionalContext` and `complexityReasoningContext`.

```text
You are an AI assistant helping with task breakdown. Generate exactly [finalSubtaskCount] subtasks based on the provided prompt and context. Respond ONLY with a valid JSON object containing a single key "subtasks" whose value is an array of the generated subtask objects. Each subtask object in the array must have keys: "id", "title", "description", "dependencies", "details", "status". Ensure the 'id' starts from [nextSubtaskId] and is sequential. Ensure 'dependencies' only reference valid prior subtask IDs generated in this response (starting from [nextSubtaskId]). Ensure 'status' is 'pending'. Do not include any other text or explanation.
```

**Dynamic Placeholders:**
*   `[finalSubtaskCount]`: The target number of subtasks, derived from explicit input, complexity report, or default.
*   `[nextSubtaskId]`: The starting ID for the new subtasks.
```
