import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { minimatch } from 'minimatch';

/* --------------------------------------------------------
 * 输出目录策略：优先使用工作区根目录，多重回退机制
 * ------------------------------------------------------ */
function getOutputDir(): string {
  // ① 工作区根目录（最高优先级）
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (workspaceFolders && workspaceFolders.length > 0) {
    return workspaceFolders[0].uri.fsPath;
  }

  // ② 当前活动文件的目录
  const activeEditor = vscode.window.activeTextEditor;
  if (activeEditor && activeEditor.document.uri.scheme === 'file') {
    return path.dirname(activeEditor.document.uri.fsPath);
  }

  // ③ 回退到临时目录
  return os.tmpdir();
}

/* --------------------------------------------------------
 * 文件过滤逻辑：根据用户配置的模式匹配规则过滤文件
 * ------------------------------------------------------ */
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

/* --------------------------------------------------------
 * 清空诊断文件：确保每次启动时都是干净状态
 * ------------------------------------------------------ */
function clearDiagnosticsFile() {
  const outDir = getOutputDir();
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  const outPath = path.join(outDir, 'vscode-diagnostics.json');
  
  // 写入空数组，确保文件存在且为干净状态
  fs.writeFileSync(outPath, JSON.stringify([], null, 2), 'utf8');
  console.log(`diagnostics-dumper ⟶ 清空诊断文件 ${outPath}`);
}

/* --------------------------------------------------------
 * 真正执行写文件的函数
 * ------------------------------------------------------ */
function dumpAllDiagnostics() {
  const outDir = getOutputDir();
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  const outPath = path.join(outDir, 'vscode-diagnostics.json');

  /* ---------- 1. 收集当前所有诊断 ---------- */
  const raw = vscode.languages.getDiagnostics(); // [Uri, Diagnostic[]][]

  /* ---------- 2. 生成最终数组 ---------- */
  const entries = raw
    .filter(([uri, diags]) => {
      // 跳过被过滤的文件，且只保留有诊断信息的条目
      return !shouldExcludeFile(uri.fsPath) && diags.length > 0;
    })
    .map(([uri, diags]) => {
      const file = uri.fsPath;
      return {
        file,
        relativePath: path.relative(outDir, file),
        diagnostics: diags.map(d => ({
          message:  d.message,
          severity: d.severity,                                // 数字 0-3
          level:    vscode.DiagnosticSeverity[d.severity],     // 文字 "Error" | …
          source:   d.source,
          code:     typeof d.code === 'object' ? d.code?.value : d.code,
          start:    { line: d.range.start.line, character: d.range.start.character },
          end:      { line: d.range.end.line,   character: d.range.end.character   }
        }))
      };
    });

  /* ---------- 3. 写入磁盘 ---------- */
  fs.writeFileSync(outPath, JSON.stringify(entries, null, 2), 'utf8');
  console.log(`diagnostics-dumper ⟶ 写入 ${entries.length} 个文件到 ${outPath}`);
}

/* --------------------------------------------------------
 * 防抖：把高频事件合并到 200 ms 内
 * ------------------------------------------------------ */
let debounceTimer: NodeJS.Timeout | undefined;
function scheduleDump() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    try { dumpAllDiagnostics(); } catch (err) { console.error(err); }
  }, 200); // 调整这里可以改防抖间隔（ms）
}

/* --------------------------------------------------------
 * VS Code 扩展入口
 * ------------------------------------------------------ */
export function activate(context: vscode.ExtensionContext) {
  console.log('🔥 vscode-diagnostics-dumper activated');

  /* ---- 启动时清空诊断文件，确保干净状态 ---- */
  clearDiagnosticsFile();

  /* ---- 监听：诊断变化 ---- */
  context.subscriptions.push(
    vscode.languages.onDidChangeDiagnostics(scheduleDump)
  );

  /* ---- 手动命令：Diagnostics Dumper: Dump Now ---- */
  context.subscriptions.push(
    vscode.commands.registerCommand('diagnosticsDumper.dumpNow', dumpAllDiagnostics)
  );

  /* ---- 激活后再写一次当前诊断 ---- */
  dumpAllDiagnostics();
}

export function deactivate() {}