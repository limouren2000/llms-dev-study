## Graph of Thoughts 速读精要

《Graph of Thoughts: Solving Elaborate Problems with Large Language Models》提出 Graph of Thoughts（GoT），把大语言模型的推理过程从链式、树式结构进一步推广成任意图结构。CoT 是一条链，ToT 是一棵树，GoT 则把每个 thought 当成图节点，把 thought 之间的依赖关系当成边。这样，模型不仅可以分叉探索，还可以把多个中间结果聚合起来，也可以对某个中间结果反复改进。

## 一句话先看懂

**GoT 的核心问题是：ToT 虽然允许分支和回溯，但树结构仍然无法自然表达“多个推理路径重新合并”或“对一个中间结果循环改进”。**

**GoT 的核心答案是：把 LLM 推理建模成图，让 thought 可以生成、聚合、评分、筛选和改进，从而把复杂任务拆成子任务、局部求解，再逐步合并成最终结果。**

## 1 引言

Prompt engineering 的演进路径是从简单到复杂的结构化推理。输入输出提示直接从问题到答案；链式思维（Chain-of-Thought, CoT）在中间加入推理步骤；自洽 CoT 生成多条链并选择较优结果；Tree of Thoughts（ToT）进一步把推理过程组织成树，允许探索不同路径并从不好的路径中回退。

GoT 认为 ToT 仍然有一个根本限制：树结构太刚性。树可以表达一个 thought 分裂成多个候选，但很难表达多个 thought 合并成一个更好的 thought。现实中的复杂思考经常不是树，而更像网络：先探索几个方向，再把不同方向中的有效部分组合起来；发现一个中间结果有问题后，也可能反复修改它，而不是只能继续向下扩展。

Figure 1: Comparison of Graph of Thoughts (GoT) to other prompting strategies.

图1：GoT 与其他 prompting 策略的比较。

解释：图1把 IO、CoT、CoT-SC、ToT 和 GoT 放在一起对比。GoT 相比 ToT 的关键增量是任意图式 thought 变换，尤其是聚合（aggregation）和改进（refining）。**GoT 不是单纯让搜索树更大，而是允许 thought 之间形成更一般的依赖网络。**

## 2 背景与符号

论文沿用语言模型记号 `pθ`，把一次 LLM 回复看作一个 thought。thought 的粒度不固定，可以是一段文字、一个文档、一段代码、一个数字序列，具体取决于任务。

IO prompting 没有中间 thought；CoT 有一条 thought 链；Multiple CoTs 有多条独立 thought 链；ToT 把 thought 组织成树，每个节点是一个部分解，可以继续生成子节点、评分和搜索。GoT 在这个基础上继续推广：链和树都只是图的特殊情况，任意图可以表达更多 thought 之间的关系。

背景部分的核心作用是把 GoT 定位成一个更一般的 prompting 抽象。它不是推翻 CoT 或 ToT，而是把它们纳入同一个图式框架里。

## 3 GoT Framework：核心贡献

GoT 被形式化为四元组：

$$
(G, T, E, R)
$$

其中，`G` 是当前 LLM 推理过程，也就是所有 thought 及其依赖关系构成的图；`T` 是 thought transformations，用来改变图结构；`E` 是 evaluator，用来给 thought 打分；`R` 是 ranking function，用来选择最相关或最高分的 thought。

这个定义把 prompting 从“写一条提示词”变成了“编排一个推理图”。LLM 不再只是生成答案，而是在一个可维护、可更新、可评分的图结构里逐步产生和组合中间结果。

## 3.1 推理过程：把 thought 建模成图节点

GoT 把推理过程建模为有向图：

$$
G = (V, E)
$$

`V` 是 thought 节点集合，`E ⊆ V × V` 是有向边集合。边 `(t1, t2)` 表示 `t2` 是在显式使用 `t1` 的基础上生成出来的。

这个定义比 ToT 更一般。ToT 中一个节点通常只有一个父节点，而 GoT 中一个 thought 可以依赖多个前驱 thought。例如文档合并时，一个新文档可以依赖多份输入文档；排序时，一个合并后的数组可以依赖两个已经排序好的子数组。

GoT 还可以使用异质图。某些任务中，不同 thought 属于不同类型，例如写作任务里有些节点是写作计划，有些节点是正文段落。这样就不必强行把所有中间结果都压成同一种形式。

