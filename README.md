# Code Cognitive System

## AI-Powered Code Understanding Platform

Code Cognitive System is an interactive Python code analysis platform that helps users understand unfamiliar Python code using AST parsing, dependency graph generation, metrics analysis, cognitive reasoning, failure simulation, code comparison, and Gemini-powered question answering.

The system takes a Python file as input and converts it into meaningful insights such as function flow, dependency relationships, code intent, risk areas, important functions, failure impact, and design quality.

---

## Project Overview

Understanding unfamiliar code can be difficult, especially when documentation is missing or the codebase has many functions and dependencies. This project solves that problem by transforming raw Python code into readable, visual, and explainable insights.

Instead of only showing source code, the system helps answer questions such as:

- What does this code do?
- What is the main workflow?
- Which function is most important?
- Which function is risky?
- What happens if a function fails?
- Which of two implementations is better designed?
- How can this code be improved?

---

## Key Features

### 1. Python Code Upload

Users can upload a Python `.py` file through the Streamlit interface. The system reads the uploaded file and analyzes its internal structure.

---

### 2. AST-Based Parsing

The project uses Python’s built-in `ast` module to extract structural components from code.

It extracts:

- Function definitions
- Class definitions
- Imports
- Function arguments
- Function calls
- Line-level structural information

This helps the system understand code structurally instead of treating it as plain text.

---

### 3. Dependency Graph Generation

The system builds a function dependency graph where:

- Nodes represent functions
- Directed edges represent function calls

Example:

```text
login() → build_session() → get_dashboard() → get_permissions()
```
This helps users understand how functions interact with each other.

The dependency graph also identifies:

Entry points
Central functions
Internal functions
External/library calls
Isolated functions

### 4. Metrics Analysis

The system calculates important code metrics such as:

Complexity Score
Shows how difficult the code structure is to understand.

Coupling
Measures how strongly functions depend on each other.

Modularity
Measures how well the code is divided into independent and meaningful components.

Risk Score
Identifies functions that may affect multiple parts of the code if changed incorrectly.

### 5. Code Intent Understanding

The system detects the high-level purpose of the uploaded code.

It can identify code types such as:

Authentication system
CRUD application
Machine learning pipeline
API/backend system
Data processing script
Event booking system
E-commerce workflow
General utility program

This is done using function names, imports, dependency flow, and structural patterns.

### 6. Cognitive Summary

The Cognitive Summary combines structural and semantic insights into one readable explanation.

It includes:

Code intent
Main workflow
Entry points
Important functions
Central function
Risk and failure insights
Overall code behavior

This avoids repeated summaries and gives one consolidated explanation.

### 7. Graph-Based Reasoning

The system performs reasoning over the dependency graph.

It identifies:
Most influential function
Deepest function
Critical execution path
Entry functions
Central functions
Isolated utilities

This makes the project more than just visualization. It reasons about the role of each function in the system.

### 8. Failure Simulation

Failure Simulation shows what happens if a selected function fails or is incorrectly modified.

It answers:

If this function fails, what gets affected?

The system shows:
Failed function
Directly affected functions
Indirectly affected functions
Impact severity
Downstream affected path

Example:

login() → build_session() → get_dashboard() → get_permissions()

This helps identify high-impact functions that require careful testing or refactoring.

### 9. Code Comparison

The system allows users to upload two Python files and compare them side by side.

It compares:
Complexity
Coupling 
Useful Modularity 
Naming clarity 
Structure clarity 
Dead code risk 
Monolithic function risk 
Final design quality 

This helps determine whihc implementation is better designed.

### 10. Gemini-Powered Ask Questions Module

The Ask Questions module allows users to ask natural language questions about the uploaded code.

Example questions:

What is the main workflow?
Which function is most important?
Which function failure affects the system most?
Explain the code simply.
How can this code be improved?
Which function should be refactored first?

The system uses Google Gemini API to answer questions using the analyzed code context.

If Gemini API is not configured, the system safely falls back to local reasoning.

### Why This Project Is Different From a Normal LLM

A general LLM reads code mostly as text.

This project first performs structured program analysis using:

AST parsing
Dependency graph modeling
Code metrics
Graph-based reasoning
Failure impact simulation
Code comparison

Then it uses Gemini only for natural-language question answering.

This makes the system more explainable because answers are based on extracted structural evidence.

