// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	const outputChannel = vscode.window.createOutputChannel('AI Assistant');
	outputChannel.appendLine('AI Assistant extension activated.');

	const disposable = vscode.commands.registerCommand('agent-extension.analyze', async () => {
		// Get the current active editor
		const editor = vscode.window.activeTextEditor;
		if (!editor) {
			vscode.window.showWarningMessage('AI Assistant: No active editor found.');
			return;
		}

		// Retrieve context of the current file
		const document = editor.document;
		const fileContent = document.getText();

		// Extract file name
		const fileName = document.fileName.split('/').pop();

		// Read backend server URL from configuration
		const config = vscode.workspace.getConfiguration('aiAssistant');
		const backendUrl = config.get<string>('backendUrl', 'http://vcm-52527.vm.duke.edu:8000');

		outputChannel.appendLine(`[${new Date().toISOString()}] Analyzing: ${fileName} (${fileContent.length} chars) → ${backendUrl}`);
		outputChannel.show(true);
	});

	context.subscriptions.push(disposable, outputChannel);
}

// This method is called when your extension is deactivated
export function deactivate() {}
