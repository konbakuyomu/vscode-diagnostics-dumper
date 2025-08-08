# VS Code 诊断信息解析器

这是一个独立的Python脚本，用于解析VS Code诊断信息导出器插件生成的`vscode-diagnostics.json`文件，并将其转换为易读的Markdown或JSON格式。

## 📁 文件位置

```
项目根目录/
├── vscode-diagnostics.json          # VS Code扩展生成的诊断文件
├── .claude/
│   └── hooks/
│       ├── diagnostics_parser.py    # 主解析脚本
│       └── README.md                # 本文档
└── 其他项目文件...
```

## 🚀 使用方法

### 基础用法

```bash
# 输出Markdown格式到控制台
python .claude/hooks/diagnostics_parser.py --format md

# 输出JSON格式到控制台  
python .claude/hooks/diagnostics_parser.py --format json
```

### 输出到文件

```bash
# 保存Markdown格式到文件
python .claude/hooks/diagnostics_parser.py --format md --output report.md

# 保存JSON格式到文件
python .claude/hooks/diagnostics_parser.py --format json --output report.json
```

### 命令行参数

- `--format, -f`: 输出格式，必需参数
  - `md`: Markdown格式输出
  - `json`: JSON格式输出
- `--output, -o`: 输出文件路径（可选，不指定则输出到控制台）

## 📄 输出格式示例

### Markdown格式输出

**无错误时的输出**：
```markdown
# VS Code 诊断报告

## 统计概览
- ✅ 代码质量状态: 优秀
- 📁 总文件数: 2
- 📊 总诊断数: 0

## 🎉 恭喜！代码无任何问题

所有文件都通过了代码质量检查，未发现任何错误、警告或其他问题。

### 已检查的文件
- LICENSE
- diagnostics_parser.py

---
*保持良好的代码质量！* 👍
```

**有错误时的输出**：
```markdown
# VS Code 诊断报告

## 统计概览
- ❌ 代码质量状态: 需要修复
- ❌ Error: 1个
- ⚠️ Warning: 2个
- 📁 总文件数: 3
- 📊 总诊断数: 3

## 详细诊断

### 📄 extension.ts (1个错误)

**第10行:5-15** - ❌ Error
- **消息**: 类型定义错误
- **来源**: TypeScript
- **错误代码**: 2304
- **文件路径**: `src/extension.ts` (项目内文件)

---

### 📄 net_func.c (1个错误)

**第29行:25-34** - ❌ Error
- **消息**: 未定义标识符 "M4_USART1"
- **来源**: C/C++
- **错误代码**: 20
- **文件路径**: `d:\MCU_Workspace\HC32_Projects\HC32F460_Projects\HC32_RTT_DONG_NET\template\source\net_func.c` (外部项目文件)

---
```

### JSON格式输出

**无错误时的输出**：
```json
{
  "summary": {
    "total_files": 2,
    "total_diagnostics": 0,
    "status": "clean",
    "message": "代码质量良好，未发现任何问题",
    "by_severity": {
      "Error": 0,
      "Warning": 0,
      "Information": 0,
      "Hint": 0
    }
  },
  "diagnostics": [],
  "checked_files": [
    "LICENSE",
    "diagnostics_parser.py"
  ],
  "clean": true
}
```

**有错误时的输出**：
```json
{
  "summary": {
    "total_files": 1,
    "total_diagnostics": 1,
    "status": "error",
    "message": "发现 1 个错误需要修复",
    "by_severity": {
      "Error": 1,
      "Warning": 0,
      "Information": 0,
      "Hint": 0
    }
  },
  "diagnostics": [
    {
      "file": "extension.ts",
      "full_path": "D:\\vscode\\extensions\\vscode-diagnostics-dumper\\vscode-diagnostics-dumper-20250807\\src\\extension.ts",
      "relative_path": "src/extension.ts",
      "issues": [
        {
          "severity": "Error",
          "message": "类型定义错误",
          "source": "TypeScript",
          "code": "2304",
          "location": {
            "line": 10,
            "start_char": 5,
            "end_char": 15
          }
        }
      ]
    },
    {
      "file": "net_func.c",
      "full_path": "d:\\MCU_Workspace\\HC32_Projects\\HC32F460_Projects\\HC32_RTT_DONG_NET\\template\\source\\net_func.c",
      "relative_path": "d:\\MCU_Workspace\\HC32_Projects\\HC32F460_Projects\\HC32_RTT_DONG_NET\\template\\source\\net_func.c",
      "issues": [
        {
          "severity": "Error",
          "message": "未定义标识符 \"M4_USART1\"",
          "source": "C/C++",
          "code": "20",
          "location": {
            "line": 29,
            "start_char": 25,
            "end_char": 34
          }
        }
      ]
    }
  ],
  "checked_files": ["extension.ts", "net_func.c"],
  "clean": false
}
```

## 🔧 工作原理

1. **路径定位**: 脚本从`.claude/hooks`目录自动定位到项目根目录的`vscode-diagnostics.json`文件
2. **数据解析**: 读取并解析JSON格式的诊断数据
3. **统计分析**: 按严重级别统计诊断信息数量
4. **智能路径转换**: 自动将文件路径转换为最佳显示格式
   - 项目内文件 → 相对路径 (如: `src/extension.ts`)
   - 项目外文件 → 绝对路径 (如: `d:\其他项目\file.c`)
5. **格式转换**: 将原始数据转换为指定的输出格式
6. **输出处理**: 输出到控制台或保存到文件

## 📋 严重级别映射

| VS Code数值 | 级别名称 | 图标 | 描述 |
|------------|----------|------|------|
| 0 | Error | ❌ | 错误 |
| 1 | Warning | ⚠️ | 警告 |
| 2 | Information | ℹ️ | 信息 |
| 3 | Hint | 💡 | 提示 |

## 💻 系统要求

- **Python**: >= 3.6
- **操作系统**: Windows / macOS / Linux
- **依赖**: 仅使用Python标准库，无需额外安装

## 🐛 错误处理

脚本包含完善的错误处理机制：

- 文件不存在时显示友好错误提示
- JSON解析失败时提供详细错误信息
- 文件写入失败时继续输出到控制台
- 所有错误信息输出到stderr，不影响正常输出

## 🔗 与VS Code扩展的集成

这个脚本设计为与[VS Code诊断信息导出器](../../README.md)扩展配合使用：

1. VS Code扩展实时监控诊断信息变化
2. 扩展将诊断数据写入`vscode-diagnostics.json`
3. 本脚本读取该文件并转换为易读格式
4. 可以集成到CI/CD流程、代码审查工具等场景

## ✨ 核心特性

### 智能路径转换
脚本自动识别文件是否属于当前项目，并智能选择最佳路径显示格式：

- **项目内文件**：显示相对路径，便于快速定位
  - 示例：`src/extension.ts`、`package.json`、`.claude/hooks/diagnostics_parser.py`
- **项目外文件**：显示完整绝对路径，保持完整信息
  - 示例：`d:\MCU_Workspace\HC32_Projects\HC32F460_Projects\HC32_RTT_DONG_NET\template\source\net_func.c`

### 双格式输出支持
- **Markdown格式**：适合人类阅读，包含丰富的格式化信息
- **JSON格式**：适合程序处理，同时提供`full_path`和`relative_path`字段

## 📝 更新记录

- **2025-08-07**: 
  - 初始版本，支持Markdown和JSON格式输出
  - 添加智能路径转换功能，自动识别项目内外文件
  - JSON格式同时提供绝对路径和相对路径字段

---

**在`.claude/hooks`目录中使用愉快！** 🎉