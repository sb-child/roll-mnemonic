# Roll Mnemonic

Let you control the entropy. Noises come from anywhere.

```py
# entropy_source.py
def extract_all_sources( ... ):
    # unavailable source just got skipped at runtime, and leave a notice on terminal.
    sources = {
        "journalctl": Action("journalctl -b 0 --no-pager"),
        "dnf-history": Action("dnf history list"),
        "systemctl-status": Action("systemctl status --no-pager"),
        "systemd-blame": Action("systemd-analyze blame"),
        "top-snapshot": Action("top -b -c -n 1"),
        "lsusb": Action("lsusb -vvv"),
        "lspci": Action("lspci -vvv"),
        "lscpu-info": Action("lscpu -y -J"),
        "lscpu-freq": Action("lscpu -y -J -e"),
        "time-sleep": time_sleep,
        "urandom": urandom,
        "mousemove": mouse_move,
        "tpm-random": tpm_random,
        "camera-entropy": camera_entropy,
        "sound": sound_entropy,
    }
    # ...
```

## Get Started

Currently only support Linux. It runs well on my python 3.14.6 environment.

```bash
git clone https://github.com/sb-child/roll-mnemonic.git
cd roll-mnemonic
uv sync
```

And you are ready to run scripts below.

## Features and How to use

**Generates and verify BIP-39 mnemonic phrases.**

1. Start `tpm_random_server.py` if your computer has a TPM2 device. It has a TRNG to produce random numbers.

If you don't have a tpm2 module, that's ok. no need to start server or set other thing, this entropy source will automatically skipped.

You can change the listen port to anyone else.

```bash
sudo uv run tpm_random_server.py -p 7900

# INFO:     Started server process [86230]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:7900 (Press CTRL+C to quit)
```

2. Open another terminal, generate our mnemonic phrases:

```bash
uv run bip39_generate.py -w 24
# or you want another word length... pass --help to get more info
uv run bip39_generate.py -w 12
# or you want to specify `tpm_random_server.py` endpoint. Notice that network data may leaks due to insecure setup.
uv run bip39_generate.py --tpm_random_server_endpoint="http://10.22.22.33:4444/get_tpm_random" -w 24

# lock_memory: setrlimit Success
# lock_memory: mlockall Failed: -1, errno=12
# [sound-entropy] Start Recording for 10.0 secs.
# [camera-entropy] Starting grab frames.
# [mouse-move] Please move you mouse randomly for 10 secs. I'm recording your activity to produce entropy.
# [mouse-move]: 100%|████████████████████| 10/10 [00:10<00:00,  1.09s/s, devices=5, events=9818]
# [mouse-move] Got 9818 events, 157157 bytes.
# [sound-entropy] Record completed, processing data...
# [sound-entropy] Data process completed, 3528000 bytes.
# [camera-entropy] Grabbed 100/100 frames, processing data...
# [camera-entropy] Data process completed.
# ... Entropy table
# Generated 24 words.
# ... Mnemonic phrases table
# Or copy this: soul moral away volume guide chuckle consider foil option razor effort december core spell review scrap neutral protect style slice easy voice potato prepare
# 
# Ethereum (#0): 0x5AcA01cBFBBE4964A50eD938b9AB5276Cba70c98
# Solana   (#0): 7PStF2BgThNyTnpYx9s6jsbveANaS8EsWVFDdFumyTxA
```

if you meet `mlockall Failed: -1, errno=12`, that means your account don't have much permission to lock a huge of memory. if you are a nerd, you can `sudo uv run ...` to enable memory locking, prevent program's memory moves to swap space.

3. You made a copy to somewhere. when you find it again, you can verify it:

```bash
uv run bip39_verify.py

# lock_memory: setrlimit Success
# lock_memory: mlockall Failed: -1, errno=12
# Input mnemonic phrase:
```

Input mnemonic phrase in the terminal then press enter:

```bash
# soul moral away volume guide chuckle consider foil option razor effort december core spell review scrap neutral protect style slice easy voice potato prepare
# Input passphrase:
```

Input passphrase in the terminal then press enter. if you don't have it or don't know wtf it is. just press enter to skip:

```bash
# Calculating...
# 
# Ethereum (#0): 0x5AcA01cBFBBE4964A50eD938b9AB5276Cba70c98
# Solana   (#0): 7PStF2BgThNyTnpYx9s6jsbveANaS8EsWVFDdFumyTxA
```

4. Compare results. if addresses are match, then your mnemonic phrase is correct.

## License

MIT. Check LICENSE file

