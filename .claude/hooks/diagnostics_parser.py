#!/usr/bin/env python3
"""
VS Code 诊断信息解析器 (Claude 钩子专用版)

本脚本作为 Claude Code PostToolUse 钩子。
**钩子模式**下会：

1. 若发现任何 Error 或 Warning，向 Claude 输出
   {"decision":"block","reason":"<多行 Markdown>"} 以阻断流程并提示修复；
2. 若无问题则静默退出，不干扰 Claude。

版本: 2.0.0  · 更新日期: 2025-08-08
"""

import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional


class DiagnosticsParser:
    """VS Code 诊断信息解析器"""

    SEVERITY_MAP = {0: "Error", 1: "Warning", 2: "Information", 3: "Hint"}
    SEVERITY_ICONS = {"Error": "❌", "Warning": "⚠️", "Information": "ℹ️", "Hint": "💡"}

    def __init__(self) -> None:
        self.diagnostics_file = self._locate_diagnostics_file()

    def _locate_diagnostics_file(self) -> Optional[Path]:
        """定位项目根目录下的 vscode-diagnostics.json"""
        script_dir = Path(__file__).parent  # .claude/hooks
        root_dir = script_dir.parent.parent  # 项目根
        json_file = root_dir / "vscode-diagnostics.json"
        return json_file if json_file.exists() else None

    # ---------- 诊断加载与统计 ---------- #

    def load_diagnostics(self) -> List[Dict[str, Any]]:
        if not self.diagnostics_file:
            print("❌ 未找到 vscode-diagnostics.json", file=sys.stderr)
            return []

        try:
            with self.diagnostics_file.open(encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"❌ 读取诊断文件失败: {e}", file=sys.stderr)
            return []

    def analyze_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    # ---------- 路径与格式化 ---------- #

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).parent.parent.parent.resolve()  # two levels up

    def _relativize(self, file_path: str) -> str:
        try:
            p = Path(file_path).resolve()
            return str(p.relative_to(self._project_root()).as_posix())
        except ValueError:
            return file_path

    # ---------- 主流程 ---------- #

    def run_hook_mode(self):
        """钩子模式：有错则阻断。"""
        time.sleep(2)  # 固定等待 2 秒
        data = self.load_diagnostics()

        stats = self.analyze_statistics(data)
        errors = stats["by_severity"].get("Error", 0)
        warnings = stats["by_severity"].get("Warning", 0)

        if errors or warnings:
            # 生成完整格式的诊断详情
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
                    detail_lines.append(
                        f"- **消息**: {diagnostic.get('message', '无')}"
                    )

                    if diagnostic.get("source"):
                        detail_lines.append(f"- **来源**: {diagnostic['source']}")

                    if diagnostic.get("code"):
                        detail_lines.append(f"- **错误代码**: {diagnostic['code']}")

                    detail_lines.append(
                        f"- **文件路径**: `{self._relativize(file_path)}`"
                    )
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

            print(
                json.dumps(
                    {"decision": "block", "reason": reason_md}, ensure_ascii=False
                )
            )
        sys.exit(0)


def ensure_unicode_stdout():
    if sys.platform.startswith("win"):
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())


def main() -> None:
    ensure_unicode_stdout()
    dp = DiagnosticsParser()
    dp.run_hook_mode()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"❌ 程序执行失败: {exc}", file=sys.stderr)
        sys.exit(1)
