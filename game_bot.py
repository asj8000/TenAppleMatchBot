import cv2
import pyautogui
import numpy as np
import os
import time
import tkinter as tk
from tkinter import Label, Button, Canvas, Checkbutton, BooleanVar


# 템플릿 이미지 경로 (숫자 템플릿)
template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")  # 템플릿 이미지 디렉토리

# 빨간색 범위 설정
LOWER_RED = np.array([0, 100, 100])
UPPER_RED = np.array([10, 255, 255])
LOWER_RED2 = np.array([170, 100, 100])
UPPER_RED2 = np.array([180, 255, 255])

def capture_screen():
    print("화면 캡처 시작")
    screenshot = pyautogui.screenshot()
    screenshot = np.array(screenshot)
    screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
    screenshot_path = "screenshot_1.png"
    cv2.imwrite(screenshot_path, screenshot)
    print(f"스크린샷 저장: {screenshot_path}")
    return screenshot

def extract_red_area(image):
    print("빨간색 영역 추출 시작")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, LOWER_RED, UPPER_RED)
    mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    red_mask = cv2.bitwise_or(mask1, mask2)
    red_area = cv2.bitwise_and(image, image, mask=red_mask)
    print(f"빨간색 영역 추출 완료, 빨간색 영역 크기: {np.sum(red_mask)}")
    return red_area

def find_template_matches(image, template):
    print("매칭해드려요~")
    result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    threshold = 0.9  # 템플릿 매칭 유사도 기준
    locations = np.where(result >= threshold)
    print(f"매칭 결과: {len(locations[0])}개의 매칭 위치가 발견됨")
    
    # 결과를 사각형으로 표시
    matches = []
    for pt in zip(*locations[::-1]):  # (x, y) 좌표 변환
        matches.append(pt)
    print(f"매칭된 위치들: {matches}")
    return matches

