#!/system/bin/sh
# BN61 live read-only capture for the currently booted alioth kernel.
# No sysfs writes, network access, charging actions, or persistent output.

set -u

echo "BN61_READONLY_CAPTURE=1"
echo "capture_timestamp=$(date '+%Y-%m-%dT%H:%M:%S%z' 2>/dev/null)"
echo "uid=$(id -u 2>/dev/null)"
echo "kernel_release=$(uname -r 2>/dev/null)"
echo "kernel_uname=$(uname -a 2>/dev/null)"
if [ -r /proc/version ]; then
  printf 'proc_version='
  cat /proc/version
else
  echo "proc_version=UNAVAILABLE"
fi
if command -v getprop >/dev/null 2>&1; then
  echo "build_fingerprint=$(getprop ro.build.fingerprint 2>/dev/null)"
  echo "android_release=$(getprop ro.build.version.release 2>/dev/null)"
  echo "build_id=$(getprop ro.build.id 2>/dev/null)"
else
  echo "build_properties=UNAVAILABLE"
fi

emit_path() {
  path="$1"
  if [ -r "$path" ]; then
    value=$(cat "$path" 2>/dev/null) || value="READ_ERROR"
    printf '%s=%s\n' "$path" "$value"
  else
    printf '%s=UNAVAILABLE\n' "$path"
  fi
}

echo "--- LIVE POWER-SUPPLY READBACKS (raw kernel values) ---"
for path in \
  /sys/class/power_supply/battery/status \
  /sys/class/power_supply/battery/health \
  /sys/class/power_supply/battery/voltage_now \
  /sys/class/power_supply/battery/current_now \
  /sys/class/power_supply/battery/temp \
  /sys/class/power_supply/usb/online \
  /sys/class/power_supply/bms/battery_type \
  /sys/class/power_supply/bms/resistance_id \
  /sys/class/power_supply/bms/capacity \
  /sys/class/power_supply/bms/charge_full \
  /sys/class/power_supply/bms/charge_full_design \
  /sys/class/power_supply/bms/voltage_now \
  /sys/class/power_supply/bms/current_now \
  /sys/class/power_supply/bms/temp \
  /sys/class/power_supply/bms/constant_charge_voltage \
  /sys/class/power_supply/bms/voltage_max_design \
  /sys/class/power_supply/bms/fastcharge_mode \
  /sys/class/power_supply/bms/vbatt_full_vol \
  /sys/class/power_supply/bms/ffc_vbatt_full_vol \
  /sys/class/power_supply/main/voltage_max
do
  emit_path "$path"
done

status=$(cat /sys/class/power_supply/battery/status 2>/dev/null || true)
usb_online=$(cat /sys/class/power_supply/usb/online 2>/dev/null || true)
if [ "$status" = "Charging" ] || [ "$usb_online" = "1" ]; then
  echo "reported_charger_state=CONNECTED_OR_CHARGING_AT_CAPTURE"
else
  echo "reported_charger_state=NOT_REPORTED_CONNECTED_AT_CAPTURE"
fi
echo "active_gen4_sram_profile=NOT_ESTABLISHED_BY_THIS_CAPTURE"
echo "physical_cell_terminal_voltage=NOT_MEASURED"
echo "charge_test_authorized=NO"
echo "capture_scope=READ_ONLY_SOFTWARE_REPORTS_ONLY"

