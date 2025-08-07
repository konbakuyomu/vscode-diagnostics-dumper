import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

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
 * 维护一个“最近见过的文件集合”
 * 作用：即使该文件目前没有诊断，也写出 diagnostics: []
 * ------------------------------------------------------ */
const seenFiles = new Set<string>();

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
  const diagMap = new Map<string, vscode.Diagnostic[]>();

  for (const [uri, diags] of raw) {
    const file = uri.fsPath;
    diagMap.set(file, diags);
    seenFiles.add(file);            // 记录到“见过”集合
  }

  /* ---------- 2. 生成最终数组 ---------- */
  const entries = Array.from(seenFiles).map(file => {
    const diags = diagMap.get(file) ?? []; // 若 Map 中没有 → 已无诊断
    return {
      file,
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

  /* ---- 监听：诊断变化 ---- */
  context.subscriptions.push(
    vscode.languages.onDidChangeDiagnostics(scheduleDump)
  );


  /* ---- 手动命令：Diagnostics Dumper: Dump Now ---- */
  context.subscriptions.push(
    vscode.commands.registerCommand('diagnosticsDumper.dumpNow', dumpAllDiagnostics)
  );

  /* ---- 激活后先写一次 ---- */
  dumpAllDiagnostics();
}

export function deactivate() {}