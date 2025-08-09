import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { minimatch } from 'minimatch';

/**
 * 获取项目的 .claude 目录
 * @returns 项目的 .claude 目录
 */
function getProjectClaudeDir(): string {

  var claudeDir = "";

  const workspaceFolders = vscode.workspace.workspaceFolders;
  const activeEditor = vscode.window.activeTextEditor;

  // 如果工作区根目录存在，则返回工作区根目录下的 .claude 目录
  if (workspaceFolders && workspaceFolders.length > 0) {
    claudeDir = path.join(workspaceFolders[0].uri.fsPath, '.claude');
  }
  // 如果工作区根目录不存在，则获取当前活动文件的目录
  else if (activeEditor && activeEditor.document.uri.scheme === 'file') {
    claudeDir = path.dirname(activeEditor.document.uri.fsPath);
  }
  else {
    claudeDir = os.homedir();
  }

  return claudeDir;
}

/**
 * 写入 vscode-diagnostics.json 文件
 * @param data 数据
 */
function writeDiagnosticsFile(data: any) {
  const claudeDir = getProjectClaudeDir();
  const hooksDir = path.join(claudeDir, "hooks");

  // 如果 hooks 目录不存在，则不写入文件
  if (!fs.existsSync(hooksDir)) {
    return;
  }

  const outPath = path.join(hooksDir, 'vscode-diagnostics.json');
  fs.writeFileSync(outPath, JSON.stringify(data, null, 2), 'utf8');
}

/**
 * 删除 vscode-diagnostics.json 文件
 */
function deleteDiagnosticsFile() {
  const claudeDir = getProjectClaudeDir();
  const hooksDir = path.join(claudeDir, "hooks");
  const outPath = path.join(hooksDir, 'vscode-diagnostics.json');
  if (fs.existsSync(outPath)) {
    fs.unlinkSync(outPath);
  }
}

/**
 * 文件过滤逻辑：根据用户配置的模式匹配规则过滤文件
 * @param filePath 文件路径
 * @returns 是否过滤
 */
function shouldExcludeFile(filePath: string): boolean {
  const config = vscode.workspace.getConfiguration('diagnosticsDumper');
  const excludePatterns: string[] = config.get('excludePatterns', []);

  if (excludePatterns.length === 0) {
    return false;
  }

  // 获取相对于工作区的路径（用于匹配）
  let relativePath = filePath;
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (workspaceFolders && workspaceFolders.length > 0) {
    const workspaceRoot = workspaceFolders[0].uri.fsPath;
    if (filePath.startsWith(workspaceRoot)) {
      relativePath = path.relative(workspaceRoot, filePath);
    }
  }

  // 标准化路径分隔符（Windows使用反斜杠，需要转换为正斜杠）
  const normalizedPath = relativePath.replace(/\\/g, '/');
  const fileName = path.basename(filePath);

  // 检查是否匹配任一过滤模式
  for (const pattern of excludePatterns) {
    // 匹配相对路径
    if (minimatch(normalizedPath, pattern)) {
      return true;
    }
    // 匹配文件名
    if (minimatch(fileName, pattern)) {
      return true;
    }
  }

  return false;
}

/**
 * 真正执行写文件的函数
 */
function dumpAllDiagnostics() {
  const raw = vscode.languages.getDiagnostics();
  const entries = raw
    .filter(([uri, diags]) => {
      // 跳过被过滤的文件，且只保留有诊断信息的条目
      return !shouldExcludeFile(uri.fsPath) && diags.length > 0;
    })
    .map(([uri, diags]) => {
      const file = uri.fsPath;
      return {
        file,
        diagnostics: diags.map(d => ({
          message: d.message,
          severity: d.severity,
          level: vscode.DiagnosticSeverity[d.severity],
          source: d.source,
          code: typeof d.code === 'object' ? d.code?.value : d.code,
          start: { line: d.range.start.line, character: d.range.start.character },
          end: { line: d.range.end.line, character: d.range.end.character }
        }))
      };
    });

  // 写入诊断文件
  writeDiagnosticsFile(entries);
}

/**
 * 防抖：将高频事件合并到指定时间间隔内
 */
