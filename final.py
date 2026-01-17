# <TODO: Step 3 - Imports>
# Complete the imports for all the necessary components from the semantic_kernel library.
import logging
import os
import asyncio
import pandas as pd
from dotenv import load_dotenv

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, AgentGroupChat, TerminationStrategy
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

load_dotenv()
# -----------------
# Logging Setup
# -----------------
# The logging setup below captures all agent interactions and saves them to 'logs/agent_chat.log'.
# 1. Create a dedicated logger for agent interactions.
agent_logger = logging.getLogger("semantic_kernel.agents")
agent_logger.setLevel(logging.DEBUG)

# 2. Prevent agent logs from propagating to other handlers (like console).
agent_logger.propagate = False

# 3. Create a file handler to write to 'agent_chat.log' in write mode.
agent_chat_handler = logging.FileHandler("logs/agent_chat.log", mode='w')
agent_chat_handler.setLevel(logging.DEBUG)

# 4. Create a minimal formatter to log only the message content.
chat_formatter = logging.Formatter('%(asctime)s - %(name)s:%(message)s')
agent_chat_handler.setFormatter(chat_formatter)

# 5. Add the dedicated file handler to the agent logger.
agent_logger.addHandler(agent_chat_handler)

# 6. Function to log agent messages
def log_agent_message(content):
    try:
        agent_logger.info(f"Agent: {content.role} - {content.name or '*'}: {content.content}")
    except Exception:
        agent_logger.exception("Failed to write agent message to log")

# -----------------
# Environment Setup
# -----------------
# <TODO: Step 2 - Environment Setup>
# Load the API key and endpoint URL from the .env file.

API_KEY = os.getenv("AZURE_OPENAI_KEY")
BASE_URL = os.getenv("URL")
API_VERSION = "2024-12-01-preview"

# -----------------
# Kernel and Chat Service
# -----------------
# <TODO: Step 3 - Kernel Initialization>
# Initialize the Kernel, define the AzureChatCompletion service, and add it to the kernel.
kernel = Kernel()
chat_service = AzureChatCompletion(
    deployment_name="none", 
    api_key=API_KEY,
    base_url=BASE_URL,
    api_version=API_VERSION
)

kernel.add_service(chat_service)

# -----------------
# Helper Functions
# -----------------
# <TODO: Step 4 - Implement Supporting Logic>
# Implement the logic for each of the helper functions below.

def load_quality_instructions(file_path):
    """
    Loads instructional text from a file within the 'specs' directory.

    This function constructs the full path to the file, reads its content,
    and processes it into a list of non-empty, stripped lines.

    Args:
        file_path (str): The name of the file in the 'specs' directory.

    Returns:
        list[str]: A list of strings, where each string is a line of instruction.
                   Returns an empty list if the file does not exist.
    """
    
    for file in os.listdir('specs'):
        if file == file_path:
            with open(os.path.join('specs', file_path), 'r') as f:
                lines = f.readlines()
                instructions = [line.strip() for line in lines if line.strip()]
                return instructions
    
    return []

def load_reports_instructions(file_path):
    """
    Loads report generation instructions from a file within the 'specs' directory.

    Args:
        file_path (str): The name of the file in the 'specs' directory.

    Returns:
        list[str]: A list of strings for building the report. Returns an
                   empty list if the file does not exist.
    """
    for file in os.listdir('specs'):
        if file == file_path:
            with open(os.path.join('specs', file_path), 'r') as f:
                lines = f.readlines()
                instructions = [line.strip() for line in lines if line.strip()]
                return instructions
    return []

def load_logs(file_path):
    """
    Loads agent interaction logs from a file within the 'logs' directory.

    Args:
        file_path (str): The name of the log file in the 'logs' directory.

    Returns:
        list[str]: A list of log entries. Returns an empty list if the file
                   does not exist.
    """
    for file in os.listdir('logs'):
        if file == file_path:
            with open(os.path.join('logs', file_path), 'r') as f:
                lines = f.readlines()
                logs = [line.strip() for line in lines if line.strip()]
                return logs
    return []

