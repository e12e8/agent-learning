
## 概览 — 我将如何整理这份学习笔记

本文件是你与模型交互的学习记录，我把它重写为：

- 目标总结（快速理解核心）
- 核心概念（可复用的心智模型）
- 代码执行与 async 行为拆解（从按键到结束）
- 常见问题与工程实践（可直接复用的技巧）
- 学习路径与阶段性练习（如何循序渐进）

原始内容的关键示例与论点已保留，结构更清晰、段落更短，便于复习与面试呈现。

------

## 目标总结（一分钟读懂）

你的 Agent 实现本质上做了这三件事：

1. 决策（Decision）：判断要做什么、拆解步骤（由 `planner`）
2. 执行（Execution）：选择并调用 `tool` 完成步骤
3. 记忆与反思（Memory & Reflection）：将结果写入 `state`，评估是否需要补充

简短公式：`Thought → Action → Observation`。工程关键在于：谁来决定结束（程序或 prompt）、以及如何保存/使用 observation。

------

## 核心概念速览（心智模型）

- `state`：Agent 的短期记忆本子。没有写入就等于“没做过”。
- `action = NONE`：表示“已经授权结束”，不是模型能力的问题，而是终止信号。
- `Observation` 应该以 `system` 角色传入模型：这是外部事实，不是模型自述。
- `Planner`：把目标拆成可执行的 step。Planner 本身不调用工具。
- `Tool`：外部能力（搜索、计算、API），由 `tool_registry` 管理；Agent 只选择而不关心实现细节。

这些概念贯穿整个工程和调试场景。

------

## 执行流程（从按回车到任务结束）

1. 你运行：

```bash
python -m agent_learning.main
```

（说明：现在项目以包方式运行更稳妥；也可用 `python main.py` 若当前工作目录在 `agent_learning` 内。）

2. `main()` 创建协程列表：

```py
tasks = [
        run_agent("解释什么是 Agent"),
        run_agent("解释什么是 async"),
        run_agent("解释什么是 asyncio")
]
results = await asyncio.gather(*tasks)
```

注意：调用 `run_agent(...)` 并不马上执行函数体，它只创建协程对象——真正启动由 `await asyncio.gather` 触发。

3. 事件循环调度：

- `asyncio` 在单线程中轮流给可运行的协程短时间片；协程在遇到 `await` 时让出控制权，便会看到打印交错。

4. 单个 `run_agent` 内部步骤（简化）：

```py
print(f"Agent 接收到任务：{task}")
steps = plan(task)          # Planner 同步返回步骤
for step in steps:
        # 记录要调用的工具协程
        tasks.append(tool_func(task))

tool_results = await asyncio.gather(*tasks)
反思并合成 final_result
return final_result
```

关键点：Planner 不 await，Tool 的协程才在 `await asyncio.gather` 时并发执行。

------

## 常见问题（Q&A 与工程级建议）

- Q：删掉 `state[action] = observation` 会怎样？
    A：Agent 会“失忆”并重复调用工具，导致死循环或浪费查询量。

- Q：如果模型永远不输出 `action = NONE`，程序会停吗？
    A：若没有外部程序级的终止条件（例如检查 `state` 或最大迭代次数），确实可能无限运行。工程上应在外部收口（例如 `if "get_current_weather" in state: return ...`）。

- Q：为什么把 Observation 当作 `system` 而不是 `assistant`？
    A：Observation 是外部事实，放在 `system` 可让模型区分“事实”与“模型自身的推理”。

- Q：为什么打印是交错的？
    A：因为协程在 `await` 时让出控制，事件循环在短时间片内切换任务。

工程建议：在 Agent 外层添加最大重试次数、超时控制、以及对低置信度结果的升级策略（换 Tool / 增补 Context）。

------

## 实际代码位置与快速阅读指南

- `agent_learning/main.py`：入口，构造并并发 `run_agent`（参见 [agent_learning/main.py](agent_learning/main.py)）。
- `agent_learning/agent.py`：`run_agent` 的具体实现，是决策—执行—反思闭环的核心（参见 [agent_learning/agent.py](agent_learning/agent.py)）。
- `agent_learning/planner.py`：任务拆解逻辑。
- `agent_learning/tools.py` 与 `agent_learning/tool_registry.py`：工具定义与可用工具注册表。

打开这些文件以查看最小实现示例，理解调用链比逐行读单文件更高效。

------

## 学习路径与阶段性练习（建议）

阶段 1 — 理解模型（1–2 天）

- 目标：掌握 `async`/`await`、事件循环与协程对象的行为。
- 练习：把 `main.py` 改为只跑 1 个 Agent，加入更多 `await asyncio.sleep(0.5)` 打点，观察输出顺序。

