"""
Script to create a KDE plot for example 2
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv('./data/4060_looks_scale.csv')

sns.set_theme(style="whitegrid")
colors = ['red', 'green', 'blue', 'purple']

plt.figure(figsize=(12, 6))

plt.title("Density of Predicted Scale per Formation", fontsize=16)
plt.xlabel("Scale (Closer to 0 = Likely Run Play)", fontsize=14)
plt.ylabel("Density", fontsize=14)

looks = data['look'].unique()
for i, look in enumerate(looks):
    look_data = data[data['look'] == look]
    color = colors[i % len(colors)]
    kde = sns.kdeplot( look_data['sum_scale'], 
                       clip=(0, None), 
                       color=color, 
                       label=look,
                       linewidth=2 )
    
    kde_data = kde.get_lines()[-1].get_data()
    plt.fill_between(kde_data[0], kde_data[1], color=color, alpha=0.1)
    
    plt.fill_between(kde_data[0], kde_data[1], color='none', edgecolor=color, alpha=0.3)
    
    max_density = kde_data[1].max()
    max_index = kde_data[1].argmax()
    max_x = kde_data[0][max_index]
    
    if look == 'SINGLEBACK 2x2':
        plt.text(max_x + 1, max_density, 'SINGLEBACK', fontsize=12, fontname='Courier New', fontweight='bold')
    
    if look == 'SHOTGUN 2x2':
        plt.text(max_x + 1, max_density + .001, 'SHOTGUN', fontsize=12, fontname='Courier New', fontweight='bold')

plt.xlim(left=0)
plt.grid(False)
plt.legend(title="Formation", fontsize=11, loc='upper right')

plt.tight_layout()
plt.show()