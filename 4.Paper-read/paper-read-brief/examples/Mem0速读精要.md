## Mem0 速读精要

《Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory》讨论的是生产级 AI Agent 的长期记忆问题。大模型上下文窗口再长，也只能“暂时装下更多内容”，不能真正解决跨会话、多主题、长周期交互里的记忆选择、记忆更新、冲突处理和低延迟检索。Mem0 的目标就是把 Agent 从“每次对话重新开始”推进到“能持续积累、整理、检索和更新用户记忆”。

## 核心问题

**Mem0 要解决的问题是：固定上下文窗口无法支撑真正长期、跨会话、可扩展的 AI Agent 记忆**。

**Mem0 的核心答案是：不要把完整历史都塞回上下文，而是动态抽取显著事实、和已有记忆比较后执行新增/更新/删除/跳过，并在回答时只检索相关记忆**。在此基础上，Mem0g 进一步把记忆组织成图，用实体和关系表示更复杂的关联与时间线索。

## 摘要

大语言模型可以生成连贯回答，但固定上下文窗口限制了多轮、多会话场景中的一致性。Mem0 提出一种以记忆为中心的架构，从持续对话中动态抽取、整合和检索关键信息。Mem0g 在 Mem0 基础上加入图记忆表示，用实体节点和关系边捕捉对话元素之间的复杂结构。

论文在 LOCOMO 长期对话记忆基准上评估 Mem0 和 Mem0g，并与六类基线比较，包括已有记忆增强系统、不同分块配置的检索增强生成、完整上下文方法、开源记忆方案、专有模型系统和记忆管理平台。结果显示，Mem0 在多类问题上超过已有记忆系统；Mem0g 总体分数比基础 Mem0 约高 2%；相比完整上下文方法，Mem0 的 p95 延迟降低 91%，token 成本节省超过 90%。

## 1 引言

人类记忆支撑长期交流：我们会记住偏好、事件、关系变化，并在未来对话中主动调用这些信息。AI Agent 如果没有持久记忆，就会忘记用户偏好、重复提问、甚至和先前事实矛盾。论文用饮食偏好举例：用户先前说自己吃素且不吃奶制品，如果系统后续推荐鸡肉或奶制品，就会直接破坏信任。

扩大上下文窗口只能延迟问题，不能根治问题。真实交互会跨越数周或数月，而且主题经常跳转。一个用户可能先说饮食偏好，中间聊很久编程任务，之后再问晚餐建议。完整上下文不仅昂贵，还会让关键事实埋在大量无关内容里；长上下文注意力也不保证模型能正确利用远处信息。

Figure 1: Illustration of memory importance in AI agents.

> 图1：AI Agent 中记忆重要性的示意图。左侧没有持久记忆，系统忘记用户的素食和无乳制品偏好，给出不合适推荐；右侧有有效记忆，系统跨会话保留饮食约束，从而给出符合上下文的建议。

解释：图1直接说明 Mem0 的产品动机：长期记忆不是“锦上添花”，而是让 Agent 保持一致性和可信度的基础能力。**记忆系统需要选择性存储重要信息、整合相关概念，并在需要时低成本检索出来**。

## 2 提出方法

论文提出两套互补架构：Mem0 和 Mem0g。Mem0 使用自然语言形式的紧凑记忆，负责高效抽取、更新和检索；Mem0g 在此基础上加入图结构，把实体和关系显式表示出来，适合需要关系推理和时间顺序判断的问题。

### 2.1 Mem0：抽取、比较、更新的自然语言记忆管线

Mem0 采用增量处理范式，随着对话持续运行。每次输入一对新消息：

$$
(m_{t-1}, m_t)
$$

其中 `m_t` 是当前消息，`m_{t-1}` 是前一条消息，通常构成一次用户与助手的完整交互单元。

Mem0 的流程分成两个阶段：抽取阶段和更新阶段。

Figure 2: Architectural overview of the Mem0 system showing extraction and update phase. The extraction phase processes messages and historical context to create new memories. The update phase evaluates these extracted memories against similar existing ones, applying appropriate operations through a Tool Call mechanism. The database serves as the central repository, providing context for processing and storing updated memories.

> 图2：Mem0 系统架构概览，展示抽取阶段和更新阶段。抽取阶段处理新消息和历史上下文以生成新记忆；更新阶段将抽取出的记忆与相似已有记忆比较，并通过工具调用机制执行相应操作。数据库作为中心存储，提供处理上下文并保存更新后的记忆。