阶段 2 — Agent 架构（3–5 天）

- 目标：分离 `Planner` / `Decision` / `Execution` / `Reflection`，实现 `state` 存取与超时。
- 练习：给 `agent.py` 增加最大重试（`max_attempts=3`），并在 `state` 中记录每次工具返回的 `confidence`，实现降级策略。

阶段 3 — 进阶与工程化（1–2 周）

- 目标：接入真实工具（API）、日志持久化、测试覆盖、性能分析。
- 练习：用 `pytest` 为关键函数（Planner、choose_tool、need_more_info）编写单元测试；用 `python -m pytest -q` 运行测试。

------

## 面试 / 汇报时可直接复述的 30 秒要点

“我实现了一个基于 `asyncio` 的 Tool Agent 框架：`main` 并发调度多个 `run_agent`，每个 Agent 由 `Planner` 拆解步骤，决策是否调用 `Tool`，执行后写入 `state` 并进行质量评估与必要的补查，工程上通过外部程序逻辑收口任务结束，从而避免模型无限循环。”

------

## 我对当前笔记所做的改动（摘要）

- 整体重构为：概览 → 核心概念 → 执行流程 → 常见问题 → 代码位置 → 学习路径。
- 保留并精炼了原文的关键比喻和结论（例如 `state`=短期记忆、`NONE`=终止信号）。
- 增加可执行练习与面试要点，方便复盘与演示。

------

如果你愿意，我可以：

- 把这个整理版另存为 `docs/整理-agen学习笔记.md`（便于发布与版本控制），或
- 在当前文件里标注重要行号并把关键代码片段补到文末供快速复制。

告诉我你更想要哪个，我将继续下一步。

------

## 附录：代码片段快速复制区（便于复查）

下面给出常用入口与关键函数的最小可复制示例，以及对应文件链接，方便你快速打开并在编辑器中查看或复制。

- `main.py`（入口示例）：[agent_learning/main.py](agent_learning/main.py)

```py
import asyncio
from agent_learning.agent import run_agent

async def main():
    tasks = [
        run_agent("解释什么是 Agent"),
        run_agent("解释什么是 async"),
        run_agent("解释什么是 asyncio")
    ]
    results = await asyncio.gather(*tasks)
    for r in results:
        print(r)

if __name__ == '__main__':
    asyncio.run(main())
```

- `agent.py`（`run_agent` 简化示例）：[agent_learning/agent.py](agent_learning/agent.py)

```py
import asyncio

async def run_agent(task: str) -> str:
    print(f"Agent 接收到任务：{task}")
    steps = plan(task)  # 同步拆解
    tasks = []
    for step in steps:
        tool = choose_tool(step)
        tasks.append(tool(step))  # 若 tool 为协程则为协程对象

    results = await asyncio.gather(*tasks)
    # 反思并合成结果
    return f"任务完成：{task}\n" + "\n".join(str(r) for r in results)
```

- `planner.py`（拆解示例）：[agent_learning/planner.py](agent_learning/planner.py)

```py
def plan(task: str):
    return [
        "理解问题的通用背景",
        "分析相关技术原理",
        "结合工程或项目实践进行说明"
    ]
```

使用方法：在编辑器中打开上面链接文件，或在项目根目录运行：

```bash
python -m agent_learning.main
```

若需要，我可以把这些片段按文件行号精确标注（生成链接到具体行）。




### ① Python 程序启动

```
python main.py
```

- Python 3.14 启动成功
- `UserWarning` **可以忽略**（只是库对 3.14 的兼容提示，不影响功能）

------

### ② 进入 `run_agent(...)`

```
Agent 正在思考和执行任务，请稍等...
```

说明：

- `main.py` 成功调用了 `run_agent`
- `client` 已经正确注入（否则会直接返回错误）

------

### ③ 第 1 步：LLM 决策

```
{
  "thought": "需要获取苏州的天气信息以判断是否需要带伞。",
  "action": "get_current_weather",
  "action_input": {
    "city": "苏州"
  }
}
```

**这一刻发生了三件关键的事：**

1. LLM 正确理解了任务
2. LLM 选择了一个**合法工具**
3. JSON 输出 **100% 可解析**

这一步如果失败，Agent 会直接卡死或反复 retry
 你这一步是**标准合格输出**

------

### ④ 工具被真正执行（不是“假执行”）

```
Action: get_current_weather
Action Input: {'city': '苏州'}
```

随后在代码中执行的是这一行：

```
result = available_tools[action](**action_input)
```

也就是说：

- **不是 LLM 说“天气是中雨”**
- 而是 **Python 函数真的返回了结果**

然后这一句极其重要：

```
state[action] = observation
```

