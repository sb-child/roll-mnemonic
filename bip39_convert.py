import base58
import base64
import re
from mnemonic import Mnemonic
from util import log_err, log_out


BYTES_TO_WORD_MAP: dict[int, int] = {
    16: 12,
    20: 15,
    24: 18,
    28: 21,
    32: 24,
}


def parse_to_bytes(s: str) -> bytes | None:
    if not isinstance(s, str):
        return None
    s_clean = s.strip()
    if not s_clean:
        return None
    try:
        hex_str = s_clean[2:] if s_clean.lower().startswith("0x") else s_clean
        if re.fullmatch(r"[0-9a-fA-F]+", hex_str) and len(hex_str) % 2 == 0:
            result = bytes.fromhex(hex_str)
            if result:
                return result
    except ValueError:
        pass
    try:
        if re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]+", s_clean):
            result = base58.b58decode(s_clean)
            if result:
                return result
    except ValueError:
        pass
    normalized_b64 = s_clean.replace("-", "+").replace("_", "/")
    missing_padding = len(normalized_b64) % 4
    if missing_padding:
        normalized_b64 += "=" * (4 - missing_padding)
    b64_decoders = [
        lambda src: base64.b64decode(src, validate=True),
        lambda src: base64.b64decode(src, validate=False),
        lambda src: base64.urlsafe_b64decode(src),
    ]
    for decoder in b64_decoders:
        try:
            result = decoder(normalized_b64)
            if result:
                return result
        except Exception:
            continue
    return None


def main():
    data = input("Input data:\n").strip()
    data = parse_to_bytes(data)
    if data is None:
        log_err("\nDecode failed.")
        return
    mnemo = Mnemonic("english")
    try:
        mnemonic_phrase = mnemo.to_mnemonic(data)
    except ValueError as e:
        log_err(f"\nDecode failed: {e}.")
        return
    words = BYTES_TO_WORD_MAP[len(data)]
    log_out(f"\nWord count: {words}")
    log_out(f"Phrase: [{mnemonic_phrase}]")


if __name__ == "__main__":
    main()
