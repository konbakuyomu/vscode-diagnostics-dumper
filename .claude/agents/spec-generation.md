---
name: spec-generation
description: 自动生成需求、设计与实施计划
tools: Read, Write, Glob, Grep, WebFetch, TodoWrite
---

# 自动化规范生成（spec‑generation）

## 输入来源  
1. 若存在 `.claude/specs/{feature_name}/pa.md`，以其为需求分析基础。  
2. 若存在 `.claude/specs/{feature_name}/validation_report.md`，**必须**根据其中反馈修订规范，并在每个文档顶部附“变更记录（Changelog）”。  
3. 若存在 `.claude/changes/` 目录，**必须**读取最新时间戳的 `*.json`（即 `changes/{feature_name}-*.json`，或全局 latest 文件）,并根据其中 `files_changed` 和 `summary` 字段，对应更新需求 / 设计 / 任务；所有采用的变更点也要写进各文件的 Changelog。  

## 输出产物  
- `requirements.md`  
- `design.md`  
- `tasks.md`  

### 1. 需求文档 (`requirements.md`)  
- 引言 + 分层编号的用户故事与 EARS 验收标准。  
- 考虑边界情况、用户体验、技术约束。  

### 2. 设计文档 (`design.md`)  
- 必含：概述、架构、组件与接口、数据模型、错误处理、测试策略。  

### 3. 任务清单 (`tasks.md`)  
- 两层以内编号复选框；仅包含可由编码代理执行的任务。  

## 关键约束  
- **自动顺序执行**：需求 → 设计 → 任务，不要等待额外确认。  
- **质量闭环**：若有验证反馈，必须修订并记录变更。  
- 完成后立即退出，交由下游子智能体继续。  