from modules.metrics import generate_metrics


ANALOGIES = {
    "login": "Like a security guard checking your ID before letting you in",
    "add": "Like adding an item to your shopping cart",
    "get": "Like asking a librarian to fetch a book for you",
    "delete": "Like throwing something in the trash",
    "update": "Like editing a saved document",
    "search": "Like using a search engine to find something",
    "queue": "Like a line at a ticket counter — first in, first out",
    "cache": "Like keeping notes so you do not re-read the whole book",
    "init": "Like setting up your desk before starting work",
    "send": "Like posting a letter to someone"
}


def compute_confidence(func_info):
    score = 0
    reasons = []

    if func_info.get("docstring"):
        score += 30
        reasons.append("has documentation")

    if len(func_info.get("args", [])) > 0:
        score += 20
        reasons.append("has clear arguments")

    if len(func_info.get("calls", [])) > 0:
        score += 20
        reasons.append("calls are traceable")

    if len(func_info.get("name", "")) > 4:
        score += 20
        reasons.append("has meaningful name")

    if func_info.get("name") not in ["f", "g", "tmp", "x"]:
        score += 10
        reasons.append("not a vague name")

    return {
        "confidence": score,
        "reasons": reasons
    }


def get_analogy(func_name):
    func_lower = func_name.lower()

    for keyword, analogy in ANALOGIES.items():
        if keyword in func_lower:
            return analogy

    return "This function performs a specific task in the system"


class UserModel:
    def __init__(self):
        self.history = []
        self.confused = []
        self.understood = []
        self.level = "intermediate"

    def log_interaction(self, question, asked_simplify=False):
        self.history.append(question)

        if asked_simplify:
            self.confused.append(question)
        else:
            self.understood.append(question)

        self.update_level()

    def update_level(self):
        if len(self.confused) > len(self.understood):
            self.level = "beginner"
        elif len(self.understood) > 3:
            self.level = "advanced"
        else:
            self.level = "intermediate"

    def get_prompt_prefix(self):
        levels = {
            "beginner": "Explain simply, avoid technical words:",
            "intermediate": "Explain clearly with some technical detail:",
            "advanced": "Give full technical explanation:"
        }
        return levels[self.level]


def generate_cognitive_explanation(parsed):
    metrics = generate_metrics(parsed)
    from modules.nlp_module import detect_system_type, workflow_to_sentence

    explanation = []
    
    # 1. Code Intent & System Type
    system_type = detect_system_type(parsed)
    explanation.append(f"### 🎯 Code Intent\n{system_type}")

    # 2. Main Workflow
    workflow = workflow_to_sentence(metrics.get("main_flow", []))
    explanation.append(f"### 🔄 Main Workflow\n{workflow}")

    # 3. Overall Code Understanding & Complexity
    comp_level = metrics['complexity']['level'].lower()
    coup_level = metrics['coupling']['level'].lower()
    mod_level = metrics['modularity']['level'].lower()
    
    understanding = [
        f"The codebase contains {len(parsed.get('functions', []))} function(s).",
        f"It exhibits a **{comp_level} complexity**, **{coup_level} coupling**, and **{mod_level} modularity** structure."
    ]
    
    if metrics["entry_points"]:
        understanding.append(f"Execution likely begins at entry point(s): **{', '.join(metrics['entry_points'])}()**.")
        
    explanation.append(f"### 🧠 Overall Code Understanding\n" + " ".join(understanding))

    # 4. Important Functions
    important = []
    if metrics.get("most_influential"):
        important.append(f"- **{metrics['most_influential']}()**: The most influential function orchestrating internal behavior.")
        
    if metrics.get("deepest_node"):
        important.append(f"- **{metrics['deepest_node']}()**: Sits at the deepest layer of the execution stack.")
        
    if metrics.get("isolated_functions"):
        iso = ", ".join(f"{name}()" for name in metrics["isolated_functions"])
        important.append(f"- **Isolated utilities**: {iso} operate independently from the main flow.")
        
    if important:
        explanation.append("### ⭐ Important Functions\n" + "\n".join(important))

    # 5. Risk / Failure Insight
    if metrics.get("risk_functions"):
        top_risks = metrics["risk_functions"][:3]
        risk_lines = []
        for item in top_risks:
            affected_count = item.get("impact_score", 0)
            affected_names = ", ".join(item.get("affected", []))
            if affected_count > 0:
                risk_lines.append(f"- **{item['name']}()**: If this fails, it directly affects {affected_count} downstream function(s) ({affected_names}).")
            else:
                risk_lines.append(f"- **{item['name']}()**: Flagged as high-risk due to its high influence or complexity.")
                
        explanation.append("### ⚠️ Risk & Failure Insight\n" + "\n".join(risk_lines))

    return "\n\n".join(explanation)


def generate_comparison_explanation(metrics_a, metrics_b, name_a, name_b):
    explanation = []
    
    # Modularity
    mod_a = metrics_a['modularity']['score']
    mod_b = metrics_b['modularity']['score']
    
    if mod_a > mod_b:
        explanation.append(f"Code {name_a} is more modular because its isolated function ratio ({mod_a}%) is higher than {name_b} ({mod_b}%).")
    elif mod_b > mod_a:
        explanation.append(f"Code {name_b} is more modular because its isolated function ratio ({mod_b}%) is higher than {name_a} ({mod_a}%).")
    else:
        explanation.append(f"Both codes have similar modularity ({mod_a}%).")
        
    # Complexity
    comp_a = metrics_a['complexity']['score']
    comp_b = metrics_b['complexity']['score']
    if comp_a < comp_b:
        explanation.append(f"Code {name_a} is less complex (score: {comp_a}) compared to {name_b} (score: {comp_b}).")
    elif comp_b < comp_a:
        explanation.append(f"Code {name_b} is less complex (score: {comp_b}) compared to {name_a} (score: {comp_a}).")
    else:
        explanation.append(f"Both codes have equal structural complexity (score: {comp_a}).")
        
    # Coupling
    coup_a = metrics_a['coupling']['score']
    coup_b = metrics_b['coupling']['score']
    if coup_a < coup_b:
        explanation.append(f"Code {name_a} has lower coupling ({coup_a} avg outgoing) meaning less rigid dependencies than {name_b} ({coup_b}).")
    elif coup_b < coup_a:
        explanation.append(f"Code {name_b} has lower coupling ({coup_b} avg outgoing) meaning less rigid dependencies than {name_a} ({coup_a}).")
    else:
        explanation.append(f"Both codes have similar coupling levels ({coup_a}).")
        
    # Central Function
    cent_a = metrics_a.get("most_influential")
    cent_b = metrics_b.get("most_influential")
    
    cent_str = []
    if cent_a:
        cent_str.append(f"{name_a}'s central function is `{cent_a}()`")
    if cent_b:
        cent_str.append(f"{name_b}'s central function is `{cent_b}()`")
        
    if cent_str:
        explanation.append("Regarding system bottlenecks, " + " and ".join(cent_str) + ".")
        
    return "\n\n".join(explanation)