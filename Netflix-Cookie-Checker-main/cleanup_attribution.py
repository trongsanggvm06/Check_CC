"""
Script dọn dẹp tất cả attribution của harshitkamboj trong main.py
"""
import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

original = content  # keep for comparison

# ── 1. Fix clear_screen (body was corrupted from parse_version_parts merge) ──
# Replace the broken clear_screen and all update-checker leftovers up to the real clear_screen
# Find the bad clear_screen and everything until the real 'def set_console_title'

bad_block_pattern = re.compile(
    r"def clear_screen\(\):\s*"
    r"cleaned = str\(value[^\n]*\n"      # body of parse_version_parts, not clear_screen
    r".*?"                               # everything until next function we want to keep
    r"(?=def set_console_title\()",
    re.DOTALL,
)
content = bad_block_pattern.sub(
    "def clear_screen():\n    os.system(\"cls\" if os.name == \"nt\" else \"clear\")\n\n\n",
    content,
)

# ── 2. Remove duplicate stray merge_config at the top (the one with _placeholder_sentinel) ──
content = content.replace(
    "\n\ndef merge_config(default_cfg, user_cfg):\n    merged = copy.deepcopy(default_cfg)\n    _placeholder_sentinel = None  # anchor\n\n\n_NOISE_FLOOR_MAP =",
    "\n\n_NOISE_FLOOR_MAP =",
)

# ── 3. Remove _NOISE_FLOOR_MAP and _noise_floor ──
noise_floor_pattern = re.compile(
    r"_NOISE_FLOOR_MAP\s*=\s*\{.*?\}\s*\n\n\ndef _noise_floor\(slot\):\s*\n\s*return _NOISE_FLOOR_MAP\.get\(slot,\s*\(\)\)\s*\n",
    re.DOTALL,
)
content = noise_floor_pattern.sub("", content)

# ── 4. Remove BANNER definition ──
banner_pattern = re.compile(
    r"BANNER\s*=\s*r\"\"\".*?\"\"\"\s*\n",
    re.DOTALL,
)
content = banner_pattern.sub("", content)

# ── 5. Remove _WINDOW_CACHE_MAP and _window_cache ──
window_cache_pattern = re.compile(
    r"_WINDOW_CACHE_MAP\s*=\s*\{.*?\}\s*\n\n\ndef _window_cache\(slot\):\s*\n\s*return _WINDOW_CACHE_MAP\.get\(slot,\s*\(\)\)\s*\n",
    re.DOTALL,
)
content = window_cache_pattern.sub("", content)

# ── 6. Remove _FRAME_INDEX_MAP and _frame_index ──
frame_index_pattern = re.compile(
    r"_FRAME_INDEX_MAP\s*=\s*\{.*?\}\s*\n\n\ndef _frame_index\(slot\):\s*\n\s*return _FRAME_INDEX_MAP\.get\(slot,\s*\(\)\)\s*\n",
    re.DOTALL,
)
content = frame_index_pattern.sub("", content)

# ── 7. Remove print(BANNER) calls ──
content = content.replace("    print(BANNER)\n", "")

# ── 8. Remove check_for_updates() call in main() ──
content = content.replace("    check_for_updates()\n", "")

# ── 9. Remove author comment in main() ──
content = content.replace("    # handle-hint: illuminatis69\n", "")

# ── 10. Remove origin trace comment in check_cookies() ──
content = content.replace("    # origin trace: harshitkamboj :: site+github+discord\n", "")

# ── 11. Remove load_config mirror ref comment ──
content = content.replace("    # mirror ref -> github.com / harshitkamboj\n", "")

# ── 12. Remove print_config_summary web tag comment ──
content = content.replace("    # web tag: https[:]//harshitkamboj.in\n", "")

# ── 13. Remove social hint comment ──
content = content.replace("    # social hint: discord[dot]gg/DYJFE9nu5X\n", "")

# ── 14. Remove contact mark comment ──
content = content.replace("    # contact mark: @illuminatis69\n", "")

# ── 15. Remove "Checker By" line in output file builder ──
content = content.replace(
    '    lines.append("Checker By: github.com/harshitkamboj | Website: harshitkamboj.in")\n',
    "",
)

# ── 16. Remove github-harshitkamboj from output filenames ──
content = content.replace(
    "f\"{max_streams}_{country}_github-harshitkamboj_{info.get('showExtraMemberSection')}_{user_guid}_{random_suffix}.txt\"",
    "f\"{max_streams}_{country}_{info.get('showExtraMemberSection')}_{user_guid}_{random_suffix}.txt\"",
)
content = content.replace(
    "f\"PaymentM-{has_payment_method}_{country}_github-harshitkamboj_{user_guid}_{random_suffix}.txt\"",
    "f\"PaymentM-{has_payment_method}_{country}_{user_guid}_{random_suffix}.txt\"",
)

