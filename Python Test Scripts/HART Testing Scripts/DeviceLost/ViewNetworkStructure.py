import os
import sys
import matplotlib.pyplot as plt
import networkx as nx

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../SSHHelper")
from InteractiveSSH import InteractiveSSH

hostname = "toc0"

# Create the SSH session
ssh = InteractiveSSH(hostname)

# Start nwconsole and get path information 
ssh.start_nwconsole()
paths = ssh.get_paths()

# Close the SSH session
ssh.shell.close()
ssh.close()

# Create a digraph for visualization the network
graph = nx.DiGraph()

# Add each path to the graph
for path in paths:
    graph.add_edge(path[1], path[0])

# Try drawing with a planar layout first since it's easiest to see but sometimes it fails
try:
    nx.draw_planar(graph, with_labels = True)
# If a planar layout cannot be used, fallback to a spectral layout
except:
    try:
        nx.draw_spectral(graph, with_labels = True)
    # If a spectral layout fails too, use a random layout
    except:
        nx.draw(graph, with_labels = True)

# Use matplotlib to show the network visualization
plt.show()
