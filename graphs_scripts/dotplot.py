import matplotlib.pyplot as plt
import brewer2mpl
import numpy as np
# Get "Set2" colors from ColorBrewer (all colorbrewer scales:
# http://bl.ocks.org/mbostock/5577023)
set2 = brewer2mpl.get_map('Set2', 'qualitative', 8).mpl_colors

# Set the random seed for consistency
np.random.seed(12)

fig, ax = plt.subplots(1)

# Show the whole color range
for i in range(8):
    x = np.random.normal(loc=i, size=1000)
    y = np.random.normal(loc=i, size=1000)
    color = set2[i]
    ax.scatter(x, y, label=str(i), color=color, alpha=0.5)

fig.savefig('scatter_matplotlib_improved_02_added_alpha.png')
