import json
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
import os
import html

def load_ro_crate(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)['@graph']

def build_graph(graph_data, crate_dir):
    G = nx.DiGraph()
    node_data_map = {}
    for node in graph_data:
        node_id = node.get('@id')
        if not node_id:
            continue
        node_label = node.get('name') or node.get('@type') or node_id
        raw_type = node.get('@type', 'Thing')
        if isinstance(raw_type, list):
            node_type = "+".join(raw_type)
        else:
            node_type = raw_type

        # Read source code content if it's a File+SoftwareSourceCode node
        if node_type == "File+SoftwareSourceCode" and node_id and not node_id.startswith("http"):
            file_path = os.path.join(crate_dir, node_id)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    node["sourceCode"] = f.read()
            except Exception as e:
                node["sourceCode"] = f"[Could not read file: {e}]"

        G.add_node(node_id, label=node_label, type=node_type)
        node_data_map[node_id] = node

        for predicate, objects in node.items():
            if predicate.startswith('@'):
                continue
            if not isinstance(objects, list):
                objects = [objects]
            for obj in objects:
                if isinstance(obj, dict) and '@id' in obj:
                    target_id = obj['@id']
                    G.add_edge(node_id, target_id, label=predicate)
    return G, node_data_map

def visualize_graph(G, node_data_map, output_file="ro_crate_graph.html"):
    net = Network(height="800px", width="100%", directed=True, notebook=False)
    net.set_options('''
    {
      "interaction": {
        "navigationButtons": true,
        "keyboard": true,
        "zoomView": true,
        "dragView": true
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.005,
          "springLength": 100,
          "springConstant": 0.08
        },
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": { "iterations": 150 }
      }
    }
    ''')

    node_labels = nx.get_node_attributes(G, 'label')
    node_types = nx.get_node_attributes(G, 'type')

    for node in G.nodes():
        label = node_labels.get(node, node)
        node_type = node_types.get(node, "Thing")
        node_data = node_data_map.get(node, {})
        data_json = json.dumps(node_data, indent=2)
        tooltip = f"<pre>{data_json}</pre>"
        net.add_node(node, label=label, title=tooltip, group=node_type)

    for source, target, data in G.edges(data=True):
        label = data.get("label", "")
        net.add_edge(source, target, label=label, title=label)

    # --- Inject filter controls and code viewer into the HTML ---
    unique_groups = sorted(set(nx.get_node_attributes(G, 'type').values()))

    filter_html = '''
    <div style="display: flex;">
      <div id="legend" style="flex: 1; min-width: 200px; max-width: 300px; padding: 10px; background: #f0f0f0;">
        <b>Filter node types:</b><br>
    '''
    for group in unique_groups:
        safe_group = group.replace('"', '\\"')
        filter_html += f'<input type="checkbox" id="{safe_group}" checked onchange="toggleGroup(\'{safe_group}\')"> <label for="{safe_group}">{group}</label><br>'
    filter_html += '''
      </div>
      <div id="code-viewer" style="flex: 1; float: right; min-width: 300px; max-width: 400px; padding: 10px; background: #f9f9f9; height: 300px; overflow: auto; border-left: 1px solid #ccc;">
        <b>Selected Source Code:</b>
        <pre><code id="code-content" style="white-space: pre-wrap;"></code></pre>
      </div>
    </div>
    '''

    toggle_script = """
    <script type="text/javascript">
      function toggleGroup(group) {
        var checkbox = document.getElementById(group);
        nodes.get().forEach(function (node) {
          if (node.group === group) {
            nodes.update({ id: node.id, hidden: !checkbox.checked });
          }
        });
      }

      function displaySource(nodeId) {
        const src = nodeSources[nodeId];
        if (src) {
          document.getElementById("code-content").textContent = src;
        } else {
          document.getElementById("code-content").textContent = "";
        }
      }
    </script>
    """

    # Collect source code mappings
    source_map = {k: v['sourceCode'] for k, v in node_data_map.items() if 'sourceCode' in v}
    source_json = json.dumps(source_map)

    source_script = f"""
    <script type="text/javascript">
      var nodeSources = {source_json};
      network.on("click", function (params) {{
        if (params.nodes.length > 0) {{
          var nodeId = params.nodes[0];
          displaySource(nodeId);
        }}
      }});
    </script>
    """

    net_html = net.generate_html()
    net_html = net_html.replace('<body>', f'<body>\n{filter_html}')
    net_html = net_html.replace('</body>', f'{toggle_script}\n{source_script}\n</body>')

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(net_html)

    print(f"Graph saved to {output_file}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python visualise.py path/to/ro-crate-metadata.json")
        sys.exit(1)

    path = sys.argv[1]
    graph_data = load_ro_crate(path)
    crate_dir = os.path.dirname(path)
    G, node_data_map = build_graph(graph_data, crate_dir)
    visualize_graph(G, node_data_map)