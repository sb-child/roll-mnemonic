from dataclasses import dataclass
import hashlib
import hmac
from Crypto.Hash import keccak
import base58
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from mnemonic import Mnemonic


@dataclass
class WalletAddress:
    ethereum: str
    solana: str


def keccak256(data: bytes) -> bytes:
    k = keccak.new(digest_bits=256)
    k.update(data)
    return k.digest()


def to_checksum_address(address_hex: str) -> str:
    address_hex = address_hex.lower().replace("0x", "")
    address_hash = keccak256(address_hex.encode("ascii")).hex()
    checksum_address = "0x"
    for i, char in enumerate(address_hex):
        if char in "0123456789":
            checksum_address += char
        else:
            if int(address_hash[i], 16) >= 8:
                checksum_address += char.upper()
            else:
                checksum_address += char.lower()
    return checksum_address


def bip32_master_key(seed: bytes) -> tuple[int, bytes]:
    h = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    secret_key = int.from_bytes(h[:32], "big")  # very long int
    chain_code = h[32:]
    return secret_key, chain_code


def bip32_ckd_priv(
    parent_key: int, parent_chain: bytes, index: int
) -> tuple[int, bytes]:
    if index >= 0x80000000:
        data = b"\x00" + parent_key.to_bytes(32, "big") + index.to_bytes(4, "big")
    else:
        priv_obj = ec.derive_private_key(parent_key, ec.SECP256K1())
        pub_bytes = priv_obj.public_key().public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint,
        )
        data = pub_bytes + index.to_bytes(4, "big")
    h = hmac.new(parent_chain, data, hashlib.sha512).digest()
    il = int.from_bytes(h[:32], "big")  # very long int
    ir = h[32:]
    SECP256K1_ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    child_key = (il + parent_key) % SECP256K1_ORDER
    return child_key, ir


def derive_ethereum_address(seed: bytes, index: int = 0) -> str:
    key, chain = bip32_master_key(seed)
    # BIP-44: m/44'/60'/0'/0/index
    for idx in [
        44 | 0x80000000,
        60 | 0x80000000,
        0 | 0x80000000,
        0,
        index,
    ]:
        key, chain = bip32_ckd_priv(key, chain, idx)
    priv_obj = ec.derive_private_key(key, ec.SECP256K1())
    uncompressed_pub = priv_obj.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )[1:]
    return to_checksum_address(keccak256(uncompressed_pub)[-20:].hex())


def derive_solana_address(seed: bytes, index: int = 0) -> str:
    # SLIP-0010 Ed25519 derive
    h = hmac.new(b"ed25519 seed", seed, hashlib.sha512).digest()
    key, chain = h[:32], h[32:]
    # BIP-44: m/44'/501'/index'/ 0'
    path = [
        44 | 0x80000000,
        501 | 0x80000000,
        index | 0x80000000,
        0 | 0x80000000,
    ]
    for idx in path:
        data = b"\x00" + key + idx.to_bytes(4, "big")
        h = hmac.new(chain, data, hashlib.sha512).digest()
        key, chain = h[:32], h[32:]
    priv_key = ed25519.Ed25519PrivateKey.from_private_bytes(key)
    pub_bytes = priv_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base58.b58encode(pub_bytes).decode("ascii")


def get_address(
    mnemonic_phrase: str, index: int = 0, passphrase: str = ""
) -> WalletAddress:
    mnemo = Mnemonic("english")
    if not mnemo.check(mnemonic_phrase):
        raise ValueError("Invalid mnemonic phrase: Checksum or wordlist failed.")
    seed = mnemo.to_seed(mnemonic_phrase, passphrase=passphrase)
    eth_address = derive_ethereum_address(seed, index=index)
    sol_address = derive_solana_address(seed, index=index)
    return WalletAddress(ethereum=eth_address, solana=sol_address)
