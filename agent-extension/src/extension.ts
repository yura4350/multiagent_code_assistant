// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';

// Define interfaces same as the backend
interface Issue {
	line: number;
	column: number | null;
	severity: string;
	rule_id: string;
	message: string;
}

interface Suggestion {
	issue: Issue;
	original_code: string | null;
	fixed_code: string | null;
	rationale: string;
	confidence: number | null;
}

interface AnalyzeResponse {
	issues: Issue[];
	suggestions: Suggestion[];
}

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
		// Currently defaults to the dev server http://vcm-52527.vm.duke.edu:8000
		const config = vscode.workspace.getConfiguration('aiAssistant');
		const backendUrl = config.get<string>('backendUrl', 'http://localhost:8000');

		// Prompt user to select an agent
		const agentPick = await vscode.window.showQuickPick(
			['ALL', 'CODE_STYLE', 'IDIOMS', 'TESTS', 'DESIGN'],
			{ placeHolder: 'Select an AI agent to run (ALL runs every agent)' }
		);

		if (!agentPick) {
			return;
		}

		const agent = agentPick === 'ALL' ? null : agentPick;

		outputChannel.appendLine(`[${new Date().toISOString()}] Analyzing: ${fileName} (${fileContent.length} chars) → ${backendUrl} [agent: ${agentPick}]`);

		try {
			const response = await fetch(`${backendUrl}/analyze`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					file_content: fileContent,
					file_name: fileName,
					agent: agent
				})
			});

			if (!response.ok) {
				throw new Error(`Server error: ${response.status}`);
			}

			const data = await response.json() as AnalyzeResponse;
			outputChannel.appendLine(`Received ${data.issues.length} issue(s), ${data.suggestions.length} suggestion(s).`);

			// Print each issue
			if (data.issues.length > 0) {
				outputChannel.appendLine('\n--- Issues ---');
				for (const issue of data.issues) {
					const col = issue.column !== null ? `:${issue.column}` : '';
					outputChannel.appendLine(`  [${issue.severity}] Line ${issue.line}${col} (${issue.rule_id}): ${issue.message}`);
				}
			}

			// Print each suggestion
			if (data.suggestions.length > 0) {
				outputChannel.appendLine('\n--- Suggestions ---');
				for (const s of data.suggestions) {
					outputChannel.appendLine(`\n  Rule: ${s.issue.rule_id} (Line ${s.issue.line})`);
					outputChannel.appendLine(`  Rationale: ${s.rationale}`);
					if (s.confidence !== null) {
						outputChannel.appendLine(`  Confidence: ${(s.confidence * 100).toFixed(0)}%`);
					}
					if (s.original_code) {
						outputChannel.appendLine(`  Before: ${s.original_code}`);
					}
					if (s.fixed_code) {
						outputChannel.appendLine(`  After:  ${s.fixed_code}`);
					}
				}
			}
		} catch (err) {
			const msg = err instanceof Error ? err.message : String(err);
			outputChannel.appendLine(`Error: ${msg}`);
			vscode.window.showErrorMessage(`AI Assistant: ${msg}`);
		}

		outputChannel.show(true);
	});

	context.subscriptions.push(disposable, outputChannel);
}

// This method is called when your extension is deactivated
export function deactivate() {}
