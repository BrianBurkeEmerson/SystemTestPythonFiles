from InteractiveSSH import InteractiveSSH
import matplotlib.pyplot as plt
import networkx as nx

ssh = InteractiveSSH("toc0")

ssh.start_nwconsole()
paths = ssh.get_paths()

graph = nx.DiGraph()

for path in paths:
    graph.add_edge(path[0], path[1])

nx.draw(graph, with_labels = True)
plt.show()

ssh.shell.close()
ssh.close()
