import json
import time
from typing import Dict, List
from anthropic import APIStatusError, APIError
from sqlalchemy.orm import Session

from .chat_db import MsgRole, NewMessage, NewProjectContext, RecordType, add_context, add_messages, get_project_data
from .context import Context
from .tools import execute_tool, get_tools_list

MAINMODEL = "claude-3-5-sonnet-20240620"
TOOLCHECKERMODEL = "claude-3-5-sonnet-20240620"


def build_system_prompt(metadata: str):
    # prompt is based on https://github.com/Doriandarko/claude-engineer
    base_system_prompt = """
    You are Claude, an AI assistant powered by Anthropic's Claude-3.5-Sonnet model. You are an exceptional software developer with vast knowledge across multiple programming languages, frameworks, and best practices. Your capabilities include:

    1. Creating project structures, including folders and files
    2. Writing clean, efficient, and well-documented code
    3. Debugging complex issues and providing detailed explanations
    4. Offering architectural insights and design patterns
    5. Staying up-to-date with the latest technologies and industry trends
    6. Reading and analyzing existing files in the project directory
    7. Listing files in the root directory of the project
    8. Creating workspace for Mify.
    9. Adding service in Mify workspace.
    10. Adding client to service in Mify workspace.
    11. Regenerating Mify boilerplate.
    12. Reading information about the project from metadata.

    Available tools and when to use them:

    1. create_folder: Use this tool to create a new folder at a specified path.
       Example: When setting up a new project structure.

    2. create_file: Use this tool to create a new file at a specified path with content.
       Example: When creating new source code files or configuration files.

    3. search_file: Use this tool to search for specific patterns in a file and get the line numbers where the pattern is found. This is especially useful for large files.
       Example: When you need to locate specific functions or variables in a large codebase.

    4. edit_file: Use this tool to edit a specific range of lines in a file. You should use this after using search_file to identify the lines you want to edit.
       Example: When you need to modify a specific function or block of code.

    5. read_file: Use this tool to read the contents of a file at a specified path.
       Example: When you need to examine the current content of a file before making changes.

    6. list_files: Use this tool to list all files and directories in a specified folder (default is the current directory).
       Example: When you need to understand the current project structure or find specific files.

    7. create_workspace: Use this tool to create Mify workspace to be able to add services.

    8. add_service: Use this tool to create new backend service in Mify workspace.

    9. add_client: Use this tool to add client to service in Mify workspace.

    10. mify_generate: Use this tool to regenerate mify boilerplate. Call this after user updates the openapi schema.

    IMPORTANT: For file modifications, always use the search_file tool first to identify the lines you want to edit, then use the edit_file tool to make the changes. This two-step process ensures more accurate and targeted edits.

    Follow these steps when editing files:
    1. Use the read_file tool to examine the current contents of the file you want to edit.
    2. For longer files, use the search_file tool to find the specific lines you want to edit.
    3. Use the edit_file tool with the line numbers returned by search_file to make the changes.
    4. If the file contains OpenAPI schema run mify_generate after updating it.

    This approach will help you make precise edits to files of any size or complexity.

    Accessing project metadata

    In each user request you'll be optionally provided with metadata about project within <metadata></metadata> tags. In this metadata you'll be able to find records of different types including:
    - file: path to the file, which belongs to the project and service.
    - openapi_schema: path to file containing the OpenAPI schema of the backend service.
    - api_handler: path to the file which contains the implementation of api handler and the name of api call.
    Metadata will presented in this format:
    <metadata>
        <project name="project">
            <services>
                <service name="service">
                    <record type="file">/path/to/file</record>
                    <record type="openapi_schema">/path/to/schema</record>
                    <record type="api_handler">/path/to/echo/handler:/echo</record>
                </service>
            </services>
        </project>
    </metadata>

    When asked to create a project:
    - Always start by creating a root folder for the project using the create_folder tool.
    - Then, create the necessary subdirectories and files within that root folder using the create_folder and create_file tools.
    - Organize the project structure logically and follow best practices for the specific type of project being created.

    When asked to make edits or improvements:
    - ALWAYS START by using the read_file tool to examine the contents of existing files.
    - Use the search_file tool to locate the specific lines you want to edit.
    - Use the edit_file tool to make the necessary changes.
    - Analyze the code and suggest improvements or make necessary edits.
    - Pay close attention to the existing code structure.
    - Ensure that you're replacing old code with new code, not just adding new code alongside the old.
    - After making changes, always re-read the entire file to check for any unintended duplications.
    - If you notice any duplicated code after your edits, immediately remove the duplication and explain the correction.

    Be sure to consider the type of project (e.g., Python, JavaScript, web application) when determining the appropriate structure and files to include.

    Always strive to provide the most accurate, helpful, and detailed responses possible.
    """

    chain_of_thought_prompt = """
    Answer the user's request using relevant tools (if they are available). Before calling a tool, do some analysis within <thinking></thinking> tags. First, think about which of the provided tools is the relevant tool to answer the user's request. Second, go through each of the required parameters of the relevant tool and determine if the user has directly provided or given enough information to infer a value. When deciding if the parameter can be inferred, carefully consider all the context to see if it supports a specific value. If all of the required parameters are present or can be reasonably inferred, close the thinking tag and proceed with the tool call. BUT, if one of the values for a required parameter is missing, DO NOT invoke the function (not even with fillers for the missing params) and instead, ask the user to provide the missing parameters. DO NOT ask for more information on optional parameters if it is not provided.

    Do not reflect on the quality of the returned search results in your response.
    """

    prompt = base_system_prompt + "\n\n" + chain_of_thought_prompt
    if metadata:
        prompt += "\n\nMetadata: " + metadata
    return prompt


