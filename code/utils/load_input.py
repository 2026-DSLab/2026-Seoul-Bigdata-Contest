import json
import os

def load_user_input(path=None):
    if path is None:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, "../../data/user_input.json")
    
    with open(path, "r", encoding="utf-8") as f:
        user_input = json.load(f)
    return user_input

if __name__ == "__main__":
    user_input = load_user_input()
    print(user_input)