解释：Mem0 不是把每轮对话都原样存入向量库，而是先结合全局摘要和最近消息判断“这轮交互里有什么值得长期保存”。抽取函数可写成：

$$
\Omega = \phi(P)
$$

其中提示 `P` 由四部分组成：全局对话摘要 `S`、最近 `m` 条历史消息、新消息对 `(m_{t-1}, m_t)`。输出 `Ω = {ω_1, ω_2, ..., ω_n}` 是候选记忆事实。

更新阶段会对每条候选事实 `ω_i` 检索最相似的 `s` 条已有记忆，然后让大模型通过工具调用决定执行哪种操作：

| 操作 | 含义 |
|---|---|
| ADD | 没有语义等价记忆，新增记忆 |
| UPDATE | 已有记忆可被新信息补充或替换 |
| DELETE | 新信息与旧记忆冲突，删除旧记忆 |
| NOOP | 候选事实已存在或无须修改 |

**Mem0 的关键不是“存储更多”，而是持续维护一个更干净、更一致、更紧凑的记忆库**。它用大模型判断候选记忆和已有记忆之间的语义关系，避免冗余、过期和冲突信息不断堆积。

实验配置中，论文设置最近消息窗口 `m=10`，相似记忆数量 `s=10`，语言模型操作使用 GPT-4o-mini，向量数据库通过稠密嵌入支持相似检索。

### 2.2 Mem0g：用图记忆表达实体和关系

Mem0g 将记忆表示为有向标注图：

$$
G = (V, E, L)
$$

其中 `V` 是实体节点，`E` 是实体之间的关系边，`L` 是节点语义类型。例如 Alice 是 Person，San Francisco 是 City，关系可以是 `lives_in`。

每个实体节点包含三类信息：实体类型、语义嵌入、元数据时间戳。关系用三元组表示：

$$
(v_s, r, v_d)
$$

其中 `v_s` 是源实体，`v_d` 是目标实体，`r` 是关系标签。

Figure 3: Graph-based memory architecture of Mem0g illustrating entity extraction and update phase. The extraction phase uses LLMs to convert conversation messages into entities and relation triplets. The update phase employs conflict detection and resolution mechanisms when integrating new information into the existing knowledge graph.

> 图3：Mem0g 的图记忆架构，展示实体抽取和更新阶段。抽取阶段使用大模型将对话消息转换成实体和关系三元组；更新阶段在新信息写入已有知识图谱时进行冲突检测与解决。

解释：Mem0g 的核心流程是先从自然语言对话中抽取实体，再生成实体之间的语义关系。例如旅行计划里，实体可能包括目的地、交通方式、日期、活动和用户偏好；关系可能表示“用户偏好某地”“活动发生在某日期”“某人计划去某城市”。

写入新三元组时，系统会计算源实体和目标实体的嵌入，在图中寻找相似节点。如果相似度超过阈值，就复用已有节点，否则创建新节点。遇到冲突关系时，Mem0g 不直接物理删除旧关系，而是用更新解析器标记旧关系失效，从而保留时间推理能力。

检索也有两条路径：

第一是实体中心检索，先识别查询中的关键实体，再在图中找对应节点，扩展其入边和出边，构造相关子图。

第二是语义三元组检索，把整条查询编码成向量，与图中每条关系三元组的文本编码做相似匹配，返回超过阈值的相关关系。

**Mem0g 的优势在于显式保留“谁和谁有什么关系、关系何时成立、后来是否被更新”**。这对时间问题、关系链问题、开放域背景整合尤其重要。

## 3 实验设置

### 3.1 数据集

论文使用 LOCOMO 数据集评估长期对话记忆。它包含 10 段扩展对话，每段平均约 600 轮、26000 tokens，并跨多个会话。每段对话后配有平均约 200 个问题和标准答案。

问题分为四类：单跳问题、多跳问题、时间问题、开放域问题。原数据集中的对抗问题由于缺少标准答案，被排除在本次评估之外。

### 3.2 评估指标

论文同时评估回答质量和部署效率。

回答质量包括传统的 F1、BLEU-1，以及更重要的大模型裁判分数。作者指出，F1 和 BLEU 只看词面重合，可能误判事实错误。例如标准答案是 “Alice was born in March”，生成答案是 “Alice is born in July”，词面重合仍然很高，但关键事实错了。因此论文使用大模型裁判来评估事实准确性、相关性、完整性和上下文适配度。

