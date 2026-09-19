# HD800 wireless conversion — revision A schematic

This is a connected engineering schematic draft, not a fabrication release. The main sheet links six circuit sheets: USB/charging, power, MCU/RF, left DAC, right DAC and balanced output. Global labels join nets across sheets. Original empty schematic is retained under `design/original-empty.kicad_sch`.

## Corrections to the supplied plan

- Balanced stereo requires four buffer channels. U5 and U8 provide two OPA1688 channels each, one for every driven audio leg.
- Eco/Turbo is an installation-time configuration, not an operating control. The four TMUX4827 input switches and four TMUX4827 output switches have been removed. This eliminates their component cost, DSBGA assembly and via-in-pad requirement.
- Each driven leg has a three-pad source selector and a separate two-pad Turbo input link. Eco bridges selector pads 1–2 and leaves the input link open. Turbo bridges selector pads 2–3 and closes the input link. These links isolate unpowered OPA1688 inputs in Eco without active switches.
- Q1/Q2 gate the positive amplifier supply; LM2776 generates the negative rail. Firmware reads fixed mode strap JP9 at boot and enables these rails only for a correctly strapped Turbo assembly. Eco can omit the complete amplifier power and buffer section.
- TP1–TP4 are 1.5 × 3 mm surface-mount wire pads for direct soldering to the left and right drivers. There is no headphone jack and no common audio return. Confirm pad size, wire gauge, strain relief and earcup mechanics before layout release.
- The DACs use separate mono differential configurations. HPREFA/B return to analog ground; L− and R− are driven outputs, never ground returns. Each DAC has its required charge-pump and reference capacitors, including separate FILT+ to VA and FILT− to −VA capacitors.
- CS43131 pin 36 (XTO) is grounded for external MCLK operation, following the manufacturer application diagram. Its project symbol models that terminal as passive for this configuration. This symbol must be revised if using a crystal oscillator instead. Firmware must select external MCLK operation.
- Supply and clock support were added around the nRF5340. VDDH/DCCH use the normal-voltage connection, with core/radio DC-DC support and decoupling. Use HFCLKAUDIO to produce 12.288 MHz for 48 kHz-family audio; a raw 32 MHz crystal clock is not the DAC clock configuration.
- IP2312 is provisionally configured for 1 A with 135 kΩ ICHG, using the fixed-4.20 V variant. Its reference inductor is changed to 1 µH, with a real ≥4 A saturation-rated component still to select. L2 intentionally has no assigned footprint.
- Q3/Q4 default charging off. CC sensing allows firmware to enable it only with a USB-C source advertising sufficient current (at least 1.5 A for this provisional setting). Rd resistors, USB ESD, battery sensing, thermistor connector and system-off switch were added.

## Required firmware behavior

At reset keep AMP_EN and CHG_EN low. Read MODE_SENSE from JP9 once during startup. Configure both DACs, distinct I2C addresses, mono differential routing, clock ratio, output range and volume before unmuting. Verify output polarity/channel mapping with a test signal.

In Eco, never assert AMP_EN. In Turbo, assert AMP_EN while the DACs remain muted, wait for both rails to settle, then ramp the DAC outputs up. On shutdown, mute/ramp down before clearing AMP_EN. This schematic does not support changing Eco/Turbo while powered. Configuration links and JP9 must agree before power-up.

Assembly configuration:

| Build | JP1/JP3/JP5/JP7 source selectors | JP2/JP4/JP6/JP8 input links | JP9 mode strap | Amplifier section |
|---|---|---|---|---|
| HD800 / Eco | Bridge 1–2 | Open | Eco | May be unpopulated |
| Low-impedance / Turbo | Bridge 2–3 | Closed | Turbo | Populate and validate |

The IP2312 has no separate system power-path output. Keep playback stopped during charging and verify charge termination with the remaining MCU/DAC load. Do not charge on a default-current USB source. Calibrate the CC ADC policy across tolerances and attachment states. The cell must permit the selected current and have a bonded compatible thermistor.

## Release blockers and limits

1. Verify the exact CS43131, antenna and configuration-switch footprints. Confirm EP pin mapping for the charger and DAC packages. Check the direct-driver solder pads and add mechanical strain relief appropriate to the installed wire. Assigned standard footprints also need procurement review.
2. Confirm the protected 1S battery's charge current, discharge current, thermistor curve, voltage limits and mechanical installation. Battery pack protection is external to this schematic. Validate charger startup, thermal dissipation, reverse current and charge termination.
3. The requested >250 mW into 18 Ω requires about 118 mA RMS / 167 mA peak through each driven output leg. The selected OPA1688 and LM2776 supply do not establish that capability. This target requires a separate output-stage/current-budget redesign or a relaxed load/power requirement. The HD800 high-impedance case still needs swing, distortion and stability measurements across battery voltage.
4. Verify amplifier capacitive-load stability, the provisional 1 Ω output resistors and startup/shutdown behavior. The negative rail is load dependent. Add an independently validated output protection strategy before permanently soldering valuable drivers to an untested prototype.
5. Copy Nordic's exact RF and DC-DC reference layout, verify crystal parameters, and tune the antenna/matching network inside the final earcup. The drawn RF values are preliminary. Layout, ground return and antenna clearance determine actual performance.
6. Validate capacitance after DC bias, ripple and temperature; printed capacitance/voltage and generic package assignments do not specify qualified BOM parts. In particular, confirm DAC charge-pump/reference capacitors and buck/charger inductors.
7. Radio/audio firmware, USB enumeration, clock synchronization, packet loss behavior, noise, latency, runtime and acoustic performance are not implemented or measured by this schematic task. 130 dBA, <10 ms and 33/47-hour values remain unverified targets.

## Sources and validation

- [Cirrus CS43131 datasheet](https://statics.cirrus.com/pubs/proDatasheet/CS43131_DS1155F2.pdf): pin table, typical application/mono differential diagrams, external clock and capacitor connections.
- [TI OPA1688 datasheet](https://www.ti.com/lit/ds/symlink/opa1688.pdf): pin map, supply, output-current and electrical limitations.
- [TI LM2776](https://www.ti.com/product/LM2776): inverting supply requirements.
- [Nordic nRF5340 reference circuitry](https://docs.nordicsemi.com/r/bundle/ps_nrf5340/page/chapters/ref_circuitry.html) and [clock documentation](https://docs.nordicsemi.com/r/bundle/ps_nrf5340/page/chapters/clock/doc/clock.html).
- [Johanson antenna product](https://www.johansontechnology.com/products/antennas/rf-antennas/2450at43b0100001e/).
- [IP2312 manufacturer datasheet, distributor-hosted copy](https://m.baixingks.com/upload/pdf/DX-IP2312.pdf).

KiCad MCP created the custom symbols and initial component schematic. Its generator placed labels away from pins, so the saved output was repaired and divided into connected hierarchical sheets with local scripts. `design/design-plan.json` is the intended pin-level connectivity; `design/check_netlist.py` compares it with KiCad's exported XML netlist. `design/erc.json` records KiCad ERC. Passing these checks establishes schematic connectivity and declared pin compatibility, not analog performance, correct firmware or manufacturing readiness.
