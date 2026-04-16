"""
사용자 입력 데이터(JSON) 로드 유틸리티
"""
import json
import os

def load_user_input(folder='test', filename='user_input5.json'):
    """
    지정된 경로의 JSON 파일을 읽어 딕셔너리 객체로 반환함 (UTF-8-sig 대응)
    """
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "../../data", folder, "inputs", filename)
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")

    with open(path, "r", encoding="utf-8-sig") as f:
        user_input = json.load(f)
    return user_input

if __name__ == "__main__":
    user_input = load_user_input()
    print(user_input)