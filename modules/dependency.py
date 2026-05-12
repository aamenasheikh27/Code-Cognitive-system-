import networkx as nx
import plotly.graph_objects as go
import numpy as np

def get_node_depths(G):
    in_degrees = dict(G.in_degree())
    entry_nodes = [n for n, d in in_degrees.items() if d == 0]
    
    # If there's a cycle or no clear entry, use all nodes
    if not entry_nodes:
        entry_nodes = list(G.nodes())
        
    depths = {n: 0 for n in G.nodes()}
    for entry in entry_nodes:
        queue = [(entry, 0)]
        visited = set()
        while queue:
            curr, d = queue.pop(0)
            if d > depths[curr]:
                depths[curr] = d
            for nxt in G.successors(curr):
                if (curr, nxt) not in visited:
                    visited.add((curr, nxt))
                    queue.append((nxt, d + 1))
    return depths

def get_bezier_curve(p0, p1, offset_factor=0.15):
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0
    dist = np.sqrt(dx**2 + dy**2)
    if dist == 0:
        return [x0, x1], [y0, y1]
    
    # Control point offset perpendicular to the line
    cx = (x0 + x1) / 2 - dy * offset_factor
    cy = (y0 + y1) / 2 + dx * offset_factor
    
    t = np.linspace(0, 1, 20)
    x = (1-t)**2 * x0 + 2*(1-t)*t * cx + t**2 * x1
    y = (1-t)**2 * y0 + 2*(1-t)*t * cy + t**2 * y1
    return list(x), list(y)