**GoT 的核心抽象是：推理状态不是一条路径，也不是一棵树，而是一张会不断增长、连接、删减和更新的 thought 图。**

## 3.2 Thought 变换：生成、聚合与改进

GoT 最重要的机制是图式 thought 变换。每次变换可以写成：

$$
G' = T(G, p_\theta)
$$

变换会在当前图 `G` 上增加或删除节点和边：

$$
V' = (V \cup V^+) \setminus V^-
$$

$$
E' = (E \cup E^+) \setminus E^-
$$

`V+` 和 `E+` 是新增 thought 和依赖边，`V-` 和 `E-` 是被移除的 thought 和边。删除能力也有实际意义：如果某些中间路径不再有价值，可以从上下文或推理状态中移除，节省空间。

### 3.2.1 聚合：把多个 thought 合成一个新 thought

聚合是 GoT 相比 ToT 最重要的新增能力。多个 thought 可以被合并成一个新 thought。基本形式是从 `v1, ..., vk` 聚合成 `v+`：

$$
V^+ = \{v^+\}
$$

$$
E^+ = \{(v_1, v^+), ..., (v_k, v^+)\}
$$

排序任务中，两个已排序子数组可以聚合成一个更大的已排序数组；文档任务中，多份文档可以聚合成一份合并文档；总结任务中，多段局部摘要可以聚合成整体摘要。

**聚合解决的是 ToT 不擅长的问题：树可以分叉，但很难合流；GoT 可以自然表达“多个中间结果共同生成一个结果”。**

### 3.2.2 改进：对一个 thought 做循环式 refinement

改进表示对已有 thought 进行修正或增强。论文用自环表示：

$$
E^+ = \{(v, v)\}
$$

这意味着一个 thought 可以基于自身被再次处理。例如排序结果中数字频率不对，可以让模型根据错误结果修正；文档合并结果冗余太高，可以让模型继续压缩；代码生成结果有缺陷，也可以通过反馈循环改进。

改进能力让 GoT 能表达反馈回路，而不只是不断向下生成新分支。它对应复杂推理中很常见的“先产出一个版本，再检查，再修正”。

### 3.2.3 生成：从一个 thought 生成多个候选 thought

生成是从已有 thought 产生一个或多个新 thought：

$$
V^+ = \{v_1^+, ..., v_k^+\}
$$

$$
E^+ = \{(v, v_1^+), ..., (v, v_k^+)\}
$$

这覆盖了 CoT-SC 和 ToT 中已有的分支展开能力。GoT 并不是抛弃 ToT，而是把 ToT 的“生成子节点”视为图操作的一种。

Figure 2: Examples of aggregation and generation thought transformations.

图2：聚合和生成两种 thought 变换示例。

解释：排序任务中，生成可以把一个大数组拆成多个子数组，聚合可以把排序后的子数组合并。写作或总结任务中，生成可以从文章得到多个摘要，聚合可以把多篇文章的信息合成一个连贯总结。图2强调了 GoT 的基本思想：**prompting 不只是继续生成文本，而是在操作 thought 图。**

## 3.3 评分与排序：决定哪些 thought 继续参与推理

GoT 用 evaluator 给 thought 评分：

$$
E(v, G, p_\theta)
$$

这里的评分不只依赖当前 thought `v`，也可以依赖整个图 `G`。这是一个很重要的泛化，因为某个 thought 的质量可能取决于它和其他 thought 的关系。

排序函数写作：

$$
R(G, p_\theta, h)
$$

它从图中选出排名最高的 `h` 个 thought。实际实现里，常见做法是保留最高分的若干 thought。

不同任务可以用不同评分方式。排序任务可以用程序计算错误元素数量；集合交集可以计算缺失、误加和重复元素；文档合并则可以让 LLM 评价冗余度和信息保留度。

评分与排序让 GoT 不只是生成更多中间结果，而是能控制哪些 thought 继续留下来、哪些 thought 被丢弃。**生成、评分、筛选、聚合组合起来，才构成完整的图式推理过程。**

## 4 系统架构与可扩展性

