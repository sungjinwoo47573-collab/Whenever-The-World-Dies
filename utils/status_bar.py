def generate_wb_hp_bar(current_hp, max_hp):
    """Generates a 10-block HP bar with phase-based coloring."""
    percentage = (current_hp / max_hp) * 100
    filled_blocks = max(0, min(10, int(percentage / 10)))
    empty_blocks = 10 - filled_blocks
    
    # Choose color based on phase
    if percentage > 65:
        color_emoji = "🟩" # Phase 1
    elif percentage > 30:
        color_emoji = "🟧" # Phase 2
    else:
        color_emoji = "🟥" # Phase 3

    bar = (color_emoji * filled_blocks) + ("⬛" * empty_blocks)
    return f"{bar} `{percentage:.1f}%` ({current_hp}/{max_hp} HP)"
  
