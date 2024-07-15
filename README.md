<h1 align="center">
Mify LLM Editor
</h1>

<div align="center">
LLM code generation paired with templates. Create backend service and update code via LLM.
This project is very much alpha.
<img src="https://github.com/user-attachments/assets/ad06d555-ec59-4cb9-bfaa-2a973daca3eb">
</div>

## About the project

Currently, in most cases when I use LLMs for coding, it can only help with
implementation of individual functions and components. There are multiple tools
and startups working on adding a full code repository to the model's context, so
it can make suggestions based on it, but complex multi-file changes are still
clunky for models.

I wanted to see if it would be simpler and more reliable for the model to
work on a repository with a known and more rigid structure, and this is where Mify
comes in. [Mify CLI](https://github.com/mify-io/mify) can generate backend
service templates with a predefined directory structure based on OpenAPI
schema. Assuming that all services in the repository are generated by Mify we
can pass the project structure in the prompt and help the model with the code
generation.

## Features

- Local web app to chat with LLM
- LLM can work with multiple projects and keep context on files
- Local agent that can do actions on your repository:
    - Read/update/search files and directories
    - Create Python services using Mify

## Demo

<div align="center">
    
https://github.com/user-attachments/assets/fa96c7e1-cc33-4e1a-bb10-68c87d9f6173

</div>

In this demo, I'm asking LLM to create an Echo service.
- It calls Mify to create workspace and service
- Updates the OpenAPI schema with the /echo handler
- Updates the handler code to return the message sent in the request

And the service is working fine after these updates!

## Installation

### Prerequisites

- Python 3.7+
- [Mify 0.1.19+](https://mify.io/docs/#installing-mify)
- [Anthropic API key](https://docs.anthropic.com/en/api/getting-started)

Python setup:
```
$ virtualenv venv
$ . ./venv/bin/activate
$ pip install -r llm-worker/requirements.txt

```

Prepare the environment for worker:
```
$ export DATABASE_URL="sqlite:///$PWD/storage.db"
$ export ANTHROPIC_API_KEY="sk-ant-api<Your key>"
```

Prepare database:
```
cd llm-worker && alembic upgrade head && cd -
```

Run llm-worker:
```
$ uvicorn llm-worker.main:app --port 3001
```

Run webapp:
```
$ cd webapp
$ npm run dev
```

## Usage

### Working with Mify services

After opening the chat in your browser try asking it to create a service. LLM
should ask for the project location and service name, after you provide them it
will run mify to create a service. It could take a bit of back and forth with
the LLM, but most of the time if you just tell it to continue, it will finish
running the commands. Then ask it to update the OpenAPI schema for the service
and it should be able to locate it and the corresponding handler and update the code there.

To run the generated service go to <project-folder>/py-services and run:
```
$ . ./venv/bin/activate
$ python -m <service-name>
```

And hopefully, it will work. If not you can try asking LLM to fix the issue.

### Editing code

Claude AI is really good at editing Tailwind-based pages, so you can use the chat to work on any other project.
The web app for this agent is generated with it!

## Contributing

We welcome contributions to this project! Check out the GitHub issues to get started.

## License

This project is licensed under the MIT License.

## Contact

For questions and suggestions, you can ping me via [email](mailto:ivan@mify.io)
or via [Twitter](https://twitter.com/ichebykin).
If you have any issues just post them on the GitHub repository.
