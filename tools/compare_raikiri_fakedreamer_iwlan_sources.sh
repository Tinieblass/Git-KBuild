#!/usr/bin/env bash
set -euo pipefail
# This script only reads the two pinned source trees and writes comparison reports.

ROOT="${GITHUB_WORKSPACE:-$PWD}"
OUT="$ROOT/ims-network-source-diff"
WORK="$ROOT/.ims-network-source-diff-work"
RAIKIRI_REPO="https://github.com/Sayemx18/kernel_xiaomi_sm8250.git"
FAKEDREAMER_REPO="https://github.com/re-noroi/kernel_sm8250.git"
RAIKIRI_SHA="4d8105023e3d1474323f4118abc3b4ce6485070d"
FAKEDREAMER_SHA="afba74c277a858f7ee46463f5ff6b7bfbdb6546a"

rm -rf "$OUT" "$WORK"
mkdir -p "$OUT" "$WORK"

checkout_exact() {
  local name="$1" url="$2" sha="$3" dir="$WORK/$name"
  mkdir -p "$dir"
  git -C "$dir" init -q
  git -C "$dir" remote add origin "$url"
  git -C "$dir" fetch --filter=blob:none --depth=1 origin "$sha"
  git -C "$dir" checkout -q --detach FETCH_HEAD
  test "$(git -C "$dir" rev-parse HEAD)" = "$sha"
}

checkout_exact raikiri "$RAIKIRI_REPO" "$RAIKIRI_SHA"
checkout_exact fakedreamer "$FAKEDREAMER_REPO" "$FAKEDREAMER_SHA"

cat > "$OUT/PROVENANCE.txt" <<EOF
Raikiri source repository: $RAIKIRI_REPO
Raikiri exact commit: $RAIKIRI_SHA
FakeDreamer source repository: $FAKEDREAMER_REPO
FakeDreamer exact commit: $FAKEDREAMER_SHA
Comparison is read-only; neither source checkout is modified.
EOF

export RA_ROOT="$WORK/raikiri" FD_ROOT="$WORK/fakedreamer" OUT
python3 - <<'PY'
from pathlib import Path
import hashlib, os, re

ra = Path(os.environ["RA_ROOT"])
fd = Path(os.environ["FD_ROOT"])
out = Path(os.environ["OUT"])
scopes = [
    "net/xfrm", "net/ipv4", "net/ipv6", "net/core", "net/netlink",
    "net/netfilter", "drivers/net/ipa", "drivers/net/rmnet",
    "drivers/net/wireless", "drivers/net/qrtr", "drivers/net/wwan",
    "drivers/soc/qcom",
]
source_suffixes = {".c", ".h", ".S", ".s", ".inc", ".lds", ".dtsi", ".dts", ".Kconfig"}
interesting = re.compile(
    r"(xfrm|ipsec|esp|ah4|ah6|udp|inet|route|rtnetlink|netlink|skb|socket|sock|"
    r"ipa|rmnet|qrtr|qmi|cnss|wlan|wireless|eap|ike|tunnel|ip6|ip4)",
    re.I,
)
def digest(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()
def files(root):
    found={}
    for scope in scopes:
        base=root/scope
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in source_suffixes:
                continue
            rel=p.relative_to(root).as_posix()
            if p.stat().st_size > 4*1024*1024:
                continue
            found[rel]=(p.stat().st_size,digest(p))
    # Include selected cross-cutting public headers used by networking/IPsec.
    for base_name in ("include/net","include/linux","include/uapi/linux"):
        base=root/base_name
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix not in source_suffixes or not interesting.search(p.name):
                continue
            if p.stat().st_size > 2*1024*1024:
                continue
            rel=p.relative_to(root).as_posix()
            found[rel]=(p.stat().st_size,digest(p))
    return found
ra_files=files(ra)
fd_files=files(fd)
rows=[]
for rel in sorted(set(ra_files)|set(fd_files)):
    a=ra_files.get(rel); b=fd_files.get(rel)
    if a==b:
        continue
    status="M" if a and b else ("A" if b else "D")
    rows.append((status,rel,a,b))
with (out/"NETWORK-SOURCE-DIFF.tsv").open("w") as f:
    f.write("status\tpath\traikiri_bytes\traikiri_sha256\tfakedreamer_bytes\tfakedreamer_sha256\n")
    for status,rel,a,b in rows:
        f.write("\t".join([status,rel,str(a[0]) if a else "",a[1] if a else "",
                            str(b[0]) if b else "",b[1] if b else ""])+"\n")
groups={}
for status,rel,a,b in rows:
    top=rel.split("/",2)
    group="/".join(top[:2]) if len(top)>1 else top[0]
    groups[group]=groups.get(group,0)+1
with (out/"SUMMARY.md").open("w") as f:
    f.write("# Raikiri vs FakeDreamer network / IWLAN source comparison\n\n")
    f.write(f"- Raikiri source files in scope: {len(ra_files)}\n")
    f.write(f"- FakeDreamer source files in scope: {len(fd_files)}\n")
    f.write(f"- Different / one-sided files: {len(rows)}\n\n")
    f.write("## Differences by source area\n\n")
    f.write("| Area | Different files |\n|---|---:|\n")
    for group,count in sorted(groups.items()):
        f.write(f"| `{group}` | {count} |\n")
    f.write("\n## Highest-priority changed paths\n\n")
    priority=[r for r in rows if interesting.search(r[1])]
    for status,rel,a,b in priority[:300]:
        f.write(f"- **{status}** `{rel}`\n")
    f.write("\nThe TSV is the complete scoped manifest. A source file being different does not by itself establish causation.\n")
PY

# Generate source diffs for changed, high-priority text files. Keep binary files out.
python3 - <<'PY'
from pathlib import Path
import os, re, subprocess
ra=Path(os.environ["RA_ROOT"]); fd=Path(os.environ["FD_ROOT"]); out=Path(os.environ["OUT"])
rows=(out/"NETWORK-SOURCE-DIFF.tsv").read_text().splitlines()[1:]
pat=re.compile(r"(xfrm|ipsec|esp|ah4|ah6|udp|inet|route|rtnetlink|netlink|skb|socket|sock|ipa|rmnet|qrtr|qmi|cnss|wlan|wireless|eap|ike|tunnel)",re.I)
selected=[]
for line in rows:
    fields=line.split("\t")
    status,rel=fields[0],fields[1]
    if pat.search(rel) and status=="M":
        a=ra/rel; b=fd/rel
        if a.is_file() and b.is_file() and a.stat().st_size<512*1024 and b.stat().st_size<512*1024:
            selected.append(rel)
patch=out/"PRIORITY-SOURCE-DIFF.patch"
with patch.open("w") as f:
    for rel in selected[:600]:
        proc=subprocess.run(["diff","-u","--label",f"Raikiri/{rel}","--label",f"FakeDreamer/{rel}",str(ra/rel),str(fd/rel)],
                            text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if proc.stdout:
            f.write(proc.stdout)
            if not proc.stdout.endswith("\n"): f.write("\n")
(out/"PRIORITY-PATCH-MANIFEST.txt").write_text(
    f"Changed matching text files selected: {len(selected)}\n"
    f"Patch includes first {min(len(selected),600)} files below 512 KiB each.\n"
)
PY

(
  cd "$OUT"
  sha256sum PROVENANCE.txt SUMMARY.md NETWORK-SOURCE-DIFF.tsv PRIORITY-SOURCE-DIFF.patch PRIORITY-PATCH-MANIFEST.txt > SHA256SUMS.txt
)
echo "Network/IWLAN source comparison complete: $OUT"
