#!/usr/bin/env bash
set -euo pipefail

ROM_NAME="surya_global_images_V12.5.8.0.RJGMIXM_20220524.0000.00_11.0_global_e2a45f1e0f.tgz"
ROM_URL="https://bigota.d.miui.com/V12.5.8.0.RJGMIXM/${ROM_NAME}"
EXPECTED_MD5="e2a45f1e0fb395852e17814a878852c0"
OUT="${1:-surya-firmware-audit}"
mkdir -p "$OUT/images" "$OUT/mounts"
REPORT="$OUT/SURYA-FIRMWARE-AUDIT.txt"

echo "POCO X3 NFC surya — official fastboot ROM audit" | tee "$REPORT"
echo "Package: $ROM_NAME" | tee -a "$REPORT"
echo "Source: $ROM_URL" | tee -a "$REPORT"
echo "Expected MD5: $EXPECTED_MD5" | tee -a "$REPORT"

if [[ ! -s "$OUT/$ROM_NAME" ]]; then
  curl --fail --location --retry 5 --retry-all-errors --connect-timeout 30 \
    --output "$OUT/$ROM_NAME" "$ROM_URL"
fi

ACTUAL_MD5="$(md5sum "$OUT/$ROM_NAME" | awk '{print $1}')"
echo "Actual MD5: $ACTUAL_MD5" | tee -a "$REPORT"
if [[ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]]; then
  echo "ERROR: MD5 mismatch; refusing to inspect an unverified archive." | tee -a "$REPORT"
  exit 2
fi

tar -tzf "$OUT/$ROM_NAME" > "$OUT/archive-members.txt"
grep -Ei '(^|/)(boot|vendor|odm|dtbo|system|system_ext|product|cust|super|vbmeta).*([.]img)$' \
  "$OUT/archive-members.txt" > "$OUT/image-members.txt" || true

echo | tee -a "$REPORT"
echo "=== Archive image members ===" | tee -a "$REPORT"
cat "$OUT/image-members.txt" | tee -a "$REPORT"

# Extract all selected partition images in one archive pass.
if [[ -s "$OUT/image-members.txt" ]]; then
  tar -xzf "$OUT/$ROM_NAME" -C "$OUT/images" -T "$OUT/image-members.txt"
fi

while IFS= read -r image; do
  [[ -n "$image" ]] || continue
  extracted="$OUT/images/$image"
  [[ -f "$extracted" ]] || continue
  base="$(basename "$extracted")"
  echo | tee -a "$REPORT"
  file "$extracted" | tee -a "$REPORT"
  if [[ "$base" =~ ^(boot|dtbo|vbmeta).*([.]img)$ ]]; then
    strings -a "$extracted" | grep -Ei 'battery|fuel.?gauge|pm855|qpnp|qg|provision|thermistor|m703|bn61|bn57|atl' \
      | head -n 250 >> "$OUT/boot-dtbo-string-hits.txt" || true
  fi
done < "$OUT/image-members.txt"

# Inspect filesystem partitions read-only.
while IFS= read -r image; do
  [[ -n "$image" ]] || continue
  extracted="$OUT/images/$image"
  [[ -f "$extracted" ]] || continue
  base="$(basename "$extracted" .img)"
  case "$base" in vendor|odm|system|product|cust) ;; *) continue ;; esac
  fsimage="$extracted"
  if file "$extracted" | grep -qi 'Android sparse image'; then
    fsimage="$OUT/${base}-raw.img"
    simg2img "$extracted" "$fsimage"
  fi
  mnt="$OUT/mounts/$base"
  mkdir -p "$mnt"
  if mount -o loop,ro,noload "$fsimage" "$mnt" 2>/dev/null; then
    echo | tee -a "$REPORT"
    echo "=== Filesystem scan: $base ===" | tee -a "$REPORT"
    find "$mnt" -type f \( -iname '*battery*' -o -iname '*fuel*gauge*' -o -iname '*provision*' -o -iname '*m703*' -o -iname '*bn61*' -o -iname '*bn57*' -o -iname '*thermistor*' \) \
      | sed "s#^$mnt/##" | tee -a "$REPORT" || true
    find "$mnt" -type f \( -name '*.dtsi' -o -name '*.dts' -o -name '*.dtb' -o -name '*.dtbo' -o -name '*.xml' -o -name '*.conf' -o -name '*.prop' -o -name '*.rc' -o -name '*.ko' -o -name '*.bin' \) -print0 \
      | xargs -0 -r -n 40 sh -c 'for f do strings -a "$f" 2>/dev/null; done' sh \
      | grep -Ei 'batterydata|battery.?profile|fuel.?gauge|pm855|qpnp.?fg|m703|bn61|bn57|atl.?6000|BATTERY[.]PROVISION|thermistor|ocv.?table|fcc.?table' \
      | head -n 1200 >> "$OUT/filesystem-string-hits.txt" || true
    umount "$mnt"
  else
    echo "Could not mount $base as ext4; retained image for manual inspection." | tee -a "$REPORT"
  fi
done < "$OUT/image-members.txt"

{
  echo
  echo "=== boot/dtbo/vbmeta string hits ==="
  cat "$OUT/boot-dtbo-string-hits.txt" 2>/dev/null || true
  echo
  echo "=== filesystem string hits (capped at 1200 lines) ==="
  cat "$OUT/filesystem-string-hits.txt" 2>/dev/null || true
} >> "$REPORT"

echo | tee -a "$REPORT"
echo "Audit complete. No profile is considered valid unless an authentic Gen4 payload and metadata are recovered and independently validated." | tee -a "$REPORT"