class ConversationHistory:
    ctx: Context

    def __init__(self, ctx: Context) -> None:
        self.ctx = ctx
        self.messages = {}

    def get_data(self, db: Session, project_id: int):
        if not project_id in self.messages:
            data = get_project_data(db, project_id)
            self.data = {project_id: {"messages": [], "metadata": {}}}
            for msg in data.messages:
                self.data[project_id]["messages"].append(json.loads(msg.content))
            for record in data.context:
                if not record.service_name in self.data[project_id]["metadata"]:
                    self.data[project_id]["metadata"][record.service_name] = []
                self.data[project_id]["metadata"][record.service_name].append(
                    {"record_type": record.record_type.value, "data": record.data}
                )
        msgs = self.data[project_id]["messages"]
        meta = self.data[project_id]["metadata"]
        self.ctx.logger.info(f"got {len(msgs)} in conversation history")
        return (msgs, meta)

    def save_conversation(
        self, db: Session, project_id: int, messages: List[Dict[str, str]]
    ):
        out = []

        self.ctx.logger.info(f"saving conversation: {len(messages)}")
        for msg in messages:
            role = MsgRole.USER if msg["role"] == "user" else MsgRole.ASSISTANT
            out.append(
                NewMessage(role=role, content=json.dumps(msg), project_id=project_id)
            )
        add_messages(db, out)

        self.data[project_id]["messages"].extend(messages)

    def append_metadata(self, metadata, new_data):
        if new_data:
            if not metadata:
                metadata = {}
            for service_name, records in new_data.items():
                if not service_name in metadata:
                    metadata[service_name] = []
                metadata[service_name].extend(records)
        return metadata

    def save_metadata(self, db: Session, project_id: int, metadata):
        if not metadata:
            return

        out_records = []
        for service_name, records in metadata.items():
            for r in records:
                out_records.append(
                    NewProjectContext(
                        service_name=service_name,
                        record_type=RecordType(r["record_type"]),
                        data=r["data"],
                        project_id=project_id,
                    )
                )
        add_context(db, out_records)

    def metadata_to_xml(self, project_id: int, metadata):
        full_text = ""
        project_block = f"<project name=\"{project_id}\">"
        full_text += project_block
        for service_name, records in metadata.items():
            full_text += f"<service name=\"{service_name}\">"
            for r in records:
                full_text += f"<record type=\"r['record_type']\">"
                full_text += r["data"]
                full_text += "</record>"
            full_text += f"</service>"

        project_end = "</project>"
        full_text += project_end
        return f"<metadata>{full_text}</metadata>"