部署指标包括 token 消耗、检索延迟和总延迟。检索延迟是查找记忆或文本块所需时间；总延迟包括检索和生成完整答案的时间。这个设计很重要，因为生产级记忆系统不能只看正确率，还要看是否够快、够便宜。

### 3.3 基线

论文比较了六类基线。

已有 LOCOMO 基线包括 LoCoMo、ReadAgent、MemoryBank、MemGPT、A-Mem。开源方案包括 LangMem。检索增强生成基线把完整对话切成不同长度的块，用向量检索 top-k 文本块。完整上下文方法直接把整段对话放进模型上下文。专有模型基线使用 OpenAI 的记忆功能。记忆管理平台基线使用 Zep。

这个实验设置覆盖了当前常见长期记忆方案：摘要记忆、向量检索、完整上下文、图记忆、商业记忆平台和 Agentic memory。

## 4 评估结果、分析与讨论

### 4.1 不同记忆系统的性能比较

Table 1: Performance comparison of memory-enabled systems across different question types in the LOCOMO dataset. Evaluation metrics include F1 score (F1), BLEU-1 (B1), and LLM-as-a-Judge score (J), with higher values indicating better performance. A-Mem* represents results from our re-run of A-Mem to generate LLM-as-a-Judge scores by setting temperature as 0. Mem0g indicates our proposed architecture enhanced with graph memory. Bold denotes the best performance for each metric across all methods. (↑) represents higher score is better.

> 表1：LOCOMO 数据集中不同问题类型上的记忆系统性能比较。评估指标包括 F1、BLEU-1 和大模型裁判分数，分数越高越好。A-Mem* 表示作者重新运行 A-Mem 得到的大模型裁判分数，Mem0g 表示加入图记忆的架构，粗体表示各指标最佳结果。

解释：表1的整体结论很清楚：Mem0 和 Mem0g 在多数问题类型上达到或接近最佳。单跳问题上，Mem0 最强，说明自然语言稠密记忆足以快速定位单个事实。多跳问题上，Mem0 也领先，说明紧凑自然语言记忆能有效整合分散在多个会话中的信息。时间问题上，Mem0g 最强，说明显式关系和时间元数据能帮助处理事件顺序、相对时间和持续时间。开放域问题上，Zep 略微领先，但 Mem0g 非常接近。

**Mem0 更像高效、精炼的事实记忆；Mem0g 更像关系清晰、适合时间和关联推理的图记忆**。

### 4.2 跨问题类型分析

单跳问题只需要找到一个事实片段，Mem0 的自然语言记忆表示最合适，因为它检索快、噪声少、表达直接。Mem0g 在这种场景下图结构没有明显优势，甚至会带来一点额外复杂度。

多跳问题需要整合多个会话中的信息，Mem0 仍然强于 Mem0g。论文认为图结构在这里没有带来预期收益，可能因为复杂图遍历引入额外开销或冗余，而自然语言记忆本身已经足够表达多跳线索。

时间问题上，Mem0g 的优势最明显。时间推理依赖事件顺序、关系变化和时间戳，图结构能够把实体、事件、关系和时间更明确地组织起来。

开放域问题上，Mem0g 接近 Zep 的表现，说明关系结构对整合对话记忆和外部知识有帮助，但 Zep 在该类问题上仍有轻微优势。

### 4.3 与 RAG 和完整上下文方法的比较

Table 2: Performance comparison of various baselines with proposed methods. Latency measurements show p50 (median) and p95 (95th percentile) values in seconds for both search time (time taken to fetch memories/chunks) and total time (time to generate the complete response). Overall LLM-as-a-Judge score (J) represents the quality metric of the generated responses on the entire LOCOMO dataset.

> 表2：不同基线与本文方法的性能比较。延迟指标包括检索时间和总响应时间的 p50 与 p95，整体大模型裁判分数表示整个 LOCOMO 数据集上的回答质量。

解释：最强 RAG 的整体裁判分数约 61%，Mem0 达到约 67%，Mem0g 超过 68%。这说明把历史对话切块后检索原文，不如先抽取成紧凑、结构化的记忆。RAG 容易带回冗长原文和无关噪声，Mem0 则把历史压缩成更直接的事实线索。

