def build_internal_graph(parsed):
    functions = parsed.get("functions", [])
    function_names = [f["name"] for f in functions]

    graph = {name: [] for name in function_names}
    incoming = {name: 0 for name in function_names}

    for func in functions:
        caller = func["name"]
        valid_calls = [call for call in func.get("calls", []) if call in function_names]
        graph[caller] = valid_calls

        for callee in valid_calls:
            incoming[callee] += 1

    return graph, incoming


def get_entry_points(graph, incoming):
    return [node for node in graph if incoming[node] == 0 and len(graph[node]) > 0]


def get_isolated_functions(graph, incoming):
    return [node for node in graph if incoming[node] == 0 and len(graph[node]) == 0]


def get_leaf_functions(graph, incoming):
    return [node for node in graph if incoming[node] > 0 and len(graph[node]) == 0]


def longest_path_from_node(graph, start):
    best_path = []

    def dfs(node, path, visited):
        nonlocal best_path

        if len(path) > len(best_path):
            best_path = path[:]

        for nxt in graph.get(node, []):
            if nxt not in visited:
                visited.add(nxt)
                path.append(nxt)
                dfs(nxt, path, visited)
                path.pop()
                visited.remove(nxt)

    dfs(start, [start], {start})
    return best_path


def get_main_flow_path(graph, incoming):
    entry_points = get_entry_points(graph, incoming)
    if not entry_points:
        return []

    best = []
    for entry in entry_points:
        candidate = longest_path_from_node(graph, entry)
        if len(candidate) > len(best):
            best = candidate
    return best


def get_central_function(graph, incoming):
    scores = {}
    for node in graph:
        scores[node] = len(graph[node]) + incoming[node]

    if not scores:
        return None, 0

    best_node = max(scores, key=scores.get)
    return best_node, scores[best_node]


def get_node_influence_scores(graph, incoming):
    scores = {}
    for node in graph:
        scores[node] = len(graph[node]) + incoming[node]

    if not scores:
        return {}, None, 0

    best_node = max(scores, key=scores.get)
    return scores, best_node, scores[best_node]


def get_function_depths_and_layers(graph, incoming):
    depths = {node: 0 for node in graph}
    entry_points = get_entry_points(graph, incoming)
    
    for entry in entry_points:
        queue = [(entry, 0)]
        visited = set()
        while queue:
            curr, d = queue.pop(0)
            if d > depths[curr]:
                depths[curr] = d
            for nxt in graph.get(curr, []):
                if (curr, nxt) not in visited:
                    visited.add((curr, nxt))
                    queue.append((nxt, d + 1))
                    
    layers = {}
    for node, d in depths.items():
        if d not in layers:
            layers[d] = []
        layers[d].append(node)
        
    layered_structure = [layers[d] for d in sorted(layers.keys())]
    deepest_node = max(depths, key=depths.get) if depths else None
    
    return depths, layered_structure, deepest_node


def compute_complexity_score(parsed, graph, incoming):
    num_functions = len(parsed.get("functions", []))
    max_depth = len(get_main_flow_path(graph, incoming))
    total_edges = sum(len(v) for v in graph.values())

    raw = num_functions * 2 + max_depth * 4 + total_edges * 2

    if raw <= 20:
        level = "Low"
    elif raw <= 40:
        level = "Medium"
    else:
        level = "High"

    return {
        "score": raw,
        "level": level,
        "functions": num_functions,
        "depth": max_depth,
        "edges": total_edges
    }


def compute_coupling_level(graph):
    if not graph:
        return {"score": 0, "level": "Low"}

    total_outgoing = sum(len(v) for v in graph.values())
    avg_outgoing = total_outgoing / len(graph)

    if avg_outgoing < 1:
        level = "Low"
    elif avg_outgoing < 2:
        level = "Medium"
    else:
        level = "High"

    return {
        "score": round(avg_outgoing, 2),
        "level": level
    }


def compute_modularity_score(graph, incoming):
    isolated = get_isolated_functions(graph, incoming)
    total = len(graph)

    if total == 0:
        return {"score": 0, "level": "Low", "isolated_count": 0}

    ratio = len(isolated) / total
    score = round(ratio * 100, 1)

    if ratio >= 0.35:
        level = "High"
    elif ratio >= 0.15:
        level = "Medium"
    else:
        level = "Low"

    return {
        "score": score,
        "level": level,
        "isolated_count": len(isolated)
    }