def build_dependency_graph(parsed, failure_sim=None, show_external=False):
    G = nx.DiGraph()
    function_types = {}

    for func in parsed.get("functions", []):
        name = func["name"]

        if name == "__init__":
            function_types[name] = "constructor"
        elif name.startswith("get_"):
            function_types[name] = "getter"
        elif name.startswith("add_") or name.startswith("set_"):
            function_types[name] = "setter"
        elif name in ["login", "logout", "authenticate"]:
            function_types[name] = "auth"
        else:
            function_types[name] = "general"

        G.add_node(
            name,
            args=str(func.get("args", [])),
            calls=str(func.get("calls", [])),
            node_type=function_types[name]
        )

        for call in func.get("calls", []):
            if call:
                if not G.has_node(call):
                    G.add_node(call, args="[]", calls="[]", node_type="external")
                G.add_edge(name, call)

    if not show_external:
        nodes_to_remove = [n for n, d in G.nodes(data=True) if d.get("node_type") == "external"]
        G.remove_nodes_from(nodes_to_remove)

    if len(G.nodes) == 0:
        return go.Figure()

    # Calculate depths for hierarchical layout
    depths = get_node_depths(G)
    
    # Adjust layer for external calls to be on the far right
    internal_depths = [d for n, d in depths.items() if G.nodes[n].get("node_type") != "external"]
    max_internal = max(internal_depths) if internal_depths else 0
    
    for node, d in depths.items():
        if G.nodes[node].get("node_type") == "external":
            G.nodes[node]["layer"] = max_internal + 1
        else:
            G.nodes[node]["layer"] = d

    # Calculate vertical hierarchical layout
    pos = {}
    layer_nodes = {}
    for node, data in G.nodes(data=True):
        layer = data.get("layer", 0)
        if layer not in layer_nodes:
            layer_nodes[layer] = []
        layer_nodes[layer].append(node)
        
    for layer, nodes in layer_nodes.items():
        width = len(nodes)
        # Sort nodes so order is stable
        for i, node in enumerate(sorted(nodes)):
            x = (i - (width - 1) / 2.0) * 2.0
            y = -float(layer) * 2.0
            pos[node] = (x, y)

    failed_node = None
    affected_nodes = []
    if failure_sim:
        failed_node = failure_sim.get("selected_function")
        affected_nodes = failure_sim.get("affected_functions", [])

    color_map = {
        "constructor": "#A29BFE",
        "getter": "#A29BFE",
        "setter": "#A29BFE",
        "auth": "#A29BFE",
        "general": "#3498DB",  # normal blue
        "external": "#7F8C8D", # gray
        "entry": "#2ECC71",    # green
        "central": "#F1C40F",  # yellow
        "failed": "#E74C3C",   # red
        "affected": "#E67E22"  # orange
    }

    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    entry_nodes = [n for n, d in in_degrees.items() if d == 0 and out_degrees[n] > 0]
    
    scores = {n: in_degrees[n] + out_degrees[n] for n in G.nodes()}
    central_node = max(scores, key=scores.get) if scores else None

    edge_traces = []
    annotations = []

    # Used to slightly vary curves between same layers to avoid overlap
    edge_count = 0
    for edge in G.edges():
        edge_count += 1
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_color = "rgba(170, 180, 190, 0.9)"
        edge_width = 2.0
        
        is_failure_path = False
        if failed_node and (edge[0] == failed_node or edge[0] in affected_nodes) and edge[1] in affected_nodes:
            edge_color = "rgba(231, 76, 60, 0.95)"
            edge_width = 3.5
            is_failure_path = True

        # Alternate curve direction slightly for variety
        offset = 0.25 if edge_count % 2 == 0 else -0.25
        if is_failure_path:
            offset = 0.3  # Emphasize failure paths

        bx, by = get_bezier_curve(pos[edge[0]], pos[edge[1]], offset_factor=offset)

        edge_traces.append(
            go.Scatter(
                x=bx,
                y=by,
                mode="lines",
                line=dict(width=edge_width, color=edge_color),
                hoverinfo="none",
                showlegend=False
            )
        )

        if len(bx) > 1:
            ax, ay = bx[-2], by[-2]
            x_end, y_end = bx[-1], by[-1]
        else:
            ax, ay = x0, y0
            x_end, y_end = x1, y1

        annotations.append(
            dict(
                ax=ax,
                ay=ay,
                x=x_end,
                y=y_end,
                xref="x",
                yref="y",
                axref="x",
                ayref="y",
                showarrow=True,
                arrowhead=2,
                arrowsize=2.5 if not is_failure_path else 3,
                arrowwidth=edge_width,
                arrowcolor=edge_color
            )
        )

    node_x = []
    node_y = []
    node_text = []
    node_hover = []
    node_colors = []
    node_sizes = []

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        data = G.nodes[node]
        node_type = data.get("node_type", "general")
        degree = in_degrees.get(node, 0) + out_degrees.get(node, 0)

        visual_role = "Internal Function"
        if node == failed_node:
            visual_role = "Failed Function"
            color = color_map["failed"]
        elif node in affected_nodes:
            visual_role = "Affected Downstream"
            color = color_map["affected"]
        elif node == central_node:
            visual_role = "Central Function"
            color = color_map["central"]
        elif node in entry_nodes:
            visual_role = "Entry Point"
            color = color_map["entry"]
        elif node_type == "external":
            visual_role = "External Call"
            color = color_map["external"]
        else:
            color = color_map["general"]

        node_text.append(f"<b>{node}</b>")
        
        hover_info = (
            f"<b>{node}</b><br>"
            f"<b>Role:</b> {visual_role}<br>"
            f"<b>Incoming Calls:</b> {in_degrees.get(node, 0)}<br>"
            f"<b>Outgoing Calls:</b> {out_degrees.get(node, 0)}<br>"
            f"<b>Calls out to:</b> {data.get('calls', '[]')}"
        )
        if failed_node and node == failed_node:
            hover_info += f"<br><i style='color:red;'>Simulated Failure Node</i>"
            
        node_hover.append(hover_info)
        node_colors.append(color)
        
        # Sizing
        if node_type == "external":
            node_sizes.append(15)
        else:
            base_size = 35
            calculated_size = base_size + (degree * 4)
            node_sizes.append(min(calculated_size, 65)) # cap at 65

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hovertext=node_hover,
        hoverinfo="text",
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=2, color="rgba(255,255,255,0.8)"),
            opacity=0.95
        ),
        showlegend=False
    )

    legend_labels = {
        "Entry Point": color_map["entry"],
        "Central Function": color_map["central"],
        "Internal Function": color_map["general"],
        "External Call": color_map["external"],
        "Failed Function": color_map["failed"],
        "Affected Function": color_map["affected"]
    }
    
    legend_traces = []
    for label, color in legend_labels.items():
        # Only add failure legend if failure sim is active
        if not failure_sim and label in ["Failed Function", "Affected Function"]:
            continue
        legend_traces.append(
            go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=15, color=color),
                name=label, showlegend=True
            )
        )

    fig = go.Figure(
        data=edge_traces + [node_trace] + legend_traces,
        layout=go.Layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.15,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(0,0,0,0)", 
                font=dict(color="#E2E8F0")
            ),
            hovermode="closest",
            margin=dict(l=40, r=40, t=110, b=100),
            height=600,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", family="Inter"),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(node_x) - 1, max(node_x) + 1] if node_x else [-1, 1]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(node_y) - 1, max(node_y) + 1] if node_y else [-1, 1]),
            annotations=annotations
        )
    )

    return fig

