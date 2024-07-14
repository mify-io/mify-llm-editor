import difflib
from importlib import metadata
import os
import re
import yaml
import subprocess
from typing import Any, Dict, Optional, Tuple


def get_tools_list():
    return [
        {
            "name": "create_folder",
            "description": "Create a new folder at the specified path. Use this when you need to create a new directory in the project structure.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path where the folder should be created",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "create_file",
            "description": "Create a new file at the specified path with content. Use this when you need to create a new file in the project structure.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path where the file should be created",
                    },
                    "content": {
                        "type": "string",
                        "description": "The content of the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
        {
            "name": "search_file",
            "description": "Search for a specific pattern in a file and return the line numbers where the pattern is found. Use this to locate specific code or text within a file.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to search",
                    },
                    "search_pattern": {
                        "type": "string",
                        "description": "The pattern to search for in the file",
                    },
                },
                "required": ["path", "search_pattern"],
            },
        },
        {
            "name": "edit_file",
            "description": "Edit a specific range of lines in a file. Use this after using search_file to identify the lines you want to edit.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to edit",
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "The starting line number of the edit",
                    },
                    "end_line": {
                        "type": "integer",
                        "description": "The ending line number of the edit",
                    },
                    "new_content": {
                        "type": "string",
                        "description": "The new content to replace the specified lines",
                    },
                },
                "required": ["path", "start_line", "end_line", "new_content"],
            },
        },
        {
            "name": "read_file",
            "description": "Read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to read",
                    }
                },
                "required": ["path"],
            },
        },
        {
            "name": "list_files",
            "description": "List all files and directories in the specified folder. Use this when you need to see the contents of a directory.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the folder to list (default: current directory)",
                    }
                },
            },
        },
        {
            "name": "create_workspace",
            "description": "Create mify workspace",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the workspace to list (default: current directory)",
                    },
                },
                "required": ["path"],
            },
        },
        {
            "name": "create_service",
            "description": "Create mify service",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the workspace to list (default: current directory)",
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the service",
                    },
                    "language": {
                        "type": "string",
                        "description": "The language of the service",
                    },
                },
                "required": ["path", "name", "language"],
            },
        },
        {
            "name": "add_client",
            "description": "Add client to service",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the workspace to list (default: current directory)",
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the service",
                    },
                    "client_name": {
                        "type": "string",
                        "description": "Name of the client service",
                    },
                },
                "required": ["path", "name", "client_name"],
            },
        },
        {
            "name": "mify_generate",
            "description": "Regenerate mify boilerplate",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the workspace to list (default: current directory)",
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the service",
                    },
                },
                "required": ["path", "name"],
            },
        },
    ]


def create_folder(path) -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        os.makedirs(path, exist_ok=True)
        return (f"Folder created: {path}", None)
    except Exception as e:
        return (f"Error creating folder: {str(e)}", None)


def create_file(path, content="") -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        with open(path, "w") as f:
            f.write(content)
        return (f"File created: {path}", None)
    except Exception as e:
        return (f"Error creating file: {str(e)}", None)


def search_file(path, search_pattern) -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        with open(path, "r") as file:
            content = file.readlines()

        matches = []
        for i, line in enumerate(content, 1):
            if re.search(search_pattern, line):
                matches.append(i)

        return (f"Matches found at lines: {matches}", None)
    except Exception as e:
        return (f"Error searching file: {str(e)}", None)


def generate_and_apply_diff(
    original_content, new_content, path
) -> Tuple[str, Optional[Dict[str, Any]]]:
    diff = list(
        difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3,
        )
    )

    if not diff:
        return ("No changes detected.", None)

    try:
        with open(path, "w") as f:
            f.writelines(new_content)

        added_lines = sum(
            1 for line in diff if line.startswith("+") and not line.startswith("+++")
        )
        removed_lines = sum(
            1 for line in diff if line.startswith("-") and not line.startswith("---")
        )

        summary = f"Changes applied to {path}:\n"
        summary += f"  Lines added: {added_lines}\n"
        summary += f"  Lines removed: {removed_lines}\n"

        return (summary, None)

    except Exception as e:
        print(f"Error: {str(e)}")
        return (f"Error applying changes: {str(e)}", None)