def get_failure_impact(graph):
    reverse_graph = {node: [] for node in graph}
    for node, edges in graph.items():
        for edge in edges:
            if edge in reverse_graph:
                reverse_graph[edge].append(node)
                
    impacts = {}
    affected_lists = {}
    
    for node in graph:
        visited = set()
        queue = [node]
        while queue:
            curr = queue.pop(0)
            for caller in reverse_graph.get(curr, []):
                if caller not in visited:
                    visited.add(caller)
                    queue.append(caller)
        impacts[node] = len(visited)
        affected_lists[node] = list(visited)
        
    return impacts, affected_lists


def get_risk_functions(graph, incoming):
    impacts, affected_lists = get_failure_impact(graph)
    risks = []

    for node in graph:
        influence = len(graph[node]) + incoming[node]
        impact_score = impacts[node]
        affected = affected_lists[node]

        if len(graph[node]) >= 2 or influence >= 3 or impact_score > 0:
            risks.append({
                "name": node,
                "outgoing": len(graph[node]),
                "incoming": incoming[node],
                "influence": influence,
                "impact_score": impact_score,
                "affected": affected
            })

    risks.sort(key=lambda x: (x["impact_score"], x["influence"]), reverse=True)
    return risks


vague_names = {
    "x", "y", "z", "f", "g", "h", "tmp", "temp",
    "foo", "bar", "test", "do_everything",
    "process_all", "handle_all", "main"
}

def detect_vague_functions(parsed):
    functions = parsed.get("functions", [])
    vague_funcs = []
    for f in functions:
        if f["name"].lower() in vague_names or len(f["name"]) <= 2:
            vague_funcs.append(f["name"])
    return vague_funcs

def detect_monolithic_functions(parsed):
    functions = parsed.get("functions", [])
    monolithic = []
    monolithic_keywords = ["do_everything", "all", "manage", "handler", "process_all", "manage_all"]
    
    for f in functions:
        name = f["name"].lower()
        is_monolithic = False
        
        if any(kw in name for kw in monolithic_keywords):
            is_monolithic = True
            
        args = f.get("args", [])
        if any(arg.lower() == "action" or arg.lower() == "command" for arg in args):
            is_monolithic = True
            
        if is_monolithic:
            monolithic.append(f["name"])
            
    return monolithic

def calculate_naming_quality(parsed):
    functions = parsed.get("functions", [])
    if not functions:
        return 0
    
    good_names = 0
    for f in functions:
        name = f["name"].lower()
        if name not in vague_names and len(name) > 2 and ("_" in name or name.islower()):
            good_names += 1
            
    return (good_names / len(functions)) * 100

def calculate_single_responsibility_score(parsed):
    functions = parsed.get("functions", [])
    if not functions:
        return 0
        
    monolithic = detect_monolithic_functions(parsed)
    ratio = 1.0 - (len(monolithic) / len(functions))
    return max(0, min(100, ratio * 100))

def calculate_useful_modularity(parsed, graph, incoming):
    functions = parsed.get("functions", [])
    if not functions:
        return 0
        
    isolated = get_isolated_functions(graph, incoming)
    vague = detect_vague_functions(parsed)
    
    connected_and_meaningful = [f for f in graph if f not in isolated and f not in vague]
    
    ratio = len(connected_and_meaningful) / len(functions)
    return ratio * 100

def calculate_design_score(parsed, graph, incoming):
    naming_quality = calculate_naming_quality(parsed)
    sr_score = calculate_single_responsibility_score(parsed)
    useful_modul = calculate_useful_modularity(parsed, graph, incoming)
    
    vague = detect_vague_functions(parsed)
    monolithic = detect_monolithic_functions(parsed)
    isolated = get_isolated_functions(graph, incoming)
    
    dead_code = [f for f in isolated if f in vague]
    dead_code_penalty = (len(dead_code) / max(1, len(parsed.get("functions", [])))) * 40
    
    monolithic_penalty = (len(monolithic) / max(1, len(parsed.get("functions", [])))) * 50
    vague_name_penalty = (len(vague) / max(1, len(parsed.get("functions", [])))) * 30
    
    structural_clarity = 100 - monolithic_penalty - (len(isolated) / max(1, len(parsed.get("functions", []))) * 20)
    structural_clarity = max(0, structural_clarity)
    
    maintainability = 100 - compute_complexity_score(parsed, graph, incoming)["score"]
    maintainability = max(0, min(100, maintainability))

    design_score = (
        (naming_quality * 0.25) +
        (sr_score * 0.25) +
        (useful_modul * 0.20) +
        (structural_clarity * 0.20) +
        (maintainability * 0.10) -
        dead_code_penalty -
        monolithic_penalty -
        vague_name_penalty
    )
    
    return {
        "final_score": round(max(0, min(100, design_score)), 1),
        "naming_quality": round(naming_quality, 1),
        "sr_score": round(sr_score, 1),
        "useful_modul": round(useful_modul, 1),
        "structural_clarity": round(structural_clarity, 1),
        "dead_code_risk": round(dead_code_penalty, 1),
        "monolithic_risk": round(monolithic_penalty, 1),
        "vague_functions": vague,
        "monolithic_functions": monolithic,
        "dead_code_functions": dead_code
    }


