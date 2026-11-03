# Flash Kernel — POCO F3 (alioth)

**Flash Kernel** é un proxecto de compilación e empaquetado de kernel mantido por **Tinieblass**, dedicado exclusivamente ao dispositivo **POCO F3 (alioth)**.

## Plataforma

- Dispositivo: POCO F3 — `alioth`
- ROM de destino: Xiaomi HyperOS 3
- Android: 16
- Base do kernel: Linux 4.19.325, fonte SM8250 fixada nun commit concreto
- KernelSU: backslashxx, revisión fixada por SHA
- NoMount: v2.2.0, integración suxeita a compilación e validación
- Batería: perfil stock FMT/GY 4520 mAh e DTBO J3S Sun 5000 mAh separado
- BN61 -6K: reservado; non existe aínda un perfil Gen4 validado nin un DTBO instalable

## Empaquetado de validación

O workflow manual de empaquetado constrúe temporalmente dous ZIPs para comprobar o contido e os hashes:

| Nome xerado no runner | Perfil |
|---|---|
| `FlashKernel<BUILD_DATE>.zip` | Batería stock |
| `FlashKernel<BUILD_DATE>-5k.zip` | J3S Sun 5000 mAh |

Este workflow é só de validación: non carga os ZIP como artefactos, non publica releases e non os distribúe. Non se debe interpretar a creación temporal dun ZIP como unha compilación validada no teléfono. O perfil `-6K` permanece reservado e non se xera.

O instalador mostra a información detectada do dispositivo e da ROM, pero non debe introducir bloqueos de compatibilidade por modelo, versión de HyperOS ou versión de Android.

## Compilar e validar

1. Abre a pestana **Actions**.
2. Executa **Flash Kernel v1.7 - alioth** para compilar o kernel e os DTBO.
3. Comproba que a compilación remata correctamente e que o artefacto bruto inclúe os hashes e o informe.
4. Só para validación do empaquetado, executa manualmente o workflow de empaquetado co `RAW_RUN_ID` da compilación correcta.
5. Revisa os resultados de integridade; o workflow non publica nin ofrece os ZIP para descarga.

## Seguridade

- Non instales artefactos procedentes de execucións fallidas ou incompletas.
- Unha compilación correcta e unha comprobación estática non substitúen as probas reais no POCO F3 alioth.
- O perfil J3S Sun é independente do perfil stock e non debe confundirse coa BN61.
- Non se debe crear un perfil BN61 cambiando só a capacidade nominal nin extrapolando as curvas QG a un payload Gen4.
- Mantén sempre o DTBO stock como opción de recuperación; non instales a variante experimental -6K mentres non exista caracterización Gen4 auténtica e validación física.

## Créditos

- Fonte do kernel e colaboradores upstream.
- Proxecto backslashxx KernelSU.
- NoMount.
- AnyKernel3, de osm0sis.
- Integración e empaquetado: **Tinieblass**.