def build_failure_impact_graph(parsed, failed_function):
    from modules.metrics import simulate_failure_impact
    impact_data = simulate_failure_impact(parsed, failed_function)
    
    valid_nodes = set(impact_data["affected_functions"])
    valid_nodes.add(failed_function)
    
    G = nx.DiGraph()
    function_types = {}

    for func in parsed.get("functions", []):
        name = func["name"]
        if name not in valid_nodes:
            continue
            
        G.add_node(name)

        # Only add edges between valid nodes
        for call in func.get("calls", []):
            if call in valid_nodes:
                # Reverse edge: call -> name (Failed -> Affected)
                G.add_edge(call, name)

    if len(G.nodes) == 0:
        return go.Figure()

    depths = get_node_depths(G)
    for node, d in depths.items():
        G.nodes[node]["layer"] = d

    pos = {}
    layer_nodes = {}
    for node, data in G.nodes(data=True):
        layer = data.get("layer", 0)
        if layer not in layer_nodes:
            layer_nodes[layer] = []
        layer_nodes[layer].append(node)
        
    for layer, nodes in layer_nodes.items():
        width = len(nodes)
        for i, node in enumerate(sorted(nodes)):
            x = (i - (width - 1) / 2.0) * 2.0
            y = -float(layer) * 2.0
            pos[node] = (x, y)

    edge_traces = []
    annotations = []

    edge_count = 0
    for edge in G.edges():
        edge_count += 1
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]

        edge_color = "rgba(231, 76, 60, 0.95)"
        edge_width = 3.5

        offset = 0.25 if edge_count % 2 == 0 else -0.25
        bx, by = get_bezier_curve(pos[edge[0]], pos[edge[1]], offset_factor=offset)

        edge_traces.append(
            go.Scatter(
                x=bx,
                y=by,
                mode="lines",
                line=dict(width=edge_width, color=edge_color),
                hoverinfo="none",
                showlegend=False
            )
        )

        if len(bx) > 1:
            ax, ay = bx[-2], by[-2]
            x_end, y_end = bx[-1], by[-1]
        else:
            ax, ay = x0, y0
            x_end, y_end = x1, y1

        annotations.append(
            dict(
                ax=ax, ay=ay, x=x_end, y=y_end,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=3,
                arrowwidth=edge_width, arrowcolor=edge_color
            )
        )

    node_x = []
    node_y = []
    node_text = []
    node_colors = []
    
    color_map = {
        "failed": "#E74C3C",
        "direct": "#E67E22",
        "indirect": "#F1C40F"
    }

    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        node_text.append(f"<b>{node}</b>")
        
        if node == failed_function:
            node_colors.append(color_map["failed"])
        elif node in impact_data["direct_affected"]:
            node_colors.append(color_map["direct"])
        else:
            node_colors.append(color_map["indirect"])

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        hoverinfo="text",
        marker=dict(
            size=45,
            color=node_colors,
            line=dict(width=2, color="rgba(255,255,255,0.8)"),
            opacity=0.95
        ),
        showlegend=False
    )

    legend_labels = {
        "Failed Function": color_map["failed"],
        "Directly Affected": color_map["direct"],
        "Indirectly Affected": color_map["indirect"]
    }
    
    legend_traces = []
    for label, color in legend_labels.items():
        legend_traces.append(
            go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=15, color=color),
                name=label, showlegend=True
            )
        )

    fig = go.Figure(
        data=edge_traces + [node_trace] + legend_traces,
        layout=go.Layout(
            showlegend=True,
            legend=dict(
                orientation="h", 
                yanchor="top", 
                y=-0.15, 
                xanchor="center", 
                x=0.5,
                bgcolor="rgba(0,0,0,0)", 
                font=dict(color="#E2E8F0")
            ),
            hovermode="closest",
            margin=dict(l=40, r=40, t=110, b=100),
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E2E8F0", family="Inter"),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(node_x) - 1, max(node_x) + 1] if node_x else [-1, 1]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[min(node_y) - 1, max(node_y) + 1] if node_y else [-1, 1]),
            annotations=annotations
        )
    )
    return fig