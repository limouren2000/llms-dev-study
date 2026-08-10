# Paper Read Brief

`paper-read-brief` 用于将论文整理成中文速读精要。

它会完整阅读论文，再沿着原论文的章节顺序提炼核心问题、方法机制、关键公式、重要图表和实验结论。最终内容比普通摘要可靠，也比完整论文精读更短，适合快速建立对一篇论文的整体认知。

如果你希望逐节展开全部细节、完整推导公式和深入分析所有实验，建议使用完整版的 `paper-read`；如果只想快速抓住论文主线，使用这个 `paper-read-brief` 即可。

## 它能做什么

- 按原论文的章节和小节顺序整理，不随意重组论文结构。
- 重点讲清论文提出了什么、为什么这样设计、各模块如何协作。
- 保留关键公式，并解释符号含义及其在方法中的作用。
- 获取并插入关键总览图、方法图和重要实验图。
- 压缩实验部分，只保留最关键的对比结果和作者想证明的结论。
- 最终生成一篇可以直接阅读、保存或继续发布的中文 Markdown 论文笔记。

完整执行规范见：[SKILL.md](https://github.com/limouren2000/llms-dev-study/blob/main/4.Paper-read/paper-read-brief/SKILL.md)。

## 快速安装

最简单的方式是把下面这段话直接发给 **Codex** 或 **Claude Code（CC）**：

```text
安装这个 Skill：https://github.com/limouren2000/llms-dev-study/blob/main/4.Paper-read/paper-read-brief/SKILL.md
```

安装完成后，让 Codex 或 Claude Code 确认已经能够识别 `paper-read-brief`。

## 怎么使用

### 速读一篇 arXiv 论文

```text
使用 paper-read-brief 速读这篇论文：
https://arxiv.org/abs/2305.10601
```

### 速读本地 PDF

```text
使用 paper-read-brief 速读这篇本地论文：
/你的目录/paper.pdf
```

### 指定保存位置

```text
使用 paper-read-brief 速读这篇论文，并把 Markdown 和图片保存到指定目录：
<论文链接或 PDF 路径>

保存目录：<你的目录>
```

你也可以继续补充要求，例如“实验部分再短一点”“重点解释方法架构”“保留全部关键公式”或“输出到现有 Markdown 文件中”。

## 输出内容

默认输出通常包括：

1. 论文解决的问题与核心结论。
2. 按原论文顺序整理的章节速读。
3. 核心方法、模块关系和必要公式。
4. 关键论文原图及中文图注。
5. 经过压缩的实验结果与结论。
6. 论文价值、适用边界和局限。

图片会保存在论文解读 Markdown 同级的 `images/` 文件夹中，并使用相对路径插入文章。

## 示例

- [ReAct 速读精要](https://limouren2000.github.io/llms-dev-study/paper-read/examples/react/)
- [Mem0 速读精要](https://limouren2000.github.io/llms-dev-study/paper-read/examples/mem0/)
- [Graph of Thoughts 速读精要](https://limouren2000.github.io/llms-dev-study/paper-read/examples/graph-of-thoughts/)
- [Tree of Thoughts 速读精要](https://limouren2000.github.io/llms-dev-study/paper-read/examples/tree-of-thoughts/)
