import sys
import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if line.startswith('from modules.cognitive import'):
        new_lines.append('from modules.cognitive import compute_confidence, get_analogy, UserModel, generate_cognitive_explanation, generate_comparison_explanation\n')
    elif line.startswith('if "parsed" not in st.session_state:'):
        new_lines.append(line)
        new_lines.append('    st.session_state.parsed = None\n\n')
        new_lines.append('if "parsed_b" not in st.session_state:\n')
        new_lines.append('    st.session_state.parsed_b = None\n\n')
        new_lines.append('if "name_a" not in st.session_state:\n')
        new_lines.append('    st.session_state.name_a = ""\n\n')
        new_lines.append('if "name_b" not in st.session_state:\n')
        new_lines.append('    st.session_state.name_b = ""\n\n')
        lines[i+1] = '' # skip the original parsed = None assignment
    elif line.startswith('with st.sidebar:'):
        new_lines.append(line)
    elif line.startswith('    st.header("📁 Upload Code")'):
        new_lines.append(line)
        new_lines.append('    mode = st.radio("Mode", ["Single File Analysis", "Compare Files"])\n')
    elif line.startswith('    uploaded = st.file_uploader("Choose a Python file", type=["py"])'):
        sidebar_code = '''
    if mode == "Single File Analysis":
        uploaded = st.file_uploader("Choose a Python file", type=["py"])
        if uploaded:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name

            st.session_state.parsed = parse_python_file(tmp_path)
            st.session_state.name_a = uploaded.name

            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            st.success("✅ Parsed successfully")

            parsed = st.session_state.parsed
            st.metric("Functions", len(parsed.get("functions", [])))
            st.metric("Classes", len(parsed.get("classes", [])))
            st.metric("Imports", len(parsed.get("imports", [])))
    else:
        uploaded_a = st.file_uploader("Choose File A", type=["py"], key="file_a")
        uploaded_b = st.file_uploader("Choose File B", type=["py"], key="file_b")
        
        if uploaded_a and uploaded_b:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_a:
                tmp_a.write(uploaded_a.read())
                tmp_path_a = tmp_a.name
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_b:
                tmp_b.write(uploaded_b.read())
                tmp_path_b = tmp_b.name
                
            st.session_state.parsed = parse_python_file(tmp_path_a)
            st.session_state.parsed_b = parse_python_file(tmp_path_b)
            st.session_state.name_a = uploaded_a.name
            st.session_state.name_b = uploaded_b.name
            
            if os.path.exists(tmp_path_a):
                os.remove(tmp_path_a)
            if os.path.exists(tmp_path_b):
                os.remove(tmp_path_b)
                
            st.success("✅ Both files parsed successfully")
'''
        new_lines.append(sidebar_code)
    # Skip the old single upload block up to st.divider()
    elif 33 <= i < 49:
        pass
    elif line.startswith('if st.session_state.parsed:'):
        main_code = '''
if mode == "Single File Analysis":
    if st.session_state.parsed:
        parsed = st.session_state.parsed
        metrics = generate_metrics(parsed)
'''
        new_lines.append(main_code)
    elif line.startswith('    parsed = st.session_state.parsed'):
        pass
    elif line.startswith('    metrics = generate_metrics(parsed)'):
        pass
    elif 57 <= i <= 245: # The block under if st.session_state.parsed:
        new_lines.append('    ' + line if line != '\n' else '\n')
    elif line.startswith('else:'):
        compare_code = '''
else:
    if st.session_state.parsed and st.session_state.parsed_b:
        parsed_a = st.session_state.parsed
        parsed_b = st.session_state.parsed_b
        name_a = st.session_state.name_a
        name_b = st.session_state.name_b
        
        metrics_a = generate_metrics(parsed_a)
        metrics_b = generate_metrics(parsed_b)
        
        st.subheader("⚖️ Side-by-Side Comparison")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 📄 File A: {name_a}")
            st.metric("Complexity", metrics_a['complexity']['score'])
            st.metric("Coupling", metrics_a['coupling']['score'])
            st.metric("Modularity", f"{metrics_a['modularity']['score']}%")
            st.metric("Central Function", metrics_a['central_function'] or "None")
            
        with col2:
            st.markdown(f"### 📄 File B: {name_b}")
            st.metric("Complexity", metrics_b['complexity']['score'])
            st.metric("Coupling", metrics_b['coupling']['score'])
            st.metric("Modularity", f"{metrics_b['modularity']['score']}%")
            st.metric("Central Function", metrics_b['central_function'] or "None")
            
        st.divider()
        st.subheader("🧠 Cognitive Comparison Explanation")
        st.write(generate_comparison_explanation(metrics_a, metrics_b, name_a, name_b))

if not st.session_state.parsed and mode == "Single File Analysis":
    st.info("👈 Upload a Python file from the sidebar to begin")
elif (not st.session_state.parsed or not st.session_state.parsed_b) and mode == "Compare Files":
    st.info("👈 Upload both Python files from the sidebar to begin comparison")
'''
        new_lines.append(compare_code)
    elif i > 246:
        pass
    else:
        new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
