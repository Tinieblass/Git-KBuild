#!/usr/bin/env bash
set -euo pipefail

FIRMWARE_NAME="surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz"
FIRMWARE_PATH="V13.0.1.0.SJGINXM/${FIRMWARE_NAME}"
FIRMWARE_HOSTS=(cdnorg.d.miui.com hugeota.d.miui.com bigota.d.miui.com)
PROBE_CONNECTIONS=16
PROBE_BYTES=65536
MIN_PROBE_SPEED=300000
FIRMWARE_URL=""
EXPECTED_MD5="15727cb7de21880a9f0ff788f1e4a035"
OUT="${1:-surya-india-firmware-audit}"
mkdir -p "$OUT/extracted" "$OUT/xbl-raw"
REPORT="$OUT/SURYA-INDIA-FASTBOOT-AUDIT.txt"

{
  echo "POCO X3 India — official SURYAINGlobal V13.0.1.0.SJGINXM boot-chain and device-tree audit"
  echo "Firmware: $FIRMWARE_NAME"
  echo "Source: Xiaomi official bigota server, indexed by HyperOS Update / XM Firmware Updater"
  echo "Candidate Xiaomi CDN hosts: ${FIRMWARE_HOSTS[*]}"
  echo "Minimum aggregate range-probe speed: ${MIN_PROBE_SPEED} B/s"
  echo "Expected MD5: $EXPECTED_MD5"
} | tee "$REPORT"

if [[ ! -s "$OUT/$FIRMWARE_NAME" ]]; then
  if ! command -v aria2c >/dev/null 2>&1; then
    echo "ERROR: aria2c is required for bounded parallel firmware download." | tee -a "$REPORT"
    exit 4
  fi

  probe_firmware_host() {
    local host="$1"
    local url="https://$host/$FIRMWARE_PATH"
    local probe_dir="$OUT/.firmware-probes/$host"
    local started="$SECONDS"
    local index start end pid
    local -a pids=()
    local failed=0
    local total_bytes=0
    mkdir -p "$probe_dir"
    rm -f "$probe_dir"/range-*.bin "$probe_dir"/status-*.txt "$probe_dir"/error-*.txt

    for ((index = 0; index < PROBE_CONNECTIONS; index++)); do
      start=$((index * PROBE_BYTES))
      end=$((start + PROBE_BYTES - 1))
      curl --fail --silent --show-error --location \
        --range "$start-$end" --connect-timeout 10 --max-time 45 \
        --max-filesize "$PROBE_BYTES" --output "$probe_dir/range-$index.bin" \
        --write-out '%{http_code}' "$url" \
        > "$probe_dir/status-$index.txt" 2> "$probe_dir/error-$index.txt" &
      pids+=("$!")
    done

    for pid in "${pids[@]}"; do
      wait "$pid" || failed=1
    done

    for ((index = 0; index < PROBE_CONNECTIONS; index++)); do
      local code size
      code="$(cat "$probe_dir/status-$index.txt" 2>/dev/null || true)"
      size="$(wc -c < "$probe_dir/range-$index.bin" 2>/dev/null || echo 0)"
      if [[ "$code" != "206" || "$size" -ne "$PROBE_BYTES" ]]; then
        failed=1
      fi
      total_bytes=$((total_bytes + size))
    done

    local elapsed=$((SECONDS - started))
    (( elapsed > 0 )) || elapsed=1
    if [[ "$failed" -eq 0 ]]; then
      PROBE_SPEED=$((total_bytes / elapsed))
      printf 'PASS: %s returned 16 valid HTTP range responses; aggregate probe speed %s B/s.\n' \
        "$host" "$PROBE_SPEED" | tee -a "$REPORT"
    else
      PROBE_SPEED=0
      printf 'SKIP: %s failed the 16-connection HTTP range probe (received %s/%s bytes).\n' \
        "$host" "$total_bytes" "$((PROBE_CONNECTIONS * PROBE_BYTES))" | tee -a "$REPORT"
    fi
  }

  BEST_HOST=""
  BEST_SPEED=0
  for host in "${FIRMWARE_HOSTS[@]}"; do
    PROBE_SPEED=0
    probe_firmware_host "$host"
    if [[ "$PROBE_SPEED" -gt "$BEST_SPEED" ]]; then
      BEST_HOST="$host"
      BEST_SPEED="$PROBE_SPEED"
    fi
  done

  if [[ -z "$BEST_HOST" || "$BEST_SPEED" -lt "$MIN_PROBE_SPEED" ]]; then
    echo "ERROR: no Xiaomi CDN host passed the HTTP range probe at $MIN_PROBE_SPEED B/s; refusing a multi-hour single-stream download." | tee -a "$REPORT"
    exit 5
  fi

  FIRMWARE_URL="https://$BEST_HOST/$FIRMWARE_PATH"
  echo "Selected Xiaomi CDN URL: $FIRMWARE_URL (probe speed $BEST_SPEED B/s)" | tee -a "$REPORT"
  aria2c --allow-overwrite=true --auto-file-renaming=false --file-allocation=none \
    --max-connection-per-server="$PROBE_CONNECTIONS" --split="$PROBE_CONNECTIONS" \
    --min-split-size=1M --max-tries=3 --retry-wait=5 --connect-timeout=30 \
    --timeout=60 --summary-interval=30 --console-log-level=notice \
    --dir="$OUT" --out="$FIRMWARE_NAME" "$FIRMWARE_URL" 2>&1 \
    | tee "$OUT/firmware-download.log"