GoT 不只是一个抽象概念，论文还给出一套可扩展系统架构。核心模块包括 Prompter、Parser、Scoring/Validation、Controller，以及两个关键结构：Graph of Operations（GoO）和 Graph Reasoning State（GRS）。

Prompter 负责构造发给 LLM 的 prompt。由于 GoT 需要表达 thought 之间的依赖关系，Prompter 必须知道如何把图结构编码进提示词。

Parser 负责解析 LLM 输出，把自然语言 thought 转成结构化 thought state。没有 Parser，系统就无法维护图状态，也无法让后续操作准确引用前面的结果。

Scoring/Validation 负责验证 thought 是否满足条件，并给 thought 打分。评分可以来自规则、LLM 或人类。例如排序可以用确定性规则打分，文档合并可以让 LLM 评价质量。

Controller 负责调度推理过程：选择哪些 thought，执行哪些 transformation，什么时候继续调用 LLM，什么时候结束。

GoO 是静态执行计划，规定要执行哪些操作、操作顺序和依赖关系。GRS 是动态运行状态，记录已经生成的 thought、分数、有效性和执行进度。

Figure 3: The system architecture of GoT, and the APIs of respective modules. The user can straightforwardly extend the design towards new prompting schemes, experiment with novel thought transformations, and plug in different LLMs. The blue part of the figure contains the architecture overview, the green part lists the API, and the red part contains example prompts together with a GRS and operations involved.

图3：GoT 的系统架构及各模块 API。用户可以扩展该设计以实现新的 prompting 方案，实验新的 thought 变换，并接入不同 LLM。蓝色部分是架构概览，绿色部分列出 API，红色部分给出示例 prompt、GRS 和相关操作。

解释：GoO 像一份“推理程序”，提前定义操作图；GRS 像运行时内存，随着 LLM 生成和评分不断更新。**这个架构把 GoT 从一个论文概念变成了可实现、可扩展、可复用的 prompting 框架。**

## 5 示例用例

### 5.1 排序

排序是论文展开最详细的用例。LLM 直接排序长数字序列时容易出错，尤其是重复数字的数量经常不一致。GoT 使用类似归并排序的思路：先把长列表拆成子列表，分别排序，再逐级合并。

Figure 4: An example graph decomposition of the sorting use case in GoT. All used operations (Generate, Aggregate, Score, KeepBest) are described in Figure 3.

图4：GoT 中排序任务的图分解示例。图中使用的所有操作，包括 Generate、Aggregate、Score、KeepBest，都在图3中描述。

解释：Generate 用于拆分或生成排序结果；Score 评估局部排序质量；KeepBest 保留最高分结果；Aggregate 合并子数组。排序任务最能体现 GoT 的基本价值：把大问题拆成局部更简单的问题，再把局部结果合成整体结果。

排序评分主要看两类错误：相邻元素是否逆序，以及输出中每个数字出现次数是否与输入一致。因此它同时惩罚顺序错误和元素频率错误。

### 5.2 集合操作

集合交集也适合 GoT。做法是把第二个集合拆成多个子集，分别计算它们和第一个集合的交集，再把子交集合并成最终结果。

评分关注三类错误：输出中不该出现的元素、应该出现却缺失的元素、重复元素。这个任务说明 GoT 适合结构化、可拆分、可聚合的符号操作。

### 5.3 关键词计数

关键词计数把长文本拆成多个 passage，分别统计关键词出现次数，再合并每个 passage 的统计结果。拆分降低了单次 prompt 的长度和难度，聚合负责把局部统计结果汇总。

这个例子展示了 GoT 在长文本处理上的价值：当输入过长或任务复杂时，先分块再汇总往往比一次性处理更可靠。

### 5.4 文档合并

文档合并任务要求基于多份 NDA 生成一份新 NDA，目标是减少重复，同时保留信息。

评分由 LLM 给出两个维度：冗余度和信息保留度，然后取调和平均。这个用例说明 GoT 不只适合确定性算法题，也能用于开放式生成任务。聚合在这里对应“把多份部分重叠的文档合成一份更完整、更少冗余的新文档”。

## 6 延迟与信息体量的权衡

论文提出 volume 作为评价 prompting 结构的新指标。一个 thought 的 volume 是图中所有能通过有向路径到达它的前驱 thought 数量。直觉上，volume 表示有多少中间信息可能影响当前输出。

