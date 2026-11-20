# TireForge Industries — Maintenance Manual, Production Line A

Document ID: TF-MM-LA-2026. Revision 4. Owner: Reliability Engineering.

This manual is fictional. It supports the Microsoft Foundry workshop labs.

## How to use this manual

1. Find the machine by its machine ID.
2. Compare the sensor pattern with the failure modes in the table for that machine.
3. Follow the procedure that the table names.
4. Open a work order for every procedure. A shift supervisor must approve each work order.

## MX-001 Mixer

Function: blends raw rubber with carbon black and chemicals.

Normal operating range: temperature 60–90 °C, pressure 2.0–4.0 bar, vibration 0–4.5 mm/s, speed 40–65 rpm.

| Sensor pattern | Likely cause | Procedure |
| --- | --- | --- |
| Temperature high and vibration high | Rotor bearing has too little grease, or the cooling jacket flow is low | MX-PRC-03 |
| Vibration high alone | Rotor imbalance or worn drive coupling | MX-PRC-05 |
| All readings high together | Runaway batch or control fault | MX-PRC-09 (stop the mixer now) |

MX-PRC-03 — Bearing and cooling check:

1. Reduce the speed to 40 rpm and finish the current batch.
2. Stop the mixer and apply lockout/tagout.
3. Grease both rotor bearings with grease TF-GR-2 (120 g for each bearing).
4. Check the cooling jacket flow. The flow must be 35 L/min or more.
5. If the bearing temperature stays above 85 °C after one hour, replace bearing TF-MX-B220.

Grease interval: every 500 operating hours.

## EX-002 Extruder

Function: shapes rubber into tread profiles.

Normal operating range: temperature 100–130 °C, pressure 10.0–15.0 bar, vibration 0–3.5 mm/s, speed 20–40 rpm.

| Sensor pattern | Likely cause | Procedure |
| --- | --- | --- |
| Temperature high and pressure high | Partial blockage at the die or a clogged screen pack | EX-PRC-02 |
| Vibration high alone | Screw wear or gearbox wear | EX-PRC-06 |

EX-PRC-02 — Die and screen pack check:

1. Reduce the screw speed to 20 rpm.
2. Stop the extruder and apply lockout/tagout.
3. Replace the screen pack with part TF-EX-SP40.
4. Clean the die with the brass tool set. Do not use steel tools on the die.
5. Restart. Pressure must fall below 14 bar within 15 minutes.

## CP-003 Curing Press

Function: vulcanizes tyres under heat and pressure in the moulds. The press does not rotate. Normal speed is 0 rpm.

Normal operating range: temperature 140–180 °C, pressure 12.0–16.0 bar, vibration 0–3.0 mm/s.

| Sensor pattern | Likely cause | Procedure |
| --- | --- | --- |
| Pressure high alone | Pressure relief valve PRV-3 is stuck closed | CP-PRC-04 |
| Temperature high and pressure high | Bladder seal leak or steam valve fault | CP-PRC-07 |
| Vibration high (the press does not rotate, so any vibration above 3.0 mm/s is a fault) | Loose platen mounting bolts or hydraulic pump cavitation | CP-PRC-07 |
| Two or more readings above the limit | Compound failure | CP-PRC-07, and stop the press now |

CP-PRC-07 — Curing press compound fault:

1. Stop the press now. Do not wait for the cure cycle to end.
2. Release the steam and hydraulic pressure. Wait until the pressure is 0 bar.
3. Apply lockout/tagout.
4. Inspect pressure relief valve PRV-3. Replace it with part TF-CP-PRV3 if it does not open at 16.5 bar on the test bench.
5. Torque the four platen mounting bolts to 320 N·m.
6. Replace the bladder seal kit with part TF-CP-SK12.
7. Hold all tyres from the stopped cycle for quality inspection.
8. Do not restart the press until Reliability Engineering signs the restart checklist.

CP-PRC-04 — Pressure relief valve test:

1. Isolate the hydraulic circuit.
2. Remove PRV-3 and test it on the bench.
3. The valve must open between 16.0 and 16.5 bar.

## CU-004 Cooling Unit

Function: cools cured tyres slowly to prevent thermal shock.

Normal operating range: temperature 20–45 °C, pressure 0.8–1.5 bar, vibration 0–2.0 mm/s, speed 80–150 rpm.

| Sensor pattern | Likely cause | Procedure |
| --- | --- | --- |
| Pressure low and speed low | Coolant pump failure or worn impeller | CU-PRC-01 |
| Temperature high alone | Fouled heat exchanger | CU-PRC-03 |

CU-PRC-01 — Coolant pump check:

1. Stop the cooling unit.
2. Hold all tyres in the unit for quality inspection. They can have thermal damage.
3. Replace the pump impeller with part TF-CU-P15.

## IS-005 Inspection Station

Function: checks tyre quality with vibration and dimensional analysis.

Normal operating range: temperature 18–30 °C, pressure 0.8–1.2 bar, vibration 0–4.0 mm/s, speed 1500–2200 rpm.

| Sensor pattern | Likely cause | Procedure |
| --- | --- | --- |
| Vibration high alone | Spindle bearing wear or a loose sensor mount | IS-PRC-02 |

IS-PRC-02 — Spindle and sensor mount check:

1. Check the sensor mount first. A loose mount caused a false alarm before (see incident INC-2026-009).
2. If the mount is tight, replace spindle bearing TF-IS-B60.
3. Recalibrate the station with the master tyre.
4. Above 4.0 mm/s, quality results are not reliable. Re-inspect all tyres since the last good calibration.
