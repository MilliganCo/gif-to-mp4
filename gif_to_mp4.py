import math
import subprocess
import sys
from pathlib import Path
from tkinter import Tk, filedialog
from tqdm import tqdm

MIN_DURATION = 2.0  # минимум 2 секунды — короткие видео могут не открываться в WE

def get_duration(path: Path) -> float:
    """Возвращает длительность в секундах или 0 при ошибке."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        return 0.0
    try:
        return float(r.stdout.strip())
    except (ValueError, TypeError):
        return 0.0

def _build_convert_cmd(input_path: Path, output_path: Path, vf: str, extra: list) -> list:
    duration = get_duration(input_path)
    loop_extra = []
    if 0 < duration < MIN_DURATION:
        total_plays = max(2, math.ceil(MIN_DURATION / duration))
        loop_extra = ["-stream_loop", str(total_plays - 1)]
    return ["ffmpeg", "-y", *loop_extra, "-i", str(input_path), "-vf", vf, *extra, str(output_path)]


def convert_to_we_mp4(input_path: Path, output_path: Path) -> bool:
    """Конвертирует видео/гиф в MP4, совместимый с Wallpaper Engine."""
    vf = "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2"
    extra = ["-c:v", "libx264", "-profile:v", "high", "-level", "4.1",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", "-r", "30"]
    cmd = _build_convert_cmd(input_path, output_path, vf, extra)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE).returncode == 0


def convert_to_webm(input_path: Path, output_path: Path) -> bool:
    """Конвертирует в WebM (VP9). В WE иногда работает лучше MP4 — см. help.wallpaperengine.io."""
    vf = "fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2"
    extra = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv420p", "-an", "-r", "30",
             "-b:v", "0", "-crf", "35", "-deadline", "good"]
    cmd = _build_convert_cmd(input_path, output_path, vf, extra)
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE).returncode == 0


def convert_to_gif1080(input_path: Path, output_path: Path) -> bool:
    """GIF → GIF: 1080p, 60 fps, nearest-neighbor (по соседним пикселям)."""
    duration = get_duration(input_path)
    loop_extra = []
    if 0 < duration < MIN_DURATION:
        total_plays = max(2, math.ceil(MIN_DURATION / duration))
        loop_extra = ["-stream_loop", str(total_plays - 1)]
    # scale: вписать в 1920×1080, nearest-neighbor, чётные размеры; palettegen+paletteuse для 256 цветов
    filt = (
        "fps=60,"
        "scale=1920:1080:force_original_aspect_ratio=decrease:flags=neighbor,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=neighbor,"
        "split[s0][s1];[s0]palettegen=stats_mode=single[p];[s1][p]paletteuse[out]"
    )
    cmd = [
        "ffmpeg", "-y", *loop_extra, "-i", str(input_path),
        "-filter_complex", filt, "-map", "[out]", "-loop", "0",
        str(output_path)
    ]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE).returncode == 0


def convert_gif_folder(use_webm: bool = False, use_gif1080: bool = False):
    """Конвертирует GIF → MP4, WebM или GIF (1080p, 60fps)."""
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Выберите папку с GIF файлами")
    if not folder:
        return
    input_dir = Path(folder)
    if use_gif1080:
        ext, suffix, convert_fn = ".gif", "_gif1080", convert_to_gif1080
    elif use_webm:
        ext, suffix, convert_fn = ".webm", "_webm", convert_to_webm
    else:
        ext, suffix, convert_fn = ".mp4", "_mp4", convert_to_we_mp4
    output_dir = input_dir.parent / f"{input_dir.name}{suffix}"
    output_dir.mkdir(exist_ok=True)
    files = list(input_dir.glob("*.gif"))
    if not files:
        print("GIF файлы не найдены.")
        return
    fmt = "GIF 1080p 60fps" if use_gif1080 else ("WebM" if use_webm else "MP4")
    print(f"Найдено {len(files)} GIF. Конвертация в {fmt}...")
    ok, fail = 0, 0
    for f in tqdm(files):
        out = output_dir / (f.stem + ext)
        if convert_fn(f, out):
            ok += 1
        else:
            fail += 1
            print(f"  Ошибка: {f.name}")
    print(f"\nГотово: {ok} OK, {fail} ошибок. Папка: {output_dir}")
    if use_webm:
        print("  Подсказка: WE → Настройки → General → WebM framework: Prefer Native")

def reconvert_mp4_folder():
    """Переконвертирует MP4 → MP4 (режим fix)."""
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Выберите папку с MP4 файлами")
    if not folder:
        return
    input_dir = Path(folder)
    output_dir = input_dir.parent / f"{input_dir.name}_we_fixed"
    output_dir.mkdir(exist_ok=True)
    files = list(input_dir.glob("*.mp4"))
    if not files:
        print("MP4 файлы не найдены.")
        return
    print(f"Найдено {len(files)} MP4. Переконвертация...")
    ok, fail = 0, 0
    for f in tqdm(files):
        out = output_dir / (f.stem + "_we.mp4")
        if convert_to_we_mp4(f, out):
            ok += 1
        else:
            fail += 1
            print(f"  Ошибка: {f.name}")
    print(f"\nГотово: {ok} OK, {fail} ошибок. Папка: {output_dir}")

def copy_mp4_folder():
    """Копирует MP4 без перекодирования (только faststart). Рабочие файлы остаются рабочими."""
    root = Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Выберите папку с MP4 файлами")
    if not folder:
        return
    input_dir = Path(folder)
    output_dir = input_dir.parent / f"{input_dir.name}_copy"
    output_dir.mkdir(exist_ok=True)
    files = list(input_dir.glob("*.mp4"))
    if not files:
        print("MP4 файлы не найдены.")
        return
    print(f"Найдено {len(files)} MP4. Копирование (без перекодирования)...")
    ok, fail = 0, 0
    for f in tqdm(files):
        out = output_dir / f.name
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", str(f), "-c", "copy", "-movflags", "+faststart", str(out)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        if r.returncode == 0:
            ok += 1
        else:
            fail += 1
            print(f"  Ошибка: {f.name}")
    print(f"\nГотово: {ok} OK, {fail} ошибок. Папка: {output_dir}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "fix":
            reconvert_mp4_folder()
        elif sys.argv[1] == "copy":
            copy_mp4_folder()
        elif sys.argv[1] == "webm":
            convert_gif_folder(use_webm=True)
        elif sys.argv[1] == "gif1080":
            convert_gif_folder(use_gif1080=True)
        else:
            convert_gif_folder()
    else:
        convert_gif_folder()

if __name__ == "__main__":
    main()