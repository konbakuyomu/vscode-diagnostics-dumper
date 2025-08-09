# VS Code - Claude Code 智能感知

一个专为 Claude Code 智能感知优化的 VS Code 扩展插件。该插件能够实时监控编辑器中的代码诊断信息（错误、警告等），并自动导出为结构化的 JSON 格式，为 Claude Code 提供精准的代码上下文，实现智能代码分析和建议。

## 快速开始

### 安装

TODO

### 使用方法

1. 按下 `ctrl` + `shift` + `p` 打开命令面板，输入 `Diagnostics Dumper: Initialize (Claude Code 智能感知初始化)` 并回车，即可完成初始化。
2. 初始化后，直接在 VS Code 中编辑代码，即可实时导出诊断信息，并被 Claude Code 智能感知。

## 配置选项

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

## 开发命令

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