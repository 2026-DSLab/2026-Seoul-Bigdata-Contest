import os
import sys
import time
from input_builder import build_input

# Windows 터미널 한글 출력 및 에모지 관련 인코딩 설정
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

def run_batch(folder_name):
    """
    특정 폴더 내의 모든 JSON 입력을 분석함
    """
    input_dir = os.path.join(os.path.dirname(__file__), "../../data", folder_name, "inputs")
    
    if not os.path.exists(input_dir):
        print(f"[Skip] 폴더가 존재하지 않음: {folder_name}")
        return 0, 0

    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    files.sort()

    total = len(files)
    success = 0
    fail = 0

    print(f"\n" + "="*50)
    print(f"[{folder_name.upper()}] 분석 시작 (총 {total}개 파일)")
    print("="*50)

    for idx, filename in enumerate(files, 1):
        start_time = time.time()
        print(f"\n[{idx}/{total}] {filename} 작업 중...")
        try:
            build_input(folder_name, filename)
            success += 1
        except Exception as e:
            print(f"[Fail] {filename} 오류 발생: {e}")
            fail += 1
        
        elapsed = time.time() - start_time
        print(f"-> 소요시간: {elapsed:.2f}초")

    return success, fail

def main():
    # 실행 인자가 있으면 해당 폴더만, 없으면 기본 2개 폴더 모두 수행
    if len(sys.argv) > 1:
        folders = [sys.argv[1]]
    else:
        folders = ["test", "storyline"]

    total_success = 0
    total_fail = 0

    for folder in folders:
        s, f = run_batch(folder)
        total_success += s
        total_fail += f

    print(f"\n" + "="*50)
    print(f"전체 분석 완료 리포트")
    print(f"- 총 성공: {total_success}")
    print(f"- 총 실패: {total_fail}")
    print("="*50)

if __name__ == "__main__":
    main()
