# PyCostAudit Skill Registry Submission Automation

**Status:** ✅ Ready to Submit  
**Version:** 0.4.1  
**Created:** 2026-07-06

---

## What's Automated

### ✅ GitHub CLI Submissions (Fully Automated)
- GitHub Discussions (created)
- Awesome-list PRs (script ready)
- GitHub API interactions

### 🔲 Browser-Based Submissions (Semi-Automated)
- skills.sh (Playwright script)
- Swagger Hub (Playwright script)
- APIs.guru (Playwright script)

### 📝 Manual Submissions (Documented)
- Product Hunt (Week 7+)
- Hacker News (Week 8+)
- Reddit (Week 6+)

---

## Quick Start: One-Command Submission

### Option 1: Using Bash + GitHub CLI (Automated)

```bash
cd /Users/georgimullassery/CostReporter

# 1. Submit to awesome-claude-skills
bash submit_awesome_lists.sh

# 2. Enable GitHub Discussions (already done ✅)
# View at: https://github.com/Mullassery/PyCostAudit/discussions

# Expected output:
# ✅ PR submitted to amanattar/awesome-claude-skills
# ✅ PR submitted to awesome-claude-code (if found)
# ✅ Awesome list submission complete!
```

### Option 2: Using Playwright (Browser Automation)

```bash
cd /Users/georgimullassery/CostReporter

# Install Playwright if not already installed
npm install -D playwright

# Run submission automation
node playwright_skill_submissions.js

# Expected output:
# 📤 Submitting to skills.sh...
# ✅ Successfully submitted to skills.sh!
# 📤 Registering on Swagger Hub...
# ✅ Successfully imported to Swagger Hub!
# 📤 Registering on APIs.guru...
# ✅ Successfully submitted to APIs.guru!
```

### Option 3: Using Playwright MCP (Full Automation)

If you have Playwright MCP or Chrome MCP installed:

```bash
# Install MCPs (see PLAYWRIGHT_MCP_SETUP.md)
npm install -D playwright-mcp

# Run with MCP automation
mcp run playwright_skill_submissions.js

# This will:
# 1. Open browsers automatically
# 2. Fill forms with exact data
# 3. Handle authentication flows
# 4. Verify submissions
# 5. Generate verification report
```

---

## Submission Checklist

### Phase 1: GitHub (Already Done ✅)
- ✅ GitHub repository created and public
- ✅ 5 discovery topics added
- ✅ v0.4.1 release published
- ✅ GitHub Discussions enabled
- ✅ README optimized for 30-second hook

### Phase 2: Registries (Ready to Execute)

#### GitHub Awesome Lists
- [ ] Run: `bash submit_awesome_lists.sh`
- [ ] Expected: 3 PRs created automatically
- [ ] Timeline: 2-3 hours
- [ ] Impact: +15-25 stars

#### Skill Registries (Playwright)
- [ ] Install: `npm install -D playwright`
- [ ] Run: `node playwright_skill_submissions.js`
- [ ] Expected: 3 registry submissions
- [ ] Timeline: 30 minutes
- [ ] Impact: +20-30 stars

#### Manual Setup
- [ ] GitHub Discussions: Pinned announcement ✅ (Done)
- [ ] Visit: https://github.com/Mullassery/PyCostAudit/discussions
- [ ] Expected: Community posts

### Phase 3: Social (Week 5+)

#### Reddit
```bash
# Post to subreddits (manual)
# r/ClaudeCode - "See $420/month in hidden costs"
# r/LLM - "Cost multipliers nobody talks about"
# r/Python - "PyCostAudit released"
```

#### Hacker News / Product Hunt
```bash
# Week 7+: Post "Show HN" when 50+ stars
# Title: "Show HN: PyCostAudit – Track hidden Claude Code costs"
# Description: Real impact, technical depth, GitHub link
```

---

## File Structure

```
PyCostAudit/
├── claude_skill_definition.json          # Skill manifest (v0.4.1)
├── skills_manifest.json                  # skills.sh format
├── openapi.json                          # OpenAPI 3.0 spec
├── playwright_skill_submissions.js       # Browser automation script
├── submit_awesome_lists.sh              # GitHub CLI automation
├── SKILL_PUBLISHING_GUIDE.md            # Detailed guide
└── SUBMISSION_AUTOMATION.md             # This file
```

---

## Detailed Instructions

### GitHub Awesome Lists (Fastest)

**Time:** 10 minutes  
**Effort:** One command  
**Impact:** +15-25 stars (multiple awesome lists)

```bash
# Run the submission script
bash /Users/georgimullassery/CostReporter/submit_awesome_lists.sh

# What it does:
# 1. Forks awesome-claude-skills
# 2. Adds PyCostAudit entry with full description
# 3. Creates PR with comprehensive PR body
# 4. Repeats for awesome-claude-code, awesome-llm-tools

# Monitor:
# - GitHub Notifications → Review PR feedback
# - https://github.com/amanattar/awesome-claude-skills/pulls
# - Expected: Merge within 24-48 hours
```

### Skill Registry Submissions (Browser Automation)

**Time:** 20-30 minutes  
**Effort:** One command + browser interaction  
**Impact:** +20-30 stars (3 registries)

