# PyCostAudit Commands Reference

**Complete guide to all commands you can use in Claude Code with PyCostAudit**

---

## 🚀 Getting Started

### Start Interactive Mode
```bash
python3 << 'EOF'
from pycostaudit.cli_interactive import main_interactive_loop
main_interactive_loop()
EOF
```

Or in a Claude Code conversation:
```python
from pycostaudit.cli_interactive import InteractiveCLI

cli = InteractiveCLI()
print(cli.welcome())

# Then input commands below:
```

---

## 📋 Command Categories

### 1. **PROJECT-SPECIFIC ANALYSIS** (Type project name)
### 2. **ANALYSIS OPTIONS** (Type 1-34)
### 3. **SPECIAL COMMANDS** (Type keyword)
### 4. **QUICK REFERENCES** (Common patterns)

---

## 1️⃣ PROJECT-SPECIFIC ANALYSIS

**Show costs for a specific project**

### Available Projects (Detected from your history):
- `statguard` — 55 sessions (your most active project)
- `clusteraudiencekit` — 41 sessions
- `prismnote` — 38 sessions
- `pyroboframes` — 31 sessions
- `streamxl` — 29 sessions
- `pycostaudit` — 14 sessions

### Command Format:
```
Type: [project-name]
```

### Examples:

#### Analyze StatGuard
```
Input:  statguard
Output: 
  ================================================================================
  📊 COST ANALYSIS FOR STATGUARD
  ================================================================================
  
  Sessions: 55
  Your focus: This is one of 6 active projects
  
  🎯 RECOMMENDED ANALYSES FOR THIS PROJECT:
    1. Cost breakdown — Where does this project's budget go?
    2. Anomalies — Any unusual spending patterns?
    3. Recommendations — How to optimize this project?
    4. Trends — Is this project getting more expensive?
    5. Comparison — How does this compare to other projects?
  
  ================================================================================
```

#### Analyze ClusterAudienceKit
```
Input:  clusteraudiencekit
Output: [Similar project-specific insights for 41 sessions]
```

#### Analyze PrismNote
```
Input:  prismnote
Output: [Project insights for 38 sessions]
```

### What Each Project Option Shows:
- Sessions count for that project
- Recommended analyses specific to that project
- Next steps related to that project's costs

---

## 2️⃣ ANALYSIS OPTIONS (1-34)

**Run specific cost analyses**

### Top 5 Most Useful (Start Here):

#### **Option 4: Detect Anomalies** ⭐ MOST URGENT
```
Input:  4
Output: 
  📊 RUNNING: Detect anomalies
  ================================================================================
  [Analysis results showing cost spikes in your projects]
  
  🎯 WHAT WOULD YOU LIKE TO EXPLORE NEXT?
  
    3. Which projects cost the most?
       → Identify focus areas
    
    6. Give me personalized recommendations
       → Get ROI targets
    
    20. Set a monthly budget
       → Lock spending limits
```

**Use this to:** Find unusual spending patterns, cost spikes, outliers

#### **Option 3: Which Projects Cost Most?** ⭐ MOST VALUABLE
```
Input:  3
Output: 
  📊 RUNNING: Which projects cost the most?
  ================================================================================
  [Breakdown showing costs by project]
  
  StatGuard: $X (highest)
  ClusterAudienceKit: $Y
  PrismNote: $Z
  [etc.]
```

**Use this to:** See where your budget is going, prioritize optimization

#### **Option 6: Personalized Recommendations** ⭐ MOST ACTIONABLE
```
Input:  6
Output: 
  📊 RUNNING: Personalized recommendations
  ================================================================================
  [ROI-ranked suggestions based on YOUR usage]
  
  1. Switch StatGuard to Haiku → Save $X/month (50% savings)
  2. Batch ClusterAudienceKit operations → Save $Y/month (30% savings)
  [etc.]
```

**Use this to:** Get specific actions to save money

#### **Option 20: Set Monthly Budget** ⭐ MOST PROTECTIVE
```
Input:  20
Output: 
  📊 RUNNING: Set monthly budget
  ================================================================================
  Set your limit and get alerted when approaching it.
  
  Current estimated spend: $X/month
  Recommended budget: $Y (conservative estimate)
```

**Use this to:** Lock in spending limits, prevent surprises

#### **Option 10: 90-Day Forecast** ⭐ BEST FOR PLANNING
```
Input:  10
Output: 
  📊 RUNNING: 90-day forecast
  ================================================================================
  Projections for next quarter:
  
  Next 30 days: $X estimated
  Next 60 days: $Y estimated
  Next 90 days: $Z estimated
  
  Trend: [↑ increasing / ↓ decreasing / → stable]
```

**Use this to:** Plan quarterly budget, anticipate costs

---

### All 34 Analysis Options:

#### 📊 Analysis & Insights (Options 1-5)
```
1.  cost trends over time        → Week-by-week costs, patterns
2.  most expensive hours         → Hour-of-day breakdown
3.  which projects cost most     → Per-project breakdown ⭐
4.  detect anomalies             → Cost spikes, unusual patterns ⭐
5.  cost per project per day     → Daily breakdown
```