fi

ACTUAL_MD5="$(md5sum "$OUT/$FIRMWARE_NAME" | awk '{print $1}')"
ACTUAL_SHA256="$(sha256sum "$OUT/$FIRMWARE_NAME" | awk '{print $1}')"
echo "Actual MD5: $ACTUAL_MD5" | tee -a "$REPORT"
echo "Actual SHA-256: $ACTUAL_SHA256" | tee -a "$REPORT"
if [[ "$ACTUAL_MD5" != "$EXPECTED_MD5" ]]; then
  echo "ERROR: MD5 mismatch; refusing to inspect an unverified ROM." | tee -a "$REPORT"
  exit 2
fi

tar -tzf "$OUT/$FIRMWARE_NAME" > "$OUT/archive-members.txt"
grep -Ei '(^|/)(xbl|xbl_config|abl|tz|hyp|devcfg|uefi_sec|imagefv|boot|vendor_boot|dtbo)([.]elf|[.]mbn|[.]img)' \
  "$OUT/archive-members.txt" > "$OUT/image-members.txt" || true
if ! grep -Eiq '(^|/)xbl([.]elf|[.]img)' "$OUT/image-members.txt"; then
  echo "ERROR: verified India fastboot ROM contains no xbl.elf or xbl.img member." | tee -a "$REPORT"
  exit 3
fi

echo | tee -a "$REPORT"
echo "=== Selected India boot-chain and device-tree members ===" | tee -a "$REPORT"
tee -a "$REPORT" < "$OUT/image-members.txt"

tar -xzf "$OUT/$FIRMWARE_NAME" -C "$OUT/extracted" --files-from="$OUT/image-members.txt"

while IFS= read -r member; do
  [[ -n "$member" ]] || continue
  image="$OUT/extracted/$member"
  test -s "$image"
  file "$image" | tee -a "$REPORT"
  sha256sum "$image" | tee -a "$REPORT"
done < "$OUT/image-members.txt"


BATTERY_HITS="$OUT/india-device-tree-battery-hits.txt"
: > "$BATTERY_HITS"

decompile_battery_properties() {
  local dtb="$1"
  local label="$2"
  local dts="$3"
  dtc -q -I dtb -O dts -o "$dts" "$dtb"
  if grep -nEi 'battery|fuel.?gauge|qcom,fg|fg-profile|nom-batt|batt-id|therm|jeita|m703|bn61|bn57|qg' "$dts" > /dev/null; then
    {
      printf '=== %s ===\n' "$label"
      grep -nEi 'battery|fuel.?gauge|qcom,fg|fg-profile|nom-batt|batt-id|therm|jeita|m703|bn61|bn57|qg' "$dts" || true
    } >> "$BATTERY_HITS"
  fi
}

DTBO_IMAGE="$(find "$OUT/extracted" -type f -name dtbo.img -print -quit)"
if [[ -n "$DTBO_IMAGE" ]]; then
  DTBO_OUT="$OUT/india-dtbo"
  python3 tools/extract_android_dtbo.py --image "$DTBO_IMAGE" --out "$DTBO_OUT" 2>&1 | tee -a "$REPORT"
  while IFS= read -r -d '' dtb; do
    dts="${dtb%.dtb}.dts"
    decompile_battery_properties "$dtb" "DTBO $(basename "$dtb")" "$dts"
  done < <(find "$DTBO_OUT" -maxdepth 1 -type f -name 'dtbo-*.dtb' -print0)
else
  echo "No dtbo.img member in the verified India fastboot archive." | tee -a "$REPORT"
fi

for name in boot vendor_boot; do
  boot_image="$(find "$OUT/extracted" -type f -name "$name.img" -print -quit)"
  [[ -n "$boot_image" ]] || continue
  fdt_out="$OUT/embedded-fdt/$name"
  set +e
  python3 tools/extract_android_dtbo.py --scan-fdt --image "$boot_image" --out "$fdt_out" 2>&1 | tee -a "$REPORT"
  scan_status=${PIPESTATUS[0]}
  set -e
  if [[ "$scan_status" -ne 0 && "$scan_status" -ne 2 ]]; then
    echo "ERROR: embedded FDT scan failed for $name.img (exit $scan_status)." | tee -a "$REPORT"
    exit "$scan_status"
  fi
  if [[ "$scan_status" -eq 0 ]]; then
    while IFS= read -r -d '' dtb; do
      dts="${dtb%.dtb}.dts"
      decompile_battery_properties "$dtb" "$name $(basename "$dtb")" "$dts"
    done < <(find "$fdt_out" -maxdepth 1 -type f -name 'fdt-*.dtb' -print0)
  fi
done

if [[ ! -s "$BATTERY_HITS" ]]; then
  echo "No battery/fuel-gauge-related properties found in extracted India DTBs/DTBOs." > "$BATTERY_HITS"
fi

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
