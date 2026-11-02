#!/usr/bin/env bash
set -euo pipefail

FIRMWARE_NAME="surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz"
FIRMWARE_URL="https://bigota.d.miui.com/V13.0.1.0.SJGINXM/${FIRMWARE_NAME}"
EXPECTED_MD5="15727cb7de21880a9f0ff788f1e4a035"
OUT="${1:-surya-india-firmware-audit}"
mkdir -p "$OUT/extracted" "$OUT/xbl-raw"
REPORT="$OUT/SURYA-INDIA-FASTBOOT-AUDIT.txt"

{
  echo "POCO X3 India — official SURYAINGlobal V13.0.1.0.SJGINXM boot-chain audit"
  echo "Firmware: $FIRMWARE_NAME"
  echo "Source: Xiaomi official bigota server, indexed by HyperOS Update / XM Firmware Updater"
  echo "URL: $FIRMWARE_URL"
  echo "Expected MD5: $EXPECTED_MD5"
} | tee "$REPORT"

if [[ ! -s "$OUT/$FIRMWARE_NAME" ]]; then
  curl --fail --location --retry 5 --retry-all-errors --connect-timeout 30 \
    --max-time 7200 --output "$OUT/$FIRMWARE_NAME" "$FIRMWARE_URL"
fi

ACTUAL_MD5="$(md5sum "$OUT/$FIRMWARE_NAME" | awk '{print $1}')"
echo "Actual MD5: $ACTUAL_MD5" | tee -a "$REPORT"
if [[ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]]; then
  echo "ERROR: MD5 mismatch; refusing to inspect an unverified ROM." | tee -a "$REPORT"
  exit 2
fi

tar -tzf "$OUT/$FIRMWARE_NAME" > "$OUT/archive-members.txt"
grep -Ei '(^|/)(xbl|xbl_config|abl|tz|hyp|devcfg|uefi_sec|imagefv)([.]elf|[.]mbn|[.]img)$' \
  "$OUT/archive-members.txt" > "$OUT/image-members.txt" || true
if ! grep -Eiq '(^|/)xbl([.]elf|[.]img)$' "$OUT/image-members.txt"; then
  echo "ERROR: verified India fastboot ROM contains no xbl.elf or xbl.img member." | tee -a "$REPORT"
  exit 3
fi

echo | tee -a "$REPORT"
echo "=== Selected India boot-chain members ===" | tee -a "$REPORT"
tee -a "$REPORT" < "$OUT/image-members.txt"

tar -xzf "$OUT/$FIRMWARE_NAME" -C "$OUT/extracted" --files-from="$OUT/image-members.txt"

while IFS= read -r member; do
  [[ -n "$member" ]] || continue
  image="$OUT/extracted/$member"
  test -s "$image"
  file "$image" | tee -a "$REPORT"
  sha256sum "$image" | tee -a "$REPORT"
done < "$OUT/image-members.txt"

XBL="$(find "$OUT/extracted" -type f \( -name xbl.elf -o -name xbl.img \) -print -quit)"
test -n "$XBL"

echo | tee -a "$REPORT"
echo "=== India XBL UEFI firmware-volume extraction ===" | tee -a "$REPORT"
python3 tools/extract_qualcomm_xbl_raw.py --image "$XBL" --out "$OUT/xbl-raw" 2>&1 | tee -a "$REPORT"

while IFS= read -r member; do
  [[ -n "$member" ]] || continue
  image="$OUT/extracted/$member"
  [[ "$image" == "$XBL" ]] && continue
  name="$(basename "$member")"
  name="${name%.*}"
  echo | tee -a "$REPORT"
  echo "=== Additional India firmware-volume scan: $member ===" | tee -a "$REPORT"
  set +e
  python3 tools/extract_qualcomm_xbl_raw.py --image "$image" --out "$OUT/other-raw/$name" 2>&1 | tee -a "$REPORT"
  scan_status=${PIPESTATUS[0]}
  set -e
  if [[ "$scan_status" -ne 0 && "$scan_status" -ne 2 ]]; then
    echo "ERROR: parser failed for $member (exit $scan_status)." | tee -a "$REPORT"
    exit "$scan_status"
  fi
  if [[ "$scan_status" -eq 2 ]]; then
    echo "No UEFI firmware volume found in $member." | tee -a "$REPORT"
  fi
done < "$OUT/image-members.txt"

echo | tee -a "$REPORT"
echo "=== India QcomChargerCfg battery / thermal settings ===" | tee -a "$REPORT"
CHARGER_CFG="$(find "$OUT/xbl-raw" -maxdepth 1 -type f -name '*QcomChargerCfg.cfg.raw' -print -quit)"
if [[ -n "$CHARGER_CFG" ]]; then
  grep -nEi '^\[Platform|^(LoadBatteryProfile|BattMissingCfg|BatteryIdTolerance|RegularBatteryIdMin|RegularBatteryIdMax|ProgramBattThermCoeffs|BattTherm(C1|C2|C3|GndSel|BiasWait)|ChgFvMax|ChgFccMax|Jeita.*|UnknownBatteryBehavior|EmergencyShutdownVbatt|SocBasedBoot)[[:space:]]*=' "$CHARGER_CFG" \
    | tee -a "$REPORT" || true
else
  echo "QcomChargerCfg.cfg not present in India XBL RAW records." | tee -a "$REPORT"
fi

echo | tee -a "$REPORT"
echo "=== India XBL battery / fuel-gauge strings ===" | tee -a "$REPORT"
strings -a "$XBL" | grep -Ei 'battery|fuel.?gauge|pm855|qpnp|qg|provision|thermistor|m703|bn61|bn57|atl|DS28E16' \
  | head -n 500 | tee "$OUT/xbl-string-hits.txt" | tee -a "$REPORT" || true

echo | tee -a "$REPORT"
echo "=== India XBL extracted RAW inventory ===" | tee -a "$REPORT"
tee -a "$REPORT" < "$OUT/xbl-raw/RAW-MANIFEST.tsv"
echo | tee -a "$REPORT"
echo "Audit complete. This India firmware is a more relevant 6000mAh variant reference than the previously audited Global NFC package; it still does not prove a BN61 PM855B Gen4 profile." | tee -a "$REPORT"