此时，全局状态变为：

```
state = {
    "get_current_weather": '{"city": "苏州", "temperature": 10, "condition": "中雨"}'
}
```

------

### ⑤ 程序级完成判断触发（重点）

在 **下一轮循环开始之前**，程序先执行了：

```
if "get_current_weather" in state:
    return f"任务完成，天气结果：{state['get_current_weather']}"
```

⚠️ **注意重点**：

- **不是 LLM 决定结束**
- 是 **Python 程序自己判断：任务已完成**

这就是你现在这个 Agent **不会死循环**、**不会失控**的原因。

------

### ⑥ 程序安全退出

```
=== Agent 最终结果 ===
任务完成，天气结果：{"city": "苏州", "temperature": 10, "condition": "中雨"}
```

至此：

- for 循环没有继续
- LLM 没有机会再“瞎想一步”
- Agent 生命周期被**工程逻辑收口**





你现在已经**确实理解了**：

1. **LLM 本身不会“知道什么时候该停”**
2. **工具调用成功 ≠ Agent 任务完成**
3. **Agent 必须由程序（不是 Prompt）决定结束**



# 一、先给你一个“全局地图”（非常重要）

你现在的程序一共只有 **3 个文件**在工作：

```
main.py        ← 总导演（入口）
agent.py       ← 执行者
planner.py     ← 出主意的
```

你现在看不懂，是因为你不知道：

> **“到底是谁先跑？谁后跑？谁在等？”**

我们现在就解决这个问题。

------

# 二、从“你按下回车”的那一刻开始

你在终端输入的是：

```
python main.py
```

### ⚠️ 这是唯一的入口

Python 做的第一件事是：

> **从上到下执行 main.py**

------

# 三、一步一步“时间线执行”（重点）

## 🕒 时间点 T0：Python 打开 `main.py`

```
import asyncio
from agent import run_agent
```

发生了什么？

- Python 把 `agent.py` **整个读一遍**
- 把 `run_agent` 函数记住
- **但没有执行 run_agent**

⚠️ 定义函数 ≠ 执行函数

------

## 🕒 时间点 T1：Python 看到这一行

```
if __name__ == "__main__":
```

意思是：

> **“如果我是被直接运行的文件”**

你现在是 `python main.py`，所以条件成立。

------

## 🕒 时间点 T2：执行这一句（极其关键）

```
asyncio.run(main())
```

这句话做了三件事：

1. 创建一个 **事件循环（调度中心）**
2. 把 `main()` 这个任务丢进去
3. 启动调度

👉 **从这一刻开始，async 世界启动了**

------

# 四、进入 async 世界：main() 是怎么跑的？

### main 的代码是：

```
async def main():
    tasks = [
        run_agent("解释什么是 Agent"),
        run_agent("解释什么是 async"),
        run_agent("解释什么是 asyncio")
    ]

    results = await asyncio.gather(*tasks)
```

------

## 🕒 时间点 T3：构造 tasks 列表

```
run_agent("解释什么是 Agent")
```

⚠️ 这里发生了一个**非常重要但容易忽略的事**：

> ❌ 没有执行 run_agent
>  ✅ **只是创建了一个“待执行任务”**

这东西叫：**协程对象**

你可以把它理解成：

> “已经写好的工作计划，但还没开始干”

------

## 🕒 时间点 T4：执行这一句

```
await asyncio.gather(*tasks)
```

翻译成人话：

> **“请同时启动这 3 个 Agent，并等它们全部完成”**

从这一刻起，**3 个 run_agent 同时被调度**。

------

# 五、进入 Agent：run_agent 怎么跑？

现在我们只盯着 **一个 Agent**，比如任务 A。

### run_agent 的第一行：

```
print(f"\nAgent 接收到任务：{task}")
```

立即执行，立刻打印。

------

### 下一行：

```
steps = plan(task)
```

Python 跳进 `planner.py`：

```
def plan(task):
    print("Planner 正在拆解任务...")
```

⚠️ 这是普通函数：

- 立刻执行
- 不会暂停
- 不会让出控制权

------

### 接下来是 for 循环：

```
for step in steps:
    print(f"执行步骤：{step}")
    await asyncio.sleep(1)
```

------

## 🕒 关键转折点：await 出现了

当执行到：

```
await asyncio.sleep(1)
```

发生了什么？

> Agent A 对事件循环说：
>  **“我现在要等 1 秒，你让别人先跑”**

于是：

- Agent A 暂停
- 控制权回到 asyncio
- asyncio 开始执行 Agent B

------

## 🕒 这就是为什么你看到“交错输出”

不是乱，不是 bug。

是：

> **事件循环在公平地轮流执行任务**

------