完整上下文方法的质量最高，约 73%，但代价很大：平均约 26000 tokens，每次查询都要让模型读完整对话，p95 总延迟约 17 秒。相比之下，Mem0 的 p95 总延迟约 1.44 秒，Mem0g 约 2.59 秒。**完整上下文在小规模评估中能拿到更高分，但不适合生产级长期交互；Mem0 系列提供了更现实的质量和成本平衡**。

### 4.4 延迟分析

Figure 4: Latency Analysis of Different Memory Approaches. These subfigures illustrate the J scores and latency comparison of various selected methods from Table 2. Subfigure (a) highlights the search/retrieval latency prior to answer generation, while Subfigure (b) shows the total latency (including LLM inference). Both plots overlay each method’s J score for a holistic view of their accuracy and efficiency.

> 图4：不同记忆方法的延迟分析。子图 (a) 展示回答生成前的搜索/检索延迟，子图 (b) 展示包含大模型推理在内的总延迟。两张图都叠加了各方法的大模型裁判分数，用于同时观察准确性和效率。

解释：Mem0 的检索延迟最低，p50 为 0.148 秒，p95 为 0.200 秒；总延迟 p50 为 0.708 秒，p95 为 1.440 秒。Mem0g 因为加入图关系建模，延迟更高，但仍明显低于多数记忆系统，并且整体裁判分数最高。

LangMem 延迟非常高，p95 搜索延迟接近 60 秒，不适合实时交互。完整上下文没有检索延迟，但生成时要处理整段上下文，因此总延迟很高。Zep 延迟中等，但后续 token 与构建开销分析显示它的图记忆成本很大。

**Mem0 的生产价值主要体现在低延迟和低 token 成本；Mem0g 的价值在于用适度延迟换取更强的关系和时间推理能力**。

### 4.5 记忆系统开销

Mem0 每段对话平均约 7k tokens 的记忆表示，Mem0g 因为包含图节点和关系，约 14k tokens。Zep 的记忆图超过 600k tokens，因为它在每个节点缓存摘要，并在边上存储事实，产生大量冗余。作为对照，完整原始对话平均约 26k tokens，甚至比 Zep 的图表示小得多。

论文还观察到 Zep 存入记忆后，立即检索常常答不好，几小时后同样查询结果变好，说明其图构建可能依赖大量异步后台处理。相比之下，Mem0 的图构建即使在最坏情况下也能在一分钟内完成，新增记忆可以更快用于问答。

这部分强调的是生产级约束：**一个记忆系统不仅要答得准，还要构建快、检索快、表示紧凑，并且新增记忆能尽快可用**。

## 5 结论与未来工作

Mem0 和 Mem0g 都是为突破固定上下文窗口限制而设计的长期记忆架构。Mem0 通过动态抽取、整合和检索紧凑记忆，在单跳和多跳推理中表现突出；Mem0g 通过图记忆增强实体和关系建模，在时间推理和开放域问题中更有优势。

论文报告在 LOCOMO 上，Mem0 系列在单跳、时间、多跳问题上相对对应最佳方法分别取得约 5%、11%、7% 的提升，并相对完整上下文方法降低超过 91% 的 p95 延迟。

未来方向包括优化 Mem0g 图操作以降低延迟，探索层次化记忆架构，发展更接近人类认知的记忆整合机制，并把框架扩展到程序推理、多模态交互等非对话场景。

## 附录核心补充

附录 A 给出大模型裁判提示和 Mem0/Mem0g 回答生成提示。提示中特别强调时间问题要根据记忆时间戳把“去年”“两个月前”等相对时间转换成具体日期或年份。这解释了为什么时间记忆和时间戳在 LOCOMO 上如此关键。

附录 B 给出更新算法。核心逻辑是对每条候选事实判断 ADD、UPDATE、DELETE、NOOP。如果事实不存在则新增；如果与旧记忆冲突则删除旧信息；如果补充了更丰富信息则更新；如果已经存在或无关则不操作。这和正文中的工具调用式更新机制一致。

## 最终核心

Mem0 的思想链路可以压成一句：

**长期 Agent 不能靠无限塞上下文解决记忆问题，而要把对话持续抽取成紧凑、可更新、可检索的记忆；Mem0 用自然语言事实记忆解决效率，Mem0g 用图关系记忆增强时间和关系推理**。

这篇论文最重要的贡献不是某个单项分数，而是把长期记忆从“检索历史文本”推进到“生产级记忆管理”：抽取、更新、冲突处理、低延迟检索和按需结构化表示。