let debounceTimer: NodeJS.Timeout | undefined;
const DEBOUNCE_DELAY = 200; // 防抖延迟时间（毫秒）

function scheduleDump(): void {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  debounceTimer = setTimeout(() => {
    try {
      dumpAllDiagnostics();
    } catch (error) {
      console.error('诊断信息导出失败:', error);
    } finally {
      debounceTimer = undefined;
    }
  }, DEBOUNCE_DELAY);
}

/**
 * 初始化 hooks，将 resource 目录下的文件复制到 .claude/hooks 目录下
 * @param context 扩展上下文
 */
function initializeHooks(context: vscode.ExtensionContext) {
  const sourceDir = path.join(context.extensionPath, 'src', 'resource');
  const hooksDir = path.join(getProjectClaudeDir(), "hooks");

  // 如果 hooks 目录不存在，则创建
  if (!fs.existsSync(hooksDir)) {
    fs.mkdirSync(hooksDir, { recursive: true });
  }

  // 如果 source 目录不存在，则直接返回
  if (!fs.existsSync(sourceDir)) {
    return;
  }

  const files = fs.readdirSync(sourceDir);

  for (const file of files) {
    const sourceFile = path.join(sourceDir, file);
    const destFile = path.join(hooksDir, file);

    // 如果目标文件不存在，则复制
    if (!fs.existsSync(destFile)) {
      fs.copyFileSync(sourceFile, destFile);
    }
  }
}

/**
 * 更新 settings.local.json 文件中的 UserPromptSubmit 钩子
 * @param settings a
 * @param newHook a
 * @param settingsPath a
 * @returns
 */
function updateUserPromptSubmitHook(settings: any, newHook: any, settingsPath: string) {
  const hookName = newHook.name;
  if (!settings.hooks) {
    settings.hooks = {};
  }
  if (!Array.isArray(settings.hooks.UserPromptSubmit)) {
    settings.hooks.UserPromptSubmit = [];
  }

  let hookExists = false;
  for (const prompt of settings.hooks.UserPromptSubmit) {
    if (prompt.hooks && Array.isArray(prompt.hooks)) {
      if (prompt.hooks.some((h: any) => h.name === hookName)) {
        hookExists = true;
        break;
      }
    }
  }

  if (hookExists) {
    console.log(`[Diagnostics Dumper] UserPromptSubmit 钩子 '${hookName}' 已存在于 ${settingsPath}。无需更改。`);
    return false; // No changes made
  }

  // 添加钩子
  if (settings.hooks.UserPromptSubmit.length === 0) {
    settings.hooks.UserPromptSubmit.push({
      hooks: [newHook],
    });
  } else {
    if (!settings.hooks.UserPromptSubmit[0].hooks) {
      settings.hooks.UserPromptSubmit[0].hooks = [];
    }
    settings.hooks.UserPromptSubmit[0].hooks.push(newHook);
  }
  console.log(`[Diagnostics Dumper] 已更新 ${settingsPath} 以添加 UserPromptSubmit 钩子 '${hookName}'。`);
  return true; // Changes made
}

/**
 * 更新 settings.local.json 文件中的 PostToolUse 钩子
 * @param settings a
 * @param newHook a
 * @param settingsPath a
 * @returns
 */
function updatePostToolUseHook(settings: any, newHook: any, settingsPath: string) {
  const matcher = newHook.matcher;
  const newInnerHook = newHook.hooks[0];
  const hookName = newInnerHook.name;

  if (!settings.hooks) {
    settings.hooks = {};
  }
  if (!Array.isArray(settings.hooks.PostToolUse)) {
    settings.hooks.PostToolUse = [];
  }

  const matcherEntry = settings.hooks.PostToolUse.find((h: any) => h.matcher === matcher);

  if (matcherEntry) {
    // Matcher entry exists, check for the specific hook by name
    if (!matcherEntry.hooks) {
      matcherEntry.hooks = [];
    }
    const hookExists = matcherEntry.hooks.some((h: any) => h.name === hookName);
    if (hookExists) {
      console.log(`[Diagnostics Dumper] PostToolUse 钩子 '${hookName}' (matcher: '${matcher}') 已存在于 ${settingsPath}。无需更改。`);
      return false; // No changes made
    } else {
      // Add the hook to the existing matcher entry
      matcherEntry.hooks.push(newInnerHook);
      console.log(`[Diagnostics Dumper] 已更新 ${settingsPath}，在 PostToolUse (matcher: '${matcher}') 中添加钩子 '${hookName}'。`);
      return true; // Changes made
    }
  } else {
    // Matcher entry does not exist, add the whole new hook configuration
    settings.hooks.PostToolUse.push(newHook);
    console.log(`[Diagnostics Dumper] 已更新 ${settingsPath} 以添加 PostToolUse 钩子 (matcher: '${matcher}')。`);
    return true; // Changes made
  }
}