# 六、你现在应该记住的 3 句话（核心）

你不用背代码，只记这 3 句话：

1. **async 函数只有遇到 await 才会暂停**
2. **await 就是“我让出执行权”**
3. **asyncio 负责在暂停点切换任务**

## 我们把你的程序“还原成机器视角”

我用你现在的结构（简化）来说明：

### main.py（核心）

```
async def main():
    tasks = [
        run_agent("解释什么是 Agent"),
        run_agent("解释什么是 async"),
        run_agent("解释什么是 asyncio")
    ]
    await asyncio.gather(*tasks)
```

### agent.py（核心）

```
async def run_agent(task):
    print(f"Agent 接收到任务：{task}")
    planner = Planner(task)
    steps = planner.plan()

    for step in steps:
        print(f"执行步骤：{step}")
        await asyncio.sleep(1)

    return f"任务完成：{task}"
```

------

## 三、程序真正的“执行主线”只有一条

这一点非常反直觉，但**必须理解**：

> **Python 只在一条线程里跑**
>
> async 没有开线程，没有并行 CPU

所以真实顺序是：

```
事件循环 → run_agent A → run_agent B → run_agent C
```

但 **每次遇到 await，都会被打断**

------

## 四、逐行“时间片”拆解（重点）

我们只看 **第一个 for 循环的第一步**。

------

### ① 事件循环调用 run_agent A

```
Agent 接收到任务：解释什么是 Agent
Planner 正在拆解任务...
执行步骤：分析任务目标
```

遇到：

```
await asyncio.sleep(1)
```

👉 **A 暂停**

------

### ② 事件循环马上切到 run_agent B

```
Agent 接收到任务：解释什么是 async
Planner 正在拆解任务...
执行步骤：分析任务目标
```

遇到：

```
await asyncio.sleep(1)
```

👉 **B 暂停**

------

### ③ 事件循环切到 run_agent C

```
Agent 接收到任务：解释什么是 asyncio
Planner 正在拆解任务...
执行步骤：分析任务目标
```

👉 **C 暂停**

------

### ④ 1 秒后，A / B / C 都“可继续”

事件循环开始轮询：

```
A → 执行下一步
B → 执行下一步
C → 执行下一步
```

这就是你看到的：

```
分析 → 查找 → 整理 → 生成
三条任务交错打印
```

------

## 五、现在你终于可以回答这个“看代码读不懂”的问题了

你之前的问题是：

> **“我主要是看代码读程序看不懂”**

原因不是你基础差，而是：

### ❌ 你用的是“函数调用视角”

### ✅ async 必须用“事件循环视角”

------

## 六、企业面试里，怎么用你这个 Agent 举例（非常重要）

如果面试官问你：

> **你做过什么 Agent / async 项目？**

你可以这样说（这是合格回答）：

> “我实现过一个基于 asyncio 的 Agent 框架，
>  主 Agent 接收任务后通过 Planner 拆解步骤，
>  多个 Agent 任务通过 asyncio.gather 并发执行，
>  每个 Agent 在 I/O 或思考阶段通过 await 主动让出事件循环，
>  从而实现高并发但单线程的任务调度模型。”

## 我们逐个“拆解责任”，像企业里 code review 一样

### A. `run_agent`

它是什么？

- 一个 **协程函数**
- 只描述了“**如果轮到我，我该怎么干活**”

👉 它**没有任何调度权**

就像员工：

> “你让我干活，我就干；不让我干，我就等。”

------

### B. `main`

它做了什么？

```
tasks = [
    run_agent(...),
    run_agent(...),
    run_agent(...)
]
await asyncio.gather(*tasks)
```

👉 它只是 **把任务交出去**

就像项目经理：

> “这三个需求，一起做吧。”

**但它不决定谁先谁后。**

------

### C. `asyncio.gather`（你选的这个）

这是**最容易被误解的地方**。

`gather` 的真实作用只有一句话：

> **把多个协程注册到事件循环里，并等待它们全部完成**

它做的是：

- 收集
- 打包
- 等结果

它 **不调度执行顺序**
 它 **不切换任务**
 它 **不决定谁先跑**

👉 `gather` ≈ “把人叫到会议室”

------

### D. ✅ 事件循环（真正的“老板”）

事件循环在干什么？

它在一个死循环里不停做这件事：

```
谁现在可以运行？
→ 执行一小步
→ 遇到 await？挂起
→ 换下一个
```

**所有你看到的：**

- A / B / C 交错执行
- “为什么会轮流打印”
- “为什么不是一个跑完再下一个”

**全部都是事件循环在干**

👉 它是 **唯一调度者**

------

## 三、用一句“面试级”对比，帮你彻底定型

