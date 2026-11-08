# BN61 read-only capture for the booted Butterflies kernel

This Termux script captures live, software-reported kernel and power-supply values from the already booted alioth device. It does not change kernel settings, battery data, sysfs state, or charger state. It makes no network calls and does not save a file on the phone; output is printed in the terminal.

## Run

1. Save `BN61-READONLY-CAPTURE-2026-11-08.sh` in the phone's Downloads folder.
2. In Termux, run:

   ```sh
   su -c 'sh /sdcard/Download/BN61-READONLY-CAPTURE-2026-11-08.sh'
   ```

3. Copy the complete terminal output into the research record. Do not connect a charger for this capture. If the phone already reports charging or USB connected, the script records that state without taking any action.

If root access is denied, stop there; do not change permissions or settings to make the capture work.

## Reading the result

- Values are printed exactly as exposed by the running kernel. `UNAVAILABLE` means that path was not readable or absent.
- A BMS `battery_type` label is an identification readback. It does not prove which 416-byte Gen4 profile is resident in SRAM.
- `voltage_now`, `current_now`, and `temp` are software reports, not calibrated measurements at the cell terminals. The script deliberately does not apply corrections or infer physical overvoltage.
- `physical_cell_terminal_voltage=NOT_MEASURED` and `charge_test_authorized=NO` remain explicit.

This is an install-and-capture diagnostic for real read-only device data. It is not a BN61 `-6K` charging profile, a kernel/DTBO build, or a charging test. The profile stays blocked until the exact pack specification and profile provenance are authenticated and a manufacturer or qualified laboratory confirms the physical cell voltage before any charge experiment.

