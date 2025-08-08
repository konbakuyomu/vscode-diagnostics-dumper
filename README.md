<!-- 语言选择 / Language Selection -->
**[🇨🇳 中文](README.md)** | **[🇺🇸 English](README_en.md)**

---

# VS Code 诊断信息导出器 (Diagnostics Dumper)

一个用于实时监控和导出VS Code编辑器中代码诊断信息的插件。该插件能够自动将错误、警告和其他诊断信息导出为JSON文件，便于外部工具进行分析和处理。

## ✨ 功能特性

- **实时监控**: 自动监听VS Code中的所有诊断变化（错误、警告、信息等）
- **智能防抖**: 内置200ms防抖机制，避免频繁文件写入操作
- **多窗口隔离**: 每个VS Code窗口自动在各自工作区根目录生成独立的诊断文件
- **启动清空**: 每次启动时自动清空诊断文件，确保没有残留的旧信息
- **文件过滤**: 支持通配符模式过滤不需要的文件类型（如*.md, *.png等）
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

### `diagnosticsDumper.excludePatterns`

- **类型**: `string[]`
- **描述**: 文件过滤模式列表，支持通配符匹配
- **默认值**: 包含常见无需诊断的文件类型（*.md, *.txt, *.json, *.png, *.jpg等）

**配置示例**:

```json
{
  "diagnosticsDumper.excludePatterns": [
    "*.md",           // 屏蔽所有Markdown文件
    "*.png",          // 屏蔽所有PNG图片
    "AAA.py",         // 屏蔽特定文件
    "docs/**/*",      // 屏蔽docs目录下所有文件
    "node_modules/**/*" // 屏蔽node_modules目录
  ]
}
```

## 📁 输出目录策略

插件使用智能的多重回退策略自动确定输出目录：

1. **工作区根目录**（最高优先级）- 如果当前有打开的工作区
2. **活动文件目录** - 如果没有工作区但有打开的文件
3. **系统临时目录** - 作为最后的回退选项

**文件名**: 固定为 `vscode-diagnostics.json`，确保多个VS Code窗口之间自动隔离

**优势**:
- 🔄 **多窗口支持**: 不同VS Code窗口生成独立的诊断文件
- 🧹 **自动清理**: 每次启动时清空旧的诊断信息
- 📂 **智能定位**: 自动选择最合适的输出目录

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

## 🛠️ 开发环境与工具链

### 项目基础

本扩展基于 **Yeoman 脚手架** 创建，使用现代化的 VS Code 扩展开发工具链：

- **VS Code 版本**: >= 1.102.0
- **Node.js**: >= 18.x (支持 ES2022)
- **TypeScript**: >= 5.8.3
- **开发工具**:
  - `yo generator-code` - Yeoman VS Code 扩展生成器
  - `@vscode/vsce` - VS Code 扩展打包发布工具

### 开发环境搭建

```bash
# 全局安装脚手架工具
npm install -g yo generator-code
npm install -g @vscode/vsce

# 创建新扩展项目
yo code

# 安装项目依赖
npm install
```

### 开发命令

```bash
# 编译 TypeScript
npm run compile

# 监视模式编译
npm run watch

# 代码质量检查
npm run lint

# 运行测试
npm run test

# 打包扩展
vsce package

# 发布到市场
vsce publish
```

## 📋 可用命令

| 命令 | 描述 |
|------|------|
| `Diagnostics Dumper: Dump Now` | 手动触发诊断信息导出 |

## 🔧 工作原理

1. **启动初始化**: 扩展激活时先清空诊断文件，确保干净状态
2. **监听机制**: 使用 `vscode.languages.onDidChangeDiagnostics` API监听诊断变化
3. **文件过滤**: 根据配置的模式规则过滤不需要的文件（如图片、文档等）
4. **数据收集**: 通过 `vscode.languages.getDiagnostics()` 获取所有当前诊断信息
5. **智能缓存**: 维护"已见文件"集合，确保即使错误修复后文件仍出现在输出中
6. **防抖处理**: 200ms延迟写入，避免频繁IO操作
7. **目录策略**: 智能选择输出目录（工作区→活动文件目录→临时目录）

## 📦 技术实现

### 核心技术栈

- **语言**: TypeScript (ES2022)
- **核心API**: VS Code Extension API (v1.102.0+)
- **测试框架**: @vscode/test-cli + Mocha
- **构建工具**: TypeScript Compiler + ESLint
- **打包工具**: @vscode/vsce

### 主要依赖

**生产依赖**:
- `minimatch` (^10.0.3) - 通配符模式匹配

**开发依赖**:
- `@vscode/test-cli` (^0.0.11) - VS Code 测试命令行工具
- `@vscode/test-electron` (^2.5.2) - Electron 测试运行器
- `typescript` (^5.8.3) - TypeScript 编译器
- `eslint` (^9.25.1) - 代码质量检查
- `@types/vscode` (^1.102.0) - VS Code API 类型定义

### 核心模块

- `vscode.languages` - 诊断信息获取和监听
- `vscode.workspace` - 配置管理和工作区检测
- `vscode.window` - 活动编辑器获取
- `vscode.commands` - 命令注册和执行
- Node.js `fs`, `path`, `os` - 文件系统操作

### 项目结构

```
├── src/
│   ├── extension.ts          # 主扩展逻辑
│   └── test/
│       └── extension.test.ts # 测试用例
├── out/                      # 编译输出目录
├── package.json              # 扩展清单和依赖
├── tsconfig.json             # TypeScript 配置
├── eslint.config.mjs         # ESLint 配置
└── LICENSE                   # MIT 许可证
```

## 🐛 已知问题

目前无已知重大问题。如果遇到问题，请在项目仓库中提交issue。

## 📝 更新日志

### 1.0.3 (当前版本)

- ✨ **新增**: 适配Cursor编辑器，完全兼容Cursor环境
- ✨ **新增**: 文件过滤功能，支持通配符模式匹配
- ✨ **新增**: 启动时自动清空诊断文件，解决残留问题  
- ♻️ **重构**: 输出目录策略，支持多窗口自动隔离
- 🔧 **移除**: outputDir配置项，改为智能自动选择
- ✅ 基础诊断信息导出功能
- ✅ 实时监听和防抖机制
- ✅ 手动导出命令
- ✅ 完整的诊断信息结构

### 0.0.1 (历史版本)

- ✅ 初始版本，基础功能实现

## 🤝 开发与贡献

### 本地开发

1. **克隆仓库**:
   ```bash
   git clone <repository-url>
   cd vscode-diagnostics-dumper
   ```

2. **安装依赖**:
   ```bash
   npm install
   ```

3. **开发调试**:
   - 在 VS Code 中打开项目
   - 按 `F5` 启动扩展开发宿主窗口
   - 在新窗口中测试扩展功能

4. **运行测试**:
   ```bash
   npm run test
   ```

5. **打包测试**:
   ```bash
   vsce package
   ```

### 贡献指南

欢迎提交 Pull Request 或 Issue！

- 🐛 **Bug 报告**: 请提供详细的重现步骤
- 💡 **功能建议**: 描述需求和使用场景
- 🔧 **代码贡献**: 遵循项目的编码规范和测试要求

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

**享受编码！** 🎉
