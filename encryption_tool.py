#!/usr/bin/env python3
"""
Simple pixel-manipulation image encryptor/decryptor.

Supports two reversible modes:
 - swap : permutes pixels using a PRNG seeded from a passphrase.
 - xor  : XOR each channel byte with a keystream derived from a passphrase.
"""
import argparse
import sys
from PIL import Image
import hashlib
import random

def derive_seed_from_key(key: str) -> int:
    h = hashlib.sha256(key.encode('utf-8')).digest()
    return int.from_bytes(h[:8], 'big')

def keystream_bytes(key: str, length: int) -> bytes:
    out = bytearray()
    state = hashlib.sha256(key.encode('utf-8')).digest()
    while len(out) < length:
        state = hashlib.sha256(state).digest()
        out.extend(state)
    return bytes(out[:length])

def mode_xor(img: Image.Image, key: str) -> Image.Image:
    mode = img.mode
    data = bytearray(img.tobytes())
    ks = keystream_bytes(key, len(data))
    for i in range(len(data)):
        data[i] ^= ks[i]
    return Image.frombytes(mode, img.size, bytes(data))

def mode_swap(img: Image.Image, key: str) -> Image.Image:
    w, h = img.size
    pixels = list(img.getdata())
    n = len(pixels)
    seed = derive_seed_from_key(key)
    rnd = random.Random(seed)
    indices = list(range(n))
    rnd.shuffle(indices)
    permuted = [pixels[i] for i in indices]
    out = Image.new(img.mode, img.size)
    out.putdata(permuted)
    return out

def invert_swap(img: Image.Image, key: str) -> Image.Image:
    w, h = img.size
    pixels = list(img.getdata())
    n = len(pixels)
    seed = derive_seed_from_key(key)
    rnd = random.Random(seed)
    indices = list(range(n))
    rnd.shuffle(indices)
    orig = [None] * n
    for i in range(n):
        orig[indices[i]] = pixels[i]
    out = Image.new(img.mode, img.size)
    out.putdata(orig)
    return out

def load_image(path):
    try:
        img = Image.open(path)
        return img.convert('RGBA')
    except Exception as e:
        print("Failed to open image:", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Pixel image encryptor/decryptor")
    parser.add_argument('operation', choices=['encrypt', 'decrypt'])
    parser.add_argument('input', help='Input image file (png/jpg)')
    parser.add_argument('output', help='Output image file')
    parser.add_argument('--mode', choices=['swap', 'xor'], default='swap')
    parser.add_argument('--key', required=True, help='Passphrase key')
    args = parser.parse_args()

    img = load_image(args.input)

    if args.mode == 'xor':
        out = mode_xor(img, args.key)
    else:
        out = mode_swap(img, args.key) if args.operation == 'encrypt' else invert_swap(img, args.key)

    out.save(args.output)
    print(f"{args.operation.capitalize()} complete → {args.output}")

if __name__ == '__main__':
    main()
