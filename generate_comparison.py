import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_text_lines(ax, x_start, y_start, lines, line_spacing=0.08):
    """
    Renders lines of text where each line is a list of (text, style) tuples.
    Styles: 'normal', 'dim', 'highlight_green', 'highlight_blue', 'bold', 'red'
    """
    y = y_start
    
    # Font settings
    font_family = 'sans-serif'
    base_size = 10
    
    for line_segments in lines:
        x = x_start
        for text, style in line_segments:
            # Determine properties based on style
            weight = 'normal'
            color = '#333333'
            bbox = None
            
            if style == 'dim':
                color = '#888888'
            elif style == 'highlight_green':
                weight = 'bold'
                color = 'black'
                bbox = dict(facecolor='#d1e7dd', edgecolor='#a3cfbb', boxstyle='round,pad=0.2')
            elif style == 'highlight_blue':
                weight = 'bold'
                color = 'black'
                bbox = dict(facecolor='#cfe2ff', edgecolor='#9ec5fe', boxstyle='round,pad=0.2')
            elif style == 'bold':
                weight = 'bold'
            elif style == 'red':
                color = '#d62728'
            
            # Render text chunk
            t = ax.text(x, y, text, fontsize=base_size, weight=weight, color=color, 
                        bbox=bbox, family=font_family, transform=ax.transAxes, va='top')
            
            # Update x position for next chunk (approximate based on length)
            char_width = 0.009  # Tuned for this font size/DPI
            x += len(text) * char_width
            
        y -= line_spacing

def main():
    fig = plt.figure(figsize=(16, 7), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    
    # Background
    fig.patch.set_facecolor('white')

    # --- LEFT COLUMN: BASELINE (Generic) ---
    # Title
    ax.text(0.25, 0.92, "BASELINE (Generic)", ha='center', fontsize=16, weight='bold', color='#6c757d')
    
    # Box background
    rect_left = patches.Rectangle((0.02, 0.05), 0.46, 0.82, linewidth=2, edgecolor='#dee2e6', facecolor='#f8f9fa')
    ax.add_patch(rect_left)

    baseline_content = [
        [("Experience: ", "bold")],
        # FIXED: Added "normal" style to the last element of these lines
        [("• Designed and implemented ", "dim"), ("post-training", "normal"), (" methods.", "normal")],
        [("• Used ", "dim"), ("Python", "normal"), (" to improve model reasoning.", "normal")],
        [("• Scaled pipelines with ", "dim"), ("PyTorch", "normal"), (" across many GPUs.", "normal")],
        [("• Developed evaluation harnesses for ", "dim"), ("accuracy", "normal"), (".", "normal")],
        [("• Debugged ", "dim"), ("distributed system", "normal"), (" issues.", "normal")],
        [],
        [("Analysis:", "bold")],
        # FIXED: Added "red" style to these analysis points
        [("❌ Vague quantifiers ('many GPUs')", "red")],
        [("❌ Misses specific job keywords", "red")],
        [("❌ Passive language", "red")]
    ]
    
    draw_text_lines(ax, 0.05, 0.82, baseline_content)

    # --- RIGHT COLUMN: FULL AGENTIC (Tailored) ---
    # Title
    ax.text(0.75, 0.92, "FULL MODE (Tailored)", ha='center', fontsize=16, weight='bold', color='#198754')

    # Box background
    rect_right = patches.Rectangle((0.52, 0.05), 0.46, 0.82, linewidth=2, edgecolor='#198754', facecolor='white')
    ax.add_patch(rect_right)

    tailored_content = [
        [("Experience: ", "bold")],
        [("• Designed ", "dim"), ("Reinforcement Learning (RLHF)", "highlight_green"), (" methods.", "normal")],
        [("• Optimized algorithms using ", "dim"), ("Python", "highlight_blue"), (" and ", "dim"), ("PyTorch", "highlight_blue"), (" .", "normal")],
        [("• Scaled ", "dim"), ("Distributed Training", "highlight_green"), (" across ", "dim"), ("1,000+ GPUs", "highlight_green"), (" .", "normal")],
        [("• Architected ", "dim"), ("Model Alignment", "highlight_green"), (" evaluations.", "normal")],
        [("• Resolved ", "dim"), ("Kubernetes", "highlight_green"), (" cluster bottlenecks.", "normal")],
        [],
        [("Analysis:", "bold")],
        # FIXED: Added "bold" style to analysis points
        [("✅ Matches 'RLHF' & 'Distributed' from JD", "bold")],
        [("✅ Concrete scale metrics (1,000+)", "bold")],
        [("✅ Active, domain-specific terminology", "bold")]
    ]

    draw_text_lines(ax, 0.55, 0.82, tailored_content)

    # Arrow between them
    ax.arrow(0.485, 0.5, 0.03, 0, head_width=0.02, head_length=0.01, fc='#6c757d', ec='#6c757d')

    output_file = "keyword_comparison.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"✅ Created: {output_file}")

if __name__ == "__main__":
    main()