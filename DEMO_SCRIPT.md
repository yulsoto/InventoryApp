# Live Demo — Troubleshooting Production Errors with Datadog

**Audience**: Customers / prospects evaluating Datadog APM + Error Tracking + Logs.
**Duration**: ~15 minutes (5 min setup explained + 10 min live).
**Goal**: Demonstrate end-to-end troubleshooting flow from "customer complaint" to "fix in production" using Datadog.

---

## 🎬 The Story

> *"Last week we deployed a new feature: `GET /api/items/<id>/velocity` — it returns how many units of a given product are sold per day on average. Useful for inventory forecasting. The feature passed CI, passed code review, passed staging. But on Monday morning, a customer messaged us: 'your velocity endpoint is throwing errors'. Let's troubleshoot it with Datadog — without SSH-ing to any server, without grepping any logs by hand."*

---

## 🐛 The Bug

The endpoint computes `total_sold / days_old`. For items created **today** (where `days_old == 0`), this raises `ZeroDivisionError` → returns HTTP 500.

This is a real-world class of bug that:
- Passes unit tests when tests use older fixture data
- Only shows in production when fresh inventory is queried
- Is exactly the kind of thing that's hard to catch without observability

Buggy line in [app/routes.py](app/routes.py) (look for `velocity = total_sold / days_old`):
```python
velocity = total_sold / days_old   # 💥 BOOM when days_old == 0
```

The fix (don't apply yet — it's the demo punchline):
```python
velocity = (total_sold / days_old) if days_old > 0 else 0.0
```

---

## 🛠️ Prerequisites

Before running the demo, confirm:

| Item | How to verify |
|------|--------------|
| InventoryApp is running on EC2 | Browse `http://44.193.209.93:8000` |
| Datadog Agent + APM is collecting | DD UI → APM → Services → `inventoryapp` visible |
| Logs are streaming | DD UI → Logs Explorer → `service:inventoryapp` |
| Buggy `/velocity` endpoint is deployed | `curl http://44.193.209.93:8000/api/items/3/velocity` returns 200 |
| At least one item created **today** exists | If not, create one via `/add` UI (the bug needs a "fresh" item) |
| GitHub repo wired to Datadog Source Code Integration | DD UI → Service → trace span → "Code Origin" links to GitHub |

If you need to create a fresh item for the demo (item with `days_old == 0`):

```bash
curl -X POST http://44.193.209.93:8000/add \
  -d "name=Demo Item $(date +%H%M%S)" \
  -d "quantity=10" \
  -d "price=9.99" \
  -d "category=Demo" \
  -L
```

Then `curl http://44.193.209.93:8000/api/items` to get its `id`. We'll call this **the fresh item ID**.

---

## 🎬 Act 1 — The Happy Path (1 min)

**Narrative**: *"Our new feature works fine for established items. Watch."*

In a terminal visible on screen:

```bash
# Item id=3 (vaso cristal) — created days ago, so days_old > 0
curl -s http://44.193.209.93:8000/api/items/3/velocity | python3 -m json.tool
```

Returns 200 with velocity data. **Talking point**: "Looks great. Deployed. Done. Or so we thought."

---

## 🎬 Act 2 — The Customer Report (1 min)

**Narrative**: *"Then a customer messages us: 'velocity is broken for our new SKUs.' Let me reproduce."*

```bash
# Replace <FRESH_ID> with the item created today
curl -i http://44.193.209.93:8000/api/items/<FRESH_ID>/velocity
```

Result: **HTTP 500 Internal Server Error**. No useful info in the response.

**Talking point**: *"Without observability, this is where the pain starts. SSH to the server. Find the log. Pray you have stack traces. Grep around. Hope you can reproduce. Let's see how Datadog changes this."*

To make the error visible in metrics, fire several:

```bash
for i in {1..15}; do
  curl -s -o /dev/null -w "Try $i: HTTP %{http_code}\n" \
    http://44.193.209.93:8000/api/items/<FRESH_ID>/velocity
  sleep 0.3
done
```

---

## 🎬 Act 3 — APM: Spot the Spike (2 min)

**Where to click**: Datadog UI → **APM** → **Services** → `inventoryapp`

**What to show**:
1. **Service Overview**: error rate chart shows a clear spike in the last few minutes (was 0%, now non-zero).
2. **Resource list**: sort by Error Rate descending. `GET /api/items/<int:item_id>/velocity` is at the top with **100% errors**.
3. **Talking points**:
   - "Datadog auto-detected the new endpoint within minutes of deployment — no config change."
   - "Endpoint-level granularity is automatic. We can see the bad actor in seconds."

---

## 🎬 Act 4 — Error Tracking: Group & Identify (2 min)

**Where to click**: APM → Service `inventoryapp` → **Errors** tab → group `ZeroDivisionError`

**What to show**:
1. **Grouped error**: `ZeroDivisionError: division by zero` (or `float division by zero` depending on Python).
2. Count, first seen, last seen, trend chart.
3. **Affected resource**: `GET /api/items/<int:item_id>/velocity`.
4. **Sample stack trace** in the right panel — directly points to `routes.py` and the offending line.
5. **Talking points**:
   - "Error Tracking automatically groups occurrences by exception type AND location. 15 errors collapse into 1 actionable issue."
   - "First seen tells you exactly when the regression was introduced — perfect for tying to a deployment."

---

