
<p align="center">
  <img src="logos/logo.png" width="180" alt="Project Logo">
</p>


# PiBootCheck

a read only toolkit that grabs the boot-chain off a Raspberry Pi and proves whether it’s running the official firmware or some mystery binary

## what it actually does

- images the sd card **read-only** so nothing gets touched
- extracts the `/boot` partition and copies the boot blobs (`bootcode.bin`, `start.elf`, `fixup*.dat`)
- runs `strings` and `binwalk` on them for a quick look inside
- computes sha256 hashes for everything
- compares those hashes against the **known good** ones from the official Raspberry Pi firmware repo
- spits out a human readable report that says “matches official firmware” or “something’s off”

that’s it. no drivers, no kernel hooks

## why it matters

if your boot firmware matches the public release **bit for bit**, it’s the same binary everyone else gets.  
no hidden code, no secret phone-home instructions. any change would flip the hash.  
this doesn’t prove the kernel or userland are clean just that the firmware that _starts_ the Pi doesn't have any surprises

## quickstart

if you're on arch you can install it from AUR

`yay -S pibootcheck`

or build it yourself
```bash
# requirements and virtual environment setup
sudo pacman -S binwalk multipath-tools p7zip dosfstools wireshark-cli picocom
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
```

once built grab a hash from the official boot files 
```
git clone --depth=1 https://github.com/raspberrypi/firmware.git
scripts/update_baseline_from_dir.sh firmware/boot \
  --source "Raspberry Pi Firmware GitHub (latest)" \
  --output data/known_hashes/raspi_boot_sha256.json
```

then image your SD card
```
sudo scripts/collect_artifacts.sh
```

finally, generate the report
```
pibootcheck summarize --root output/<timestamp>
pibootcheck report --root output/<timestamp> --format md
```

the report lives under `output/<timestamp>/reports/`. open it, scroll down to “baseline comparison,” and you’ll see every boot file marked _match_, _mismatch_, or _unknown_.

## what you’ll see

**match** → byte-for-byte official  
**mismatch** → probably just a newer firmware, but check  
**unknown** → file not in baseline (add it if it’s official)

if everything’s green, congrats your Pi isn’t running some secret firmware

## safety notes

- everything is read-only; imaging uses `dd if=…`, mounts are read-only loops.
- nothing writes back to the card.
- requires `sudo` for the imaging part because linux is picky about block devices.
- not a platform security researcher, feel free to tell me everything i did wrong


