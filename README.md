# raspberry pi boot-chain capture

i got ragebaited by a tiktok into platform security research so here we go...

this is a small, readonly toolkit to capture and analyze raspberry pi boot-chain artifacts. should grab SD image, boot partition blobs)
this should produce reproducible, human readable reports. but then again i am writing this out of rage at 1 in the morning so fingers crossed, gang. 

## Quickstart (Arch Linux)
i'm on arch because i'm an idiot.

```bash
git clone <this-repo>
cd pi-forensics
pip install -e .
# collect artifacts (run as a normal user; script will require sudo for imaging/mount, installing my backdoor, etc)
scripts/collect_artifacts.sh
# summarize and render reports
# theres no way i am sticking with these names
pi-forensics summarize --root output/<ts>
pi-forensics report --root output/<ts> --format md
```

*not even close to being done, i dont even have the folder structure right. seriously, how are you reading this?*
