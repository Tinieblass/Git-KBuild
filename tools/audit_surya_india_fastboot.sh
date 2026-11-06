#!/usr/bin/env bash
set -euo pipefail

FIRMWARE_NAME="surya_in_global_images_V13.0.1.0.SJGINXM_20220818.0000.00_12.0_in_15727cb7de.tgz"
FIRMWARE_PATH="V13.0.1.0.SJGINXM/${FIRMWARE_NAME}"
FIRMWARE_HOSTS=(cdnorg.d.miui.com hugeota.d.miui.com bigota.d.miui.com)
PROBE_CONNECTIONS=16
PROBE_BYTES=2097152
MIN_PROBE_SPEED=300000
FIRMWARE_URL=""
EXPECTED_MD5="15727cb7de21880a9f0ff788f1e4a035"
OUT="${1:-surya-india-firmware-audit}"
mkdir -p "$OUT/extracted" "$OUT/xbl-raw"
REPORT="$OUT/SURYA-INDIA-FASTBOOT-AUDIT.txt"

{
  echo "POCO X3 India — official SURYAINGlobal V13.0.1.0.SJGINXM boot-chain, device-tree and dynamic-partition audit"
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
        --range "$start-$end" --connect-timeout 10 --max-time 60 \
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
grep -Ei '(^|/)(xbl|xbl_config|abl|tz|hyp|devcfg|uefi_sec|imagefv|boot|vendor_boot|dtbo|super)([.]elf|[.]mbn|[.]img)' \
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

# Inspect the India ROM's dynamic partitions as a separate firmware layer.
SUPER_IMAGE="$(find "$OUT/extracted" -type f -name super.img -print -quit)"
if [[ -n "$SUPER_IMAGE" ]]; then
  SUPER_AUDIT="$OUT/super-audit"
  SUPER_TOOL="$SUPER_AUDIT/lucky-arch-src"
  SUPER_PARTS="$SUPER_AUDIT/partitions"
  SUPER_FILES="$SUPER_AUDIT/files"
  SUPER_BIN="$(realpath -m "$SUPER_AUDIT/lucky-arch")"
  [[ "$SUPER_BIN" = /* ]]
  SUPER_TOOL_COMMIT='09ba1a6b4b2c8d603fcb1d8bfe7cf167c9e0463b'
  mkdir -p "$SUPER_AUDIT" "$SUPER_PARTS" "$SUPER_FILES"
  : > "$SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
  {
    echo
    echo "=== India super.img dynamic-partition inspection ==="
    echo "super.img: $SUPER_IMAGE"
    echo "super.img bytes: $(stat -c %s "$SUPER_IMAGE")"
    echo "super.img SHA-256: $(sha256sum "$SUPER_IMAGE" | awk '{print $1}')"
    echo "Partition reader: https://github.com/soe1hom-arch/lucky-arch"
    echo "Pinned source commit: $SUPER_TOOL_COMMIT"
  } | tee -a "$REPORT"

  git clone --filter=blob:none --no-checkout https://github.com/soe1hom-arch/lucky-arch.git "$SUPER_TOOL"
  git -C "$SUPER_TOOL" fetch --depth=1 origin "$SUPER_TOOL_COMMIT"
  git -C "$SUPER_TOOL" checkout --detach "$SUPER_TOOL_COMMIT"
  test "$(git -C "$SUPER_TOOL" rev-parse HEAD)" = "$SUPER_TOOL_COMMIT"

  # The pinned reader's initial extractor omitted zero extents from partition
  # sizes/offsets and silently continued after extraction failures. Patch those
  # cases explicitly and unit-test zero extents plus LP metadata checksums before use.
  python3 - "$SUPER_TOOL/super.go" <<'PY'
from pathlib import Path
import sys

p = Path(sys.argv[1])
s = p.read_text()
changes = [
    (
        '''if h.BlockDevices.NumElements == 0 {
\t\treturn nil, fmt.Errorf("LP metadata has no block devices")
\t}''',
        '''if h.BlockDevices.NumElements != 1 {
\t\treturn nil, fmt.Errorf("expected exactly one super block device, got %d", h.BlockDevices.NumElements)
\t}'''
    ),
    (
        '''if len(buf) < 64 {
\t\treturn nil, fmt.Errorf("metadata buffer too small: %d", len(buf))
\t}''',
        '''if len(buf) < 128 {
\t\treturn nil, fmt.Errorf("metadata buffer too small: %d", len(buf))
\t}'''
    ),
    (
        '''if int64(h.HeaderSize) < 64 {
\t\treturn nil, fmt.Errorf("LP header size too small: %d", h.HeaderSize)
\t}

\treturn h, nil''',
        '''if int64(h.HeaderSize) < 128 || int64(h.HeaderSize) > int64(len(buf)) {
\t\treturn nil, fmt.Errorf("invalid LP header size: %d (buffer %d)", h.HeaderSize, len(buf))
\t}
\ttmp := make([]byte, h.HeaderSize)
\tcopy(tmp, buf[:h.HeaderSize])
\tfor i := 12; i < 44; i++ {
\t\ttmp[i] = 0
\t}
\tif sha256.Sum256(tmp) != h.HeaderChecksum {
\t\treturn nil, fmt.Errorf("LP metadata header checksum mismatch")
\t}

\treturn h, nil'''
    ),
    (
        '''if e.TargetType == LPTargetTypeLinear {
\t\t\t\tpExts = append(pExts, e)
\t\t\t\tpSize += e.NumSectors * LPSectorSize
\t\t\t}''',
        '''if e.TargetType == LPTargetTypeLinear || e.TargetType == LPTargetTypeZero {
\t\t\t\tpExts = append(pExts, e)
\t\t\t\tpSize += e.NumSectors * LPSectorSize
\t\t\t} else {
\t\t\t\treturn nil, fmt.Errorf("partition %s: unsupported extent target type %d", name, e.TargetType)
\t\t\t}'''
    ),
    (
        '''func (sp *SuperImage) ExtractPartitions(outDir string) error {
\tif err := os.MkdirAll(outDir, 0755); err != nil {
\t\treturn fmt.Errorf("creating output directory: %w", err)
\t}

\textracted := 0
\tfor _, part := range sp.Partitions {
\t\tif sp.verbose {
\t\t\tfmt.Printf("Extracting %s (%s)...\\n", part.Name, formatSize(int64(part.Size)))
\t\t}
\t\tif err := sp.extractOne(part, outDir); err != nil {
\t\t\tfmt.Fprintf(os.Stderr, "Warning: %s: %v\\n", part.Name, err)
\t\t\tcontinue
\t\t}
\t\textracted++
\t}

\tif sp.verbose {
\t\tfmt.Printf("\\nExtracted %d partition(s) to %s\\n", extracted, outDir)
\t}
\treturn nil
}''',
        '''func (sp *SuperImage) ExtractPartitions(outDir string) error {
\tif err := os.MkdirAll(outDir, 0755); err != nil {
\t\treturn fmt.Errorf("creating output directory: %w", err)
\t}

\tselected := 0
\textracted := 0
\tfor _, part := range sp.Partitions {
\t\tif !strings.HasPrefix(part.Name, "vendor") && !strings.HasPrefix(part.Name, "odm") && part.Name != "product" && part.Name != "system_ext" {
\t\t\tcontinue
\t\t}
\t\tselected++
\t\tif sp.verbose {
\t\t\tfmt.Printf("Extracting %s (%s)...\\n", part.Name, formatSize(int64(part.Size)))
\t\t}
\t\tif err := sp.extractOne(part, outDir); err != nil {
\t\t\treturn fmt.Errorf("extract %s: %w", part.Name, err)
\t\t}
\t\textracted++
\t}

\tif selected == 0 {
\t\treturn fmt.Errorf("no battery-relevant vendor/odm/product/system_ext logical partitions found")
\t}
\tif extracted != selected {
\t\treturn fmt.Errorf("extracted %d of %d selected battery-relevant logical partitions", extracted, selected)
\t}
\tif sp.verbose {
\t\tfmt.Printf("\\nExtracted %d vendor/odm partition(s) to %s\\n", extracted, outDir)
\t}
\treturn nil
}'''
    ),
    (
        '''\tfor idx, ext := range part.Extents {
\t\tif ext.TargetType != LPTargetTypeLinear {
\t\t\tcontinue
\t\t}
\t\tphysOff := int64(ext.TargetData * LPSectorSize)
\t\tdataSize := int64(ext.NumSectors * LPSectorSize)
\t\tif dataSize == 0 {
\t\t\tcontinue
\t\t}''',
        '''\tfor idx, ext := range part.Extents {
\t\tdataSize := int64(ext.NumSectors * LPSectorSize)
\t\tif dataSize == 0 {
\t\t\tcontinue
\t\t}
\t\tif ext.TargetType == LPTargetTypeZero {
\t\t\twritten += dataSize
\t\t\tcontinue
\t\t}
\t\tif ext.TargetType != LPTargetTypeLinear {
\t\t\treturn fmt.Errorf("extent %d: unsupported target type %d", idx, ext.TargetType)
\t\t}
\t\tphysOff := int64(ext.TargetData * LPSectorSize)'''
    ),
    (
        '''\treturn out.Sync()
}''',
        '''\tif written != int64(part.Size) {
\t\treturn fmt.Errorf("partition %s: extracted extent size %d != metadata size %d", part.Name, written, part.Size)
\t}
\treturn out.Sync()
}'''
    )
]
for old, new in changes:
    count = s.count(old)
    if count != 1:
        raise SystemExit(f"Expected one patch target in super.go, found {count}: {old[:90]!r}")
    s = s.replace(old, new, 1)
p.write_text(s)
print("PATCHED: zero extents preserve partition offsets; unknown extents and multi-device metadata fail closed; vendor/odm/product/system_ext partitions are extracted; extraction failures are fatal.")
PY

  cat > "$SUPER_TOOL/super_zero_extent_test.go" <<'GO'
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"os"
	"path/filepath"
	"testing"
)

func TestExtractOnePreservesZeroExtentOffset(t *testing.T) {
	payload := make([]byte, 2*LPSectorSize)
	for i := 0; i < LPSectorSize; i++ {
		payload[i] = 0xA1
		payload[LPSectorSize+i] = 0xB2
	}
	sp := &SuperImage{reader: bytes.NewReader(payload)}
	part := PartitionInfo{
		Name: "vendor_a",
		Size: 3 * LPSectorSize,
		Extents: []LpMetadataExtent{
			{NumSectors: 1, TargetType: LPTargetTypeLinear, TargetData: 0},
			{NumSectors: 1, TargetType: LPTargetTypeZero},
			{NumSectors: 1, TargetType: LPTargetTypeLinear, TargetData: 1},
		},
	}
	dir := t.TempDir()
	if err := sp.extractOne(part, dir); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(filepath.Join(dir, "vendor_a.img"))
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 3*LPSectorSize {
		t.Fatalf("output size = %d, want %d", len(got), 3*LPSectorSize)
	}
	for i := 0; i < LPSectorSize; i++ {
		if got[i] != 0xA1 {
			t.Fatalf("first linear extent mismatch at %d", i)
		}
		if got[LPSectorSize+i] != 0 {
			t.Fatalf("zero extent is not zero at %d", LPSectorSize+i)
		}
		if got[2*LPSectorSize+i] != 0xB2 {
			t.Fatalf("second linear extent mismatch at %d", 2*LPSectorSize+i)
		}
	}
}

func TestParseHeaderValidatesHeaderChecksum(t *testing.T) {
	buf := make([]byte, 128)
	binary.LittleEndian.PutUint32(buf[0:4], LPMetadataHeaderMagic)
	binary.LittleEndian.PutUint16(buf[4:6], 10)
	binary.LittleEndian.PutUint16(buf[6:8], 0)
	binary.LittleEndian.PutUint32(buf[8:12], 128)
	sum := sha256.Sum256(buf)
	copy(buf[12:44], sum[:])
	if _, err := parseHeader(buf); err != nil {
		t.Fatalf("valid header rejected: %v", err)
	}
	buf[44] ^= 1
	if _, err := parseHeader(buf); err == nil {
		t.Fatal("tampered LP header accepted without checksum error")
	}
}
GO

  (
    cd "$SUPER_TOOL"
    gofmt -w super.go super_zero_extent_test.go
    go test ./...
    go build -trimpath -o "$SUPER_BIN" .
  )
  {
    echo "Reader source commit: $SUPER_TOOL_COMMIT"
    echo "Reader binary SHA-256: $(sha256sum "$SUPER_BIN" | awk '{print $1}')"
    echo "Reader zero-extent test: PASS"
    echo "Reader LP header checksum test: PASS"
    echo "Reader validates geometry and LP header/table SHA-256 checksums"
    echo "Extraction scope: vendor*, odm*, product and system_ext logical partitions"
  } > "$SUPER_AUDIT/SUPER-TOOLCHAIN.txt"

  "$SUPER_BIN" -v -l "$SUPER_IMAGE" 2>&1 | tee "$SUPER_AUDIT/SUPER-PARTITIONS.txt"
  "$SUPER_BIN" -v -o "$SUPER_PARTS" "$SUPER_IMAGE" 2>&1 | tee "$SUPER_AUDIT/SUPER-EXTRACTION-LOG.txt"

  printf 'partition\tbytes\tsha256\tfile_type\n' > "$SUPER_AUDIT/SUPER-PARTITION-MANIFEST.tsv"
  : > "$SUPER_AUDIT/SUPER-BATTERY-PATH-HITS.txt"
  : > "$SUPER_AUDIT/SUPER-BATTERY-CONTENT-HITS.txt"
  mapfile -d '' SUPER_PARTITION_FILES < <(find "$SUPER_PARTS" -maxdepth 1 -type f \( -name 'vendor*.img' -o -name 'odm*.img' -o -name 'product*.img' -o -name 'system_ext*.img' \) -print0 | sort -z)
  if [[ "${#SUPER_PARTITION_FILES[@]}" -eq 0 ]]; then
    echo "ERROR: the super image exposed no battery-relevant vendor/odm/product/system_ext partition images." | tee -a "$REPORT"
    exit 6
  fi

  for partition_image in "${SUPER_PARTITION_FILES[@]}"; do
    partition_name="$(basename "${partition_image%.img}")"
    partition_bytes="$(stat -c %s "$partition_image")"
    partition_sha="$(sha256sum "$partition_image" | awk '{print $1}')"
    partition_type="$(file -b "$partition_image")"
    printf '%s\t%s\t%s\t%s\n' "$partition_name" "$partition_bytes" "$partition_sha" "$partition_type" >> "$SUPER_AUDIT/SUPER-PARTITION-MANIFEST.tsv"
    partition_root="$SUPER_FILES/$partition_name"
    mkdir -p "$partition_root"

    case "$partition_type" in
      *ext4*|*ext3*|*ext2*)
        for internal_path in /etc /firmware; do
          destination="$partition_root/${internal_path#/}"
          rm -rf "$destination"
          mkdir -p "$(dirname "$destination")"
          if debugfs -R "rdump $internal_path $destination" "$partition_image" > "$partition_root/rdump-${internal_path#/}.log" 2>&1; then
            printf '%s\t%s\textracted\n' "$partition_name" "$internal_path" >> "$SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
          else
            printf '%s\t%s\tnot-present-or-unreadable\n' "$partition_name" "$internal_path" >> "$SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
          fi
        done
        ;;
      *EROFS*)
        destination="$partition_root/erofs-root"
        rm -rf "$destination"
        mkdir -p "$(dirname "$destination")"
        if fsck.erofs --extract="$destination" "$partition_image" > "$partition_root/erofs-extract.log" 2>&1; then
          printf '%s\t%s\textracted-whole-erofs-filesystem\n' "$partition_name" "$partition_image" >> "$SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
        else
          printf '%s\t%s\terofs-extraction-failed\n' "$partition_name" "$partition_image" >> "$SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
        fi
        ;;
      *)
        printf '%s\tfilesystem-not-recognized\t%s\n' "$partition_name" "$partition_type" >> "$SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
        ;;
    esac

    strings -a -n 8 "$partition_image" \
      | grep -Ei 'BN61|M703|BATTERY[.]PROVISION|PM855GUI|qcom,fg-profile-data|qcom,nom-batt-capacity-mah|qcom,pc-temp-|batterydata-M703|qg-battery-profile|qpnp-qg|qpnp-fg-gen4|thermistor|QG-D|QBG-D|(^|[^[:alnum:]_])ATL([^[:alnum:]_]|$)' \
      | head -n 250 \
      | sed "s#^#[$partition_name raw] #" >> "$SUPER_AUDIT/SUPER-BATTERY-CONTENT-HITS.txt" || true
  done

  find "$SUPER_FILES" -type f -print \
    | grep -Ei 'battery|fuel.?gauge|qg|fg.?profile|pmic|charger|thermistor|provision|bn61|m703' \
    > "$SUPER_AUDIT/SUPER-BATTERY-PATH-HITS.txt" || true
  grep -RInaI -E 'BN61|M703|BATTERY[.]PROVISION|PM855GUI|qcom,fg-profile-data|qcom,nom-batt-capacity-mah|qcom,pc-temp-|batterydata-M703|qg-battery-profile|qpnp-qg|qpnp-fg-gen4|thermistor|QG-D|QBG-D' \
    "$SUPER_FILES" 2>/dev/null | head -n 500 >> "$SUPER_AUDIT/SUPER-BATTERY-CONTENT-HITS.txt" || true

  PARTITION_COUNT=$(($(wc -l < "$SUPER_AUDIT/SUPER-PARTITION-MANIFEST.tsv") - 1))
  {
    echo
    echo "Dynamic partitions: $PARTITION_COUNT vendor/odm/product/system_ext partition image(s) extracted and hashed."
    echo "Partition manifest: $SUPER_AUDIT/SUPER-PARTITION-MANIFEST.tsv"
    echo "Battery-related file paths: $(wc -l < "$SUPER_AUDIT/SUPER-BATTERY-PATH-HITS.txt" | tr -d '[:space:]')"
    echo "Battery-related file/string hits: $(wc -l < "$SUPER_AUDIT/SUPER-BATTERY-CONTENT-HITS.txt" | tr -d '[:space:]')"
    echo "Filesystem extraction log: $SUPER_AUDIT/SUPER-FILESYSTEM-EXTRACTION.log"
  } | tee -a "$REPORT"
  sed -n '1,250p' "$SUPER_AUDIT/SUPER-BATTERY-PATH-HITS.txt" | tee -a "$REPORT"
  sed -n '1,500p' "$SUPER_AUDIT/SUPER-BATTERY-CONTENT-HITS.txt" | tee -a "$REPORT"

  # Keep only compact, reproducible evidence in the artifact.
  rm -rf "$SUPER_PARTS" "$SUPER_FILES" "$SUPER_TOOL" "$SUPER_BIN"
else
  echo "WARNING: no super.img member found in the checksum-verified India fastboot ROM; dynamic partitions were not inspected." | tee -a "$REPORT"
fi


BATTERY_HITS="$OUT/india-device-tree-battery-hits.txt"
M703_PROFILE_HITS="$OUT/india-M703-profile-details.txt"
M703_PROFILE_MANIFEST="$OUT/india-M703-profile-manifest.tsv"
M703_PROFILE_COUNT=0
: > "$BATTERY_HITS"
: > "$M703_PROFILE_HITS"
printf 'dtbo\tprofile\tbytes\tsha256\n' > "$M703_PROFILE_MANIFEST"

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

  local node node_file node_sha node_bytes
  for node in qcom,m703-atl-6000mah qcom,m703-pm7150b-atl-5160mah; do
    if grep -qE "${node}[[:space:]]*\{" "$dts"; then
      node_file="$(mktemp "$OUT/m703-node.XXXXXX")"
      awk -v target="$node" '
        index($0, target) && index($0, "{") { capture = 1; depth = 0 }
        capture {
          print
          line = $0
          opens = gsub(/\{/, "", line)
          closes = gsub(/\}/, "", line)
          depth += opens - closes
          if (depth == 0) capture = 0
        }
      ' "$dts" > "$node_file"
      if [[ -s "$node_file" ]]; then
        node_sha="$(sha256sum "$node_file" | awk '{print $1}')"
        node_bytes="$(wc -c < "$node_file" | tr -d '[:space:]')"
        printf '%s\t%s\t%s\t%s\n' "$(basename "$dts")" "$node" "$node_bytes" "$node_sha" >> "$M703_PROFILE_MANIFEST"
        if ! grep -qF "$node_sha" "$M703_PROFILE_HITS"; then
          {
            printf '=== %s: %s (sha256 %s) ===\n' "$label" "$node" "$node_sha"
            cat "$node_file"
            printf '\n'
          } >> "$M703_PROFILE_HITS"
        fi
        M703_PROFILE_COUNT=$((M703_PROFILE_COUNT + 1))
      fi
      rm -f "$node_file"
    fi
  done
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

if [[ "$M703_PROFILE_COUNT" -gt 0 ]]; then
  echo "PASS: extracted $M703_PROFILE_COUNT M703 QG profile node occurrence(s) from the official India DTBO." | tee -a "$REPORT"
  echo "M703 profile manifest: $M703_PROFILE_MANIFEST" | tee -a "$REPORT"
else
  echo "WARNING: no M703 QG profile node was found in the official India DTBO." | tee -a "$REPORT"
  echo "No M703 profile node was found in the official India DTBO." > "$M703_PROFILE_HITS"
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

echo | tee -a "$REPORT"
echo "=== Deep EFI section extraction (uefi_firmware 1.16) ===" | tee -a "$REPORT"
DEEP_ROOT="$OUT/uefi-deep"
TOOL_DIR="$OUT/uefi-tooling"
VENV="$OUT/uefi-venv"
DEEP_MANIFEST="$DEEP_ROOT/DEEP-UEFI-MANIFEST.tsv"
DEEP_HITS="$DEEP_ROOT/DEEP-UEFI-SEARCH.txt"
mkdir -p "$DEEP_ROOT/xbl" "$TOOL_DIR"
printf 'path\tbytes\tsha256\n' > "$DEEP_MANIFEST"
: > "$DEEP_HITS"
python3 -m venv "$VENV"
set +e
"$VENV/bin/python" -m pip download --disable-pip-version-check --no-deps --no-binary=:all: \
  --dest "$TOOL_DIR" uefi_firmware==1.16 2>&1 | tee "$DEEP_ROOT/pip-download.log"
pip_download_status=${PIPESTATUS[0]}
set -e
SDIST="$TOOL_DIR/uefi_firmware-1.16.tar.gz"
if [[ "$pip_download_status" -eq 0 && -s "$SDIST" ]]; then
  echo "1626b9930b1006f9ec10b75ef889ffc17c632e0b43a4aba07a1090d9023133ea  $SDIST" \
    | sha256sum -c - | tee -a "$REPORT"
  set +e
  "$VENV/bin/python" -m pip install --disable-pip-version-check --no-deps "$SDIST" \
    2>&1 | tee "$DEEP_ROOT/pip-install.log"
  pip_install_status=${PIPESTATUS[0]}
  set -e
  if [[ "$pip_install_status" -eq 0 ]]; then
    set +e
    "$VENV/bin/uefi-firmware-parser" -b -e -o "$DEEP_ROOT/xbl" "$XBL" \
      2>&1 | tee "$DEEP_ROOT/uefi-firmware-parser.log" | tee -a "$REPORT"
    deep_parser_status=${PIPESTATUS[0]}
    set -e
    echo "Deep UEFI parser exit status: $deep_parser_status" | tee -a "$REPORT"
    if [[ "$deep_parser_status" -ne 0 ]]; then
      echo "WARNING: deep UEFI parser returned $deep_parser_status; inspect its log and partial extraction." \
        | tee -a "$REPORT"
    fi
  else
    echo "WARNING: uefi_firmware 1.16 installation failed (exit $pip_install_status); custom XBL parser results remain available." \
      | tee -a "$REPORT"
  fi
else
  echo "WARNING: could not download the pinned uefi_firmware 1.16 source distribution; deep extraction skipped." \
    | tee -a "$REPORT"
fi

if [[ -d "$DEEP_ROOT/xbl" ]]; then
  while IFS= read -r -d '' deep_file; do
    rel="${deep_file#"$DEEP_ROOT"/xbl/}"
    bytes="$(wc -c < "$deep_file" | tr -d '[:space:]')"
    digest="$(sha256sum "$deep_file" | awk '{print $1}')"
    printf '%s\t%s\t%s\n' "$rel" "$bytes" "$digest" >> "$DEEP_MANIFEST"
    if strings -a "$deep_file" | grep -Ei 'BATTERY[.]PROVISION|M703|BN61|BN57|ATL|PM855|QP(NP|N)|qcom,fg|nom-batt-capacity|fg-profile-data|thermistor|DS28E16|fuel.?gauge' \
      > "$DEEP_ROOT/deep-file-hits.tmp"; then
      {
        printf '=== %s ===\n' "$rel"
        head -n 80 "$DEEP_ROOT/deep-file-hits.tmp"
        printf '\n'
      } >> "$DEEP_HITS"
    fi
  done < <(find "$DEEP_ROOT/xbl" -type f -print0 | sort -z)
fi
rm -f "$DEEP_ROOT/deep-file-hits.tmp"
if [[ ! -s "$DEEP_HITS" ]]; then
  echo "No matching battery/BN61/M703/PM855GUI strings in deep-extracted XBL sections." > "$DEEP_HITS"
fi
echo "Deep UEFI extracted files: $(($(wc -l < "$DEEP_MANIFEST") - 1))" | tee -a "$REPORT"
echo "Deep UEFI manifest: $DEEP_MANIFEST" | tee -a "$REPORT"
echo "Deep UEFI search report: $DEEP_HITS" | tee -a "$REPORT"
echo "=== Deep UEFI battery-string hits (first 600 lines) ===" | tee -a "$REPORT"
sed -n '1,600p' "$DEEP_HITS" | tee -a "$REPORT"

while IFS= read -r member; do
  [[ -n "$member" ]] || continue
  image="$OUT/extracted/$member"
  [[ "$image" == "$XBL" ]] && continue
  name="$(basename "$member")"
  name="${name%.*}"
  if [[ "$name" == "super" ]]; then
    continue
  fi
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
