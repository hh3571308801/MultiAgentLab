# 如何把 README 中的 Mock 占位替换成真实运行结果

> ⏱ 预计耗时：**15-30 分钟**（包括注册 DeepSeek）
>
> 💰 预计花费：**¥1-2**（10 元充值能用几千次）

本指南会带你把 README.md 里的所有 TODO 占位符替换成真实的 DeepSeek 运行结果，让你的 GitHub 项目"看起来像真的"。

---

## Step 1：注册 DeepSeek 并充值（5 分钟）

1. 打开 https://platform.deepseek.com
2. 点击右上角"注册"（支持手机号或邮箱）
3. 完成实名认证（学生用学号或身份证，可能免认证）
4. 进入"充值"页面 → 充值 ¥10（够你跑几千次实验）
5. 进入"API Keys"页面 → 点击"创建新 Key" → **立即复制保存**（只显示一次！）

---

## Step 2：配置 .env（1 分钟）

```bash
cd C:\Users\35713\Desktop\MultiAgentLab
cp .env.example .env
```

用记事本（或 VSCode）打开 `.env`，把这一行：
```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```
改成：
```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
（你刚才复制的真实 key）

确认 `LLM_PROVIDER=deepseek` 这一行没被改动。

---

## Step 3：启动服务（1 分钟）

打开第一个终端窗口：
```bash
cd C:\Users\35713\Desktop\MultiAgentLab
python -m backend.main
```

你应该看到这样的启动日志：
```
============================================================
MultiAgentLab v0.1.0 启动
LLM Provider: deepseek | Model: deepseek-chat
Max Rounds: 5 | Trajectory Dir: ./data/trajectories
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**如果报错 `Invalid API Key`**：检查 .env 文件是否正确保存（无 BOM 头、无多余空格）。

---

## Step 4：跑真实任务（30 秒）

打开**第二个终端窗口**，运行：
```bash
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d @examples/math_problem.json
```

你应该看到类似这样的输出（**这就是真实数据**，记下来）：
```json
{
  "run_id": "abc-123-def-456-...",
  "task": "小红有 15 元钱，买了 3 支铅笔...",
  "status": "success",
  "rounds_used": 1,
  "total_steps": 4,
  "total_tokens": 850,
  "total_latency_ms": 3200,
  "final_answer": "小红还剩 9 元钱。"
}
```

**注意真实的 final_answer 和 token 数**——下面要填到 README。

---

## Step 5：导出完整轨迹 JSON（30 秒）

把上一步拿到的 `run_id` 用在这里：
```bash
# 把 abc-123-def-456 替换成你的真实 run_id
curl -s http://localhost:8000/api/v1/trajectories/abc-123-def-456 > examples/sample_real_run.json
```

或者直接复制 `./data/trajectories/{run_id}.json` 的内容覆盖 `examples/sample_real_run.json`。

---

## Step 6：截一张运行截图（2 分钟）

在第二个终端里**截图保存**整段：
```
[你的终端截图内容]
$ curl -X POST http://localhost:8000/api/v1/run ...
{"run_id": "...", "status": "success", ...}
```

保存到：
```
docs/images/real_run_screenshot.png
```

**截图小技巧**：
- Windows：用 `Win + Shift + S` 截屏工具
- Mac：用 `Cmd + Shift + 4`
- 推荐把窗口放大、字体调大、黑色背景，看起来更专业

---

## Step 7：替换 README.md 的 TODO 占位符（5 分钟）

打开 `README.md`，找到"📸 Real Run Showcase"这一节，替换 3 处 TODO：

### TODO 1：响应摘要

找到：
```json
"run_id": "TODO_真实_run_id",
...
"final_answer": "TODO_真实答案"
```

替换为 Step 4 的真实输出。

### TODO 2：完整轨迹片段

找到：
```
> 📁 **TODO**：跑真实 DeepSeek 后，把 `./data/trajectories/{run_id}.json` 的内容...
```

替换为：
```markdown
> 📁 完整轨迹见 [`examples/sample_real_run.json`](examples/sample_real_run.json)（基于真实 DeepSeek-V3 运行）

![Real Run Screenshot](docs/images/real_run_screenshot.png)
```

### TODO 3：删除"当前展示"警告

把这一节开头的警告框删掉或改写：
```markdown
> ⚠️ **当前展示**：以下示例使用 mock 模式...
```
改成：
```markdown
> ✅ **真实运行**：以下数据来自 DeepSeek-V3 在 2026-09-XX 的真实调用。
```

---

## Step 8：更新 ASCII 时间线（3 分钟，可选但强烈推荐）

README 里的 ASCII 时间线是基于"预期"写的。跑出真实结果后，**强烈建议手动更新**真实数据：

- 替换每个 Step 的 `Thought`、`Action`、`Observation` 为真实内容
- 替换 `Tokens: XXX in / XXX out | XXXms` 为真实数字
- 替换 `Total: 4 steps | 722 tokens | 760ms` 为真实统计

这一段是面试官**第一眼看到**的内容，必须真实。

---

## Step 9：提交到 Git（1 分钟）

```bash
cd C:\Users\35713\Desktop\MultiAgentLab
git add .
git commit -m "docs: replace mock showcase with real DeepSeek run"
git push origin main
```

---

## Step 10：检查 GitHub 显示效果（2 分钟）

打开你的 GitHub 仓库，**确认这些都能正常显示**：

- [ ] README 顶部项目亮点 ✓
- [ ] ASCII 时间线渲染正常（不被代码块破坏）✓
- [ ] 截图清晰可见 ✓
- [ ] 表格对齐 ✓
- [ ] 链接可点击（Trajectory Format Compatibility 那节）✓

---

## 🎁 Bonus：录个 1 分钟 Demo 视频

如果你想让 GitHub 项目更出彩，可以：
1. 用 Windows 自带录屏（`Win + G`）录一个 1 分钟的 demo
2. 把视频上传到 B站/YouTube
3. 在 README 顶部加一行：
   ```markdown
   🎬 [观看 1 分钟 Demo 视频](https://www.bilibili.com/video/BVxxxxx)
   ```

我也可以帮你**自动生成带中文讲解的演示视频**（用 edge-tts + 屏幕录屏），你说一声就开干。

---

## ❓ 常见问题

**Q1：跑真实 LLM 时 planner 输出不是 JSON 怎么办？**
A：这是常见问题。说明你的 LLM 没按格式输出。让我帮你加更强的 prompt 或重试机制。

**Q2：token 用得太快怎么办？**
A：检查是不是开了 verbose 日志。在 `.env` 里把 `LOG_LEVEL=WARNING` 即可。

**Q3：DeepSeek 响应慢怎么办？**
A：默认 60 秒超时。可以设 `REQUEST_TIMEOUT=30` 取消慢任务。

**Q4：想换成 GPT-4o 效果更好怎么办？**
A：在 `.env` 里改 `LLM_PROVIDER=openai` + 填 `OPENAI_API_KEY`，但成本是 DeepSeek 的 3 倍。

---

## 📞 跑出问题随时叫我

把**完整的错误信息**（终端输出）贴给我，我马上帮你 debug。