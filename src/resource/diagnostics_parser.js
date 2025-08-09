import { readFileSync } from 'fs';
import { join } from 'path';

// 定义替换枚举
const REPLACE_ENUM = {
    'diagnostics': '{{VSCODE-DIAGNOSTICS}}'
}

/**
 * 解析诊断文件
 * @returns {Object} 诊断对象
 */
function parseDiagnostics() {
    const diagnosticsPath = join(__dirname, 'vscode-diagnostics.json');
    try {
        const diagnosticsContent = readFileSync(diagnosticsPath, 'utf-8');
        const diagnostics = JSON.parse(diagnosticsContent);
        return diagnostics;
    } catch (error) {
        return null;
    }
}

/**
 * 获取前置提示词
 * @returns {String} 提示词
 */
function getPrompt() {
    const promptPath = join(__dirname, "prompt.md");
    const promptContent = readFileSync(promptPath, 'utf-8');
    return promptContent;
}

// /**
//  * 输出JSON构建
//  * @param {String} decision 决策
//  * @param {String} reason 原因
//  */
// function outputJson(decision, reason) {
//     console.log(JSON.stringify({ "decision": decision, "reason": reason }, null, 2));
// }

const main = () => {
    const prompt = getPrompt();
    const diagnostics = parseDiagnostics();
    const promptContent = prompt.replace(REPLACE_ENUM.diagnostics, JSON.stringify(diagnostics, null, 2));
    // outputJson("block", promptContent);
    console.log(promptContent);
}

main();