#!/usr/bin/env python3
"""
Claude Code VS Code 诊断检查钩子脚本

## 设计思路

### 1. 核心设计理念
这是一个专为Claude Code设计的智能诊断钩子脚本，实现了嵌入式开发环境中的代码质量自动检查。
核心设计理念是**零配置智能化**：通过多种输入方式和环境检测，自动适应不同的执行环境，
无需用户手动配置即可在Claude Code工作流中无缝工作。

### 2. 架构设计特点
- **事件驱动架构**: 基于Claude Code钩子系统的PostToolUse事件触发
- **多源输入支持**: 命令行参数 → 环境变量 → stdin → 智能环境检测的降级策略
- **智能文件定位**: 通过脚本位置、工作目录、环境变量等多种方式定位诊断文件
- **容错机制**: 5次重试机制处理文件读写竞态条件和编码问题
- **编码兼容**: Windows UTF-8编码问题的综合解决方案

### 3. 业务逻辑设计
- **静默模式**: 无问题时不输出，避免干扰正常工作流
- **阻断决策**: 发现Error/Warning时输出结构化的阻断信息
- **详细报告**: 生成Markdown格式的诊断报告，包含文件、行号、错误类型等
- **统计分析**: 按严重级别统计问题，提供全局视图

## 详细使用方法

### 基础使用方式

#### 1. 作为Claude Code钩子（推荐）
在 `.claude/settings.json` 中配置：
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/diagnostics_parser.py"
          }
        ]
      }
    ]
  }
}
```

#### 2. 命令行直接调用
```bash
# 基础调用
python diagnostics_parser.py --event PostToolUse

# 启用调试模式
python diagnostics_parser.py --event PostToolUse --debug

# Windows环境
python .claude/hooks/diagnostics_parser.py --event PostToolUse --debug
```

#### 3. 环境变量方式
```bash
# Linux/Mac
export CLAUDE_HOOK_EVENT=PostToolUse
export CLAUDE_HOOK_DEBUG=true
python diagnostics_parser.py

# Windows
set CLAUDE_HOOK_EVENT=PostToolUse
set CLAUDE_HOOK_DEBUG=true
python diagnostics_parser.py
```

#### 4. 管道输入方式（传统）
```bash
# JSON格式输入
echo '{"hook_event_name": "PostToolUse"}' | python diagnostics_parser.py

# 复杂参数
echo '{"hook_event_name": "PostToolUse", "debug": true}' | python diagnostics_parser.py
```

### 高级配置选项

#### 环境变量配置
- `CLAUDE_PROJECT_DIR`: 指定项目根目录，影响诊断文件定位
- `CLAUDE_HOOK_EVENT`: 指定钩子事件类型
- `CLAUDE_HOOK_DEBUG`: 启用调试模式 (true/false)
- `PYTHONIOENCODING`: UTF-8编码设置（脚本会自动设置）

#### 诊断文件定位策略
脚本按以下顺序查找 `vscode-diagnostics.json`：
1. `脚本目录/../../../vscode-diagnostics.json` (基于脚本相对位置)
2. `当前工作目录/vscode-diagnostics.json`
3. `$CLAUDE_PROJECT_DIR/vscode-diagnostics.json`

### 输出格式说明

#### 1. 正常情况（无问题）
脚本静默退出，不产生任何输出，exit code = 0

#### 2. 发现问题时
输出JSON格式的阻断决策：
```json
{
  "decision": "block",
  "reason": "### 诊断摘要\n\n- ❌ Error: 2\n- ⚠️ Warning: 5\n\n### 📄 main.c (2个error, 3个warning)\n\n**第45行:12-25** - ❌ Error\n- **消息**: 未声明的标识符 'undefined_var'\n- **来源**: C/C++\n- **错误代码**: C2065\n- **文件路径**: `template/source/main.c`\n"
}
```

#### 3. 调试模式输出
启用 `--debug` 时，会在stderr输出详细的执行日志：
```
[DEBUG] 脚本启动，参数: ['diagnostics_parser.py', '--event', 'PostToolUse', '--debug']
[DEBUG] 使用命令行参数事件: PostToolUse
[DIAG_DEBUG] 开始诊断检查
[DIAG_DEBUG] 等待3秒让诊断文件稳定
[DIAG_DEBUG] 使用诊断文件: /path/to/project/vscode-diagnostics.json
[DIAG_DEBUG] 诊断统计: 2个错误, 5个警告
[DIAG_DEBUG] 发现问题，生成详细报告
```

功能：
1. 解析钩子事件名称
2. 当 hook_event_name 为 PostToolUse 时，执行诊断检查
3. 其他事件类型则输出事件名称

版本: 2.1.0  · 创建日期: 2025-08-08 · 更新日期: 2025-08-08
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


def ensure_utf8_output():
    """
    综合 UTF-8 设置，适用于 Windows 钩子环境。
    修复 Claude Code 钩子中文字符乱码问题。
    """
    if sys.platform.startswith("win"):
        # 方法1: 设置环境变量为 UTF-8
        os.environ["PYTHONIOENCODING"] = "utf-8"
        os.environ["PYTHONLEGACYWINDOWSSTDIO"] = "0"

        # 方法2: 尝试设置控制台代码页为 UTF-8
        try:
            import subprocess

            subprocess.run(["chcp", "65001"], shell=True, capture_output=True)
        except Exception:
            pass

        # 方法3: 强制 UTF-8 编码输出
        import codecs

        try:
            # 重新配置 stdout 和 stderr 使用 UTF-8
            if hasattr(sys.stdout, "detach"):
                sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
            if hasattr(sys.stderr, "detach"):
                sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())
        except Exception:
            # 备用方案
            try:
                sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
                sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer)
            except Exception:
                pass


def normalize_paths_in_json(json_text: str) -> str:
    """
    规范化 JSON 文本中的 Windows 路径，使用正斜杠。
    避免反斜杠转义序列问题。
    """
    # 匹配 Windows 风格路径的模式
    windows_path_pattern = r'"([A-Za-z]:\\\\[^"]*)"'

    def replace_path(match):
        path = match.group(1)
        # 将双反斜杠替换为正斜杠
        normalized_path = path.replace("\\\\", "/")
        # 处理单反斜杠
        normalized_path = normalized_path.replace("\\", "/")
        return f'"{normalized_path}"'

    # 应用替换
    normalized_text = re.sub(windows_path_pattern, replace_path, json_text)

    # 处理 UNC 路径
    unc_pattern = r'"(\\\\\\\\[^"]*)"'

    def replace_unc_path(match):
        path = match.group(1)
        normalized_path = path.replace("\\\\\\\\", "//")
        normalized_path = normalized_path.replace("\\\\", "/")
        normalized_path = normalized_path.replace("\\", "/")
        return f'"{normalized_path}"'

    normalized_text = re.sub(unc_pattern, replace_unc_path, normalized_text)
    return normalized_text


class DiagnosticsChecker:
    """VS Code 诊断信息检查器"""

    SEVERITY_MAP = {0: "Error", 1: "Warning", 2: "Information", 3: "Hint"}
    SEVERITY_ICONS = {"Error": "❌", "Warning": "⚠️", "Information": "ℹ️", "Hint": "💡"}

    def __init__(self) -> None:
        self.diagnostics_file = self._locate_diagnostics_file()

    def _locate_diagnostics_file(self) -> Optional[Path]:
        """定位项目根目录下的 vscode-diagnostics.json"""
        # 尝试多个可能的路径
        possible_paths = [
            # 方法1：基于脚本位置推断
            Path(__file__).parent.parent.parent / "vscode-diagnostics.json",
            # 方法2：当前工作目录
            Path.cwd() / "vscode-diagnostics.json",
            # 方法3：环境变量指定的项目目录
            Path(os.environ.get("CLAUDE_PROJECT_DIR", ".")) / "vscode-diagnostics.json",
        ]

        for json_file in possible_paths:
            if json_file.exists():
                return json_file.resolve()
        return None

    def load_diagnostics(self) -> List[Dict[str, Any]]:
        """加载诊断数据，带重试机制"""
        if not self.diagnostics_file:
            return []

        # 重试机制：最多尝试5次，每次间隔1秒
        for attempt in range(5):
            try:
                # 检查文件是否存在且可读
                if not self.diagnostics_file.exists():
                    time.sleep(1)
                    continue

                # 检查文件大小，避免读取正在写入的文件
                file_size = self.diagnostics_file.stat().st_size
                if file_size == 0:
                    time.sleep(1)
                    continue

                # 尝试读取文件
                with self.diagnostics_file.open(encoding="utf-8") as f:
                    content = f.read().strip()
                    if not content:
                        time.sleep(1)
                        continue
                    return json.loads(content)

            except (json.JSONDecodeError, OSError, PermissionError) as e:
                if attempt < 4:  # 不是最后一次尝试
                    time.sleep(1)
                    continue
                # 最后一次尝试失败，记录错误但不中断
                print(f"诊断文件读取失败 (尝试 {attempt+1}/5): {e}", file=sys.stderr)

        return []

    def analyze_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析诊断统计信息"""
        total_files, total_diagnostics = 0, 0
        severity_count: Counter[str] = Counter()

        for file_data in data:
            total_files += 1
            diagnostics = file_data.get("diagnostics", [])
            total_diagnostics += len(diagnostics)
            for diag in diagnostics:
                sev = self.SEVERITY_MAP.get(diag.get("severity", 0), "Unknown")
                severity_count[sev] += 1

        return {
            "total_files": total_files,
            "total_diagnostics": total_diagnostics,
            "by_severity": dict(severity_count),
        }

    @staticmethod
    def _project_root() -> Path:
        """获取项目根目录"""
        return Path(__file__).parent.parent.parent.resolve()

    def _relativize(self, file_path: str) -> str:
        """将绝对路径转换为相对路径"""
        try:
            p = Path(file_path).resolve()
            return str(p.relative_to(self._project_root()).as_posix())
        except ValueError:
            return file_path

    def generate_reason_markdown(self, debug_mode: bool = False) -> Optional[str]:
        """
        生成诊断报告 Markdown。当存在 Error 或 Warning 时返回报告字符串，否则返回 None。
        """

        def debug_log(msg: str) -> None:
            if debug_mode:
                print(f"[DIAG_DEBUG] {msg}", file=sys.stderr)

        debug_log("开始诊断检查")

        # 智能等待：先等待3秒，然后检查文件是否更新
        debug_log("等待3秒让诊断文件稳定")
        time.sleep(3)

        # 如果诊断文件不存在，再等待2秒重新定位
        if not self.diagnostics_file or not self.diagnostics_file.exists():
            debug_log("诊断文件不存在，等待2秒后重新定位")
            time.sleep(2)
            self.diagnostics_file = self._locate_diagnostics_file()

        if self.diagnostics_file:
            debug_log(f"使用诊断文件: {self.diagnostics_file}")
        else:
            debug_log("未找到诊断文件")

        data = self.load_diagnostics()
        if not data:
            debug_log("诊断数据为空或加载失败")
            return None

        stats = self.analyze_statistics(data)
        errors = stats["by_severity"].get("Error", 0)
        warnings = stats["by_severity"].get("Warning", 0)

        debug_log(f"诊断统计: {errors}个错误, {warnings}个警告")

        # 如果没有 Error 或 Warning，静默
        if not errors and not warnings:
            debug_log("没有错误或警告，静默退出")
            return None

        debug_log("发现问题，生成详细报告")

        # 生成详细诊断报告
        detail_lines: List[str] = []

        for file_data in data:
            diagnostics = file_data.get("diagnostics", [])
            if not diagnostics:
                continue

            file_path = file_data["file"]
            file_name = Path(file_path).name

            # 按严重级别统计该文件的问题
            file_errors = sum(1 for d in diagnostics if d.get("severity") == 0)
            file_warnings = sum(1 for d in diagnostics if d.get("severity") == 1)
            file_infos = sum(1 for d in diagnostics if d.get("severity") == 2)
            file_hints = sum(1 for d in diagnostics if d.get("severity") == 3)

            # 生成文件摘要
            summary_parts = []
            if file_errors:
                summary_parts.append(f"{file_errors}个error")
            if file_warnings:
                summary_parts.append(f"{file_warnings}个warning")
            if file_infos:
                summary_parts.append(f"{file_infos}个information")
            if file_hints:
                summary_parts.append(f"{file_hints}个hint")
            summary_text = ", ".join(summary_parts)

            detail_lines.append(f"### 📄 {file_name} ({summary_text})")
            detail_lines.append("")

            # 生成该文件下每个诊断的详细信息
            for diagnostic in diagnostics:
                severity_name = self.SEVERITY_MAP.get(
                    diagnostic.get("severity", 0), "Unknown"
                )
                icon = self.SEVERITY_ICONS.get(severity_name, "📋")

                start = diagnostic.get("start", {})
                end = diagnostic.get("end", {})
                line = start.get("line", 0)
                start_char = start.get("character", 0)
                end_char = end.get("character", 0)

                detail_lines.append(
                    f"**第{line}行:{start_char}-{end_char}** - {icon} {severity_name}"
                )
                detail_lines.append(f"- **消息**: {diagnostic.get('message', '无')}")

                if diagnostic.get("source"):
                    detail_lines.append(f"- **来源**: {diagnostic['source']}")

                if diagnostic.get("code"):
                    detail_lines.append(f"- **错误代码**: {diagnostic['code']}")

                detail_lines.append(f"- **文件路径**: `{self._relativize(file_path)}`")
                detail_lines.append("")

        # 生成最终的 reason，包含摘要和详细信息
        header = [
            "### 诊断摘要",
            "",
            f"- ❌ Error: {errors}",
            f"- ⚠️ Warning: {warnings}",
            "",
        ]

        reason_md = "\n".join(header + detail_lines)
        return reason_md

    def check_and_report(self, debug_mode: bool = False) -> bool:
        """
        执行诊断检查并报告结果（PostToolUse 路径）。

        Returns:
            bool: True 如果发现 Error 或 Warning（应阻断流程），False 如果没有问题
        """

        reason_md = self.generate_reason_markdown(debug_mode)
        if not reason_md:
            return False

        # 输出阻断决策（PostToolUse 使用 reason 字段）
        print(
            json.dumps({"decision": "block", "reason": reason_md}, ensure_ascii=False)
        )
        return True