> ❌ asyncio.gather 负责并发
>  ✅ 事件循环负责调度并发

你以后脑子里只要记住这一句话，就不会再乱。

------

## 四、现在回到你刚才那个“困扰你很久的问题”

你问过：

> **“run_agent A 为什么后面变成 run_agent B？”**

真正答案是：

> **不是 run_agent 主动切换**
>
> **是事件循环在每个 await 之后，把 CPU 时间给了别人**

------

## 五、你现在已经站在“真正 Agent 工程师”的门槛上了

我们盘一下你现在**已经具备但你自己没意识到的能力**：

你已经能理解：

- async ≠ 并发魔法
- await = 主动让出控制权
- Agent 并发 = 事件循环调度
- Planner / 执行步骤 / 任务流



Tool Agent = 被授予有限权限、可以在多种外部能力之间做选择并执行的 Agent 

> **只能回答问题的 Agent 本质是语言模型的封装，而能调用 Tool 的 Agent 本质是一个具备决策与执行能力的任务系统。**

这句话，**面试官会点头的那种**。



Tool = Agent 可以调用的“外部知识来源” 

Agent 并不是自己会判断工具，而是开发者为 Agent 设计了一套“从语义到能力”的映射机制。 

> **Agent 的“智能”来自架构约束，而不是自由意志。**

------

## 七、你现在正站在一个非常关键的位置

你已经开始意识到：

- Agent ≠ 魔法

- Agent ≠ 自己会想

- Agent = 被设计出来的决策系统

  ## 一、什么叫「Tool Agent」——一句话定义

  > **Tool Agent = 能在运行时判断： 是否需要“调用外部能力”来完成当前步骤**

  外部能力包括但不限于：

  - 查询数据库
  - 读文件
  - 调用 API
  - 执行系统命令
  - 访问知识库

  ⚠️ 重点不是“调用函数”，而是 **判断要不要调用**

  ------

  ## 二、普通 Agent vs Tool Agent（本质差异）

  ### 你现在的 Agent 是这样：

  ```
  任务 → Planner → 固定步骤 → 直接返回结果
  ```

  ### Tool Agent 是这样：

  ```
  任务
   ↓
  Planner 拆解
   ↓
  Agent 执行每一步时：
      ├─ 只靠思考就能完成 → 继续
      └─ 需要外部信息 / 动作 → 选择 Tool
                                 ↓
                               执行 Tool
                                 ↓
                            拿结果继续推理
  ```

  👉 **差别不在“有没有函数” 👉 差别在“有没有判断权”**

  ------

  ## 三、关键问题：

  ### Agent 为什么“能自己判断用哪个 Tool”？

  答案很重要，你已经接近了：

  > **因为 Tool 被“描述”了，而不是被“写死”调用**

  也就是说，Agent 不关心函数名，只关心：

  - Tool 是干什么的
  - 什么时候适合用
  - 输入是什么
  - 输出是什么

  ### 1️⃣ tools.py —— 干什么？

  只回答一个问题：

  > **“我能干什么事？”**

  示例（先不写代码，只讲语义）：

  - 搜索信息
  - 计算
  - 读取配置
  - 查询数据库

  **它不关心谁用、什么时候用。**

  ------

  ### 2️⃣ tool_registry.py —— 干什么？

  只回答一个问题：

  > **“现在 Agent 有哪些可用能力？”**

  它像一个 **工具清单 / 能力白名单**

  Agent 只和它打交道：

  ```
  Agent：你现在有什么能力？
  Registry：我这里有 search、calc
  ```

  ------

  ### 3️⃣ Agent —— 干什么？

  只干三件事：

  1. 看当前步骤要做什么
  2. 判断「是否需要 Tool」
  3. 如果需要 → 通过 Registry 调用

  ⚠️ Agent **不知道 Tool 细节**
   ⚠️ Agent **不 import tools.py**



# 第一段输出：为什么会出现 3 次「Agent 接收到任务」

你看到的是：

```
Agent 接收到任务：解释什么是 Agent
...
Agent 接收到任务：解释什么是 async
...
Agent 接收到任务：解释什么是 asyncio
...
```

### 这是因为在 `main.py` 里，你做了什么？

你一定写了类似这种代码（简化版）：

```
tasks = [
    run_agent("解释什么是 Agent"),
    run_agent("解释什么是 async"),
    run_agent("解释什么是 asyncio")
]

await asyncio.gather(*tasks)
```

👉 **结论：**

- 你不是跑了 1 个 Agent
- 而是 **并发跑了 3 个 Agent 实例**

每一个 `run_agent(...)`：

> 都是一个**独立的 Agent**

------

# 三、为什么「准备执行步骤」会连着出现 3 次？

