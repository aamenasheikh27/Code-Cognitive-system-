import math

def login(username, password):
    if username == "admin" and password == "1234":
        return get_dashboard()
    return "Access denied"

def get_dashboard():
    data = fetch_user_data()
    return data

def fetch_user_data():
    return {"name": "Amaan", "role": "admin"}

class User:
    def __init__(self, name):
        self.name = name

    def greet(self):
        return f"Hello, {self.name}"