def generate_metrics(parsed):
    graph, incoming = build_internal_graph(parsed)

    complexity = compute_complexity_score(parsed, graph, incoming)
    coupling = compute_coupling_level(graph)
    modularity = compute_modularity_score(graph, incoming)
    risk_functions = get_risk_functions(graph, incoming)
    main_flow = get_main_flow_path(graph, incoming)
    entry_points = get_entry_points(graph, incoming)
    isolated = get_isolated_functions(graph, incoming)
    central_function, central_score = get_central_function(graph, incoming)
    
    influence_scores, most_influential, _ = get_node_influence_scores(graph, incoming)
    depths, layered_structure, deepest_node = get_function_depths_and_layers(graph, incoming)
    
    design_metrics = calculate_design_score(parsed, graph, incoming)

    return {
        "graph": graph,
        "incoming": incoming,
        "complexity": complexity,
        "design_metrics": design_metrics,
        "coupling": coupling,
        "modularity": modularity,
        "risk_functions": risk_functions,
        "main_flow": main_flow,
        "critical_path": main_flow,
        "entry_points": entry_points,
        "isolated_functions": isolated,
        "central_function": central_function,
        "central_score": central_score,
        "influence_scores": influence_scores,
        "most_influential": most_influential,
        "depths": depths,
        "layered_structure": layered_structure,
        "deepest_node": deepest_node
    }

def simulate_failure_impact(parsed, failed_function):
    graph, incoming = build_internal_graph(parsed)
    
    reverse_graph = {node: [] for node in graph}
    for node, edges in graph.items():
        for edge in edges:
            if edge in reverse_graph:
                reverse_graph[edge].append(node)
                
    if failed_function not in reverse_graph:
        return {
            "failed_function": failed_function,
            "affected_functions": [],
            "direct_affected": [],
            "indirect_affected": [],
            "impact_count": 0,
            "severity": "No Impact",
            "impact_paths": [],
            "impact_table": []
        }
        
    direct_affected = []
    indirect_affected = []
    distances = {}
    
    queue = [(failed_function, 0)]
    visited = {failed_function}
    
    while queue:
        curr, dist = queue.pop(0)
        distances[curr] = dist
        
        for caller in reverse_graph.get(curr, []):
            if caller not in visited:
                visited.add(caller)
                queue.append((caller, dist + 1))
                if dist + 1 == 1:
                    direct_affected.append(caller)
                else:
                    indirect_affected.append(caller)
                    
    affected_functions = direct_affected + indirect_affected
    impact_count = len(affected_functions)
    
    if impact_count == 0:
        severity = "No Impact"
    elif impact_count == 1:
        severity = "Low"
    elif impact_count <= 3:
        severity = "Medium"
    else:
        severity = "High"
        
    impact_paths = []
    def dfs_paths(node, current_path):
        is_leaf = True
        for caller in reverse_graph.get(node, []):
            if caller in visited and caller not in current_path:
                is_leaf = False
                dfs_paths(caller, current_path + [caller])
        if is_leaf and len(current_path) > 1:
            impact_paths.append(current_path)
            
    if affected_functions:
        dfs_paths(failed_function, [failed_function])
        
    impact_table = []
    for node in affected_functions:
        dist = distances[node]
        impact_type = "Direct dependency" if dist == 1 else "Indirect dependency"
        node_sev = "High" if dist == 1 else "Medium" if dist == 2 else "Low"
        impact_table.append({
            "Function": node,
            "Distance": dist,
            "Impact Type": impact_type,
            "Severity": node_sev
        })
        
    return {
        "failed_function": failed_function,
        "affected_functions": affected_functions,
        "direct_affected": direct_affected,
        "indirect_affected": indirect_affected,
        "impact_count": impact_count,
        "severity": severity,
        "impact_paths": impact_paths,
        "impact_table": impact_table
    }