以其中一个 Agent 为例：

```
准备执行步骤：理解问题的通用背景
准备执行步骤：分析相关技术原理
准备执行步骤：结合工程或项目实践进行说明
```

### 对应代码是这里（agent.py）：

```
steps = plan_task(task)

for step in steps:
    print(f"准备执行步骤：{step}")
    tool_type = choose_tool(step)
    tool_func = TOOLS[tool_type]
    tasks.append(tool_func(task))
```

### 这里发生了什么？

1️⃣ Planner 返回 3 个 step
 2️⃣ Agent **没有执行 Tool**
 3️⃣ Agent **只是登记任务**

⚠️ 非常关键一句话：

> **此时 Tool 还没跑，只是被“记下来”**

------

# 四、为什么「信息不充分」只出现 3 次，而不是 9 次？

你看到的是：

```
信息不充分，尝试使用技术工具补充
信息不充分，尝试使用技术工具补充
信息不充分，尝试使用技术工具补充
```

不是 9 次，对吧？

### 原因非常关键：

- 每个 Agent 有 **3 个 Tool 任务**
- 但你在反馈闭环里，是：

```
for result in results:
    if need_more_info(result):
        ...
```

而你的 Tool 返回是类似：

```
{
    "type": "project",
    "confidence": 0.4
}
```

### 也就是说：

- 每个 Agent **只有一个结果触发了补充逻辑**
- 不是每个 step 都触发

👉 **这说明你的反馈闭环逻辑是生效的，而且是“有选择的”**

------

# 五、为什么最终结果是「项目实践经验 + 技术相关内容」？

你输出的是：

```
任务完成：解释什么是 Agent
项目实践经验
技术相关内容
```

### 我们拆开来看它是怎么拼出来的

------

## 第 1 部分：项目实践经验

来自哪个 Tool？

👉 来自你第一次并发调用的 Tool，例如：

```
search_project_knowledge()
```

返回了：

```
{
    "type": "project",
    "confidence": 0.4,
    "content": "项目实践经验"
}
```

Agent 先无条件加上：

```
final_result += result["content"]
```

------

## 第 2 部分：技术相关内容

为什么会出现？

因为：

```
if need_more_info(result):
    tech_result = await tech_tool(task)
```

而 `need_more_info` 是：

```
return confidence < 0.6
```

👉 **这是你亲手写出来的反馈闭环**

------

# 六、现在你要真正理解的一句话（请慢慢看）

> **你的 Agent 不是“按流程跑完”**
>
> 而是：
>
> - 先尝试
> - 再评估
> - 再补救

到这一刻，你已经可以在简历 / 面试中真实地说：

- 我实现了多 Agent 并发执行
- 每个 Agent 内部支持 Tool 并发调用
- Agent 会根据 Tool 返回结果进行质量评估
- 当结果不足时，会主动触发补充 Tool 调用

这不是“照抄 demo”，
 这是**完整的 Agent 行为闭环**。



# 第一步：你敲 `python main.py` 的那一刻

### 发生的第一件事（100%确定）

Python 做三件事：

1. 打开 `main.py`
2. **从上往下执行**
3. 找到 `asyncio.run(...)`

假设你现在的 `main.py` 类似这样：

```
import asyncio
from agent import run_agent

async def main():
    tasks = [
        run_agent("解释什么是 Agent"),
        run_agent("解释什么是 async"),
        run_agent("解释什么是 asyncio")
    ]
    results = await asyncio.gather(*tasks)

asyncio.run(main())
```

------

# 三、第二步：`run_agent(...)` 并没有立刻执行

⚠️ **这是你现在最容易误解的地方**

### 这一行：

```
run_agent("解释什么是 Agent")
```

**不是**马上执行函数体。

而是：

> 👉 **创建一个“协程对象”**

你可以把它理解成：

```
“一张待办任务单”
```

所以此时：

```
tasks = [
    <协程1>,
    <协程2>,
    <协程3>
]
```

⚠️ 这一步 **没有任何 print 输出**

------

# 四、第三步：真正的开始点 —— `await asyncio.gather`

```
results = await asyncio.gather(*tasks)
```

这句是**真正的启动按钮**。

从这里开始：

- 协程 1：run_agent("Agent")
- 协程 2：run_agent("async")
- 协程 3：run_agent("asyncio")

**同时开始执行**

------

# 五、进入 run_agent（你看到的第一行输出）

```
print(f"\nAgent 接收到任务：{task}")
```

所以你看到：

```
Agent 接收到任务：解释什么是 Agent
Agent 接收到任务：解释什么是 async
Agent 接收到任务：解释什么是 asyncio
```

### 为什么顺序看起来是“乱的”？

因为：