#### 💡 Optimization & Recommendations (Options 6-10)
```
6.  personalized recommendations → ROI-ranked suggestions ⭐
7.  prompt caching ROI           → Cache savings potential
8.  batch operations impact      → Batching savings
9.  efficiency benchmarks        → Compare to industry
10. 90-day forecast              → Quarterly projection ⭐
```

#### 📋 Reporting & Exports (Options 11-14)
```
11. weekly report                → Email, PDF, Slack
12. executive summary            → High-level overview
13. slack export                 → Slack integration
14. email reports                → Automated emails
```

#### 🔍 Deep Dives (Options 15-19)
```
15. github ops breakdown         → GitHub-specific costs
16. most expensive interactions  → Top 10 costly sessions
17. efficiency metrics           → Tokens per dollar
18. session comparison           → By session type
19. workflow patterns            → Work style analysis
```

#### 🎯 Budget & Planning (Options 20-23)
```
20. set monthly budget           → Spending limits ⭐
21. ROI analysis                 → Value delivered
22. plan comparison              → API vs Pro vs Max
23. quarterly planning           → Q-level budget
```

#### 📈 Advanced (Options 24-27)
```
24. slack alerts                 → Real-time notifications
25. observability export         → Prometheus/Datadog
26. team tracking                → Multi-user costs
27. compliance audit             → SOC 2/HIPAA ready
```

#### 🛠️ Technical (Options 28-30)
```
28. python api examples          → Custom integrations
29. sql export                   → Raw data export
30. custom metrics               → Track anything
```

#### 📚 Learning (Options 31-34)
```
31. all commands                 → Full reference
32. advanced filtering           → Query examples
33. cost dimensions explained    → What affects price
34. custom breakdowns            → Analyze by anything
```

---

## 3️⃣ SPECIAL COMMANDS

**Keywords that trigger special behaviors**

### `all` — See All 34 Options
```
Input:  all
Output: 
  📚 ALL AVAILABLE ANALYSES (34 options)
  ================================================================================
  
  📊 Analysis & Insights
    1. Cost trends over time
    2. Most expensive hours
    3. Projects by cost
    [etc - all 34 listed]
```

**Use this to:** Browse all available analyses, understand what's possible

### `path` — Learning Sequence
```
Input:  path
Output: 
  🚀 RECOMMENDED FIRST-TIME PATH
  ================================================================================
  
  Step 1: Detect anomalies in my usage
    → Find cost spikes
    (Option #4)
  
  Step 2: Which projects cost the most?
    → Identify where to focus
    (Option #3)
  
  Step 3: Give me personalized recommendations
    → Get specific ROI targets
    (Option #6)
  
  Step 4: Connect to Slack for alerts
    → Monitor going forward
    (Option #24)
  
  Step 5: Set a monthly budget and track it
    → Lock in spending limits
    (Option #20)
```

**Use this to:** Follow the recommended flow for first-time users

### `projects` — List Your Projects
```
Input:  projects
Output: 
  📦 ANALYZE YOUR PROJECTS
  ================================================================================
  
  • STATGUARD
    Sessions: 55
    Options:
      ├─ Cost breakdown for statguard
      ├─ Anomalies in statguard
      ├─ Optimization for statguard
      └─ Trend analysis for statguard
  
  • CLUSTERAUDIENCEKIT
    Sessions: 41
    [etc for all 6 projects]
```

**Use this to:** Remember project names, see all at once

### `help` — Get Help
```
Input:  help
Output: 
  📖 HELP - WHAT CAN PYCOSTAUDIT DO?
  ================================================================================
  
  PyCostAudit tracks Claude Code costs across 34 different analyses.
  Start by picking ANY of these:
  
  👉 FOR FIRST-TIME USERS:
     type: path
     (Shows 5-step learning sequence)
  
  👉 TO SEE ALL OPTIONS:
     type: all
     (Shows all 34 analyses)
  
  👉 TO RUN AN ANALYSIS:
     type: 1-34
     (Example: type "4" for anomaly detection)
```

**Use this to:** Get oriented if you're lost

### `quit` or `exit` — Exit PyCostAudit
```
Input:  quit
Output: Thanks for using PyCostAudit! 👋
        Bye!
```

**Use this to:** Exit the interactive loop

---

## 4️⃣ QUICK REFERENCE PATTERNS

### Pattern 1: Quick Daily Check
```python
from pycostaudit.cli_interactive import InteractiveCLI

cli = InteractiveCLI()
print(cli.welcome())        # See your projects
print(cli.process_user_input("4"))    # Check for anomalies
print(cli.process_user_input("3"))    # See project costs
```

**Result:** 2 minutes, full cost picture for today

### Pattern 2: Find Money to Save
```
1. Type: 4          (detect anomalies)
2. Type: 3          (see which project is expensive)
3. Type: 6          (get recommendations for that project)
```

**Result:** Actionable savings suggestions

### Pattern 3: Quarterly Planning
```
1. Type: 3          (see project breakdown)
2. Type: 10         (see 90-day forecast)
3. Type: 20         (set budget for next quarter)
```

