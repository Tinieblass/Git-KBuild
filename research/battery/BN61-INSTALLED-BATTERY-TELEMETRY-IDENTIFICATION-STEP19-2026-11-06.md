# BN61 — auditoría inversa con telemetría da batería instalada, step 19

Data: 2026-11-06
Repositorio: Tinieblass/Git-KBuild
Rama: Flash-Kernel

## Obxectivo

A BN61 Nohon 6000mAh está instalada no POCO F3 (alioth, SM8250). Isto permite pasar dunha reconstrución baseada en perfís proxy a unha identificación experimental do comportamento real da unidade, sen desmontala e sen modificar o kernel nin o perfil.

Este documento define unha ruta de extracción **só lectura**. Aínda non se recibiron datos do dispositivo; non se afirma que ningunha propiedade concreta estea exposta na ROM actual.

## 1. Evidencia do controlador Qualcomm

O controlador público `qpnp-fg-gen4.c` para PM8150B define o Fuel Gauge Gen4 e expón unha fonte de alimentación chamada `bms`. Segundo a revisión do controlador, a lista de propiedades inclúe:

- `voltage_now`, `voltage_avg`, `voltage_ocv`
- `current_now`, `current_avg`
- `temp`
- `resistance`
- `esr_actual`, `esr_nominal`
- `capacity`, `capacity_raw`
- `charge_counter`, `charge_now`, `charge_full`, `charge_full_design`
- `cycle_counts`, `soh`
- `battery_type`, `resistance_id`
- propiedades adicionais dependentes da revisión, como `constant_charge_voltage` e datos de carga.

Fontes:
- https://android.googlesource.com/kernel/msm/%2B/ee690bb327ba17c858522b0260d388055d7b262e/drivers/power/supply/qcom/qpnp-fg-gen4.c
- https://android.googlesource.com/kernel/msm/%2B/074e4ba126d86174a7633c5416debff514b4a270/drivers/power/supply/qcom/qpnp-fg-gen4.c

**Limitación:** isto proba que o controlador sabe fornecer esas propiedades, non que todas estean compiladas, habilitadas ou accesibles no kernel HyperOS actual do alioth. A inspección real de `/sys/class/power_supply` é o primeiro paso.

## 2. Inventario de lectura no teléfono

En Termux, con acceso root dispoñible, o inventario pódese facer sen escribir nada no sistema:

```sh
su -c 'for d in /sys/class/power_supply/*; do
  echo "===== $d ====="
  for p in type status capacity capacity_raw voltage_now voltage_avg voltage_ocv current_now current_avg temp resistance esr_actual esr_nominal charge_counter charge_now charge_full charge_full_design cycle_count cycle_counts soh battery_type resistance_id constant_charge_voltage; do
    if [ -r "$d/$p" ]; then
      printf "%-28s " "$p"
      cat "$d/$p"
    fi
  done
done'
```

Este comando só le os atributos existentes e imprime os valores. Non cambia perfís, propiedades persistentes, voltaxes, carga nin configuración.

O resultado debe conservar o nome da fonte (`bms`, `battery`, `usb`, etc.) porque non se deben mesturar os valores do BMS cos valores agregados da batería Android.

## 3. Unidades e interpretación inicial

No ABI habitual de Linux power_supply e no controlador Qualcomm:
- `voltage_now`, `voltage_avg`, `voltage_ocv`: normalmente microvoltios.
- `current_now`, `current_avg`: normalmente microamperios; o signo depende da implementación.
- `temp`: habitualmente décimas de °C no controlador Qualcomm.
- `resistance`, `esr_actual`, `esr_nominal`: verificar unidade na implementación concreta antes de converter; non asumir que todos usan a mesma escala.
- `charge_counter`, `charge_now`, `charge_full`: verificar ABI e implementación; normalmente microampere-hora en power_supply.

Non converter nin axustar ata comprobar magnitudes, signos, estabilidade e coherencia entre fontes.

## 4. Captura dinámica necesaria

Unha mostra estática non identifica constantes de tempo. Cómpre unha serie temporal sincronizada:
- timestamp monotónico ou epoch;
- tensión instantánea e media;
- corrente instantánea e media;
- temperatura;
- OCV se está dispoñible;
- ESR/resistencia reportada polo BMS;
- SOC e contador de carga.

Unha frecuencia de 1 Hz durante transicións naturais de carga/descarga pode revelar caída instantánea e recuperación. Para constantes rápidas podería ser necesaria unha frecuencia maior, se o BMS e o sysfs realmente actualizan a esa velocidade. A frecuencia de lectura non equivale á frecuencia de actualización do sensor.

Non se debe provocar unha descarga extrema, quentar a batería, bloquear proteccións nin realizar ciclos profundos só para obter datos. As transicións normais de pantalla/CPU/carga son suficientes para unha primeira identificación.

## 5. Que parámetros se poden identificar

Con tensión/corrente sincronizadas e escalóns suficientemente claros:
- resistencia serie aproximada: caída inmediata de tensión dividida polo cambio de corrente, con corrección de offset e retardo;
- constantes de tempo RC: axuste da relaxación tras o pulso, se hai resolución temporal suficiente e se separan polo menos dous modos;
- dependencia con SOC e temperatura: repetir en bandas distintas, sen forzar condicións inseguras;
- contraste do modelo: comparar estimación do BMS (`resistance`, `esr_actual`) co ESR dinámico calculado.

Con estas medidas poderemos restrinxir mellor o modelo QG e os parámetros de resistencia lenta. Non se debe asumir que unha resistencia medida identifica directamente KI ou slope.

## 6. O que non se obtén automaticamente

- KI non é unha simple transformación de OCV/FCC nin de resistencia; é unha familia de ganancias do estimador Gen4.
- Slope-limit é outra familia de calibración.
- Rslow require identificar a resposta lenta e a forma exacta de codificación.
- Un rexistro de sysfs non recupera por si só o blob de 416 bytes orixinal nin o seu checksum.

A ponte a Gen4 seguirá requirindo referencias comparables, coñecemento exacto do formato e validación do checksum. Non se fabricará un blob de instalación a partir de parámetros non identificados.

## 7. Estado e seguinte acción

Estado:
- Perfil QG proxy de 5850mAh: candidato matemático provisional, step 17.
- Sensibilidade OCV/dQdV: calculada sobre a curva proxy, step 18.
- Telemetría real da BN61: pendente de inventario no teléfono.
- KI/slope/Rslow e blob Gen4 416 bytes: aínda non identificados.

Seguinte acción: executar o inventario de lectura da sección 2 e compartir a saída completa. A partir dela prepararase unha captura temporal adaptada só ás propiedades que existan realmente.

Non se modificou o teléfono, o kernel, DTBO, perfil de batería nin configuración persistente.
