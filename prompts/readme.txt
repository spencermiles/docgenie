Please analyze the following code repository and generate comprehensive technical documentation. 

Repository Path: {repo_path}

Files in repository:
{files_content}

Please generate a comprehensive technical documentation that includes:

1. **Project Overview**: What this project does, its purpose and main functionality
2. **Architecture**: High-level architecture and design patterns used. Include mermaid diagrams where applicable.
3. **Directory Structure**: Explanation of the project organization
4. **Key Components**: Main modules, classes, and functions with their purposes
5. **Dependencies**: External libraries and frameworks used
6. **Setup and Installation**: How to set up and run the project
7. **Usage Examples**: How to use the main features
8. **API Documentation**: If applicable, document the main APIs/interfaces
9. **Configuration**: Any configuration files or environment variables
10. **Development**: How to contribute, build, test, and deploy

Rules:
1. Focus on being comprehensive but concise. Use markdown formatting for better readability.
2. Make sure to explain the purpose and functionality rather than just listing what exists.
3. If you can't clearly determine how to document a section, include the section in the documentation but mark it as "UNDETERMINED" and explain why you couldn't determine it. 
4. Quote ALL mermaid keys to ensure no parse errors are present
    CORRECT: Ext_Cloud["Cloud Storage (GCS)"]
    INCORRECT (will fail to render): Ext_Cloud[Cloud Storage (GCS)]