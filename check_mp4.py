"""
Проверка MP4 файлов на совместимость с Wallpaper Engine.
Запуск: python check_mp4.py [путь_к_папке]
"""

import subprocess
import sys
from pathlib import Path
from tkinter import Tk, filedialog
from typing import List, Optional, Tuple


def check_mp4(path: Path) -> Tuple[bool, List[str]]:
    """Проверяет MP4 через ffprobe. Возвращает (ok, список проблем)."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_streams", "-select_streams", "v:0",
        "-of", "default=noprint_wrappers=1",
        str(path)
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, [f"ffprobe ошибка: {r.stderr[:200]}"]

    out = r.stdout
    problems = []

    def get(key: str) -> Optional[str]:
        for line in out.splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip()
        return None

    codec = get("codec_name")
    if codec and codec.lower() not in ("h264", "avc1"):
        problems.append(f"Кодек: {codec} (нужен h264)")

    pix_fmt = get("pix_fmt")
    if pix_fmt and pix_fmt != "yuv420p":
        problems.append(f"Пиксельный формат: {pix_fmt} (нужен yuv420p)")

    width = get("width")
    height = get("height")
    if width and height:
        w, h = int(width), int(height)
        if w % 2 or h % 2:
            problems.append(f"Разрешение {w}x{h} — должно быть кратным 2")

    r_frame = get("r_frame_rate")
    if r_frame and "/" in r_frame:
        try:
            num, den = map(int, r_frame.split("/"))
            if den and num / den < 1:
                problems.append(f"FPS очень низкий: {r_frame}")
        except (ValueError, ZeroDivisionError):
            pass

    # Проверка VFR через ffprobe с другим выводом
    r2 = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=avg_frame_rate,r_frame_rate",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True
    )
    if r2.returncode == 0 and r2.stdout.strip():
        parts = r2.stdout.strip().split(",")
        if len(parts) >= 2 and parts[0] != parts[1]:
            problems.append("Возможный VFR (variable frame rate)")

    return len(problems) == 0, problems


def main():
    if len(sys.argv) > 1:
        folder = Path(sys.argv[1])
    else:
        root = Tk()
        root.withdraw()
        folder = filedialog.askdirectory(title="Выберите папку с MP4")
        folder = Path(folder) if folder else None

    if not folder or not folder.exists():
        print("Папка не выбрана или не существует.")
        return

    files = sorted(folder.glob("*.mp4"))
    if not files:
        print("MP4 файлы не найдены.")
        return

    print(f"Проверка {len(files)} MP4 в {folder}\n")
    ok_count = 0
    for f in files:
        is_ok, problems = check_mp4(f)
        status = "OK" if is_ok else "ПРОБЛЕМЫ"
        if is_ok:
            ok_count += 1
        else:
            print(f"[{status}] {f.name}")
            for p in problems:
                print(f"    — {p}")
            print()

    print(f"Итого: {ok_count}/{len(files)} файлов совместимы с Wallpaper Engine")
    if ok_count < len(files):
        print("\nРекомендация: переконвертируйте проблемные файлы командой:")
        print("  python gif_to_mp4.py fix")


if __name__ == "__main__":
    main()
