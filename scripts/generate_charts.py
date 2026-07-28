"""Generate IEEE paper charts for Scam Radar"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os

output_dir = r"D:\scam-risk-detection2\paper_assets"
os.makedirs(output_dir, exist_ok=True)

# ============================================================
# CHART 1: Performance Comparison Bar Chart
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5))

models = ['TF-IDF\nBaseline', 'BERT\n(Standalone)', 'Proposed\nEnsemble']
accuracy =  [82.4, 91.2, 94.8]
precision = [80.1, 90.5, 93.2]
recall =    [78.3, 88.7, 92.5]
f1_score =  [79.2, 89.6, 92.8]

x = np.arange(len(models))
width = 0.18

bars1 = ax.bar(x - 1.5*width, accuracy,  width, label='Accuracy',  color='#2196F3', edgecolor='black', linewidth=0.5)
bars2 = ax.bar(x - 0.5*width, precision, width, label='Precision', color='#4CAF50', edgecolor='black', linewidth=0.5)
bars3 = ax.bar(x + 0.5*width, recall,    width, label='Recall',    color='#FF9800', edgecolor='black', linewidth=0.5)
bars4 = ax.bar(x + 1.5*width, f1_score,  width, label='F1-Score',  color='#F44336', edgecolor='black', linewidth=0.5)

# Add value labels on bars
for bars in [bars1, bars2, bars3, bars4]:
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=7, fontweight='bold')

ax.set_ylabel('Score (%)', fontsize=12, fontweight='bold')
ax.set_title('Fig. 5: Classification Performance Comparison', fontsize=13, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(models, fontsize=10, fontweight='bold')
ax.set_ylim(70, 100)
ax.legend(loc='lower right', fontsize=9, framealpha=0.9)
ax.grid(axis='y', alpha=0.3, linestyle='--')
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'performance_comparison.png'), dpi=300, bbox_inches='tight')
print("Chart 1 saved: performance_comparison.png")
plt.close()

# ============================================================
# CHART 2: Ensemble Weight Distribution Pie Chart
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

# English weights
labels1 = ['Rule-Based\nEngine (50%)', 'BERT\n(30%)', 'TF-IDF +\nRandom Forest (20%)']
sizes1 = [50, 30, 20]
colors1 = ['#F44336', '#2196F3', '#4CAF50']
explode1 = (0.05, 0.02, 0.02)

ax1.pie(sizes1, explode=explode1, labels=labels1, colors=colors1,
        autopct='%1.0f%%', shadow=True, startangle=90,
        textprops={'fontsize': 9, 'fontweight': 'bold'},
        pctdistance=0.55)
ax1.set_title('(a) English Input Weights', fontsize=11, fontweight='bold', pad=10)

# Non-English weights
labels2 = ['XLM-RoBERTa\n(50%)', 'Rule-Based\nEngine (30%)', 'TF-IDF +\nRandom Forest (20%)']
sizes2 = [50, 30, 20]
colors2 = ['#9C27B0', '#F44336', '#4CAF50']
explode2 = (0.05, 0.02, 0.02)

ax2.pie(sizes2, explode=explode2, labels=labels2, colors=colors2,
        autopct='%1.0f%%', shadow=True, startangle=90,
        textprops={'fontsize': 9, 'fontweight': 'bold'},
        pctdistance=0.55)
ax2.set_title('(b) Non-English Input Weights', fontsize=11, fontweight='bold', pad=10)

fig.suptitle('Fig. 6: Ensemble Weight Distribution', fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'ensemble_weights.png'), dpi=300, bbox_inches='tight')
print("Chart 2 saved: ensemble_weights.png")
plt.close()

# ============================================================
# CHART 3: Risk Score Classification Ranges
# ============================================================
fig, ax = plt.subplots(figsize=(8, 2))

# Draw horizontal bar showing score ranges
ax.barh(0, 35, left=0, height=0.5, color='#4CAF50', edgecolor='black', linewidth=1)
ax.barh(0, 30, left=35, height=0.5, color='#FF9800', edgecolor='black', linewidth=1)
ax.barh(0, 35, left=65, height=0.5, color='#F44336', edgecolor='black', linewidth=1)

# Labels
ax.text(17.5, 0, 'LEGITIMATE\n(0 - 35)', ha='center', va='center', fontsize=11, fontweight='bold', color='white')
ax.text(50, 0, 'SUSPICIOUS\n(36 - 65)', ha='center', va='center', fontsize=11, fontweight='bold', color='white')
ax.text(82.5, 0, 'SCAM\n(66 - 100)', ha='center', va='center', fontsize=11, fontweight='bold', color='white')

ax.set_xlim(0, 100)
ax.set_ylim(-0.5, 0.5)
ax.set_xlabel('Risk Score', fontsize=11, fontweight='bold')
ax.set_title('Fig. 7: Risk Score Classification Ranges', fontsize=12, fontweight='bold', pad=10)
ax.set_yticks([])
ax.set_xticks([0, 10, 20, 30, 35, 40, 50, 60, 65, 70, 80, 90, 100])
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'risk_score_ranges.png'), dpi=300, bbox_inches='tight')
print("Chart 3 saved: risk_score_ranges.png")
plt.close()

print(f"\nAll charts saved to: {output_dir}")
print("Files created:")
for f in os.listdir(output_dir):
    if f.endswith('.png'):
        size = os.path.getsize(os.path.join(output_dir, f))
        print(f"  - {f} ({size:,} bytes)")
