# Animatronic Figure Build (AnnDroid)

## Overview
Full-scale animatronic figure project — a 3D-printed shell over an internal
aluminum skeleton, with servo-driven arms, neck, jaw, and eyes, TTS-based
speech, and onboard logging. Controlled by a Raspberry Pi 5 + ESP32/Arduino
Mega pairing, with a PCA9685 driving all servo channels.

## Specs
- Height: 5'7" (170 cm)
- Skeleton: aluminum T-slot extrusion + tube, bearing-mounted joints
- Shell: PETG/ASA structural panels, resin face/hands, silicone skin overlay
- Motion: neck (pan/tilt), eyes (pan/tilt + eyelids), jaw (audio-driven),
  arms (shoulder/elbow/wrist, 2 DOF+ per side)
- Voice: TTS engine (generic/licensed voice — no real-person voice cloning)
- Compute: Raspberry Pi 5 (8GB) + ESP32/Mega for real-time servo timing
- Storage/logging: onboard SSD, SQLite/CSV logs of servo state, audio
  triggers, errors, uptime

## Documentation
See the project docs for full detail:
- 01_System_Architecture_Diagram
- 02_Mechanical_CAD_Models
- 03_Bill_of_Materials
- 04_Electronics_and_Wiring
- 05_Component_Datasheets
- 06_Control_Theory
- 07_Operating_Software
- 08_Source_Code
- 09_Calibration_Logs

## Installation
TBC — full setup and assembly instructions will be added in the coming
months as the build progresses.

## Notes
- Likeness and voice: if this figure depicts a real, identifiable person
  and is intended for anything beyond private personal use, obtain
  permission for likeness and voice use.
- This is a prototype-stage project; specs and BOM quantities may change
  as parts are bench-tested.