**Result:** Budget plan for next 3 months

### Pattern 4: Team Reporting
```
1. Type: 3          (cost by project)
2. Type: 12         (executive summary)
3. Type: 11         (weekly report)
4. Type: 13         (export to Slack)
```

**Result:** Shareable report for team

### Pattern 5: Explore a Specific Project
```
1. Type: statguard              (project analysis)
2. Type: 4                      (anomalies in StatGuard)
3. Type: 6                      (recommendations for StatGuard)
```

**Result:** Deep dive on one project

---

## 📊 Command Anatomy

Every command produces output with this structure:

```
1. TITLE
   What analysis is running

2. RESULTS
   [Actual analysis output]

3. NEXT STEPS
   🎯 WHAT WOULD YOU LIKE TO EXPLORE NEXT?
   
   X. Option name
      → Benefit/description
   
   Y. Another option
      → Benefit/description
   
   Z. Third option
      → Benefit/description

4. PROMPT
   ✨ What next? → [awaits user input]
```

---

## 🔗 Integration in Claude Code

### Method 1: Terminal Loop
```bash
python3 << 'EOF'
from pycostaudit.cli_interactive import main_interactive_loop
main_interactive_loop()
EOF
```

Then type commands as shown above.

### Method 2: Single Queries
```python
from pycostaudit.cli_interactive import InteractiveCLI

cli = InteractiveCLI()

# Get specific result
result = cli.process_user_input("statguard")
print(result)

# Then ask what's next
result = cli.process_user_input("4")
print(result)
```

### Method 3: Programmatic
```python
from pycostaudit.user_context import UserContext

ctx = UserContext()
profile = ctx.get_user_profile()

print(f"Your projects: {profile['projects']}")
print(f"Sessions analyzed: {profile['sessions_count']}")
print(f"Recommended next step: {ctx.get_personalized_recommendation()}")
```

---

## ✅ Command Cheatsheet

| Want to... | Type | Example |
|---|---|---|
| See your projects | `projects` | See all 6 projects at once |
| Check for cost spikes | `4` | Find anomalies |
| See which project costs most | `3` | Per-project breakdown |
| Get money-saving suggestions | `6` | Personalized recommendations |
| Plan next quarter | `10` | 90-day forecast |
| Lock in spending limit | `20` | Set monthly budget |
| Analyze StatGuard specifically | `statguard` | Project deep dive |
| See all 34 options | `all` | Browse all analyses |
| Follow recommended path | `path` | 5-step learning sequence |
| Get help | `help` | How to use PyCostAudit |
| See top 5 most useful | `1` through `5` | Then `6`, `10`, `20`, `24` |
| Exit | `quit` | Leave PyCostAudit |

---

## 🎯 Recommended First Commands

**If you're new:**
1. `path` — Follow the learning sequence
2. `4` — See anomalies
3. `3` — See project breakdown

**If you're busy:**
1. `3` — Quick cost check
2. `6` — Get suggestions
3. `20` — Set budget

**If you want to explore:**
1. `all` — See all options
2. `[any number]` — Try one
3. `[another number]` — Try another

---

## 💡 Pro Tips

### Tip 1: Commands are case-insensitive
```
✓ Valid: statguard, STATGUARD, StatGuard, StatGuard
✓ Valid: 4, path, ALL, HELP
```

### Tip 2: Invalid input shows options
```
Input:  invalid
Output: Shows valid options (not error)
        Try: statguard, 4, path, all, help
```

### Tip 3: Every analysis shows next steps
```
After any analysis → 3 options automatically displayed
No dead ends → always know what to do next
```

### Tip 4: Combine project + analysis
```
1. Type: statguard     → See StatGuard insights
2. Type: 4             → Analyze StatGuard anomalies specifically
3. Type: 6             → Get StatGuard recommendations
```

### Tip 5: Use copy-paste in Claude Code
```
You can paste these sequences into Claude Code:
- Type: 4
- [See results]
- Type: 3
- [See results]
- Type: 6
- [See results]
```

---

## 📞 Quick Help

### "I don't know what to do"
**Command:** `path` → Shows 5-step recommended sequence

### "I want to see all possibilities"
**Command:** `all` → Shows all 34 analyses

### "I want to analyze a specific project"
**Command:** `[project-name]` → e.g., `statguard`, `prismnote`

### "I want to save money"
**Command:** `4` → `3` → `6` (Anomalies → Projects → Recommendations)

### "I want to plan my budget"
**Command:** `3` → `10` → `20` (Projects → Forecast → Budget)

### "I'm lost"
**Command:** `help` → Get reoriented

---

## 🚀 Start Using These Commands Now

In Claude Code, try:

```python
from pycostaudit.cli_interactive import InteractiveCLI

cli = InteractiveCLI()

# 1. See welcome
print(cli.welcome())

# 2. Try first command
print(cli.process_user_input("4"))

# 3. Follow next steps shown in output
```

Then follow the options that appear!

---

**All commands work with YOUR real Claude Code data — no dummy values.**

**See PRIORITY_ROADMAP.md for what's being built next.**
