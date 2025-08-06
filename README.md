# VS Code 诊断信息导出器 (Diagnostics Dumper)

一个用于实时监控和导出VS Code编辑器中代码诊断信息的插件。该插件能够自动将错误、警告和其他诊断信息导出为JSON文件，便于外部工具进行分析和处理。

## ✨ 功能特性

- **实时监控**: 自动监听VS Code中的所有诊断变化（错误、警告、信息等）
- **智能防抖**: 内置200ms防抖机制，避免频繁文件写入操作
- **灵活配置**: 支持自定义输出目录，默认保存到桌面
- **完整信息**: 导出详细的诊断信息，包括位置、严重级别、错误代码等
- **文件跟踪**: 保持"已见文件"记录，即使错误已修复也会在输出中显示为空诊断数组
- **手动导出**: 提供命令面板命令，支持手动触发导出

## 🚀 快速开始

### 安装

1. 在VS Code扩展市场搜索 "vscode-diagnostics-dumper"
2. 点击安装并启用插件

### 使用方法

插件激活后会自动开始工作：

1. **自动模式**: 插件会自动监听代码中的错误和警告，实时更新JSON文件
2. **手动导出**: 使用 `Ctrl+Shift+P` 打开命令面板，搜索 "Diagnostics Dumper: Dump Now"

## ⚙️ 配置选项

插件提供以下配置项：

### `diagnosticsDumper.outputDir`

- **类型**: `string`
- **默认值**: `""` (空字符串，将使用默认路径)
- **描述**: 诊断JSON文件的输出目录

**配置方式**:

```json
{
  "diagnosticsDumper.outputDir": "C:\\Users\\YourName\\Documents\\diagnostics"
}
```

**默认行为**: 如果未设置此选项，文件将保存到 `桌面/vscode-diagnostics-dumper/vscode-diagnostics.json`

## 📄 输出格式

插件生成的JSON文件结构如下：

```json
[
  {
    "file": "绝对文件路径",
    "diagnostics": [
      {
        "message": "错误信息",
        "severity": 0,
        "level": "Error",
        "source": "TypeScript",
        "code": "2322",
        "start": { "line": 10, "character": 15 },
        "end": { "line": 10, "character": 25 }
      }
    ]
  }
]
```

### 严重级别说明

- `0` / `"Error"`: 错误
- `1` / `"Warning"`: 警告  
- `2` / `"Information"`: 信息
- `3` / `"Hint"`: 提示

## 🛠️ 开发环境要求

- VS Code 版本 >= 1.102.0
- Node.js (用于开发和编译)

## 📋 可用命令

| 命令 | 描述 |
|------|------|
| `Diagnostics Dumper: Dump Now` | 手动触发诊断信息导出 |

## 🔧 工作原理

1. **监听机制**: 使用 `vscode.languages.onDidChangeDiagnostics` API监听诊断变化
2. **数据收集**: 通过 `vscode.languages.getDiagnostics()` 获取所有当前诊断信息
3. **智能缓存**: 维护"已见文件"集合，确保即使错误修复后文件仍出现在输出中
4. **防抖处理**: 200ms延迟写入，避免频繁IO操作
5. **配置监听**: 自动响应用户配置变更，立即应用新的输出路径

## 📦 技术实现

- **语言**: TypeScript
- **核心API**: VS Code Extension API
- **主要模块**:
  - `vscode.languages` - 诊断信息获取
  - `vscode.workspace` - 配置管理
  - `vscode.commands` - 命令注册
  - Node.js `fs` - 文件系统操作

## 🐛 已知问题

目前无已知重大问题。如果遇到问题，请在项目仓库中提交issue。

## 📝 更新日志

### 0.0.1 (当前版本)

- ✅ 基础诊断信息导出功能
- ✅ 自定义输出目录支持
- ✅ 实时监听和防抖机制
- ✅ 手动导出命令
- ✅ 完整的诊断信息结构

## 🤝 贡献指南

欢迎提交Pull Request或Issue！

## 📄 许可证

本项目采用标准VS Code扩展许可证。

---

**享受编码！** 🎉
