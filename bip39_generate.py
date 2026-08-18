import argparse
import signal
from address import get_address
from entropy_source import extract_all_sources
from extract import extract_from_entropy_list
from mnemonic import Mnemonic
from options import ExtractAllSourcesOptions
from util import (
    handle_sig_exit,
    lock_memory,
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


def main(args: argparse.Namespace):
    target_bytes = WORD_TO_BYTES_MAP[args.words]
    opts = ExtractAllSourcesOptions(
        tpm_random_server_endpoint=args.tpm_random_server_endpoint
    )
    final_entropy = extract_from_entropy_list(extract_all_sources(opts), target_bytes)
    mnemonic_phrase = ""
    try:
        mnemo = Mnemonic("english")
        mnemonic_phrase = mnemo.to_mnemonic(bytes(final_entropy))
        index = 0
        addresses = get_address(mnemonic_phrase, index=index)
        log_out(f"\n\nGenerated {args.words} words.")
        log_out(f"Mnemonic: {mnemonic_phrase}\n")
        log_out(f"Ethereum (#{index}): {addresses.ethereum}")
        log_out(f"Solana   (#{index}): {addresses.solana}\n")
        log_out_flush()
        if args.qrcode:
            print_qr(mnemonic_phrase)
        log_err_flush()
    finally:
        wipe_memory(final_entropy)
        del mnemonic_phrase


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