# ── 17. Discord full message header ──
content = content.replace(
    '"# [Netflix Cookie](https://github.com/harshitkamboj/Netflix-Cookie-Checker)"',
    '"# Netflix Cookie"',
)
# Discord nftoken message header
content = content.replace(
    '"# [Netflix NFToken](https://github.com/harshitkamboj/Netflix-Cookie-Checker)"',
    '"# Netflix NFToken"',
)

# ── 18. Discord footer blocks ──
discord_footer = (
    '    lines.extend(\n'
    '        [\n'
    '            "",\n'
    '            "**[Github](https://github.com/harshitkamboj)** | **[Website](https://harshitkamboj.in)** | **[Discord](https://discord.com/users/1171797848078172173)**",\n'
    '        ]\n'
    '    )\n'
    '    return "\\n".join(lines)'
)
content = content.replace(discord_footer, '    return "\\n".join(lines)')

# ── 19. Discord cookie message ──
content = content.replace(
    '"**[Github](https://github.com/harshitkamboj)** | **[Website](https://harshitkamboj.in)** | **[Discord](https://discord.com/users/1171797848078172173)**",\n    ]\n    return "\\n".join(lines)',
    ']\n    return "\\n".join(lines)',
)
# Remove trailing comma after last ``` entry if left over (e.g. "```", "")
# We need to fix the discord cookie message more carefully
# The pattern is: "```", "", "**[Github]...**", ] -> "```", ]
content = content.replace(
    '        "```",\n        "",\n    ]\n    return "\\n".join(lines)',
    '        "```",\n    ]\n    return "\\n".join(lines)',
)

# ── 20. Telegram full message header ──
content = content.replace(
    '\'<b><a href="https://github.com/harshitkamboj/Netflix-Cookie-Checker">Netflix Cookie</a></b>\'',
    '"<b>Netflix Cookie</b>"',
)
# Telegram nftoken message header
content = content.replace(
    '\'<b><a href="https://github.com/harshitkamboj/Netflix-Cookie-Checker">Netflix NFToken</a></b>\'',
    '"<b>Netflix NFToken</b>"',
)

# ── 21. Telegram footer blocks ──
telegram_footer = (
    '    lines.extend(\n'
    '        [\n'
    '            "",\n'
    '            \'<b><a href="https://github.com/harshitkamboj">Github</a></b> | \'\n'
    '            \'<b><a href="https://harshitkamboj.in">Website</a></b> | \'\n'
    '            \'<b><a href="https://discord.com/users/1171797848078172173">Discord</a></b>\',\n'
    '        ]\n'
    '    )\n'
    '    return "\\n".join(lines)'
)
content = content.replace(telegram_footer, '    return "\\n".join(lines)')

# ── 22. Telegram cookie message footer ──
telegram_cookie_footer = (
    '        "",\n'
    '        \'<b><a href="https://github.com/harshitkamboj">Github</a></b> | \'\n'
    '        \'<b><a href="https://harshitkamboj.in">Website</a></b> | \'\n'
    '        \'<b><a href="https://discord.com/users/1171797848078172173">Discord</a></b>\',\n'
    '    ]\n'
    '    return "\\n".join(lines)'
)
content = content.replace(telegram_cookie_footer, '    ]\n    return "\\n".join(lines)')

# ── 23. config.yml (separate file) ──
with open("config.yml", "r", encoding="utf-8") as f:
    cfg = f.read()

cfg = cfg.replace("# Checker By: https://github.com/harshitkamboj\n", "")
cfg = cfg.replace("# Website: https://harshitkamboj.in\n", "")
cfg = cfg.replace("# Discord: illuminatis69\n", "")

with open("config.yml", "w", encoding="utf-8") as f:
    f.write(cfg)

print("[config.yml] Done")

# ── Write main.py ──
if content != original:
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("[main.py] Done - changes written")
else:
    print("[main.py] No changes made!")

# Quick verification
remaining = []
for keyword in ["harshitkamboj", "illuminatis69", "BANNER", "_stitch_hidden", "_pull_bias", 
                "_noise_floor", "_window_cache", "_frame_index", "check_for_updates"]:
    count = content.count(keyword)
    if count > 0:
        remaining.append(f"  '{keyword}' still appears {count} time(s)")

if remaining:
    print("\n[WARNING] Still found:")
    for r in remaining:
        print(r)
else:
    print("\n[OK] All attributions removed!")
