"""
scripts/generate_pwa_icons.py
=============================
纯标准库生成 TRINITY QUANT 工业级高清 PWA App 图标 (192x192 & 512x512)。
零依赖，基于 zlib + struct 规范生成标准 RGBA PNG 文件。
"""
import math
import os
import struct
import zlib


def write_png(filename: str, width: int, height: int, rgba_data: bytes) -> None:
    def chunk(chunk_type: bytes, data: bytes) -> bytes:
        content = chunk_type + data
        crc = zlib.crc32(content) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + content + struct.pack(">I", crc)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ihdr = chunk(b"IHDR", ihdr_data)

    raw_lines = bytearray()
    row_bytes = width * 4
    for y in range(height):
        raw_lines.append(0)
        raw_lines.extend(rgba_data[y * row_bytes : (y + 1) * row_bytes])

    compressed = zlib.compress(bytes(raw_lines), level=9)
    idat = chunk(b"IDAT", compressed)
    iend = chunk(b"IEND", b"")

    with open(filename, "wb") as fp:
        fp.write(header + ihdr + idat + iend)


def generate_icon(size: int, output_path: str) -> None:
    buf = bytearray(size * size * 4)
    center = (size - 1) / 2.0
    radius = size * 0.44
    inner_radius = size * 0.30

    for y in range(size):
        for x in range(size):
            dx = x - center
            dy = y - center
            dist = math.hypot(dx, dy)
            idx = (y * size + x) * 4

            ratio_y = y / size
            bg_r = int(3 + ratio_y * 8)
            bg_g = int(8 + ratio_y * 12)
            bg_b = int(22 + ratio_y * 18)

            ring_dist = abs(dist - radius * 0.78)
            if ring_dist < size * 0.045:
                factor = 1.0 - (ring_dist / (size * 0.045))
                r = int(bg_r * (1 - factor) + 6 * factor)
                g = int(bg_g * (1 - factor) + 182 * factor)
                b = int(bg_b * (1 - factor) + 212 * factor)
            elif dist < inner_radius:
                core_factor = 1.0 - (dist / inner_radius)
                r = int(bg_r * (1 - core_factor) + 16 * core_factor)
                g = int(bg_g * (1 - core_factor) + 220 * core_factor)
                b = int(bg_b * (1 - core_factor) + 180 * core_factor)
            else:
                r, g, b = bg_r, bg_g, bg_b

            if abs(dx) < size * 0.035 and abs(dy) < size * 0.20:
                r, g, b = 240, 253, 250
            elif abs(dy) < size * 0.035 and abs(dx) < size * 0.16:
                r, g, b = 240, 253, 250

            buf[idx] = max(0, min(255, r))
            buf[idx + 1] = max(0, min(255, g))
            buf[idx + 2] = max(0, min(255, b))
            buf[idx + 3] = 255

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    write_png(output_path, size, size, bytes(buf))


def main() -> None:
    root = "/Volumes/tianyou-168/顶级量化"
    generate_icon(192, os.path.join(root, "data", "icon-192.png"))
    generate_icon(512, os.path.join(root, "data", "icon-512.png"))
    print("PWA 高清图标生成完成: data/icon-192.png, data/icon-512.png")


if __name__ == "__main__":
    main()
