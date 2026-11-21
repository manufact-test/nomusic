"""Generate owned 8-second sine WAVs, not service content or catalog uploads."""
import math
import struct
import wave
from pathlib import Path

root = Path(__file__).parent / "app/src/main/res/raw"
root.mkdir(parents=True, exist_ok=True)
for name, frequency in (("original", 220), ("alternate", 440)):
    with wave.open(str(root / (name + ".wav")), "wb") as output:
        output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        output.writeframes(b"".join(
            struct.pack("<h", int(1800 * math.sin(2 * math.pi * frequency * n / 16000)))
            for n in range(8 * 16000)
        ))