def process_image(image, is_save_debug_image):
    print("이미지 처리 시작")

    detected_numbers = []  # 숫자 리스트
    positions = []  # 위치 리스트

    # HSV 변환 (배경과 사과 제거)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, LOWER_RED, UPPER_RED)
    mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    red_mask = cv2.bitwise_or(mask1, mask2)

    # 숫자 영역만 흰색으로, 나머지는 검은색으로 변환
    processed_image = np.zeros_like(image)  # 배경을 검은색으로 초기화
    processed_image[red_mask == 255] = [255, 255, 255]  # 빨간색 영역을 흰색으로 설정

    # 템플릿 이미지 목록 가져오기
    templates = []
    for i in range(10):  # 0부터 9까지의 숫자 템플릿 이미지
        template_path = os.path.join(template_dir, f"{i}.png")
        if os.path.exists(template_path):
            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            templates.append((i, template))
    print("템플릿 이미지 리스트 호출 완료")

    # 각 템플릿에 대해 매칭 수행
    for num, template in templates:
        gray = cv2.cvtColor(processed_image, cv2.COLOR_BGR2GRAY)
        print(f"{num}번 템플릿을 사용한 매칭 시작")
        matches = find_template_matches(gray, template)

        for match in matches:
            x, y = match
            w, h = template.shape[::-1]
            detected_numbers.append(num)
            positions.append((x + w//2, y + h//2))

            if is_save_debug_image:  # 디버그 이미지 저장 여부 확인
                cv2.rectangle(processed_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 사각형 표시

    print(f"검출된 숫자들: {detected_numbers}")
    return detected_numbers, positions

def find_sum_10_pairs(numbers, positions):
    """합이 10이 되는 숫자 쌍을 찾아 위치 쌍 리스트로 반환"""
    print(f"합이 10인 쌍 찾기 시작, 숫자들: {numbers}")
    pairs = []
    used = set()

    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] + numbers[j] == 10 and i not in used and j not in used:
                pairs.append((positions[i], positions[j]))
                used.add(i)
                used.add(j)

    print(f"합이 10인 쌍 찾기 완료, 총 {len(pairs)}개의 쌍 발견")
    return pairs

def perform_drag(pairs):
    """좌표 쌍을 받아서 마우스 드래그 수행"""
    print(f"마우스 드래그 시작, 드래그할 좌표 쌍: {pairs}")
    for (start, end) in pairs:
        pyautogui.moveTo(start[0], start[1])  # 시작점 이동
        pyautogui.mouseDown()  # 마우스 버튼 누름
        time.sleep(0.2)  # 자연스러운 동작을 위한 딜레이
        pyautogui.moveTo(end[0], end[1])  # 끝점으로 이동
        pyautogui.mouseUp()  # 마우스 버튼 뗌
        time.sleep(0.5)  # 다음 동작을 위한 간격
    print("마우스 드래그 완료")

class GameBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("자동 플레이 봇")

        self.capture_btn = Button(root, text="화면 캡처", command=self.capture_and_detect)
        self.capture_btn.pack()

        self.label = Label(root, text="게임 화면을 캡처하세요")
        self.label.pack()

        # 숫자 배치를 위한 Canvas (15x10 그리드)
        self.canvas = Canvas(root, width=600, height=400, bg="white")
        self.canvas.pack()

        self.play_btn = Button(root, text="자동 드래그 실행", command=self.auto_play)
        self.play_btn.pack()

        # 체크박스: 디버그 이미지 저장 여부
        self.debug_var = tk.BooleanVar()  # BooleanVar 객체 생성
        self.debug_checkbox = Checkbutton(root, text="디버그 이미지 저장", variable=self.debug_var)
        self.debug_checkbox.pack()

        self.detected_numbers = []
        self.positions = []
        self.grid_numbers = [[None for _ in range(15)] for _ in range(10)]  # 15x10 배열

    def capture_and_detect(self):
        self.label.config(text="화면 캡처 중...")
        self.root.update()

        try:
            img = capture_screen()
            self.label.config(text="빨간색 영역 추출 중...")
            self.root.update()

            red_area = extract_red_area(img)
            self.label.config(text="이미지 처리 중...")
            self.root.update()

            # 체크박스 상태 전달
            is_save_debug_image = self.debug_var.get()
        if not self.positions:
            print("위치 정보가 없습니다.")
            return

        # 화면 크기에서 셀 크기 계산 (대략적인 그리드 스케일링)
        min_x = min(pos[0] for pos in self.positions)
        max_x = max(pos[0] for pos in self.positions)
        min_y = min(pos[1] for pos in self.positions)
        max_y = max(pos[1] for pos in self.positions)

        x_spacing = (max_x - min_x) / 14  # 15칸
        y_spacing = (max_y - min_y) / 9   # 10칸

        self.grid_numbers = [[None for _ in range(15)] for _ in range(10)]  # 초기화

        for num, (x, y) in zip(self.detected_numbers, self.positions):
            grid_x = round((x - min_x) / x_spacing)
            grid_y = round((y - min_y) / y_spacing)

            if 0 <= grid_x < 15 and 0 <= grid_y < 10:


            self.detected_numbers, self.positions = process_image(red_area, is_save_debug_image)

            if self.detected_numbers:
                self.label.config(text=f"인식된 숫자: {len(self.detected_numbers)}")
                self.assign_numbers_to_grid()
                self.display_grid()
            else:
                self.label.config(text="숫자를 인식하지 못했습니다.")
        except Exception as e:
            print(f"오류 발생: {e}")
            self.label.config(text=f"오류 발생: {e}")

    def assign_numbers_to_grid(self):
        """ 숫자를 15×10 그리드에 맞게 정렬 """
        print("숫자 그리드에 배치 시작")
        self.grid_numbers[grid_y][grid_x] = num
        print("숫자 그리드에 배치 완료")

    def display_grid(self):
        """ 캔버스에 15×10 숫자 그리드 표시 """
        self.canvas.delete("all")  # 기존 내용 삭제

        cell_width = 40
        cell_height = 40

        for row in range(10):
            for col in range(15):
                x = col * cell_width + 20
                y = row * cell_height + 20
                self.canvas.create_rectangle(x-15, y-15, x+15, y+15, outline="black")  # 칸 그리기

                if self.grid_numbers[row][col] is not None:
                    self.canvas.create_text(x, y, text=str(self.grid_numbers[row][col]), font=("Arial", 14), fill="blue")

    def auto_play(self):
        self.label.config(text="자동 드래그 실행 중...")
        self.root.update()

        pairs = find_sum_10_pairs(self.detected_numbers, self.positions)
        if pairs:
            perform_drag(pairs)
            self.label.config(text="자동 플레이 완료!")
        else:
            self.label.config(text="합이 10이 되는 조합이 없음.")
        self.root.update()


if __name__ == "__main__":
    root = tk.Tk()
    app = GameBotGUI(root)
    root.mainloop()
