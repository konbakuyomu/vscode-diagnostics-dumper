---
description: 合并 .claude/changes 下的变更到各级 CLAUDE.md，并同步更新 .claude/index.json
allowed-tools: Read(.claude/changes/*.json, .claude/index.json, CLAUDE.md, **/CLAUDE.md), Write(CLAUDE.md, **/CLAUDE.md, .claude/index.json)
argument-hint: <NO_ARGS>
# version: 1.0.0
# author: @your_name
# timeout: 300s
# examples:
#   - /doc-sync
---

## 用法
`/doc-sync`

## 目标
读取 `.claude/changes/*.json` 与 `.claude/index.json`，将最新变更**合并**到：
- 根级 `CLAUDE.md` 的“模块索引、运行与测试、变更记录”
- 各模块 `CLAUDE.md` 的“对外接口、相关文件清单、FAQ、变更记录”
- `.claude/index.json` 的入口/接口/测试/覆盖率统计

## 子智能体
调用 `doc-syncer`（见下）一次完成。