> **并发不是轮流，而是谁先跑到就先打印**

------

# 六、Planner 是什么时候执行的？

紧接着 run_agent 里：

```
steps = plan_task(task)
```

Planner **没有并发、没有 await**，是普通函数。

```
def plan_task(task):
    return [
        "理解问题的通用背景",
        "分析相关技术原理",
        "结合工程或项目实践进行说明"
    ]
```

所以：

- 立刻返回
- 每个 Agent 都得到 **完全相同的 steps**

------

# 七、你看到的「准备执行步骤」到底干了什么？

代码（关键）：

```
tasks = []

for step in steps:
    print(f"准备执行步骤：{step}")
    tool_type = choose_tool(step)
    tool_func = TOOLS[tool_type]
    tasks.append(tool_func(task))
```

我们一行一行拆：

------

### ① print

```
print(f"准备执行步骤：{step}")
```

👉 **只是打印，没有执行任何 Tool**

------

### ② tool_func = TOOLS[tool_type]

你自己说得非常对：

> tool_registry 本质就是一个「函数字典」

这里仅仅是：

```
拿到函数本身
```

------

### ③ 最重要的一行（你之前完全没意识到）

```
tasks.append(tool_func(task))
```

⚠️ 注意：
 如果 `tool_func` 是 async 函数：

> **它返回的不是结果，而是协程对象**

也就是说你现在的 `tasks` 是：

```
[
  <tool协程1>,
  <tool协程2>,
  <tool协程3>
]
```

👉 **到这里，Tool 仍然一个都没执行**

------

# 八、Tool 真正执行的唯一位置

这一句：

```
results = await asyncio.gather(*tasks)
```

这时才发生：

- 所有 Tool **同时开始执行**
- 谁快谁先返回
- Agent 在这里“挂起等待”

------

# 九、为什么会出现「信息不充分，尝试使用技术工具补充」

现在你进入这段代码：

```
for result in results:
    final_result += result["content"]

    if need_more_info(result):
        print("信息不充分，尝试使用技术工具补充")
```

说明两件事：

1. Tool **已经执行完**
2. Tool 返回了结构化数据

例如：

```
{
  "type": "project",
  "confidence": 0.4,
  "content": "项目实践经验"
}
```

而你写了：

```
if confidence < 0.6:
```

👉 **这是你第一次写出“Agent 自我判断”逻辑**

------

# 十、最后为什么能顺利结束？

因为：

```
return f"任务完成：{task}\n{final_result}"
```

每个 run_agent：

- 返回一个字符串
- 被 `asyncio.gather` 收集
- main.py 打印



# 先给你一句总纲（非常重要）

> **Agent ≠ async + tool + llm**
>
> **Agent = 决策（Decision）→ 执行（Execution）→ 反思（Reflection）的闭环**

你现在的 `run_agent`，**已经同时包含了这三件事**，只是**混在一起了**。

我们这一步做的事情叫：

> **职责分离（Separation of Concerns）**

这是**工程能力，而不是语法能力**。

------

# 二、先不看代码，先看“Agent 的三层结构”

请你先记住这张**逻辑结构图**：

```
run_agent(task)
│
├── 决策层 Decision
│     ├── 任务拆解（Planner）
│     ├── 步骤判断
│     ├── 工具选择
│
├── 执行层 Execution
│     ├── 调用 Tool
│     ├── 并发 / 串行
│     ├── 拿到结果
│
└── 反思层 Reflection
      ├── 判断结果是否足够
      ├── 是否补充
      ├── 是否调整策略
```

**注意**：
 这不是“写法”，这是**Agent 的思维模型**。

------

# 三、现在我们回到你现有的 run_agent（概念级拆解）

你现在的 `run_agent`，逻辑上是这样跑的：

------

## ① 决策层（你已经写了，但没意识到）

这些代码 **本质都是 Decision**：

### 1️⃣ 任务拆解

```
steps = plan_task(task)
```

含义不是“函数调用”，而是：

> Agent 在**决定要怎么做这件事**

------

### 2️⃣ 步骤 → 工具判断

```
tool_type = choose_tool(step)
```

这是一个**典型的 Agent 决策行为**：

- 输入：当前 step
- 输出：使用哪种能力

注意一句话（非常重要）：

> **决策层不执行任何实际动作**

它只回答：
 **“该用什么能力？”**

------

## ② 执行层（Agent 的“手”）

下面这些代码，**都是 Execution**：

```
tool_func = TOOLS.get(tool_type)
tool_result = await tool_func(task)
```

含义是：

> Agent 不再思考
>  👉 **开始动手做事**

执行层的特点：

- 不判断“该不该做”
- 不判断“做得好不好”
- 只负责 **把能力跑完**

