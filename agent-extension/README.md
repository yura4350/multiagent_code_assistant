# AI Assistant Extension

A VS Code extension that connects to an AI-powered code analysis backend to scan for issues, suggest fixes, and apply them directly in your editor.

## Features

- **Scan for Issues**: Detect code style, idiom, or test issues in the active file
- **Scan Issues + Suggest Fixes (for one agent)**: Get issues and AI-generated fix suggestions with inline diff preview (or test file) for the selected agent.
- **Scan Issues + Suggest Fixes (for all agents)**: Run all agents at once; option to apply changes.
- **Quick Fixes**: Hover over squiggly underlines to apply a single fix or all fixes via lightbulb actions.

## Extension Settings

- `aiAssistant.backendUrl`: Backend server URL (default: `http://vcm-52418.vm.duke.edu:4003`)
- If you're unable to connect to the server using the above URL, try fixing the url to `http://vcm-52427.vm.duke.edu:4003` (dev server) manually:

    1. Open Settings (`Cmd+,`)
    2. Search for "Ai Assistant: Backend Url". 
    3. Modify the URL to `http://vcm-52427.vm.duke.edu:4003`

## Installation

1. Download the `agent-extension-0.0.1.vsix` file.
2. Open VS Code.
3. Open the Extensions panel (`Cmd+Shift+X`).
4. Click the `...` menu (top-right of the panel) and select **Install from VSIX...**.
5. Select the downloaded `.vsix` file.
6. Reload VS Code when prompted.

## Usage

Open a Python file, then run **AI Code Analysis: Analyze Current File** from the Command Palette (`Cmd+Shift+P`).

## Note
- When running **Scan Issues + Suggest Fixes (for one agent)**, a diff preview and inline suggestions will appear. On the bottom right corner, there will be an option to apply the changes or ignore.
- For `Tests` specifically, the extension will detect whether a test file with the name `test_<current_file_name>.py` exists in the repository. If it exists, tests will be added on top of the existing file, and if not, a new file with the corresponding name will by generated.
- When running for all agents, you'll be provided with options to apply the change for each agents.
- All LLM-powered agents will take some time to load the issues and suggestions. Please wait 1-2 minutes until the agents finish their analysis.
- It takes around 30-60 seconds for the apply option to pop up after printing issues and suggestions in the output channel.
- If you get no issues or suggestions for the `Code Style` option on our `sample_bad_code_style.py`, try running the extension again after removing the first line (`# ruff: noqa`) of the file.