Table 2: Comparison of prompting schemes, with respect to their fundamental tradeoff between latency and volume. GoT offers the best tradeoff.

表2：不同 prompting 方案在延迟和信息体量基本权衡上的比较。GoT 提供最佳权衡。

| 方案 | 延迟 | 信息体量 |
|---|---:|---:|
| CoT | N | N |
| CoT-SC | N/k | N/k |
| ToT | log_k N | O(log_k N) |
| GoT | log_k N | N |

解释：CoT 的信息体量大，但延迟高；CoT-SC 降低延迟，也降低信息体量；ToT 延迟低，但最终结果通常只继承树上一条路径的信息；GoT 通过聚合让最终 thought 汇集更多中间 thought 的信息，因此同时拥有低延迟和高信息体量。

这部分给 GoT 一个理论视角：**图结构的优势不只是表达更自由，还能在较短推理路径中汇聚更多中间信息。**

## 7 实验

实验主要验证 GoT 是否在质量和成本上优于 IO、CoT、ToT。论文主要使用 GPT-3.5，每个任务 100 个样本，并尽量让不同方案成本可比。

### 7.1 实验方法

主要 baseline 是 ToT，因为 ToT 是最相关也最强的对比对象。论文还设置两个 ToT 变体：一个分支更多、深度更浅；另一个分支更少、层数更深。这样可以避免只和某个弱 ToT 配置比较。

### 7.2 GoT 的优势

GoT 在排序、集合交集、关键词计数、文档合并上整体质量更高，并且相对 ToT 降低推理成本。

排序任务中，问题规模为 `P=128` 时，GoT 相比 ToT 中位错误数降低约 62%，成本降低超过 31%。更重要的是，问题越复杂，GoT 优势越明显：小规模时提升有限，大规模时优势明显扩大。

**实验真正支撑的结论是：GoT 特别适合 elaborate problems，也就是可以自然拆成子任务、局部求解、再聚合的大问题。**

### 7.3 任务分解

任务分解不是越细越好，而是要拆到 LLM 能够稳定解决子任务的粒度。拆得太粗，子任务仍然难；拆得太细，few-shot 示例等固定 prompt 开销会变大。

论文的经验判断是：合并子结果通常比从头解决一个大问题更容易。GoT 的收益来自两个方向：降低每个子任务难度，以及通过聚合把局部结果组合成更可靠的整体结果。

## 8 相关工作

GoT 与 prompting paradigms 的关系最直接。CoT、CoT-SC、ToT 都可以看作图结构的特殊情况，GoT 把 thought 组织推广到任意图。

Self-reflection 和 self-evaluation 与 GoT 的评分和验证模块相关。GoT 在选择和扩展 thought 时，也会依赖自评或评分机制。

LLM planning 方向研究如何让模型完成复杂任务规划。GoT 可以看作一种通用图式规划框架，用来表达更复杂的 prompting 计划。

Graphs and graph computing 是作者特别强调的背景。图抽象已经在数据库、图挖掘、图神经网络、药物发现、交通等领域长期有效；GoT 把这种抽象引入 prompt engineering。

## 9 结论

GoT 的核心贡献是把 LLM reasoning 建模成任意图。thought 是节点，依赖是边，图操作允许生成、聚合、评分、筛选和改进。

相对 ToT，GoT 的关键增量是聚合和反馈式改进。多个中间结果可以合成一个新结果，一个 thought 也可以被循环修正。这让 GoT 更接近复杂任务中的非线性思考过程。

GoT 的适用场景也很清楚：适合可以拆成子任务、局部求解、再逐步合并的问题。它不适合无脑替代所有 prompting，因为 GoT 需要设计操作图、prompt、parser、scorer 和任务分解方式，工程复杂度明显高于普通 CoT 或 ToT。

## 最终核心

GoT 的思想链路可以压成一句：

**CoT 是链，ToT 是树，GoT 是任意图；通过生成、聚合、改进、评分和筛选 thought，复杂任务可以被拆分求解再合并，从而在大问题上获得更好的质量和成本权衡。**

这篇论文最重要的地方不是某个实验数字，而是提出了一种更一般的 prompting 抽象：**把 LLM 推理当成一个可编排的图式操作过程，而不是一条推理链或一棵搜索树。**