def get_csv_name():
    """
    Interactively prompts the user to select a CSV file from the 'data' directory.

    It lists all available .csv files and asks for a numerical selection.

    Returns:
        str: The relative path to the selected CSV file (e.g., 'data/my_file.csv').
    """
    csv_files = [file for file in os.listdir('data') if file.endswith('.csv')]
    if not csv_files:
        raise FileNotFoundError("No CSV files found in the 'data' directory.")

    print("Available CSV files:")
    for i, file in enumerate(csv_files):
        print(f"{i + 1}. {file}")

    while True:
        try:
            choice = int(input("Select a CSV file by number: "))
            if 1 <= choice <= len(csv_files):
                return os.path.join('data', csv_files[choice - 1])
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def load_csv_file(file_path):
    """
    Reads a CSV file and converts its entire content into a single string.

    The CSV data is flattened into a list and then joined by ', '.

    Args:
        file_path (str): The path to the CSV file to load.

    Returns:
        str: A single string containing all the data from the CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        data_as_list = df.astype(str).values.flatten().tolist()
        return ', '.join(data_as_list)
    except Exception as e:
        logging.error(f"Error loading CSV file {file_path}: {e}")   
    return ""

class PythonExecutor:
    """
    A safe executor for dynamically generated Python code strings.

    This class is designed to run code provided by an AI agent in a controlled
    manner. It includes a retry mechanism and captures execution errors.
    """
    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts

    def run(self, code):
        """
        Executes a string of Python code using the exec() function.

        Args:
            code (str): The Python code to execute.

        Returns:
            tuple[bool, str | None]: A tuple containing:
                - A boolean indicating if the execution was successful.
                - The error traceback as a string if an exception occurred,
                  otherwise None.
        """
        for attempt in range(self.max_attempts):
            try:
                local_scope = {}
                exec(code, {}, local_scope)
                return True, None
            except Exception as e:
                logging.error(f"Execution attempt {attempt + 1} failed: {e}")
                if attempt == self.max_attempts - 1:
                    return False, str(e)
        return False, "Not implemented"

def save_final_report(report, path='artifacts/final_report.md'):
    """
    Saves the generated final report to a markdown file.

    Args:
        report (str): The content of the report to be saved.
        path (str, optional): The file path for the saved report.
                              Defaults to 'artifacts/final_report.md'.
    """
    try:
        with open(path, 'w') as f:
            f.write(report)
        logging.info(f"Final report saved to {path}")
    except Exception as e:
        logging.error(f"Error saving final report: {e}")
    


# -----------------
# Agent Instructions
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 1. Complete the AGENT_CONFIG with detailed prompts for each agent.
data_quality_instructions = ''.join(load_quality_instructions("Data_Quality_Instructions.txt"))
report_instructions = ''.join(load_reports_instructions("Report_Instructions.txt"))

AGENT_CONFIG = {
    "PythonExecutorAgent": '''
    AI Agent Persona: Python Visualization Code Generator
    Role: A specialized assistant focused exclusively on generating executable Python code for data visualization.
    Behavior: The agent does not answer questions outside the scope of code generation. It only outputs Python code.
    Response Style: Output ONLY valid Python code. No explanations, no markdown formatting, no commentary.

    Agent Instructions:
    1. Analyze the provided cleaned dataset to determine appropriate visualizations.
    2. Generate Python code that creates meaningful visualizations:
       - Histograms for data distribution
       - Box plots for outlier visualization
       - Bar charts for categorical comparisons
       - Scatter plots for relationships (if applicable)

    Code Requirements:
    - Use pandas for data manipulation
    - Use matplotlib and/or seaborn for plotting
    - Create a figure with multiple subplots if needed
    - Include proper labels, titles, and legends
    - Save the final figure to 'artifacts/data_visualization.png' using plt.savefig()
    - Call plt.close() after saving to free memory
    - Handle edge cases (empty data, missing values)

    Output Format:
    Output ONLY the Python code block. No explanations, no markdown code fences, no additional text.
''',

    "DataCleaning": '''
    AI Agent Persona: Data Cleaning Specialist
    Role: A specialized assistant focused exclusively on cleaning datasets by identifying and removing outliers.
    Behavior: The agent does not answer questions outside the scope of data cleaning.
    Response Style: Always provide results in a clear, structured JSON format.

    Agent Instructions:
    1. Parse the provided CSV data and identify all numeric columns.
    2. For each numeric column, detect outliers using the IQR method:
       - Calculate Q1 (25th percentile) and Q3 (75th percentile)
       - Calculate IQR = Q3 - Q1
       - Identify outliers as values < Q1 - 1.5*IQR or > Q3 + 1.5*IQR
    3. Remove identified outliers from the dataset.
    4. Document all removed values with their original positions.

    Output Format - MUST be valid JSON:
    {
        "original_data": {
            "row_count": <number>,
            "columns": [...],
            "sample_values": [...]
        },
        "outliers_detected": {
            "column_name": [<list of outlier values>],
            ...
        },
        "cleaned_data": {
            "row_count": <number>,
            "values": [...]
        },
        "removal_summary": {
            "total_outliers_removed": <number>,
            "by_column": {...}
        }
    }
''',

    "DataStatistics": '''
    AI Agent Persona: Statistical Analysis Specialist
    Role: A specialized assistant focused exclusively on computing descriptive statistics on cleaned datasets.
    Behavior: The agent does not answer questions outside the scope of statistical analysis.
    Response Style: Always provide calculated results clearly in structured JSON format.

    Agent Instructions:
    1. From the cleaned dataset provided, extract all numeric columns.
    2. Calculate the following descriptive statistics for each numeric column:
       - Count of values
       - Mean (average)
       - Median (50th percentile)
       - Standard deviation
       - Minimum value
       - Maximum value
       - Q1 (25th percentile)
       - Q3 (75th percentile)
    3. Ensure calculations are based ONLY on the cleaned data (post-outlier removal).

    Output Format - MUST be valid JSON:
    {
        "statistics": {
            "<column_name>": {
                "count": <number>,
                "mean": <number>,
                "median": <number>,
                "std_dev": <number>,
                "min": <number>,
                "max": <number>,
                "q1": <number>,
                "q3": <number>
            },
            ...
        },
        "summary": "<brief interpretation of the statistical findings>"
    }
''',

    "AnalysisChecker": f'''
    AI Agent Persona: Data Analysis Validation Auditor
    Role: A specialized agent responsible for verifying that data cleaning and statistical analysis are completed correctly.
    Behavior: The agent does not perform analysis itself but evaluates the completeness and accuracy of other agents' outputs.
    Response Style: Always provide a clear, structured validation report or approval.

    Quality Check Instructions:
    {data_quality_instructions}

    Validation Tasks:
    1. Outlier Removal Check:
       - Verify that the cleaned dataset contains no values previously marked as outliers
       - Confirm outlier detection method was applied correctly (IQR method)

    2. Statistical Validity Check:
       - Confirm descriptive statistics (mean, median, std, min, max) are computed using cleaned data only
       - Verify all required statistics are present for each numeric column
       - Check that count values match between cleaning and statistics outputs

    3. Data Consistency Check:
       - Verify original data, cleaned data, and removed data tables are all present
       - Confirm row counts are consistent (original = cleaned + removed)

    Decision Logic:
    - If ALL checks pass → output "Approved" with validation summary
    - If ANY check fails → output detailed error message specifying:
      * Which check failed
      * What specific requirement was not met
      * What needs to be corrected

    Output Format - MUST be valid JSON:
    {{
        "title": "Approved" or "Failed",
        "original_data_table": [...],
        "cleaned_data_table": [...],
        "removed_data_table": [...],
        "descriptive_statistics": {{...}},
        "validation_notes": "<explanation of validation results>"
    }}
''',

    "ReportGenerator": f'''
    AI Agent Persona: Professional Data Analysis Report Writer
    Role: A specialized assistant focused exclusively on generating comprehensive data analysis reports.
    Behavior: The agent does not perform analysis but compiles results from other agents into a formatted report.
    Response Style: Always output in clean markdown format following the exact template provided.

    Report Format Instructions:
    {report_instructions}

    Agent Instructions:
    1. Extract all relevant data from the analysis results provided:
       - Original dataset information
       - Outliers detected and removed
       - Cleaned dataset summary
       - Descriptive statistics
       - Validation results

    2. Fill in ALL placeholders in the report template:
       - Replace XXXX-XX-XX with the current date
       - Replace XX with actual numeric values
       - Complete all tables with actual data

    3. Include the visualization reference:
       - Use: ![Data Visualization](artifacts/data_visualization.png)

    4. Document the agent workflow in the summary table:
       - List each agent that participated
       - Describe the action taken
       - Include the status/result

    Output Format:
    Output a complete markdown report following the exact template structure.
    Include all sections: Overview, Data Cleaning, Descriptive Statistics, Validation Summary, Data Visualization, Conclusions.
''',

    "ReportChecker": f'''
    AI Agent Persona: Report Quality Assurance Reviewer
    Role: A specialized agent responsible for verifying that generated reports meet all requirements.
    Behavior: The agent does not write reports but evaluates completeness and accuracy of the report.
    Response Style: Always provide a clear validation decision with specific feedback.

    Report Format Requirements:
    {report_instructions}

    Validation Tasks:
    1. Section Completeness Check:
       - Overview section is present and filled
       - Data Cleaning section includes approach, detected outliers, cleaned data summary
       - Descriptive Statistics section has complete statistics table
       - Validation Summary documents iteration results
       - Data Visualization section references the correct image path
       - Conclusions section provides meaningful insights
       - Agent Workflow Summary table is complete

    2. Data Consistency Check:
       - All numeric values are consistent throughout the report
       - Row counts match between sections
       - Statistics values match the analysis output

    3. Format Check:
       - Proper markdown formatting
       - All placeholders have been replaced with actual values
       - Tables are properly formatted
       - Image reference uses correct path: artifacts/data_visualization.png

    Decision Logic:
    - If ALL sections are complete and accurate → output: "Approved"
    - If ANY section is missing or incorrect → output detailed feedback:
      * Which section failed
      * What is missing or incorrect
      * Specific corrections needed

    Output Format:
    "Approved" if all checks pass, OR a detailed correction list if any checks fail.
'''
}


# -----------------
# Agent Factory
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 2. Implement the agent factory function.
def create_agent(name, instructions, service, settings=None):
    """Factory function to create a new ChatCompletionAgent."""
    return ChatCompletionAgent(
        kernel=kernel,  
        service=chat_service,
        name=name,
        instructions=instructions
    )


# -----------------
# Termination Strategy
# -----------------
# A custom termination strategy that stops after user approval.
class ApprovalTerminationStrategy(TerminationStrategy):
    """A custom termination strategy that stops after user approval."""
    async def should_agent_terminate(self, agent, history):
        if "approved" in history[-1].content.lower():
            return True
        return await super().should_agent_terminate(agent, history)


# -----------------
# Agent Instantiation
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 3. Instantiate each agent with the correct name, prompt, and temperature setting.
python_agent = create_agent(
    name="PythonExecutorAgent",
    instructions=AGENT_CONFIG["PythonExecutorAgent"],
    service=chat_service
)

cleaning_agent = create_agent(
    name="DataCleaning",
    instructions=AGENT_CONFIG["DataCleaning"],
    service=chat_service
)

stats_agent = create_agent(
    name="DataStatistics",
    instructions=AGENT_CONFIG["DataStatistics"],
    service=chat_service
)

checker_agent = create_agent(
    name="AnalysisChecker",
    instructions=AGENT_CONFIG["AnalysisChecker"],
    service=chat_service
)

report_agent = create_agent(
    name="ReportGenerator",
    instructions=AGENT_CONFIG["ReportGenerator"],
    service=chat_service
)

report_checker_agent = create_agent(
    name="ReportChecker",
    instructions=AGENT_CONFIG["ReportChecker"],
    service=chat_service
)


# -----------------
# Group Chats
# -----------------
# <TODO: Step 5 - Build the Agents and Teams>
# 4. Create the three agent group chats.
analysis_chat = AgentGroupChat(
    agents=[cleaning_agent, stats_agent, checker_agent],
    termination_strategy=ApprovalTerminationStrategy(
        agents=[checker_agent],
        maximum_iterations=10
    )
)

code_chat = AgentGroupChat(
    agents=[python_agent],
    termination_strategy=ApprovalTerminationStrategy(
        agents=[python_agent],
        maximum_iterations=5
    )
)

report_chat = AgentGroupChat(
    agents=[report_agent, report_checker_agent],
    termination_strategy=ApprovalTerminationStrategy(
        agents=[report_checker_agent],
        maximum_iterations=10
    )
)


# -----------------
# Main Workflow
# -----------------
# <TODO: Step 6 - Orchestrate the Main Workflow>
# Implement the main workflow logic, following the sequence described in the instructions.
async def main():
    """The main entry point for the agentic workflow."""
    # 1. Load the CSV data.
    csv_path = get_csv_name()
    csv_data = load_csv_file(csv_path)
    print(f"Loaded data from {csv_path}")

    # 2. Invoke the analysis chat.
    print("\n--- Starting Analysis Chat ---")
    await analysis_chat.add_chat_message(
        message=f"Please analyze and clean this CSV data, then compute statistics:\n{csv_data}"
    )

    analysis_result = None
    async for content in analysis_chat.invoke():
        log_agent_message(content)
        print(f"{content.name}: {content.content[:200]}..." if len(content.content) > 200 else f"{content.name}: {content.content}")
        analysis_result = content.content

    # 3. Get human approval.
    print("\n--- Analysis Complete ---")
    print("Please review the analysis results above.")
    approval = input("Do you approve the cleaned data? (yes/no): ").strip().lower()

    if approval != "yes":
        print("Analysis not approved. Exiting workflow.")
        return

    # 4. Save the cleaned data.
    print("\n--- Saving Cleaned Data ---")
    with open("artifacts/cleaned_data.txt", "w") as f:
        f.write(analysis_result)
    print("Cleaned data saved to artifacts/cleaned_data.txt")

    # 5. Invoke the code chat to generate and execute visualization code.
    print("\n--- Starting Code Chat ---")
    await code_chat.add_chat_message(
        message=f"Generate Python visualization code for this cleaned data. Save the plot to 'artifacts/data_visualization.png':\n{analysis_result}"
    )

    generated_code = None
    async for content in code_chat.invoke():
        log_agent_message(content)
        print(f"{content.name}: Generated code")
        generated_code = content.content

    # 6. Execute the code in a retry loop.
    print("\n--- Executing Visualization Code ---")
    executor = PythonExecutor(max_attempts=3)

    # Extract code block if wrapped in markdown
    code_to_run = generated_code
    if "```python" in code_to_run:
        code_to_run = code_to_run.split("```python")[1].split("```")[0]
    elif "```" in code_to_run:
        code_to_run = code_to_run.split("```")[1].split("```")[0]

    success, error = executor.run(code_to_run)

    if not success:
        print(f"Code execution failed: {error}")
        # Retry with error feedback
        await code_chat.add_chat_message(
            message=f"The code failed with error: {error}. Please fix it."
        )
        async for content in code_chat.invoke():
            log_agent_message(content)
            generated_code = content.content

        code_to_run = generated_code
        if "```python" in code_to_run:
            code_to_run = code_to_run.split("```python")[1].split("```")[0]
        elif "```" in code_to_run:
            code_to_run = code_to_run.split("```")[1].split("```")[0]

        success, error = executor.run(code_to_run)

    if success:
        print("Visualization code executed successfully!")
    else:
        print(f"Code execution failed after retries: {error}")

    # 7. Save the working visualization script.
    print("\n--- Saving Visualization Script ---")
    with open("artifacts/visualization_script.py", "w") as f:
        f.write(code_to_run)
    print("Visualization script saved to artifacts/visualization_script.py")

    # 8. Invoke the report chat to generate the final report.
    print("\n--- Starting Report Chat ---")
    logs = load_logs("agent_chat.log")
    logs_content = "\n".join(logs[-50:])  # Get last 50 log entries

    await report_chat.add_chat_message(
        message=f"Generate a comprehensive data analysis report based on the following analysis results and agent workflow:\n\nAnalysis Results:\n{analysis_result}\n\nAgent Logs:\n{logs_content}"
    )

    final_report = None
    async for content in report_chat.invoke():
        log_agent_message(content)
        print(f"{content.name}: {content.content[:200]}..." if len(content.content) > 200 else f"{content.name}: {content.content}")
        final_report = content.content

    # 9. Save the final report.
    print("\n--- Saving Final Report ---")
    save_final_report(final_report)
    print("Workflow completed successfully!")


# -----------------
# Main Execution
# -----------------
if __name__ == "__main__":
    asyncio.run(main())