def get_hook_input() -> Dict[str, Any]:
    """
    多源输入获取：支持命令行参数、环境变量、stdin输入

    Returns:
        Dict[str, Any]: 钩子数据字典
    """
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(
        description="Claude Code 集成钩子脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--event", type=str, help="钩子事件名称 (如: PostToolUse)")
    parser.add_argument("--debug", action="store_true", help="启用调试输出")

    args = parser.parse_args()

    # 调试信息输出
    def debug_log(msg: str) -> None:
        if args.debug:
            print(f"[DEBUG] {msg}", file=sys.stderr)

    debug_log(f"脚本启动，参数: {sys.argv}")

    # 方法1: 命令行参数
    if args.event:
        debug_log(f"使用命令行参数事件: {args.event}")
        return {"hook_event_name": args.event}

    # 方法2: 环境变量
    env_event = os.environ.get("CLAUDE_HOOK_EVENT")
    if env_event:
        debug_log(f"使用环境变量事件: {env_event}")
        return {"hook_event_name": env_event}

    # 方法3: stdin 输入（传统方式）
    try:
        debug_log("尝试从stdin读取输入")

        # 检查是否有可用的stdin
        if sys.stdin.isatty():
            debug_log("检测到交互式终端，没有stdin管道输入")
        else:
            input_data = sys.stdin.read().strip()
            debug_log(f"从stdin读取到数据长度: {len(input_data)}")

            if input_data:
                try:
                    normalized_input = normalize_paths_in_json(input_data)
                    data = json.loads(normalized_input)
                    debug_log(f"成功解析JSON: {data}")
                    return data
                except json.JSONDecodeError as e:
                    debug_log(f"JSON解析失败: {e}")
    except Exception as e:
        debug_log(f"stdin读取异常: {e}")

    # 方法4: 默认钩子事件（钩子环境检测）
    # 检测 Claude Code 钩子环境的多个指标
    claude_indicators = [
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.environ.get("CLAUDE_USER_ID"),
        os.environ.get("CLAUDE_SESSION_ID"),
        # 检查是否在 .claude 目录下执行
        ".claude" in str(Path(__file__).resolve()),
        # 检查进程名是否包含 claude
        any("claude" in arg.lower() for arg in sys.argv if isinstance(arg, str)),
    ]

    if any(claude_indicators):
        debug_log(f"检测到Claude环境指标: {[i for i in claude_indicators if i]}")
        debug_log("使用默认PostToolUse事件")
        return {"hook_event_name": "PostToolUse"}

    debug_log("所有输入方法都失败，使用Unknown事件")
    return {"hook_event_name": "Unknown"}