def edit_file(
    path, start_line, end_line, new_content
) -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        with open(path, "r") as file:
            content = file.readlines()

        original_content = "".join(content)

        start_index = start_line - 1
        end_index = end_line

        content[start_index:end_index] = new_content.splitlines(True)

        new_content = "".join(content)

        diff_result = generate_and_apply_diff(original_content, new_content, path)

        return (
            f"Successfully edited lines {start_line} to {end_line} in {path}\n{diff_result}",
            None,
        )
    except Exception as e:
        return (f"Error editing file: {str(e)}", None)


def read_file(path) -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        with open(path, "r") as f:
            content = f.read()
        return (content, None)
    except Exception as e:
        return (f"Error reading file: {str(e)}", None)


def list_files(path=".") -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        files = os.listdir(path)
        return ("\n".join(files), None)
    except Exception as e:
        return (f"Error listing files: {str(e)}", None)


def call_binary(path, args) -> str:
    try:
        cmdline = [path, *args]
        print(f"running {cmdline}")
        output = subprocess.check_output(cmdline)
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"


def create_workspace(path=".") -> Tuple[str, Optional[Dict[str, Any]]]:
    out = call_binary("mify", ["init", "-p", path])
    return (out, None)


def get_openapi_paths(file_path):
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            paths = data.get("paths", [])
            return paths
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file: {e}")


def build_service_metadata(name, path):
    schema = path + f"/schemas/{name}/api/api.yaml"
    metadata = {
        name: [
            {
                "record_type": "openapi_schema",
                "data": schema,
            }
        ],
    }

    paths = get_openapi_paths(schema)
    for p in paths:
        metadata[name].append(
            {
                "record_type": "api_handler",
                "data": f"{path}/py-services/{name}/handlers{p}/service.py:{p}",
            }
        )
    return metadata

def create_service(name, language, path=".") -> Tuple[str, Optional[Dict[str, Any]]]:
    # python needs underscores in packages
    name = name.replace('-', '_')
    out = call_binary(
        "mify", ["add", "service", name, "--language", language, "-p", path]
    )
    return (out, build_service_metadata(name, path))

def mify_generate(name, path=".")  -> Tuple[str, Optional[Dict[str, Any]]]:
    name = name.replace('-', '_')
    out = call_binary(
        "mify", ["generate", "-p", path]
    )
    return (out, build_service_metadata(name, path))

def add_client(name, client_name, path=".") -> Tuple[str, Optional[Dict[str, Any]]]:
    name = name.replace('-', '_')
    out = call_binary("mify", ["add", "client", name, "--to", client_name, "-p", path])
    return (out, None)

def execute_tool(tool_name, tool_input) -> Tuple[str, Optional[Dict[str, Any]]]:
    try:
        if tool_name == "create_folder":
            print(f"create_folder {tool_input['path']}")
            return create_folder(tool_input["path"])
        elif tool_name == "create_file":
            print(f"create_file {tool_input['path']}")
            return create_file(tool_input["path"], tool_input.get("content", ""))
        elif tool_name == "search_file":
            print(f"search_file {tool_input['path']}")
            return search_file(tool_input["path"], tool_input["search_pattern"])
        elif tool_name == "edit_file":
            print(f"edit_file {tool_input['path']}")
            return edit_file(
                tool_input["path"],
                tool_input["start_line"],
                tool_input["end_line"],
                tool_input["new_content"],
            )
        elif tool_name == "read_file":
            print(f"read_file {tool_input['path']}")
            return read_file(tool_input["path"])
        elif tool_name == "list_files":
            print(f"list_files {tool_input['path']}")
            return list_files(tool_input.get("path", "."))
        elif tool_name == "create_workspace":
            return create_workspace(tool_input.get("path", "."))
        elif tool_name == "create_service":
            return create_service(
                tool_input["name"], tool_input["language"], tool_input.get("path", ".")
            )
        elif tool_name == "add_client":
            return add_client(
                tool_input["name"],
                tool_input["client_name"],
                tool_input.get("path", "."),
            )
        elif tool_name == "mify_generate":
            return mify_generate(
                tool_input["name"], tool_input.get("path", ".")
            )
        else:
            return (f"Unknown tool: {tool_name}", None)
    except KeyError as e:
        return (
            f"Error: Missing required parameter {str(e)} for tool {tool_name}",
            None,
        )
    except Exception as e:
        return (f"Error executing tool {tool_name}: {str(e)}", None)
