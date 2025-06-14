# Prompts for Task Complexity Analysis

Source: `scripts/modules/task-manager/analyze-task-complexity.js`

## System Prompt

```text
You are an expert software architect and project manager analyzing task complexity. Respond only with the requested valid JSON array.
```

## User Prompt Structure (from `generateInternalComplexityAnalysisPrompt`)

```text
Analyze the following tasks to determine their complexity (1-10 scale) and recommend the number of subtasks for expansion. Provide a brief reasoning and an initial expansion prompt for each.

Tasks:
[tasksString]

Respond ONLY with a valid JSON array matching the schema:
[
  {
    "taskId": <number>,
    "taskTitle": "<string>",
    "complexityScore": <number 1-10>,
    "recommendedSubtasks": <number>,
    "expansionPrompt": "<string>",
    "reasoning": "<string>"
  },
  // ... more task analysis objects
]

Do not include any explanatory text, markdown formatting, or code block markers before or after the JSON array.
```

**Dynamic Placeholders:**
*   `[tasksString]`: A JSON string representing the array of task objects to be analyzed.
```
