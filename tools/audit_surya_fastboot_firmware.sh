#!/usr/bin/env bash
set -euo pipefail

FIRMWARE_NAME="fw_surya_miui_SURYAGlobal_V12.5.8.0.RJGMIXM_e57b4eef74_11.0.zip"
FIRMWARE_URL="https://sourceforge.net/projects/syahiddrakness/files/Project/Kernel/surya/OSS/Stable/firmware/${FIRMWARE_NAME}/download"
EXPECTED_MD5="b3e15a6733140e8783995bc555c3aa60"
OUT="${1:-surya-firmware-audit}"
mkdir -p "$OUT/images" "$OUT/xbl-raw"
REPORT="$OUT/SURYA-FIRMWARE-AUDIT.txt"

echo "POCO X3 NFC surya — official firmware XBL / UEFI battery audit" | tee "$REPORT"
echo "Firmware package: $FIRMWARE_NAME" | tee -a "$REPORT"
echo "Source: XM Firmware Updater mirror (firmware extracted from official MIUI)" | tee -a "$REPORT"
echo "Download: $FIRMWARE_URL" | tee -a "$REPORT"
echo "Expected MD5: $EXPECTED_MD5" | tee -a "$REPORT"

if [[ ! -s "$OUT/$FIRMWARE_NAME" ]]; then
  curl --fail --location --retry 5 --retry-all-errors --connect-timeout 30 \
    --output "$OUT/$FIRMWARE_NAME" "$FIRMWARE_URL"
fi

ACTUAL_MD5="$(md5sum "$OUT/$FIRMWARE_NAME" | awk '{print $1}')"
echo "Actual MD5: $ACTUAL_MD5" | tee -a "$REPORT"
if [[ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]]; then
  echo "ERROR: MD5 mismatch; refusing to inspect an unverified archive." | tee -a "$REPORT"
  exit 2
fi

unzip -Z1 "$OUT/$FIRMWARE_NAME" > "$OUT/archive-members.txt"
grep -Ei '(^|/)(xbl|xbl_config|abl|tz|hyp|devcfg|uefi_sec|imagefv)([.]elf|[.]mbn|[.]img)$' \
  "$OUT/archive-members.txt" > "$OUT/image-members.txt" || true

echo | tee -a "$REPORT"
echo "=== Selected boot-chain firmware members ===" | tee -a "$REPORT"
tee -a "$REPORT" < "$OUT/image-members.txt"

while IFS= read -r member; do
  [[ -n "$member" ]] || continue
  name="$(basename "$member")"
  unzip -p "$OUT/$FIRMWARE_NAME" "$member" > "$OUT/images/$name"
  test -s "$OUT/images/$name"
  file "$OUT/images/$name" | tee -a "$REPORT"
  sha256sum "$OUT/images/$name" | tee -a "$REPORT"
done < "$OUT/image-members.txt"

XBL="$OUT/images/xbl.elf"
if [[ ! -s "$XBL" ]]; then
  XBL="$OUT/images/xbl.img"
fi
if [[ ! -s "$XBL" ]]; then
  echo "ERROR: verified firmware ZIP contains no xbl.elf or xbl.img member." | tee -a "$REPORT"
  exit 3
fi

echo | tee -a "$REPORT"
echo "=== Qualcomm XBL UEFI firmware-volume extraction ===" | tee -a "$REPORT"
python3 tools/extract_qualcomm_xbl_raw.py --xbl "$XBL" --out "$OUT/xbl-raw" \
  2>&1 | tee -a "$REPORT"

echo | tee -a "$REPORT"
echo "=== XBL boot-chain string hits ===" | tee -a "$REPORT"
strings -a "$XBL" | grep -Ei 'battery|fuel.?gauge|pm855|qpnp|qg|provision|thermistor|m703|bn61|bn57|atl|DS28E16' \
  | head -n 500 | tee "$OUT/xbl-string-hits.txt" | tee -a "$REPORT" || true

echo | tee -a "$REPORT"
echo "=== Extracted RAW inventory ===" | tee -a "$REPORT"
tee -a "$REPORT" < "$OUT/xbl-raw/RAW-MANIFEST.tsv"
echo | tee -a "$REPORT"
echo "Audit complete. Any BATTERY.PROVISION recovered here is a firmware source artifact, not automatically an alioth Gen4 profile." | tee -a "$REPORT"
