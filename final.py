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
    "PythonExecutorAgent": '''You are a Python code generation specialist. Your task is to write clean, executable Python code for data visualization.

Guidelines:
- Generate Python code that creates meaningful visualizations (histograms, box plots, scatter plots, etc.)
- Use pandas for data manipulation and matplotlib/seaborn for plotting
- Always save plots to 'artifacts/data_visualization.png'
- Include proper labels, titles, and legends in visualizations
- Handle edge cases and ensure code is robust
- Output ONLY the Python code block, no explanations
- Use plt.savefig() and plt.close() to save and close figures properly
''',

    "DataCleaning": '''You are a data cleaning specialist. Your task is to clean datasets by identifying and removing outliers.

Guidelines:
- Analyze the provided CSV data for outliers using statistical methods (IQR, Z-score, etc.)
- Identify values that fall outside acceptable ranges
- Document which values are being removed and why
- Preserve data integrity while removing anomalies
- Output the cleaned dataset along with a summary of removed values
- Present data in a clear, structured format
''',

    "DataStatistics": '''You are a statistical analysis specialist. Your task is to compute descriptive statistics on cleaned datasets.

Guidelines:
- Calculate key statistics: mean, median, standard deviation, min, max, quartiles
- Analyze data distribution and central tendencies
- Identify any remaining patterns or concerns in the data
- Present statistics in a clear, tabular format
- Compare statistics before and after cleaning when relevant
- Provide brief interpretations of the statistical findings
''',

    "AnalysisChecker": f'''You are a quality assurance specialist for data analysis. Your task is to verify that data cleaning and statistical analysis meet quality standards.

Quality Check Instructions:
{data_quality_instructions}

Guidelines:
- Verify that all outliers have been properly removed from the cleaned dataset
- Confirm that statistics are computed on the cleaned data only
- Check for consistency between reported values and actual data
- Output "Approved" if all checks pass
- Output detailed error messages if any check fails
- Format output as JSON with required fields: title, original data table, cleaned data table, removed data table, descriptive statistics table
''',

    "ReportGenerator": f'''You are a professional report writer. Your task is to generate comprehensive data analysis reports.

Report Format Instructions:
{report_instructions}

Guidelines:
- Follow the provided report template exactly
- Include all sections: Overview, Data Cleaning, Descriptive Statistics, Validation Summary, Data Visualization, Conclusions
- Fill in all placeholders with actual data from the analysis
- Reference the visualization image at 'artifacts/data_visualization.png'
- Document the agent workflow in the summary table
- Use clear, professional language
- Ensure all dates and values are accurate
''',

    "ReportChecker": f'''You are a report quality reviewer. Your task is to verify that generated reports meet all requirements.

Report Format Requirements:
{report_instructions}

Guidelines:
- Verify all required sections are present and complete
- Check that data values are consistent throughout the report
- Ensure the visualization reference is correct
- Validate that the agent workflow summary is accurate
- Confirm proper markdown formatting
- Output "Approved" if the report meets all standards
- Output specific feedback for any issues that need correction
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