/**
 * 初始化 settings.local.json 文件中的钩子配置
 */
function initializeSettingsLocal() {
  const claudeDir = getProjectClaudeDir();
  if (!claudeDir) {
    vscode.window.showWarningMessage("无法确定 Claude 设置的项目目录。");
    return;
  }

  const settingsPath = path.join(claudeDir, 'settings.local.json');
  const hookName = 'diagnostics_parser';
  const commandString = `node "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\diagnostics_parser.js"`;

  const userPromptSubmitHook = {
    name: hookName,
    type: 'command',
    command: commandString,
  };

  const postToolUseHook = {
    matcher: "Write|Edit|MultiEdit|Read|Grep|Glob",
    hooks: [
      {
        name: hookName,
        type: 'command',
        command: commandString,
      },
    ],
  };

  if (!fs.existsSync(settingsPath)) {
    // 文件不存在，创建并写入默认配置
    const defaultConfig = {
      hooks: {
        UserPromptSubmit: [
          {
            hooks: [userPromptSubmitHook],
          },
        ],
        PostToolUse: [postToolUseHook],
      },
    };
    fs.writeFileSync(settingsPath, JSON.stringify(defaultConfig, null, 4), 'utf8');
    console.log(`[Diagnostics Dumper] 已创建 ${settingsPath} 并添加了 UserPromptSubmit 和 PostToolUse 钩子。`);
    return;
  }

  // 文件存在，读取并更新
  try {
    const settingsContent = fs.readFileSync(settingsPath, 'utf8');
    let settings: any = {};

    // 如果文件为空或解析失败，则从空对象开始
    try {
      settings = settingsContent ? JSON.parse(settingsContent) : {};
    } catch (e) {
      console.warn(`[Diagnostics Dumper] '${settingsPath}' 已损坏或为空，将被覆盖。`);
      settings = {};
    }

    const changed1 = updateUserPromptSubmitHook(settings, userPromptSubmitHook, settingsPath);
    const changed2 = updatePostToolUseHook(settings, postToolUseHook, settingsPath);

    if (changed1 || changed2) {
      fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 4), 'utf8');
    }

  } catch (error) {
    console.error(`[Diagnostics Dumper] 更新 ${settingsPath} 失败:`, error);
    vscode.window.showErrorMessage(`更新 settings.local.json 失败: ${error}`);
  }
}

/**
 * 手动初始化函数
 * @param context 扩展上下文
 */
function manualInitialize(context: vscode.ExtensionContext) {
  try {
    // 初始化 hooks
    initializeHooks(context);
    // 初始化 settings.local.json
    initializeSettingsLocal();
    vscode.window.showInformationMessage("Claude-diagnostics-dumper initialized successfully!");
  } catch (error: any) {
    vscode.window.showErrorMessage(`Initialization failed: ${error.message}`);
  }
}

/**
 * VS Code 扩展入口
 */
export function activate(context: vscode.ExtensionContext) {
  console.log('vscode-diagnostics-dumper activated');

  // 注册手动初始化命令
  const initCommand = vscode.commands.registerCommand('diagnosticsDumper.initialize', () => {
    manualInitialize(context);
  });
  context.subscriptions.push(initCommand);

  // 删除之前残留的诊断文件
  deleteDiagnosticsFile();

  // 当诊断发生变化时，触发写入
  context.subscriptions.push(
    vscode.languages.onDidChangeDiagnostics(scheduleDump)
  );
}

export function deactivate() { }