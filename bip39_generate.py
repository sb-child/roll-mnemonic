import argparse
import signal

from prettytable import HRuleStyle, PrettyTable, VRuleStyle
from address import get_address
from sources import extract_all_sources
from extract import ExtractResult, extract_from_entropy_list
from mnemonic import Mnemonic
from options import ExtractAllSourcesOptions
from util import (
    handle_sig_exit,
    lock_memory,
    log_err,
    log_err_flush,
    log_out,
    log_out_flush,
    print_qr,
    wipe_memory,
)

WORD_TO_BYTES_MAP: dict[int, int] = {
    12: 16,
    15: 20,
    18: 24,
    21: 28,
    24: 32,
}


def process_extract_results(input: list[ExtractResult]) -> list[bytes]:
    el = []
    table = PrettyTable()
    table.field_names = ["Source", "Randomness", "Bytes", "Error"]
    table.align = "l"
    for res in input:
        table.add_row(
            [
                res.comment,
                "-" if res.entropy <= 0 else f"{res.entropy:.8f}",
                len(res.data),
                "-" if res.error == "" else res.error,
            ]
        )
        el.append(res.data)
    log_err("\n" + table.__repr__())
    return el


def print_mnemonic_table(mnemonic_str: str):
    words = [word.strip() for word in mnemonic_str.split() if word.strip()]
    total_words = len(words)
    valid_lengths = [12, 15, 18, 21, 24]
    assert total_words in valid_lengths
    num_cols = 3 if total_words <= 15 else 4
    num_rows = (total_words + num_cols - 1) // num_cols
    table = PrettyTable()
    table.title = f"Your {total_words}-word mnemonic phrases"
    table.header = False
    table.hrules = HRuleStyle.FRAME
    table.vrules = VRuleStyle.FRAME
    table.field_names = [f"Col{i}" for i in range(num_cols)]
    for field in table.field_names:
        table.align[field] = "l"
    for row_idx in range(num_rows):
        row_cells = []
        for col_idx in range(num_cols):
            word_idx = row_idx + col_idx * num_rows
            if word_idx < total_words:
                num_str = str(word_idx + 1).rjust(2)
                combined_cell = f"{num_str}. {words[word_idx]}"
                row_cells.append(combined_cell)
            else:
                row_cells.append("")
        table.add_row(row_cells)
    log_err(table.__repr__() + "\n")


def main(args: argparse.Namespace):
    target_bytes = WORD_TO_BYTES_MAP[args.words]
    opts = ExtractAllSourcesOptions(
        tpm_random_server_endpoint=args.tpm_random_server_endpoint
    )
    sources = extract_all_sources(opts)
    extract_res = process_extract_results(sources)
    final_entropy = extract_from_entropy_list(extract_res, target_bytes)
    mnemonic_phrase = ""
    mnemo = Mnemonic("english")
    mnemonic_phrase = mnemo.to_mnemonic(bytes(final_entropy))
    index = 0
    addresses = get_address(mnemonic_phrase, index=index)
    log_out(f"\nGenerated {args.words} words.\n")
    print_mnemonic_table(mnemonic_phrase)
    log_out(f"Or copy this: {mnemonic_phrase}\n")
    log_out(f"Ethereum (#{index}): {addresses.ethereum}")
    log_out(f"Solana   (#{index}): {addresses.solana}\n")
    log_out_flush()
    if args.qrcode:
        print_qr(mnemonic_phrase)
    log_err_flush()


if __name__ == "__main__":
    lock_memory()
    signal.signal(signal.SIGINT, handle_sig_exit)
    parser = argparse.ArgumentParser(description="BIP-39 Mnemonic phrase Generator")
    parser.add_argument(
        "-w",
        "--words",
        type=int,
        choices=[12, 15, 18, 21, 24],
        required=True,
        help="Target word count",
    )
    parser.add_argument(
        "-q",
        "--qrcode",
        action="store_true",
        required=False,
        default=False,
        help="Show a QRCode for the phrases",
    )
    parser.add_argument(
        "--tpm_random_server_endpoint",
        required=False,
        default=None,
        help="TPM Random Server Endpoint URL",
    )
    args = parser.parse_args()
    main(args)
