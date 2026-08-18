import argparse
import signal
from address import get_address
from util import (
    handle_sig_exit,
    lock_memory,
    log_out,
    log_out_flush,
)


def main(args: argparse.Namespace):
    mnemonic_phrase = input("Input mnemonic phrase:\n").strip()
    passphrase = input("Input passphrase:\n").strip()
    try:
        index = int(args.account)
        log_out("\nCalculating...\n")
        addresses = get_address(mnemonic_phrase, index, passphrase)
        log_out(f"Ethereum (#{index}): {addresses.ethereum}")
        log_out(f"Solana   (#{index}): {addresses.solana}\n")
        log_out_flush()
    finally:
        del passphrase
        del mnemonic_phrase


if __name__ == "__main__":
    lock_memory()
    signal.signal(signal.SIGINT, handle_sig_exit)
    parser = argparse.ArgumentParser(description="BIP-39 Mnemonic phrase Verifier")
    parser.add_argument(
        "-a",
        "--account",
        type=int,
        choices=range(2147483648),
        metavar="0..=2147483647",
        required=False,
        default=0,
        help="Account ID",
    )
    args = parser.parse_args()
    main(args)
