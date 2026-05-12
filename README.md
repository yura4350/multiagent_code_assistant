Multiagent AI Code Assistant
====

This project implements various agents to make code improvements.

### Tutorial, LLMs, and other Code used
- GPT-5.3 Codex - suggestions about how to use Ruff
- Claude Code (Sonnet 4.6) - help understand minimal Extension API and its capabilities, some testing
- Claude Code - Generate sample files


### Resource Attributions


### Running the Program

Main class: `main.py`

Data files needed: any file you wish to inspect using our AI agents. Some of the data files to try out are provided in the `data/` folder

Inputs: file path to reference the file, choice of agent (optional), --apply flag

Known Bugs:

### Deployed dev server

- Dev: http://vcm-53428.vm.duke.edu:4003/

### Instructions

#### CLI non-docker interface
Create and activate virtual environment as below:
```
python3 -m venv <venv-name-here>
source <venv-name-here>/bin/activate # macOS/Linux
pip install -r requirements.txt
```

To run our application, you may choose between 4 agents: `CODE_STYLE`, `IDIOMS`, `TESTS`, `CLEAN_CODE`.
If you run the application without specifying an agent, the system will run all four agents.

```
python -m src.main <path_to_your_file> --agent <agent_chosen> <include or exclude --apply flag>
python -m src.main data/sample_bad_code_style.py --agent CODE_STYLE --apply
```

#### Extension API

See the [agent-extension README](agent-extension/README.md) for installation and usage instructions.

The packaged extension ships pre-configured to talk to the deployed dev server. To use a local backend instead, run `docker-compose up` (see [Running the backend locally](#running-the-backend-locally)) and override `aiAssistant.backendUrl` to `http://localhost:4003`.

#### Server-deployed REST API
- To verify that the program is up and running on the server you can go to the dev server at http://vcm-53428.vm.duke.edu:4003/health and try out the endpoints.

#### Running the backend locally

```bash
# Requires Docker and a populated .env (LITELLM_TOKEN, MODEL_ID, etc.)
docker-compose up --build
# Backend is now reachable at http://localhost:4003
# Verify: curl http://localhost:4003/health
```

Then point the extension at it by overriding `aiAssistant.backendUrl` in VS Code settings to `http://localhost:4003`.

### Notes/Assumptions
- To test the program, run
```python
python -m pytest -q
```
- To check if program meets the project's style and quality standards before pushing run the local pipeline:
```bash
# Requires Docker to be running
gitlab-ci-local
```

