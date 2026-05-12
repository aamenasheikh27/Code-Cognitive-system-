def generate_code_summary(parsed):
    functions = parsed.get("functions", [])
    classes = parsed.get("classes", [])

    function_names = [func["name"] for func in functions]
    call_map = {func["name"]: func.get("calls", []) for func in functions}

    incoming_count = {name: 0 for name in function_names}
    outgoing_count = {name: 0 for name in function_names}

    for func_name, calls in call_map.items():
        valid_calls = [call for call in calls if call in function_names]
        outgoing_count[func_name] = len(valid_calls)
        for call in valid_calls:
            incoming_count[call] += 1

    isolated_functions = []
    for name in function_names:
        if incoming_count[name] == 0 and outgoing_count[name] == 0:
            isolated_functions.append(name)

    most_calling_functions = []
    if outgoing_count:
        max_outgoing = max(outgoing_count.values())
        if max_outgoing > 0:
            most_calling_functions = [
                name for name, count in outgoing_count.items() if count == max_outgoing
            ]

    central_functions = []
    total_connections = {
        name: incoming_count[name] + outgoing_count[name] for name in function_names
    }
    if total_connections:
        max_connections = max(total_connections.values())
        if max_connections > 0:
            central_functions = [
                name for name, count in total_connections.items() if count == max_connections
            ]

    summary_lines = []
    summary_lines.append(f"The code contains {len(functions)} function(s) and {len(classes)} class(es).")

    if most_calling_functions:
        summary_lines.append(
            "The function(s) that call the most others: " +
            ", ".join(f"{name}()" for name in most_calling_functions) + "."
        )
    else:
        summary_lines.append("No function in the code calls any other user-defined function.")

    if isolated_functions:
        summary_lines.append(
            "The isolated function(s): " +
            ", ".join(f"{name}()" for name in isolated_functions) + "."
        )
    else:
        summary_lines.append("There are no isolated functions.")

    if central_functions:
        summary_lines.append(
            "The most central function(s) in the code flow: " +
            ", ".join(f"{name}()" for name in central_functions) + "."
        )
    else:
        summary_lines.append("No central function could be identified from the dependency flow.")

    dependency_sentences = []
    for caller, calls in call_map.items():
        valid_calls = [call for call in calls if call in function_names]
        for callee in valid_calls:
            dependency_sentences.append(f"{caller}() depends on {callee}().")

    if dependency_sentences:
        summary_lines.extend(dependency_sentences)
    else:
        summary_lines.append("No internal function-to-function dependencies were detected.")

    return "\n".join(summary_lines)