class LLM:
    ctx: Context
    tools: List

    def __init__(self, ctx: Context) -> None:
        self.conversation_history = []
        self.ctx = ctx
        self.tools = get_tools_list()

    def send_message(self, db: Session, project_id: int, msg: str):
        (history, metadata) = self.ctx.deps.conversation_history.get_data(db, project_id)
        metadata_xml = self.ctx.deps.conversation_history.metadata_to_xml(project_id, metadata)
        self.ctx.logger.info(f"metadata xml: {metadata_xml}")

        current_conversation = []
        current_conversation.append({"role": "user", "content": msg})
        messages = history + current_conversation
        try:
            response = self.ctx.anthropic_client.messages.create(
                model=MAINMODEL,
                max_tokens=4000,
                system=build_system_prompt(metadata_xml),
                messages=messages,
                tools=self.tools,
                tool_choice={"type": "auto"},
            )
            assistant_response = ""
            tool_uses = []
            for content_block in response.content:
                if content_block.type == "text":
                    assistant_response += content_block.text
                elif content_block.type == "tool_use":
                    tool_uses.append(content_block)

            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_input = tool_use.input
                tool_use_id = tool_use.id

                self.ctx.logger.info(f"used tool {tool_name}")
                self.ctx.logger.info(f"tool input: {json.dumps(tool_input, indent=2)}")

                metadata_maybe = None
                metadata = None
                try:
                    (result, metadata_maybe) = execute_tool(tool_name, tool_input)
                    self.ctx.logger.info(f"tool result {result}")
                except Exception as e:
                    result = f"Error executing tool: {str(e)}"
                    self.ctx.logger.info(f"tool error {result}")

                current_conversation.append(
                    {
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_use",
                                "id": tool_use_id,
                                "name": tool_name,
                                "input": tool_input,
                            }
                        ],
                    }
                )
                current_conversation.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": result,
                            }
                        ],
                    }
                )

                if metadata_maybe:
                    metadata = self.ctx.deps.conversation_history.append_metadata(metadata, metadata_maybe)

                messages = history + current_conversation

                try:
                    tool_response = self.ctx.anthropic_client.messages.create(
                        model=TOOLCHECKERMODEL,
                        max_tokens=4000,
                        system=build_system_prompt(metadata_xml),
                        messages=messages,
                        tools=self.tools,
                        tool_choice={"type": "auto"},
                    )

                    tool_checker_response = ""
                    for tool_content_block in tool_response.content:
                        if tool_content_block.type == "text":
                            tool_checker_response += tool_content_block.text
                    assistant_response += "\n\n" + tool_checker_response
                except APIError as e:
                    error_message = f"Error in tool response: {str(e)}"
                    self.ctx.logger.info(f"error {error_message}")
                    assistant_response += f"\n\n{error_message}"

            current_conversation.append(
                {"role": "assistant", "content": assistant_response}
            )
            self.ctx.deps.conversation_history.save_conversation(
                db, project_id, current_conversation
            )
            self.ctx.deps.conversation_history.save_metadata(db, project_id, metadata)

            return {"msg": assistant_response, "raw": response}
        except APIStatusError as e:
            if e.status_code == 429:
                self.ctx.logger.info(f"error 429, retrying")
                time.sleep(5)
                return self.send_message(db, project_id, msg)
            else:
                raise RuntimeError(f"API Error {str(e)}")
        except APIError as e:
            self.ctx.logger.info(f"API Error: {str(e)}")
            raise RuntimeError(f"API Error {str(e)}")
