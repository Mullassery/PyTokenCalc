#!/bin/bash
# Complete setup script for Skill + CLI Monitor

set -e

SKILL_DIR="/Users/georgimullassery/PyCostAudit"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="$HOME/.config/pycostaudit"
LOG_DIR="$HOME/.local/share/pycostaudit"

echo ""
echo "=========================================="
echo "🚀 PyCostAudit Complete Setup"
echo "=========================================="
echo ""

# 1. Create directories
echo "📁 Creating directories..."
mkdir -p "$BIN_DIR" "$CONFIG_DIR" "$LOG_DIR"

# 2. Install skill symlink
echo "⚙️  Installing Claude Code Skill..."
ln -sf "$SKILL_DIR/pycostaudit_skill.py" "$BIN_DIR/cost-audit"
chmod +x "$BIN_DIR/cost-audit"

# 3. Create monitor launcher script
echo "📊 Creating CLI Monitor launcher..."
cat > "$BIN_DIR/cost-monitor" << 'EOF'
#!/bin/bash
# PyCostAudit CLI Monitor launcher

SKILL_DIR="/Users/georgimullassery/PyCostAudit"
REFRESH=${1:-2}

python3 "$SKILL_DIR/pycostaudit_monitor.py" --refresh "$REFRESH"
EOF
chmod +x "$BIN_DIR/cost-monitor"

# 4. Add to PATH if needed
if ! echo "$PATH" | grep -q "$BIN_DIR"; then
    echo "📝 Adding $BIN_DIR to PATH..."
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.zshrc
    echo "export PATH=\"$BIN_DIR:\$PATH\"" >> ~/.bashrc
fi

# 5. Create config file
echo "⚙️  Creating configuration file..."
cat > "$CONFIG_DIR/config.json" << 'EOF'
{
  "version": "0.6.0",
  "data_location": "~/.pycostaudit/skill_data.json",
  "skill": {
    "enabled": true,
    "auto_track": true,
    "pricing_model": "claude-opus-4-8"
  },
  "monitor": {
    "enabled": true,
    "default_refresh": 2,
    "show_sparklines": true,
    "color_output": true
  },
  "alerts": {
    "daily_budget": 50.0,
    "weekly_budget": 350.0,
    "alert_channels": ["stdout"]
  },
  "logging": {
    "enabled": true,
    "log_file": "~/.local/share/pycostaudit/activity.log",
    "level": "INFO"
  }
}
EOF

# 6. Create startup script
echo "🔧 Creating parallel launcher script..."
cat > "$BIN_DIR/cost-audit-dashboard" << 'EOF'
#!/bin/bash
# Launch both Skill and Monitor in parallel

BIN_DIR="$HOME/.local/bin"

echo ""
echo "=========================================="
echo "💰 PyCostAudit Dashboard"
echo "=========================================="
echo ""
echo "Starting monitors in parallel..."
echo ""
echo "📊 CLI Monitor running (refresh every 2s)"
echo "💡 Tip: In another terminal, run: cost-audit report"
echo ""

# Launch monitor
"$BIN_DIR/cost-monitor" 2 &
MONITOR_PID=$!

# Trap to kill monitor on exit
trap "kill $MONITOR_PID 2>/dev/null" EXIT

# Wait for monitor
wait $MONITOR_PID
EOF
chmod +x "$BIN_DIR/cost-audit-dashboard"

# 7. Create .zshrc alias
echo "✨ Setting up command aliases..."
cat >> ~/.zshrc << 'EOF'

# PyCostAudit aliases
alias cost-report='cost-audit report'
alias cost-forecast='cost-audit forecast'
alias cost-monitor='cost-monitor'
alias cost-dashboard='cost-audit-dashboard'
alias cost-track='cost-audit track'
alias cost-alerts='cost-audit alerts'

# Helper function to track operation quickly
cost-quick() {
    local op=${1:-"quick_operation"}
    local input=${2:-1000}
    local output=${3:-250}
    cost-audit track "$op" "$input" "$output"
}
EOF

# 8. Create activity log
echo "📝 Creating activity log..."
cat > "$LOG_DIR/activity.log" << 'EOF'
[2026-07-06T02:00:00] System initialized
[2026-07-06T02:00:00] Skill installed and registered
[2026-07-06T02:00:00] CLI Monitor configured
EOF

# 9. Create quick reference
echo "📖 Creating quick reference guide..."
cat > "$CONFIG_DIR/quick-reference.txt" << 'EOF'
PyCostAudit - Quick Reference

COMMANDS:
  cost-report              View today's costs
  cost-forecast            Weekly/monthly forecast
  cost-track <op> <in> <out>  Manually track operation
  cost-alerts              Check budget alerts
  cost-monitor             Start real-time dashboard
  cost-dashboard           Start both skill + monitor
  cost-quick <op>          Quick track (default tokens)

EXAMPLES:
  # View costs
  cost-report

  # Track an operation
  cost-track "code_review" 2000 500

  # Quick track with defaults (1000 in, 250 out)
  cost-quick "debugging"

  # Start monitoring
  cost-monitor

  # Check forecast
  cost-forecast

  # See alerts
  cost-alerts

DATA LOCATION:
  ~/.pycostaudit/skill_data.json

CONFIG LOCATION:
  ~/.config/pycostaudit/config.json

LOGS:
  ~/.local/share/pycostaudit/activity.log

FOR MORE INFO:
  cat ~/.config/pycostaudit/quick-reference.txt
EOF

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "📍 Commands available:"
echo "   cost-report              # View today's costs"
echo "   cost-forecast            # Weekly forecast"
echo "   cost-monitor             # Real-time dashboard"
echo "   cost-dashboard           # Both together"
echo "   cost-track <op> <in> <out>  # Manual track"
echo "   cost-quick <op>          # Quick track"
echo ""
echo "🚀 Quick Start:"
echo "   1. Reload shell: source ~/.zshrc"
echo "   2. View costs:  cost-report"
echo "   3. Start monitoring: cost-monitor"
echo ""
echo "📂 Configuration files:"
echo "   ~/.config/pycostaudit/config.json"
echo "   ~/.config/pycostaudit/quick-reference.txt"
echo ""
echo "📊 Data location:"
echo "   ~/.pycostaudit/skill_data.json"
echo ""
echo "💾 Logs:"
echo "   ~/.local/share/pycostaudit/activity.log"
echo ""
