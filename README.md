# Flash Kernel — POCO F3 (alioth)

**Flash Kernel** é un proxecto de compilación e empaquetado de kernel mantido por **Tinieblass**, dedicado exclusivamente ao dispositivo **POCO F3 (alioth)**.

## Plataforma actual

- Dispositivo: POCO F3 — `alioth`
- ROM de destino: Xiaomi HyperOS 3
- Android: 16
- Base do kernel: Linux 4.19.325, fonte SM8250 fixada nun commit concreto
- KernelSU: controlador backslashxx KernelSU
- NoMount: integrado na compilación
- VoWiFi/IMS: consérvase o código da fonte; este fluxo de traballo non modifica os ficheiros IMS.

## Paquetes instalables

O workflow de empaquetado xera dous ZIP independentes:

| Arquivo | Perfil de batería |
|---|---|
| `Flash-Kernel-alioth.zip` | Batería stock |
| `Flash-Kernel-alioth-5K.zip` | Perfil J3S Sun de 5000 mAh |

O instalador verifica que o dispositivo sexa `alioth` e que a ROM sexa HyperOS. O perfil de 5000 mAh selecciónase unicamente co ZIP cuxo nome remata en `-5K`; o paquete normal, sen sufixo, utiliza o perfil stock. O sufixo `-6K` queda reservado para a variante BN61 ata dispoñer dun perfil Gen4 validado; non se debe instalar un perfil aproximado.

## Compilar e empaquetar

1. Abre a pestana **Actions**.
2. Executa **Flash Kernel - alioth** para compilar o kernel.
3. Só despois dunha compilación correcta, executa o workflow de empaquetado.
4. Introduce en `RAW_RUN_ID` o identificador da execución que xerou o artefacto `flash-kernel-alioth-raw`.
5. Descarga os dous ZIP do artefacto `Flash-Kernel-alioth-flashable`.

## Seguridade

- Non instales artefactos procedentes de execucións fallidas ou incompletas.
- Unha compilación correcta non substitúe as probas reais no dispositivo.
- Non cambies o nome do ZIP stock para obter o perfil de 5000 mAh: utiliza o paquete `-5K` xerado polo workflow. O sufixo `-6K` non se debe usar ata que exista un DTBO BN61 validado.

## Créditos

- Fonte do kernel e colaboradores upstream.
- Proxecto backslashxx KernelSU.
- NoMount.
- AnyKernel3, de osm0sis.
- Integración e empaquetado: **Tinieblass**.
