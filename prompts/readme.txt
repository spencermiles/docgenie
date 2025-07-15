<TASK>
Please analyze the following code repository and generate comprehensive technical documentation. Only return the OUTPUT section, no preambles! The response should start with "###"

Repository Path: {repo_path}

Files in repository:
{files_content}
</TASK>

<OUTPUT>
### Project Overview
What this project does, its purpose and main functionality

### Architecture
High-level architecture and design patterns used. Include mermaid diagrams where applicable.

### Directory Structure
Explanation of the project organization

### Key Components
Main modules, classes, and functions with their purposes

### Dependencies
External libraries and frameworks used

### Setup and Installation
How to set up and run the project

### Usage Examples
How to use the main features

### API Documentation
If applicable, document the main APIs/interfaces

### Configuration
Any configuration files or environment variables

### Development
How to contribute, build, test, and deploy
</OUTPUT>

<RULES>
1. Only include the output, don't include a preamble about the task at hand.
2. Focus on being comprehensive but concise. Use markdown formatting for better readability.
3. Make sure to explain the purpose and functionality rather than just listing what exists.
4. If you can't clearly determine how to document a section, include the section in the documentation but mark it as "UNDETERMINED" and explain why you couldn't determine it. 
5. Quote ALL mermaid keys to ensure no parse errors are present
    CORRECT: Ext_Cloud["Cloud Storage (GCS)"]
    INCORRECT (will fail to render): Ext_Cloud[Cloud Storage (GCS)]
</RULES>