# How to Replace Mock Placeholders with Real Run Results in the README

> ⏱ Estimated time: **15–30 minutes** (including signing up for DeepSeek)
>
> 💰 Estimated cost: **¥1–2** (a ¥10 top-up covers thousands of runs)

This guide walks you through replacing every TODO placeholder in README.md with real DeepSeek run results, so your GitHub project "looks real".

---

## Step 1: Register on DeepSeek and top up (5 minutes)

1. Open https://platform.deepseek.com
2. Click "Sign up" at the top right (mobile or email supported)
3. Complete real-name verification (students may use student ID or national ID, possibly exempted)
4. Go to the "Top up" page → top up ¥10 (enough for thousands of runs)
5. Go to the "API Keys" page → click "Create new Key" → **copy and save it immediately** (shown only once!)

---

## Step 2: Configure .env (1 minute)

```bash
cd C:\Users\35713\Desktop\MultiAgentLab
cp .env.example .env
```

Open `.env` in Notepad (or VSCode) and change this line:
```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```
to:
```
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
(the real key you just copied)

Make sure the line `LLM_PROVIDER=deepseek` is unchanged.

---

## Step 3: Start the service (1 minute)

Open the first terminal window:
```bash
cd C:\Users\35713\Desktop\MultiAgentLab
python -m backend.main
```

You should see startup logs like this:
```
============================================================
MultiAgentLab v0.1.0 starting
LLM Provider: deepseek | Model: deepseek-chat
Max Rounds: 5 | Trajectory Dir: ./data/trajectories
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**If you see `Invalid API Key`**: check that `.env` was saved correctly (no BOM header, no extra spaces).

---

## Step 4: Run a real task (30 seconds)

Open a **second terminal window** and run:
```bash
curl -X POST http://localhost:8000/api/v1/run \
  -H "Content-Type: application/json" \
  -d @examples/math_problem.json
```

You should see output similar to this (this is real data — copy it down):
```json
{
  "run_id": "abc-123-def-456-...",
  "task": "Alice has 15 dollars, bought 3 pencils...",
  "status": "success",
  "rounds_used": 1,
  "total_steps": 4,
  "total_tokens": 850,
  "total_latency_ms": 3200,
  "final_answer": "Alice has 9 dollars left."
}
```

**Note the real `final_answer` and token count** — you'll paste them into the README next.

---

## Step 5: Export the full trajectory JSON (30 seconds)

Use the `run_id` you got in the previous step:
```bash
# Replace abc-123-def-456 with your real run_id
curl -s http://localhost:8000/api/v1/trajectories/abc-123-def-456 > examples/sample_real_run.json
```

Or directly copy `./data/trajectories/{run_id}.json` and overwrite `examples/sample_real_run.json` with it.

---

## Step 6: Take a screenshot of the run (2 minutes)

In the second terminal, **take a screenshot** of the entire output:
```
[your terminal screenshot content]
$ curl -X POST http://localhost:8000/api/v1/run ...
{"run_id": "...", "status": "success", ...}
```

Save it to:
```
docs/images/real_run_screenshot.png
```

**Screenshot tips**:
- Windows: use `Win + Shift + S`
- Mac: use `Cmd + Shift + 4`
- Recommend enlarging the window, increasing font size, and using a dark background for a more professional look

---

## Step 7: Replace TODO placeholders in README.md (5 minutes)

Open `README.md`, find the "📸 Real Run Showcase" section, and replace 3 TODOs:

### TODO 1: Response summary

Find:
```json
"run_id": "TODO_real_run_id",
...
"final_answer": "TODO_real_answer"
```

Replace with the real output from Step 4.

### TODO 2: Full trajectory snippet

Find:
```
> 📁 **TODO**: after running real DeepSeek, paste the content of `./data/trajectories/{run_id}.json`...
```

Replace with:
```markdown
> 📁 Full trajectory is available at [`examples/sample_real_run.json`](examples/sample_real_run.json) (produced by a real DeepSeek-V3 run)

![Real Run Screenshot](docs/images/real_run_screenshot.png)
```

### TODO 3: Remove the "currently mock" warning

Find the warning box at the top of this section:
```markdown
> ⚠️ **Currently shown**: the example below uses mock mode...
```

Change it to:
```markdown
> ✅ **Real run**: the data below comes from a real DeepSeek-V3 call on 2026-09-XX.
```

---

## Step 8: Update the ASCII timeline (3 minutes, optional but strongly recommended)

The ASCII timeline in README was written based on "expectations". After you get the real result, **we strongly recommend manually updating** with the real data:

- Replace every Step's `Thought`, `Action`, `Observation` with the real content
- Replace `Tokens: XXX in / XXX out | XXXms` with the real numbers
- Replace `Total: 4 steps | 722 tokens | 760ms` with the real statistics

This is the section the repo homepage **shows first**, so it must be real.

---

## Step 9: Commit to git (1 minute)

```bash
cd C:\Users\35713\Desktop\MultiAgentLab
git add .
git commit -m "docs: replace mock showcase with real DeepSeek run"
git push origin main
```

---

## Step 10: Check the GitHub rendering (2 minutes)

Open your GitHub repo and **confirm these all render correctly**:

- [ ] Highlights at the top of README ✓
- [ ] ASCII timeline renders correctly (not broken by code blocks) ✓
- [ ] Screenshot is clearly visible ✓
- [ ] Tables align properly ✓
- [ ] Links are clickable (the Trajectory Format Compatibility section) ✓

---

## 🎁 Bonus: Record a 1-minute demo video

If you want the GitHub project to stand out more, you can:
1. Use Windows' built-in screen recorder (`Win + G`) to record a 1-minute demo
2. Upload the video to Bilibili / YouTube
3. Add a line at the top of README:
   ```markdown
   🎬 [Watch the 1-minute demo](https://www.bilibili.com/video/BVxxxxx)
   ```

I can also **auto-generate a demo video with Chinese narration** for you (using edge-tts + screen recording) — just say the word.

---

## ❓ FAQ

**Q1: What if the planner doesn't output JSON when running with a real LLM?**
A: This is a common issue. It means your LLM didn't follow the format. Let me add a stronger prompt or retry mechanism.

**Q2: Tokens are being consumed too fast?**
A: Check whether verbose logging is enabled. In `.env`, set `LOG_LEVEL=WARNING`.

**Q3: DeepSeek responses are slow?**
A: Default timeout is 60s. You can set `REQUEST_TIMEOUT=30` to cancel slow tasks.

**Q4: Want to switch to GPT-4o for better quality?**
A: In `.env`, set `LLM_PROVIDER=openai` + fill in `OPENAI_API_KEY`, but the cost is 3× of DeepSeek.

---

## 📞 Call me anytime if something breaks

Paste the **complete error output** from the terminal and I'll debug it for you right away.