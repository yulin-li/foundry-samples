# pylint: disable=line-too-long,useless-suppression
# ------------------------------------
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# ------------------------------------

"""
DESCRIPTION:
    This sample demonstrates how to use agent operations with code interpreter from
    the Azure Agents service using a synchronous client.

USAGE:
    python sample_agents_code_interpreter.py

    Before running the sample:

    pip install azure-ai-projects azure-identity

    Set these environment variables with your own values:
    1) PROJECT_ENDPOINT - The project endpoint, as found in the overview page of your
       Azure AI Foundry project.
    2) MODEL_DEPLOYMENT_NAME - The deployment name of the AI model, as found under the "Name" column in 
       the "Models + endpoints" tab in your Azure AI Foundry project.
"""

# <imports>
import os
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import CodeInterpreterTool
from azure.ai.agents.models import FilePurpose, MessageRole
from azure.identity import DefaultAzureCredential
from pathlib import Path
# </imports>

# <client_initialization>
endpoint = os.environ["PROJECT_ENDPOINT"]
model_deployment_name = os.environ["MODEL_DEPLOYMENT_NAME"]

with AIProjectClient(
    endpoint=endpoint,
    credential=DefaultAzureCredential(exclude_interactive_browser_credential=False),
) as project_client:
# </client_initialization>

    # Upload a file and wait for it to be processed
    # [START upload_file_and_create_agent_with_code_interpreter]
    # <file_upload>
    file = project_client.agents.upload_file_and_poll(
        file_path=str(Path(__file__).parent / "nifty_500_quarterly_results.csv"), purpose=FilePurpose.AGENTS
    )
    print(f"Uploaded file, file ID: {file.id}")
    # </file_upload>

    # <code_interpreter_setup>
    code_interpreter = CodeInterpreterTool(file_ids=[file.id])
    # </code_interpreter_setup>

    # <agent_creation>
    # Create agent with code interpreter tool and tools_resources
    agent = project_client.agents.create_agent(
        model=os.environ["MODEL_DEPLOYMENT_NAME"],
        name="my-assistant",
        instructions="You are helpful assistant",
        tools=code_interpreter.definitions,
        tool_resources=code_interpreter.resources,
    )
    # [END upload_file_and_create_agent_with_code_interpreter]
    print(f"Created agent, agent ID: {agent.id}")
    # </agent_creation>

    # <thread_management>
    thread = project_client.agents.create_thread()
    print(f"Created thread, thread ID: {thread.id}")

    # Create a message
    message = project_client.agents.create_message(
        thread_id=thread.id,
        role="user",
        content="Could you please create bar chart in TRANSPORTATION sector for the operating profit from the uploaded csv file and provide file to me?",
    )
    print(f"Created message, message ID: {message.id}")
    # </thread_management>

    # <message_processing>
    run = project_client.agents.create_and_process_run(thread_id=thread.id, agent_id=agent.id)
    print(f"Run finished with status: {run.status}")

    if run.status == "failed":
        # Check if you got "Rate limit is exceeded.", then you want to get more quota
        print(f"Run failed: {run.last_error}")
    # </message_processing>

    # <file_handling>
    project_client.agents.delete_file(file.id)
    print("Deleted file")

    # [START get_messages_and_save_files]
    messages = project_client.agents.list_messages(thread_id=thread.id)
    print(f"Messages: {messages}")

    for image_content in messages.image_contents:
        file_id = image_content.image_file.file_id
        print(f"Image File ID: {file_id}")
        file_name = f"{file_id}_image_file.png"
        project_client.agents.save_file(file_id=file_id, file_name=file_name)
        print(f"Saved image file to: {Path.cwd() / file_name}")

    for file_path_annotation in messages.file_path_annotations:
        print(f"File Paths:")
        print(f"Type: {file_path_annotation.type}")
        print(f"Text: {file_path_annotation.text}")
        print(f"File ID: {file_path_annotation.file_path.file_id}")
        print(f"Start Index: {file_path_annotation.start_index}")
        print(f"End Index: {file_path_annotation.end_index}")
    # [END get_messages_and_save_files]
    # </file_handling>

    last_msg = messages.get_last_text_message_by_role(MessageRole.AGENT)
    if last_msg:
        print(f"Last Message: {last_msg.text.value}")

    # <cleanup>
    project_client.agents.delete_agent(agent.id)
    print("Deleted agent")
    # </cleanup>