------

## ③ 反思层（这是 Agent 的“灵魂”）

这一段非常关键：

```
confidence = tool_result.get("confidence", 0.5)

if confidence < 0.6:
    # 再调用技术工具
```

这一步在做什么？

不是执行，也不是决策下一步任务，而是：

> **Agent 在“回看自己刚才的结果”**

这就是 Reflection。

反思层关注的不是“我有没有执行”，而是：

- 结果是否足够？
- 是否需要补充？
- 是否需要改变策略？

------

# 四、为什么一定要“拆层”，而不是继续堆代码？

我用一句工作中的真话告诉你原因：

> **企业要的是“能演化的 Agent”，不是“能跑的脚本”**

如果你不拆层，后果是：

- Planner 换 LLM → 整个 run_agent 要改
- Tool 增加 5 个 → choose_tool 混乱
- 要加 Memory → 全文件重构

而**拆层之后**：

- 决策层可换策略
- 执行层可并发优化
- 反思层可接 Memory / Reward

这就是**架构设计能力**。
一、Agent 结构设计文档（简化但企业可用）

文档定位：
Agent 应用工程师 / AI 应用开发工程师（偏工程）

1. Agent 的核心职责（不是聊天机器人）

Agent ≠ ChatBot

Agent 的职责是：

接收一个目标（Task），通过自主决策调用工具（Tool），
在执行过程中评估结果质量，必要时调整策略，直到完成目标。

2. Agent 总体架构（逻辑视图）
┌─────────────┐
│    Task     │  ← 用户目标
└─────┬───────┘
      ↓
┌─────────────┐
│   Planner   │  ← 任务拆解（Step）
└─────┬───────┘
      ↓
┌─────────────┐
│  Decision   │  ← 选择使用哪些 Tool
└─────┬───────┘
      ↓
┌─────────────┐
│ Execution   │  ← 执行 Tool（可并发）
└─────┬───────┘
      ↓
┌─────────────┐
│ Reflection  │  ← 结果评估 / Retry 判断
└─────┬───────┘
      ↓
┌─────────────┐
│   Result    │  ← 最终输出
└─────────────┘

二、你问的核心问题：Task → Tool → Result → Retry

下面是标准 Agent 执行闭环。

Step 1：Task（目标输入）
输入的不是“问题”，而是“目标”

例子：

❌「什么是 Agent？」

✅「生成一份关于 Agent 的工程级解释」

Agent 只关心：我要达成什么目标

Step 2：Planner（任务拆解）
为什么要拆？

因为：

一个 Tool 无法一次性完成复杂任务

每个 Tool 只负责一种能力

示例拆解：

1. 理解 Agent 的基本概念
2. 分析 Agent 的技术实现
3. 结合工程实践进行说明


📌 重要原则：

Step 是“可执行单元”，不是自然语言段落

Step 3：Decision（选择 Tool）
Agent 为什么能“自己判断用什么 Tool”？

不是魔法，是规则 +上下文判断

Agent 会根据：

Step 的语义

Tool 的能力描述

当前状态（是否失败过）

做判断，例如：

Step 内容	决策
通用概念	general_tool
技术原理	tech_tool
工程实践	project_tool

📌 本质是一个 策略选择器（Policy）

Step 4：Execution（执行 Tool）
Tool 是什么？

Tool 是：

Agent 可以调用的外部能力

例如：

搜索知识

查询数据库

调用 API

运行脚本

执行特点（关键）

可并发（async / gather）

无状态或弱状态

只负责干活，不负责决策

📌 Tool 不知道自己“为什么被调用”

Step 5：Result（读取 Tool 结果）

Tool 返回结构化结果，例如：

{
  "status": "ok",
  "content": "Agent 是一种...",
  "confidence": 0.55
}


Agent 关注的是：

成功 or 失败？

信息是否足够？

是否可信？

Step 6：Reflection（反思 / Retry 判断）

这一步决定 Agent 是否高级。

Agent 如何判断要不要 Retry？

常见规则：

status != ok → Retry

confidence < 阈值 → 换 Tool 再查

内容重复 / 模糊 → 升级策略

示例逻辑：

如果信息过泛：
    → 换技术工具
如果技术工具仍不充分：
    → 标记为部分完成


📌 重点：

Retry 不是“重复执行”，而是策略升级

Step 7：Finish（终止条件）

Agent 什么时候停？

所有 Step 完成

Retry 次数用尽

达到可接受结果

三、用一句话总结整个闭环（面试级）

Agent 通过 Planner 将目标拆解为可执行步骤，
在每个步骤中根据上下文动态选择 Tool，
执行后评估结果质量，并在必要时调整策略进行 Retry，
最终完成目标。