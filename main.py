
import json
import time
import re
import math

EPSILON = 1e-9


# 1. MAC 연산
def mac(pattern, filter_data):
    score = 0.0

    for i in range(len(pattern)):
        for j in range(len(pattern[i])):
            score += pattern[i][j] * filter_data[i][j]

    return score


# 2. 점수 비교
def classify(score_a, score_b, label_a="Cross", label_b="X"):
    difference = abs(score_a - score_b)

    if difference < EPSILON:
        return "UNDECIDED"
    elif score_a > score_b:
        return label_a
    else:
        return label_b


# 3. 라벨 정규화
def normalize_label(label):
    labels = {
        "+": "Cross",
        "cross": "Cross",
        "x": "X"
    }

    return labels.get(str(label).strip().lower())

# 배열 크기 및 숫자 검증
def validate_matrix(matrix, size, name):

    if not isinstance(matrix, list):
        raise ValueError(f"{name}: 배열 형식이 아닙니다.")

    if len(matrix) != size:
        raise ValueError(
            f"{name}: 행 개수 오류 "
            f"(예상 {size}, 실제 {len(matrix)})"
        )

    for i, row in enumerate(matrix):
        if not isinstance(row, list):
            raise ValueError(f"{name}: {i + 1}행이 리스트가 아닙니다.")

        if len(row) != size:
            raise ValueError(
                f"{name}: {i + 1}행 열 개수 오류 "
                f"(예상 {size}, 실제 {len(row)})"
            )

        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{name}: 잘못된 숫자 값 {value}")

# 4. 성능 측정
def benchmark(pattern, filter_data, repeat=1000):
    start = time.perf_counter()

    for _ in range(repeat):
        mac(pattern, filter_data)

    end = time.perf_counter()

    return (end - start) * 1000 / repeat


# 5. 3x3 배열 입력
def input_matrix(name):
    while True:
        matrix = []
        print(f"\n{name} (3x3)")

        try:
            for i in range(3):
                text = input(f"{i + 1}행: ")
                row = list(map(float, text.split()))

                if len(row) != 3:
                    raise ValueError("열 개수 오류")

                matrix.append(row)

            return matrix

        except ValueError:
            print("입력 형식 오류: 각 줄에 숫자 3개를 입력하세요.")
            print("처음부터 다시 입력합니다.")


# 6. 사용자 입력 모드
def manual_mode():
    print("\n[1] 필터 입력")

    filter_a = input_matrix("필터 A")
    filter_b = input_matrix("필터 B")

    print("\n필터 A, B 저장 완료")

    print("\n[2] 패턴 입력")
    pattern = input_matrix("패턴")

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    result = classify(score_a, score_b, "A", "B")

    print("\n[3] MAC 결과")
    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"판정: {result}")

    avg_time = benchmark(pattern, filter_a)

    print("\n[4] 성능 분석")
    print(f"3x3 평균 시간: {avg_time:.6f} ms")
    print("연산 횟수: 9")


# 7. JSON 분석 모드

def json_mode():

    try:
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"JSON 파일 오류: {error}")
        return

    if not isinstance(data, dict):
        print("JSON 스키마 오류: 최상위 데이터는 객체여야 합니다.")
        return

    filters = data.get("filters")
    patterns = data.get("patterns")

    if not isinstance(filters, dict):
        print("JSON 스키마 오류: filters가 객체가 아닙니다.")
        return

    if not isinstance(patterns, dict):
        print("JSON 스키마 오류: patterns가 객체가 아닙니다.")
        return

    total_count = 0
    pass_count = 0
    fail_cases = []

    print("\n[1] JSON 패턴 분석")

    for name, pattern_data in patterns.items():
        total_count += 1

        try:
            # 키 규칙 확인: size_N_idx
            match = re.fullmatch(
                r"size_(\d+)_(\d+)", name
            )

            if match is None:
                raise ValueError("패턴 키 형식 오류")

            size = int(match.group(1))
            filter_key = f"size_{size}"

            if not isinstance(pattern_data, dict):
                raise ValueError("패턴 데이터 형식 오류")

            # 필터 존재 여부 확인
            filter_group = filters.get(filter_key)

            if not isinstance(filter_group, dict):
                raise ValueError(f"{filter_key} 필터 없음 또는 형식 오류")

            pattern = pattern_data["input"]
            cross_filter = filter_group["cross"]
            x_filter = filter_group["x"]

            # 행과 열 크기 및 숫자 검증
            validate_matrix(pattern, size, "입력 패턴")
            validate_matrix(cross_filter, size, "Cross 필터")
            validate_matrix(x_filter, size, "X 필터")

            # expected 라벨 검증
            expected = normalize_label(pattern_data["expected"])

            if expected not in ("Cross", "X"):
                raise ValueError("expected 라벨 오류")

            # MAC 연산
            cross_score = mac(pattern, cross_filter)
            x_score = mac(pattern, x_filter)

            result = classify(cross_score, x_score)

            print(f"\n[{name}]")
            print(f"Cross 점수: {cross_score}")
            print(f"X 점수: {x_score}")
            print(f"판정: {result}")
            print(f"예상 정답: {expected}")

            if result == expected:
                pass_count += 1
                print("결과: PASS")

            else:
                if result == "UNDECIDED":
                    reason = "허용오차 이내 동점"
                else:
                    reason = f"판정 {result}, 예상 {expected} 불일치"

                fail_cases.append((name, reason))
                print(f"결과: FAIL ({reason})")

        except (ValueError, KeyError, TypeError) as error:
            reason = f"데이터/스키마 오류: {error}"

            fail_cases.append((name, reason))

            print(f"\n[{name}]")
            print(f"결과: FAIL ({reason})")

    # 성능 측정
    print("\n[2] 성능 분석 (평균/1000회)")
    print(f"{'크기':<10} {'평균 시간(ms)':<18} {'연산 횟수'}")
    print("-" * 43)

    for size in (3, 5, 13, 25):

        # 성능 측정용 정상 Cross 배열 생성
        center = size // 2

        test_pattern = [
            [
                1.0 if i == center or j == center else 0.0
                for j in range(size)
            ]
            for i in range(size)
        ]

        avg_time = benchmark(test_pattern, test_pattern)

        print(
            f"{size}x{size:<7} "
            f"{avg_time:<18.6f} "
            f"{size * size}"
        )

    # 전체 결과 요약
    print("\n[3] 결과 요약")
    print(f"전체 테스트: {total_count}개")
    print(f"통과: {pass_count}개")
    print(f"실패: {len(fail_cases)}개")

    if fail_cases:
        print("\n실패 케이스:")
        for name, reason in fail_cases:
            print(f"- {name}: {reason}")
    else:
        print("실패 케이스 없음")



# 8. 메인 실행 함수
def main():
    print("=== Mini NPU Simulator ===")

    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        choice = input("\n선택 (1 또는 2): ").strip()

        if choice == "1":
            manual_mode()
            break

        elif choice == "2":
            json_mode()
            break

        else:
            print("잘못된 선택입니다. 1 또는 2를 입력하세요.")


# 9. 프로그램 시작
if __name__ == "__main__":
    main()
