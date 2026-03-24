"""
Сравнение рабочего и нерабочего MP4 — выясняет, чем они отличаются.
Запуск: python compare_mp4.py
"""

import subprocess
import sys
from pathlib import Path
from tkinter import Tk, filedialog


def ffprobe_full(path: Path) -> str:
    """Полный вывод ffprobe для файла."""
    r = subprocess.run(
        ["ffprobe", "-v", "warning", "-show_streams", "-show_format",
         "-select_streams", "v:0", str(path)],
        capture_output=True
    )
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", errors="replace")
        return f"Ошибка ffprobe: {err}"
    out = (r.stdout or b"").decode("utf-8", errors="replace")
    err = (r.stderr or b"").decode("utf-8", errors="replace")
    return out + err


def get_key_params(path: Path) -> dict:
    """Извлекает ключевые параметры для сравнения."""
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_entries", "stream=codec_name,pix_fmt,width,height,r_frame_rate,avg_frame_rate,duration,nb_frames:format=duration,format_name",
         "-of", "default=noprint_wrappers=1", str(path)],
        capture_output=True
    )
    text = (r.stdout or b"").decode("utf-8", errors="replace")
    params = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            params[k.strip()] = v.strip()
    return params


def main():
    root = Tk()
    root.withdraw()

    print("Выберите РАБОЧИЙ файл (который открывается в WE, с превью):")
    working = filedialog.askopenfilename(
        title="Рабочий MP4",
        filetypes=[("MP4", "*.mp4"), ("Все", "*.*")]
    )
    if not working:
        print("Отменено.")
        return

    print("Выберите НЕРАБОЧИЙ файл (без превью, не открывается в WE):")
    broken = filedialog.askopenfilename(
        title="Нерабочий MP4",
        filetypes=[("MP4", "*.mp4"), ("Все", "*.*")]
    )
    if not broken:
        print("Отменено.")
        return

    wp = get_key_params(Path(working))
    bp = get_key_params(Path(broken))

    print("\n" + "=" * 60)
    print("СРАВНЕНИЕ ПАРАМЕТРОВ")
    print("=" * 60)
    print(f"{'Параметр':<25} {'Рабочий':<20} {'Нерабочий':<20}")
    print("-" * 60)

    all_keys = sorted(set(wp) | set(bp))
    for k in all_keys:
        wv = wp.get(k, "—")
        bv = bp.get(k, "—")
        diff = " ⚠ РАЗНИЦА" if wv != bv else ""
        print(f"{k:<25} {str(wv):<20} {str(bv):<20}{diff}")

    full_working = ffprobe_full(Path(working))
    full_broken = ffprobe_full(Path(broken))

    print("\n" + "=" * 60)
    print("ПОЛНЫЙ FFPROBE — РАБОЧИЙ")
    print("=" * 60)
    print(full_working)

    print("\n" + "=" * 60)
    print("ПОЛНЫЙ FFPROBE — НЕРАБОЧИЙ")
    print("=" * 60)
    print(full_broken)

    # Сохранить в файл для удобства
    out_file = Path(working).parent / "compare_result.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("СРАВНЕНИЕ\n")
        f.write(f"Рабочий: {working}\n")
        f.write(f"Нерабочий: {broken}\n\n")
        for k in all_keys:
            f.write(f"{k}: {wp.get(k)} vs {bp.get(k)}\n")
        f.write("\n\n--- FFPROBE РАБОЧИЙ ---\n\n")
        f.write(full_working)
        f.write("\n\n--- FFPROBE НЕРАБОЧИЙ ---\n\n")
        f.write(full_broken)
    print(f"\nРезультат сохранён в: {out_file}")


if __name__ == "__main__":
    main()