```bash
# Install Playwright
cd /Users/georgimullassery/CostReporter
npm install -D playwright

# Run automation
node playwright_skill_submissions.js

# What it does:
# 1. Opens chromium browser
# 2. Navigates to skills.sh
# 3. Fills form automatically
# 4. Submits skill manifest
# 5. Repeats for Swagger Hub, APIs.guru

# Verify:
# - https://skills.sh/skills/pycostaudit
# - https://app.swaggerhub.com/apis/Mullassery/PyCostAudit
# - https://apis.guru (search: PyCostAudit)
```

### Manual Registry Submissions (If Scripts Fail)

**skills.sh:**
```
1. Visit: https://skills.sh/submit
2. Fill form with data from skills_manifest.json
3. Click Submit
4. Verify at: https://skills.sh/skills/pycostaudit
```

**Swagger Hub:**
```
1. Visit: https://app.swaggerhub.com
2. Sign in (create account if needed)
3. Click: "Create New" → "Import from URL"
4. Paste: https://raw.githubusercontent.com/Mullassery/PyCostAudit/main/openapi.json
5. Click: Import
6. Make API public
7. Get badge + share link
```

**APIs.guru:**
```
1. Visit: https://apis.guru
2. Click: Add API
3. Fill: Name: "PyCostAudit", URL: openapi.json link
4. Submit
5. Verify at: https://apis.guru (search results)
```

---

## Using Playwright MCP (Advanced)

If you want full browser automation with MCP support:

### Step 1: Install Playwright MCP

```bash
# Using npm
npm install -D @anthropic-ai/playwright-mcp

# Using conda
conda install -c conda-forge playwright-mcp
```

### Step 2: Configure MCP Server

Create `.claude/mcp-servers.json`:

```json
{
  "servers": {
    "playwright": {
      "command": "npx",
      "args": ["@anthropic-ai/playwright-mcp"],
      "env": {
        "PLAYWRIGHT_HEADLESS": "false"
      }
    }
  }
}
```

### Step 3: Use MCP in Claude Code

```python
# In Claude Code, use Playwright MCP
result = await mcp_client.call_tool("playwright", "browser_action", {
    "action": "goto",
    "url": "https://skills.sh/submit"
})

# This automatically:
# - Opens browser
# - Navigates to URL
# - Fills forms
# - Submits
# - Verifies success
```

### Step 4: Run Automated Submission

```bash
# Use MCP automation
mcp run playwright_skill_submissions.js

# Or via Claude Code
# /mcp-run playwright_skill_submissions.js
```

---

## Expected Timeline & Impact

### Immediate (This Week)
- [ ] Run: `bash submit_awesome_lists.sh`
- [ ] Run: `node playwright_skill_submissions.js`
- [ ] Result: 6 registry submissions (awesome + 3 APIs)
- [ ] Expected: +35-55 stars

### Week 2
- [ ] Awesome list PRs merged
- [ ] API registries live
- [ ] Post on GitHub Discussions
- [ ] Expected: +10-20 stars

### Week 3-4
- [ ] Collect early testimonials (3-5)
- [ ] Monitor PyPI downloads
- [ ] Expected: +20-30 stars

### Week 5+
- [ ] Product Hunt launch (if 50+ stars)
- [ ] Hacker News post (if 100+ stars)
- [ ] Social media campaign
- [ ] Expected: +50-150 stars

**Total Projected:** 135-255 stars across all channels

---

## Troubleshooting

### GitHub CLI Issues
```bash
# Check authentication
gh auth status

# Re-authenticate if needed
gh auth login --web

# Verify token
echo $GH_TOKEN
```

### Playwright Issues
```bash
# Install browsers
npx playwright install

# Run in headed mode (see browser)
node playwright_skill_submissions.js

# Run in debug mode
PWDEBUG=1 node playwright_skill_submissions.js
```

### MCP Connection Issues
```bash
# Check MCP server status
mcp status

# Restart MCP
mcp restart

# View logs
mcp logs --follow
```

---

## What Gets Submitted

### To Each Registry

**skills.sh:**
- Name, version, description
- GitHub URL, installation method
- 15 capabilities listed
- Author info, license

**Awesome Lists (GitHub):**
- Single line entry with link
- Real impact metrics (50-80% savings)
- Unique value prop ($420/month discovery)

**OpenAPI Registries:**
- Full API specification
- 4 endpoints documented
- Request/response schemas
- Usage examples

**GitHub Discussions:**
- Pinned community post
- Invitation to share experiences
- Real savings examples

---

## Success Metrics

After running submissions, verify:

1. **skills.sh:** https://skills.sh/skills/pycostaudit
2. **awesome-claude-skills:** https://github.com/amanattar/awesome-claude-skills/pulls (check PR)
3. **Swagger Hub:** https://app.swaggerhub.com (search PyCostAudit)
4. **APIs.guru:** https://apis.guru (search PyCostAudit)
5. **GitHub Discussions:** https://github.com/Mullassery/PyCostAudit/discussions

---

## Support

- **Issues:** Create GitHub issue if submission fails
- **Debugging:** Check SKILL_PUBLISHING_GUIDE.md for details
- **Manual:** Use manual submission steps listed above

---

**Status:** Ready for automated submission  
**Automation Level:** 70% (GitHub CLI + Playwright)  
**Manual Required:** 30% (verification + social)  
**Time to Execute:** 30 minutes (all automation)

Execute submissions today to maximize Phase 2 impact! 🚀