## 🎬 Act 5 — Trace + Code Origin: The Aha Moment (3 min)

**Where to click**: from the Error Tracking detail → "Latest Sample Trace" → flame graph

**What to show**:
1. **Flame graph**: top span is `flask.request GET /api/items/<int:item_id>/velocity` — colored **red** because it errored.
2. Click the span. Right panel shows:
   - Full exception type + message
   - Stack trace
   - **Code Origin**: clickable link to `app/routes.py:LINE_NUMBER` — opens GitHub directly at the bad line.
3. **Click the Code Origin link**. GitHub opens. The buggy line is highlighted: `velocity = total_sold / days_old`.
4. **Talking points** (this is the WOW moment):
   - "We never SSH'd anywhere. We never grepped a log. Datadog took us from 'something is broken' to **the exact line of code** in three clicks."
   - "Source Code Integration is enabled via Datadog's GitHub integration — set up once, works for every service."

---

## 🎬 Act 6 — Logs Correlation: Full Story (2 min)

**Where to click**: from the trace → **Logs** tab (within the trace view)

**What to show**:
1. The actual gunicorn / Python error log line for **this specific request** — automatically correlated via `trace_id` (set via `DD_LOGS_INJECTION=true`).
2. Full Python traceback visible inline.
3. **Optional cross-product**: jump to **Logs Explorer**, search `service:inventoryapp status:error`, click any log, sidebar shows "View Trace" — same trace.
4. **Talking points**:
   - "Logs and traces are bi-directional. From a trace you see its logs. From a log you see its trace. No correlation IDs to plumb manually."
   - "This is where SRE teams save hours per incident."

---

## 🎬 Act 7 — The Fix & Recovery (3 min)

Open `app/routes.py` in your editor, find the velocity endpoint, change the line:

```python
# Before
velocity = total_sold / days_old

# After
velocity = (total_sold / days_old) if days_old > 0 else 0.0
```

Deploy:

```bash
# In Mac terminal
cd "/Users/yuliethe.soto/Documents/App Development/InventoryApp"
git add app/routes.py
git commit -m "Fix ZeroDivisionError in /velocity for items created today"
git push

# Then in EC2 SSH
ssh -i ~/.ssh/inventoryapp-key.pem ec2-user@44.193.209.93
cd ~/InventoryApp
git pull
sudo systemctl restart inventoryapp
exit
```

Verify the fix:

```bash
curl -s http://44.193.209.93:8000/api/items/<FRESH_ID>/velocity | python3 -m json.tool
```

Should return 200 with `avg_daily_velocity: 0.0`.

**Back in Datadog**:
- Refresh APM Service Overview → error rate is dropping toward 0% in real time.
- Error Tracking group: "Last seen" stops advancing — Datadog auto-detects the issue is resolved.

**Talking points**:
- "End-to-end: from customer ping to deployed fix in ~15 minutes."
- "Without Datadog, this same investigation could've been hours: tail logs, miss the stack trace, reproduce locally, debug, ship blindly, hope it works."

---

## 🎬 Act 8 — Recap (1 min)

| Stage | Time without Datadog | Time with Datadog |
|-------|---------------------|-------------------|
| Detect the issue | Wait for customer escalation (hours) | Auto-flagged in APM (minutes) |
| Identify the endpoint | Grep access logs | One click in Resources table |
| Find the exception type | SSH + grep stack trace | One click in Error Tracking |
| Locate the line of code | Read stack trace, scroll the file | One click → GitHub at the line |
| Correlate to a specific request | Manually trace timestamps | Automatic via `trace_id` |
| Verify the fix | Curl and wait for next customer report | Watch the live metrics drop |

**Closing line**: *"Datadog is not just dashboards. It's the single pane of glass that turns 'we're flying blind' into 'we know exactly what happened, when, and why' — for any production issue."*

---

## 🧹 Reset for Next Demo

After running the demo, leave it ready to re-run:

1. Re-introduce the bug — `git revert HEAD --no-edit && git push` (then pull+restart on EC2).
2. OR keep the fix and use a different bug next time (memory leak, slow SQL, etc.).
3. Create a fresh item if the previous one's `days_old` has aged past 0.

---

## 📚 Datadog Features Showcased

| Product | Where it shines in this demo |
|---------|------------------------------|
| **APM** | Service map, endpoint discovery, latency/error metrics, trace exploration |
| **Error Tracking** | Auto-grouping, first/last-seen, stack traces inline |
| **Source Code Integration** | Click from span → GitHub line directly |
| **Logs ↔ APM correlation** | Bi-directional traversal via `trace_id` |
| **Real-time metrics** | Watch error rate drop after deploy |
| **Logs discovery** (`DD_LOGS_CONFIG_PROCESS_COLLECT_ALL`) | Auto-tailed gunicorn logs, no per-app config |

---

## 🎙️ Talking Points to Customize per Audience

- **For DevOps / SRE leads**: focus on Acts 3-6, emphasize MTTR reduction and the cross-product investigation flow.
- **For developers**: focus on Acts 5 (Code Origin) and 6 (logs/trace correlation) — "your IDE-level debugger, in production".
- **For execs**: lead with the recap table — quantifiable time savings per incident.
- **For Datadog-curious teams already using competitor APM**: highlight `DD_LOGS_CONFIG_PROCESS_COLLECT_ALL` single-step setup and unified product UX as differentiators.