### Tech Stack 
 Layer                 Technology Used             
 --------------------  --------------------------- 
 Programming Language  Python                      
 Code Parsing          Python AST                  
 Graph Analysis        NetworkX                    
 Visualization         Plotly                      
 UI Dashboard          Streamlit                   
 NLP / Reasoning       Rule-based NLP + Gemini API 
 LLM Integration       Google Gemini API           
 Metrics               Custom Python algorithms    
 Version Control       Git + GitHub                

### Project Structure 
code-cognitive-system/
│
├── app.py
├── requirements.txt
├── sample.py
├── README.md
├── .gitignore
│
└── modules/
    ├── __init__.py
    ├── parser.py
    ├── dependency.py
    ├── metrics.py
    ├── nlp_module.py
    ├── cognitive.py
    ├── summary_module.py
    └── llm_module.py

### Installation and Set up 
1. Clone the Repository
git clone https://github.com/aamenasheikh27/Code-Cognitive-system-.git
cd Code-Cognitive-system-

2. Create Virtual Environment
python -m venv .venv

Activate it on Windows PowerShell:
.\.venv\Scripts\Activate.ps1

3. Install Dependencies
pip install -r requirements.txt

4. Set Gemini API Key
The Gemini API key is required only for the Ask Questions module.
Do not hardcode the API key inside the code.

Set it in PowerShell:
$env:GEMINI_API_KEY="your_gemini_api_key_here"

To check whether the key is detected:
python -c "import os; print(bool(os.getenv('GEMINI_API_KEY')))"

It should print:
True

5. Run the Project
streamlit run app.py

If Streamlit is not recognized:
python -m streamlit run app.py

### How to Use 
--Single File Analysis
Open the Streamlit app.
Select Single File Analysis.
Upload a Python .py file.
View:
Overview
Dependency Graph
Metrics
Cognitive Summary
Failure Simulation
Ask Questions

--Code Comparison
1.Select Compare Files.
2.Upload File A and File B.
3.The system compares both implementations.
4.View the final verdict and explanation.


-- Ask Questions

After uploading a file, go to the Ask Questions tab.

Ask questions like:
What is the main workflow?
Which function is most important?
How can this code be improved?
Which function failure affects the system most?

If Gemini API is connected, answers will show:
Answered using Gemini

If not connected, answers will show:
Answered using local reasoning fallback

--Example Output

For an authentication system, the system may identify:
Code Intent: User management / authentication system
Main Workflow: login → build_session → get_dashboard → get_permissions
Central Function: login
Failure-sensitive Function: hash_password

### Testing 
The project can be tested using different types of Python programs:

Authentication system
CRUD application
Machine learning pipeline
Flask API backend
Data cleaning ETL script
Banking transaction system
IoT sensor pipeline
Poor monolithic code
Clean modular code
Async notification system

This helps evaluate whether the system can handle diverse code structures.

### Important Concepts Used
AST Parsing
AST converts Python code into a structured tree format, allowing the system to extract functions, classes, imports, and calls.

Dependency Graph
A graph representation of function relationships. It helps visualize how code flows internally.

Coupling
Coupling measures how much functions depend on each other. High coupling usually means changing one function may affect many others.

Modularity
Modularity measures how well the code is divided into meaningful independent parts. Good modularity improves readability and maintainability.

Failure Simulation
Failure simulation estimates the downstream impact of a function failure.

Cognitive Reasoning 
Cognitive reasoning identifies important functions, critical paths, bottlenecks and failure-sensitive components.

### Current Limitations
The system currently focuses mainly on Python files.
It uses static analysis and does not execute the uploaded code.
Runtime behavior, dynamic imports, decorators, and advanced object-oriented flows may not always be fully captured.
Gemini answers depend on API availability and the provided context.

### Future Scope

Future improvements can include:
Multi-file project analysis
Repository-level dependency mapping
Runtime execution tracing
Bug prediction
Advanced refactoring suggestions
Support for Java, C++, and JavaScript
More detailed LLM-assisted code review
Exportable reports in PDF/HTML
Integration with VS Code extensions

### Safety and API Key Handling

This project does not store API keys in the source code.

Use environment variables:
os.getenv("GEMINI_API_KEY")

Never commit:
.env
API keys
.venv/

The .gitignore file prevents sensitive and unnecessary files from being uploaded.


