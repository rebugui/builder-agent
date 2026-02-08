#!/usr/bin/env python3
"""
File Converter 프로젝트 생성 스크립트
"""

import os
import subprocess
import sys

# 프로젝트 경로 설정
BUILDER_DIR = "/Users/nabang/Documents/OpenClaw/modules/builder"
PROJECT_DIR = os.path.join(BUILDER_DIR, "Project", "File Converter")
PROJECT_NAME = "File Converter"
PROJECT_DESCRIPTION = """이미지, 문서 파일 형식 변환 도구.

주요 기능:
- 이미지 변환: PNG ↔ JPEG ↔ WEBP ↔ GIF
- 문서 변환: PDF ↔ Word ↔ Markdown ↔ HTML
- 대용량 파일 배치 처리
- 변환 품질/해상도 설정
- 변환 내역 저장 및 관리
- 드래그앤드롭 GUI 지원

기술 스택:
- Python 3.11+
- Pillow (이미지 처리)
- pdf2docx (PDF 변환)
- pandoc (문서 변환)
- CustomTkinter (GUI)
"""

def create_project_structure():
    """프로젝트 디렉토리 구조 생성"""

    print("=" * 80)
    print(f"🚀 {PROJECT_NAME} 프로젝트 생성")
    print("=" * 80)
    print()

    # 1. 디렉토리 생성
    print("📁 Step 1: 디렉토리 구조 생성")
    print("-" * 80)

    dirs = [
        PROJECT_DIR,
        os.path.join(PROJECT_DIR, "src"),
        os.path.join(PROJECT_DIR, "src", "converters"),
        os.path.join(PROJECT_DIR, "src", "ui"),
        os.path.join(PROJECT_DIR, "tests"),
        os.path.join(PROJECT_DIR, "docs"),
        os.path.join(PROJECT_DIR, "assets"),
    ]

    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
        print(f"  ✅ Created: {dir_path}")

    print()

    # 2. 소스 파일 생성
    print("📝 Step 2: 소스 파일 생성")
    print("-" * 80)

    # main.py
    main_py = '''#!/usr/bin/env python3
"""
File Converter - 메인 진입점
"""

import sys
import os

# src 모듈 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import run_application


def main():
    """메인 함수"""
    run_application()


if __name__ == "__main__":
    main()
'''

    with open(os.path.join(PROJECT_DIR, "src", "main.py"), "w", encoding="utf-8") as f:
        f.write(main_py)
    print("  ✅ Created: src/main.py")

    # converters/image_converter.py
    image_converter_py = '''#!/usr/bin/env python3
"""
이미지 변환기
"""

from PIL import Image
import os
from typing import Optional


class ImageConverter:
    """이미지 변환 클래스"""

    SUPPORTED_FORMATS = ["PNG", "JPEG", "WEBP", "GIF", "BMP"]

    def __init__(self, input_path: str, output_path: str, output_format: str):
        """
        초기화

        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로
            output_format: 출력 포맷 (PNG, JPEG, WEBP, GIF)
        """
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format.upper()
        self.quality = 95  # 기본 품질

    def set_quality(self, quality: int):
        """
        변환 품질 설정

        Args:
            quality: 품질 (1-100)
        """
        self.quality = max(1, min(100, quality))

    def convert(self) -> bool:
        """
        이미지 변환 실행

        Returns:
            성공 여부
        """
        try:
            # 이미지 열기
            with Image.open(self.input_path) as img:
                # RGBA 모드인 경우 JPEG로 변환 시 RGB로 변환
                if self.output_format == "JPEG" and img.mode == "RGBA":
                    # 흰색 배경 생성
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background

                # 저장 옵션
                save_kwargs = {}
                if self.output_format in ["JPEG", "WEBP"]:
                    save_kwargs["quality"] = self.quality

                # 변환 및 저장
                img.save(self.output_path, format=self.output_format, **save_kwargs)

            return True

        except Exception as e:
            print(f"변환 실패: {e}")
            return False

    @staticmethod
    def get_image_info(image_path: str) -> dict:
        """
        이미지 정보 반환

        Args:
            image_path: 이미지 파일 경로

        Returns:
            이미지 정보 딕셔너리
        """
        try:
            with Image.open(image_path) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "file_size": os.path.getsize(image_path)
                }
        except Exception as e:
            return {"error": str(e)}
'''

    with open(os.path.join(PROJECT_DIR, "src", "converters", "image_converter.py"), "w", encoding="utf-8") as f:
        f.write(image_converter_py)
    print("  ✅ Created: src/converters/image_converter.py")

    # converters/document_converter.py
    document_converter_py = '''#!/usr/bin/env python3
"""
문서 변환기
"""

import os
import subprocess
from typing import Optional


class DocumentConverter:
    """문서 변환 클래스"""

    SUPPORTED_FORMATS = ["PDF", "DOCX", "MD", "HTML", "TXT"]

    def __init__(self, input_path: str, output_path: str, output_format: str):
        """
        초기화

        Args:
            input_path: 입력 파일 경로
            output_path: 출력 파일 경로
            output_format: 출력 포맷 (PDF, DOCX, MD, HTML)
        """
        self.input_path = input_path
        self.output_path = output_path
        self.output_format = output_format.upper()

    def convert(self) -> bool:
        """
        문서 변환 실행 (pandoc 사용)

        Returns:
            성공 여부
        """
        try:
            # pandoc 명령어构建
            cmd = [
                "pandoc",
                self.input_path,
                "-o", self.output_path,
                "--standalone"
            ]

            # 변환 실행
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True
            else:
                print(f"변환 실패: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("변환 시간 초과 (60초)")
            return False
        except FileNotFoundError:
            print("pandoc이 설치되지 않았습니다.")
            return False
        except Exception as e:
            print(f"변환 실패: {e}")
            return False

    @staticmethod
    def check_pandoc_installed() -> bool:
        """
        pandoc 설치 확인

        Returns:
            설치 여부
        """
        try:
            result = subprocess.run(
                ["pandoc", "--version"],
                capture_output=True
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
'''

    with open(os.path.join(PROJECT_DIR, "src", "converters", "document_converter.py"), "w", encoding="utf-8") as f:
        f.write(document_converter_py)
    print("  ✅ Created: src/converters/document_converter.py")

    # ui/main_window.py
    main_window_py = '''#!/usr/bin/env python3
"""
메인 윈도우 (CustomTkinter)
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
from converters.image_converter import ImageConverter
from converters.document_converter import DocumentConverter


class MainWindow(ctk.CTk):
    """메인 윈도우 클래스"""

    def __init__(self):
        super().__init__()

        self.title("File Converter")
        self.geometry("800x600")

        # 변환 모드
        self.mode = ctk.StringVar(value="image")
        self.input_files = []

        # UI 생성
        self.create_widgets()

    def create_widgets(self):
        """UI 위젯 생성"""
        # 상단 프레임 (모드 선택)
        top_frame = ctk.CTkFrame(self, height=80)
        top_frame.pack(fill="x", padx=10, pady=10)

        # 모드 선택 라디오 버튼
        mode_label = ctk.CTkLabel(top_frame, text="변환 모드:", font=("Bold", 14))
        mode_label.pack(side="left", padx=10)

        ctk.CTkRadioButton(
            top_frame,
            text="이미지",
            variable=self.mode,
            value="image",
            command=self.on_mode_change
        ).pack(side="left", padx=5)

        ctk.CTkRadioButton(
            top_frame,
            text="문서",
            variable=self.mode,
            value="document",
            command=self.on_mode_change
        ).pack(side="left", padx=5)

        # 중앙 프레임 (파일 선택)
        center_frame = ctk.CTkFrame(self)
        center_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 파일 선택 버튼
        select_btn = ctk.CTkButton(
            center_frame,
            text="파일 선택",
            command=self.select_files,
            height=40
        )
        select_btn.pack(pady=20)

        # 선택된 파일 리스트
        self.file_listbox = ctk.CTkTextbox(center_frame, height=200)
        self.file_listbox.pack(fill="both", expand=True, padx=10, pady=10)

        # 하단 프레임 (변환 옵션)
        bottom_frame = ctk.CTkFrame(self, height=120)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        # 출력 포맷 선택
        format_label = ctk.CTkLabel(bottom_frame, text="출력 포맷:")
        format_label.pack(side="left", padx=10)

        self.format_var = ctk.StringVar(value="PNG")
        self.format_combo = ctk.CTkComboBox(
            bottom_frame,
            variable=self.format_var,
            values=["PNG", "JPEG", "WEBP", "GIF"],
            width=100
        )
        self.format_combo.pack(side="left", padx=5)

        # 품질 슬라이더
        quality_label = ctk.CTkLabel(bottom_frame, text="품질:")
        quality_label.pack(side="left", padx=10)

        self.quality_slider = ctk.CTkSlider(bottom_frame, from_=1, to=100, number=65)
        self.quality_slider.set(95)
        self.quality_slider.pack(side="left", padx=5)

        self.quality_label = ctk.CTkLabel(bottom_frame, text="95")
        self.quality_label.pack(side="left", padx=5)
        self.quality_slider.configure(command=self.on_quality_change)

        # 변환 버튼
        convert_btn = ctk.CTkButton(
            bottom_frame,
            text="변환 시작",
            command=self.start_conversion,
            height=40,
            width=150
        )
        convert_btn.pack(side="right", padx=10)

    def on_mode_change(self):
        """모드 변경 시"""
        mode = self.mode.get()

        if mode == "image":
            self.format_combo.configure(values=["PNG", "JPEG", "WEBP", "GIF"])
            self.format_var.set("PNG")
        else:
            self.format_combo.configure(values=["PDF", "DOCX", "MD", "HTML"])
            self.format_var.set("PDF")

    def on_quality_change(self, value):
        """품질 슬라이더 변경"""
        self.quality_label.configure(text=f"{int(value)}")

    def select_files(self):
        """파일 선택 다이얼로그"""
        mode = self.mode.get()

        if mode == "image":
            filetypes = [
                ("이미지 파일", "*.png *.jpg *.jpeg *.webp *.gif *.bmp"),
                ("모든 파일", "*.*")
            ]
        else:
            filetypes = [
                ("문서 파일", "*.pdf *.docx *.md *.html *.txt"),
                ("모든 파일", "*.*")
            ]

        files = filedialog.askopenfilenames(filetypes=filetypes)

        if files:
            self.input_files = list(files)
            self.update_file_list()

    def update_file_list(self):
        """파일 리스트 업데이트"""
        self.file_listbox.delete("1.0", "end")

        for i, file_path in enumerate(self.input_files, 1):
            filename = os.path.basename(file_path)
            self.file_listbox.insert("end", f"{i}. {filename}\\n")

    def start_conversion(self):
        """변환 시작"""
        if not self.input_files:
            messagebox.showwarning("경고", "파일을 선택해주세요.")
            return

        # 저장 디렉토리 선택
        output_dir = filedialog.askdirectory(title="저장할 폴더 선택")

        if not output_dir:
            return

        output_format = self.format_var.get()
        quality = int(self.quality_slider.get())

        # 변환 실행
        success_count = 0
        fail_count = 0

        for input_path in self.input_files:
            filename = os.path.basename(input_path)
            name_without_ext = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{name_without_ext}.{output_format.lower()}")

            mode = self.mode.get()

            if mode == "image":
                converter = ImageConverter(input_path, output_path, output_format)
                converter.set_quality(quality)
            else:
                converter = DocumentConverter(input_path, output_path, output_format)

            if converter.convert():
                success_count += 1
            else:
                fail_count += 1

        # 결과 메시지
        messagebox.showinfo(
            "변환 완료",
            f"성공: {success_count}개\\n실패: {fail_count}개"
        )


def run_application():
    """애플리케이션 실행"""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    run_application()
'''

    with open(os.path.join(PROJECT_DIR, "src", "ui", "main_window.py"), "w", encoding="utf-8") as f:
        f.write(main_window_py)
    print("  ✅ Created: src/ui/main_window.py")

    print()

    # 3. 설정 파일 생성
    print("⚙️  Step 3: 설정 파일 생성")
    print("-" * 80)

    # requirements.txt
    requirements_txt = '''# File Converter Requirements

# GUI
customtkinter>=5.2.0

# 이미지 처리
Pillow>=10.0.0

# 문서 변환
pdf2docx>=0.5.6
pandoc>=2.3  # pandoc 시스템 설치 필요
'''

    with open(os.path.join(PROJECT_DIR, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write(requirements_txt)
    print("  ✅ Created: requirements.txt")

    # .gitignore
    gitignore = '''__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
.env
.DS_Store
*.log
'''

    with open(os.path.join(PROJECT_DIR, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(gitignore)
    print("  ✅ Created: .gitignore")

    # README.md
    readme_md = f'''# {PROJECT_NAME}

{PROJECT_DESCRIPTION}

## 설치

```bash
# Python 3.11+ 설치 확인
python --version

# 가상 환경 생성 (권장)
python -m venv venv

# 가상 환경 활성화
# macOS/Linux
source venv/bin/activate
# Windows
venv\\Scripts\\activate

# 의존성 설치
pip install -r requirements.txt

# pandoc 설치 (문서 변환용)
# macOS
brew install pandoc
# Ubuntu/Debian
sudo apt-get install pandoc
# Windows
# https://pandoc.org/installing.html
```

## 사용법

```bash
cd {PROJECT_DIR}
python src/main.py
```

## 기능

- 이미지 변환: PNG ↔ JPEG ↔ WEBP ↔ GIF
- 문서 변환: PDF ↔ Word ↔ Markdown ↔ HTML
- 대용량 파일 배치 처리
- 변환 품질/해상도 설정
- 드래그앤드롭 GUI

## 라이선스

MIT License
'''

    with open(os.path.join(PROJECT_DIR, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_md)
    print("  ✅ Created: README.md")

    print()

    # 4. 완료 메시지
    print("=" * 80)
    print("✅ 프로젝트 생성 완료!")
    print("=" * 80)
    print()
    print(f"📁 프로젝트 경로: {PROJECT_DIR}")
    print()
    print("📋 다음 단계:")
    print("   1. cd \"" + PROJECT_DIR + "\"")
    print("   2. python -m venv venv")
    print("   3. source venv/bin/activate  # macOS/Linux")
    print("   4. pip install -r requirements.txt")
    print("   5. python src/main.py")
    print()


if __name__ == "__main__":
    create_project_structure()
