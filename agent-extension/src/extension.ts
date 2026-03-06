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

interface ScanResponse {
	issues: Issue[];
}

interface SuggestResponse {
	suggestions: Suggestion[];
}

interface ApplyResponse {
	fixed_content: string;
	remaining_issues: Issue[];
}

function printIssues(issues: Issue[], outputChannel: vscode.OutputChannel) {
	if (issues.length === 0) {
		outputChannel.appendLine('No issues found.');
		return;
	}
	outputChannel.appendLine('\n--- Issues ---');
	for (const issue of issues) {
		const col = issue.column !== null ? `:${issue.column}` : '';
		outputChannel.appendLine(`  [${issue.severity}] Line ${issue.line}${col} (${issue.rule_id}): ${issue.message}`);
	}
}

function printSuggestions(suggestions: Suggestion[], outputChannel: vscode.OutputChannel) {
	if (suggestions.length === 0) { return; }
	outputChannel.appendLine('\n--- Suggestions ---');
	for (const s of suggestions) {
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

function issuesToDiagnostics(issues: Issue[], document: vscode.TextDocument): vscode.Diagnostic[] {
	return issues.map(issue => {
		const line = Math.max(0, issue.line - 1); // convert 1-based to 0-based
		const col = issue.column !== null ? Math.max(0, issue.column - 1) : 0;
		const lineLength = document.lineAt(line).text.length;
		const range = new vscode.Range(line, col, line, lineLength);

		const severity = issue.severity === 'error'
			? vscode.DiagnosticSeverity.Error
			: issue.severity === 'warning'
				? vscode.DiagnosticSeverity.Warning
				: vscode.DiagnosticSeverity.Information;

		const diagnostic = new vscode.Diagnostic(range, issue.message, severity);
		diagnostic.code = issue.rule_id;
		diagnostic.source = 'AI Assistant';
		return diagnostic;
	});
}

// Virtual document provider for diff preview
const previewScheme = 'ai-assistant-preview';
const previewContentMap = new Map<string, string>();

// Store suggestions per document for code actions (quick fixes)
interface StoredSuggestions {
	fileContent: string;
	suggestions: Suggestion[];
	backendUrl: string;
	agent: string;
}
const documentSuggestions = new Map<string, StoredSuggestions>();

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {

	const outputChannel = vscode.window.createOutputChannel('AI Assistant');
	const diagnosticCollection = vscode.languages.createDiagnosticCollection('ai-assistant');
	outputChannel.appendLine('AI Assistant extension activated.');

	const previewProvider = vscode.workspace.registerTextDocumentContentProvider(previewScheme, {
		provideTextDocumentContent(uri: vscode.Uri): string {
			return previewContentMap.get(uri.toString()) ?? '';
		}
	});
	context.subscriptions.push(previewProvider);

	// Command: apply a single suggestion
	const applySingleFix = vscode.commands.registerCommand(
		'agent-extension.applySingleFix',
		async (documentUri: vscode.Uri, suggestion: Suggestion) => {
			const stored = documentSuggestions.get(documentUri.toString());
			if (!stored) { return; }
			const document = await vscode.workspace.openTextDocument(documentUri);
			const fileName = documentUri.path.split('/').pop();
			const applyResponse = await fetch(`${stored.backendUrl}/agents/${stored.agent}/apply`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ file_content: stored.fileContent, file_name: fileName, suggestions: [suggestion] })
			});
			if (!applyResponse.ok) {
				vscode.window.showErrorMessage(`AI Assistant: apply failed (${applyResponse.status})`);
				return;
			}
			const applyData = await applyResponse.json() as ApplyResponse;
			const edit = new vscode.WorkspaceEdit();
			edit.replace(documentUri, new vscode.Range(document.positionAt(0), document.positionAt(stored.fileContent.length)), applyData.fixed_content);
			await vscode.workspace.applyEdit(edit);
			diagnosticCollection.set(documentUri, issuesToDiagnostics(applyData.remaining_issues, document));
		}
	);

	// Command: apply all suggestions
	const applyAllFixes = vscode.commands.registerCommand(
		'agent-extension.applyAllFixes',
		async (documentUri: vscode.Uri) => {
			const stored = documentSuggestions.get(documentUri.toString());
			if (!stored) { return; }
			const document = await vscode.workspace.openTextDocument(documentUri);
			const fileName = documentUri.path.split('/').pop();
			const applyResponse = await fetch(`${stored.backendUrl}/agents/${stored.agent}/apply`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ file_content: stored.fileContent, file_name: fileName, suggestions: stored.suggestions })
			});
			if (!applyResponse.ok) {
				vscode.window.showErrorMessage(`AI Assistant: apply failed (${applyResponse.status})`);
				return;
			}
			const applyData = await applyResponse.json() as ApplyResponse;
			const edit = new vscode.WorkspaceEdit();
			edit.replace(documentUri, new vscode.Range(document.positionAt(0), document.positionAt(stored.fileContent.length)), applyData.fixed_content);
			await vscode.workspace.applyEdit(edit);
			diagnosticCollection.set(documentUri, issuesToDiagnostics(applyData.remaining_issues, document));
		}
	);

	// Code action provider: lightbulb on squiggly lines
	const codeActionProvider = vscode.languages.registerCodeActionsProvider(
		{ scheme: 'file' },
		{
			provideCodeActions(document, _range, context): vscode.CodeAction[] {
				const stored = documentSuggestions.get(document.uri.toString());
				if (!stored) { return []; }

				const actions: vscode.CodeAction[] = [];
				for (const diagnostic of context.diagnostics) {
					if (diagnostic.source !== 'AI Assistant') { continue; }
					const suggestion = stored.suggestions.find(s =>
						String(s.issue.rule_id) === String(diagnostic.code) &&
						s.issue.line - 1 === diagnostic.range.start.line
					);
					if (!suggestion) { continue; }

					const fixOne = new vscode.CodeAction(
						`AI Fix: ${suggestion.issue.rule_id} — ${suggestion.issue.message}`,
						vscode.CodeActionKind.QuickFix
					);
					fixOne.diagnostics = [diagnostic];
					fixOne.command = {
						command: 'agent-extension.applySingleFix',
						title: 'Apply single fix',
						arguments: [document.uri, suggestion]
					};
					actions.push(fixOne);
				}

				// "Fix all" action if there are any stored suggestions
				if (stored.suggestions.length > 0 && context.diagnostics.some(d => d.source === 'AI Assistant')) {
					const fixAll = new vscode.CodeAction(
						`AI Fix All: Apply all ${stored.suggestions.length} suggestion(s)`,
						vscode.CodeActionKind.QuickFix
					);
					fixAll.command = {
						command: 'agent-extension.applyAllFixes',
						title: 'Apply all fixes',
						arguments: [document.uri]
					};
					actions.push(fixAll);
				}

				return actions;
			}
		},
		{ providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] }
	);

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
		// Currently defaults to the dev server http://vcm-52409.vm.duke.edu:4003
		const config = vscode.workspace.getConfiguration('aiAssistant');
		const backendUrl = config.get<string>('backendUrl', 'http://vcm-52418.vm.duke.edu:4003/');

		// Pick operation
		const operationPick = await vscode.window.showQuickPick(
			[
				{ label: 'Scan for Issues', description: 'Find issues only' },
				{ label: 'Scan Issues & Suggest Fixes (for one agent)', description: 'Find issues, get fix suggestions, and optionally apply them' },
				{ label: 'Scan Issue & Suggest Fixes (for all agents)', description: 'Run all agents (scan + suggest)' },
			],
			{ placeHolder: 'Select operation' }
		);

		if (!operationPick) {
			return;
		}

		// Pick agent (if not analyze all)
		let agentPick: string | undefined;
		if (operationPick.label !== 'Scan Issue & Suggest Fixes (for all agents)') {
			const agentOptions = [
				{ label: 'Code Style', description: 'Check formatting and naming conventions', value: 'CODE_STYLE' },
				{ label: 'Idioms', description: 'Check for language-idiomatic patterns', value: 'IDIOMS' },
				{ label: 'Tests', description: 'Check test quality and coverage', value: 'TESTS' },
				{ label: 'Clean Code', description: 'Check for clean code principles', value: 'CLEAN_CODE' },
			];
			const agentSelection = await vscode.window.showQuickPick(agentOptions, { placeHolder: 'Select an agent' });
			if (!agentSelection) {
				return;
			}
			agentPick = agentSelection.value;
		}

		outputChannel.appendLine(`[${new Date().toISOString()}] ${operationPick.label}: ${fileName} (${fileContent.length} chars) → ${backendUrl} [agent: ${agentPick ?? 'ALL'}]`);

		try {
			// Full Analysis (All Agents)
			if (operationPick.label === 'Scan Issue & Suggest Fixes (for all agents)') {
				const response = await fetch(`${backendUrl}/analyze`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ file_content: fileContent, file_name: fileName, agent: null })
				});
				if (!response.ok) {
					throw new Error(`Server error: ${response.status}`);
				}
				const data = await response.json() as AnalyzeResponse;
				outputChannel.appendLine(`Received ${data.issues.length} issue(s), ${data.suggestions.length} suggestion(s).`);
				printIssues(data.issues, outputChannel);
				printSuggestions(data.suggestions, outputChannel);
			diagnosticCollection.set(document.uri, issuesToDiagnostics(data.issues, document));

			// Scan
			} else if (operationPick.label === 'Scan for Issues') {
				const scanResponse = await fetch(`${backendUrl}/agents/${agentPick}/scan`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ file_content: fileContent, file_name: fileName })
				});
				if (!scanResponse.ok) {
					throw new Error(`Server error (scan): ${scanResponse.status}`);
				}
				const scanData = await scanResponse.json() as ScanResponse;
				outputChannel.appendLine(`Received ${scanData.issues.length} issue(s).`);
				printIssues(scanData.issues, outputChannel);
			diagnosticCollection.set(document.uri, issuesToDiagnostics(scanData.issues, document));

			// Scan and Suggest
			} else {
				const scanResponse = await fetch(`${backendUrl}/agents/${agentPick}/scan`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ file_content: fileContent, file_name: fileName })
				});
				if (!scanResponse.ok) {
					throw new Error(`Server error (scan): ${scanResponse.status}`);
				}
				const scanData = await scanResponse.json() as ScanResponse;

				const suggestResponse = await fetch(`${backendUrl}/agents/${agentPick}/suggest`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ file_content: fileContent, file_name: fileName, issues: scanData.issues })
				});
				if (!suggestResponse.ok) {
					throw new Error(`Server error (suggest): ${suggestResponse.status}`);
				}
				const suggestData = await suggestResponse.json() as SuggestResponse;

				outputChannel.appendLine(`Received ${scanData.issues.length} issue(s), ${suggestData.suggestions.length} suggestion(s).`);
				printIssues(scanData.issues, outputChannel);
				printSuggestions(suggestData.suggestions, outputChannel);
			diagnosticCollection.set(document.uri, issuesToDiagnostics(scanData.issues, document));
				documentSuggestions.set(document.uri.toString(), {
					fileContent,
					suggestions: suggestData.suggestions,
					backendUrl,
					agent: agentPick!
				});

				// Optional apply with diff preview
				if (suggestData.suggestions.length > 0) {
					// Fetch fixed content first so we can show a diff
					const applyResponse = await fetch(`${backendUrl}/agents/${agentPick}/apply`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ file_content: fileContent, file_name: fileName, suggestions: suggestData.suggestions })
					});
					if (!applyResponse.ok) {
						throw new Error(`Server error (apply): ${applyResponse.status}`);
					}
					const applyData = await applyResponse.json() as ApplyResponse;

					// Show diff between current file and fixed content
					const previewUri = vscode.Uri.parse(`${previewScheme}:${fileName} (Fixed)`);
					previewContentMap.set(previewUri.toString(), applyData.fixed_content);
					await vscode.commands.executeCommand(
						'vscode.diff',
						document.uri,
						previewUri,
						`AI Assistant: ${fileName} — Current ↔ Fixed`
					);

					const confirm = await vscode.window.showInformationMessage(
						`Apply ${suggestData.suggestions.length} suggestion(s) to ${fileName}?`,
						'Apply', 'Cancel'
					);

					// Close the diff editor
					await vscode.commands.executeCommand('workbench.action.closeActiveEditor');

					if (confirm === 'Apply') {
						const workspaceEdit = new vscode.WorkspaceEdit();
						workspaceEdit.replace(
							document.uri,
							new vscode.Range(document.positionAt(0), document.positionAt(fileContent.length)),
							applyData.fixed_content
						);
						await vscode.workspace.applyEdit(workspaceEdit);

						outputChannel.appendLine(`\nFixes applied. Remaining issues: ${applyData.remaining_issues.length}`);
						printIssues(applyData.remaining_issues, outputChannel);
						diagnosticCollection.set(document.uri, issuesToDiagnostics(applyData.remaining_issues, document));
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

	context.subscriptions.push(disposable, outputChannel, diagnosticCollection, applySingleFix, applyAllFixes, codeActionProvider);
}

// This method is called when your extension is deactivated
export function deactivate() {}
