#!/system/bin/sh
# Passive-only battery telemetry capture for BN61 characterization.
# Reads sysfs; never writes charge limits, current, voltage, or power_supply nodes.

set -u

BASE="${BATTERY_SYSFS:-/sys/class/power_supply/battery}"
INTERVAL="${INTERVAL_SECONDS:-5}"
DURATION="${DURATION_SECONDS:-1800}"
OUT="${1:-/sdcard/Download/BN61-telemetry-$(date +%Y%m%d-%H%M%S).csv}"

if [ ! -d "$BASE" ]; then
    echo "Battery power_supply directory not found: $BASE" >&2
    exit 2
fi

read_attr() {
    file="$BASE/$1"
    if [ -r "$file" ]; then
        value="$(cat "$file" 2>/dev/null | tr '\r\n,' '   ')"
        printf '%s' "$value"
    fi
}

mkdir -p "$(dirname "$OUT")" 2>/dev/null || exit 3
{
    printf '%s\n' 'epoch,status,health,present,capacity_pct,voltage_now_uV,voltage_ocv_uV,current_now_uA,current_avg_uA,temp_raw,charge_counter_uAh,charge_full_uAh,charge_full_design_uAh,cycle_count,technology'
} > "$OUT" || exit 4

start="$(date +%s)"
end=$((start + DURATION))

while :; do
    now="$(date +%s)"
    [ "$now" -ge "$end" ] && break

    printf '%s' "$now" >> "$OUT"
    for attr in status health present capacity voltage_now voltage_ocv current_now current_avg temp charge_counter charge_full charge_full_design cycle_count technology; do
        printf ',%s' "$(read_attr "$attr")" >> "$OUT"
    done
    printf '\n' >> "$OUT"

    sleep "$INTERVAL"
done

echo "Passive capture complete: $OUT"
echo "No charging or battery-control sysfs node was written."