def main():
    """主调度逻辑"""
    # 确保 UTF-8 编码输出
    ensure_utf8_output()

    try:
        # 多源输入获取
        data = get_hook_input()
        hook_event_name = data.get("hook_event_name", "Unknown")

        # 条件分发逻辑
        if hook_event_name == "PostToolUse":
            # 获取调试模式参数
            debug_mode = (
                "--debug" in sys.argv
                or os.environ.get("CLAUDE_HOOK_DEBUG", "").lower() == "true"
            )

            # 执行诊断检查
            checker = DiagnosticsChecker()
            if not checker.check_and_report(debug_mode):
                # 没有问题时静默退出
                pass
        elif hook_event_name == "UserPromptSubmit":
            # 获取调试模式参数
            debug_mode = (
                "--debug" in sys.argv
                or os.environ.get("CLAUDE_HOOK_DEBUG", "").lower() == "true"
            )

            checker = DiagnosticsChecker()
            reason_md = checker.generate_reason_markdown(debug_mode)
            if reason_md:
                # 不阻断，仅将报告注入上下文 additionalContext
                out = {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": reason_md,
                    }
                }
                print(json.dumps(out, ensure_ascii=False))
            else:
                # 静默
                pass
        else:
            # 其他事件类型，输出事件名称
            try:
                print(f"{hook_event_name}：钩子触发")
            except UnicodeEncodeError:
                print(f"{hook_event_name}: Hook Triggered (Encoding Fallback)")

        sys.exit(0)

    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        # 改进异常处理，提供更多上下文信息
        error_info = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "script_path": __file__,
            "argv": sys.argv,
            "env_vars": {
                "CLAUDE_PROJECT_DIR": os.environ.get("CLAUDE_PROJECT_DIR"),
                "CLAUDE_HOOK_EVENT": os.environ.get("CLAUDE_HOOK_EVENT"),
                "CLAUDE_HOOK_DEBUG": os.environ.get("CLAUDE_HOOK_DEBUG"),
            },
        }
        print(
            f"钩子脚本异常: {json.dumps(error_info, ensure_ascii=False, indent=2)}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
