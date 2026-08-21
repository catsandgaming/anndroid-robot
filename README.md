# Animatronic Figure Build (AnnDroid)

# BEFORE YOU EVEN START DO NOT GO ON UNLESS YOU ARE A PROFESSIONAL AND YOU KNOW WHAT YOU ARE DOING!
# Animatronic Figure Build

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

---

# KiCad Symbol Libraries
This directory contains the schematic symbol libraries (`.kicad_sym`) for the Raspberry Pi Compute Module series (CM4 and CM5) for KiCad 9.
---
## 📦 Contents
| File Name | Description |
| :--- | :--- |
| `Raspberry-Pi-CM4.kicad_sym` | Schematic symbols for Raspberry Pi Compute Module 4 |
| `Raspberry-Pi-CM5.kicad_sym` | Schematic symbols for Raspberry Pi Compute Module 5 |
---
## ⚙️ Installation Guide
Follow these steps to add the symbol libraries to your global or project-level KiCad 9 configuration:
1. Open **KiCad 9**.
2. From the main window, select **Preferences** > **Manage Symbol Libraries...**
3. Select either the **Global Libraries** tab (available across all projects) or **Project Specific Libraries** tab.
4. Click the **`+`** (Add existing library) button at the bottom of the table.
5. Configure the library entries:
   - **Nickname:** `Raspberry-Pi-CM4`
   - **Library Path:** Browse to and select `Raspberry-Pi-CM4.kicad_sym`
   - **Plugin Type:** `KiCad`
6. Repeat for the CM5 library:
   - **Nickname:** `Raspberry-Pi-CM5`
   - **Library Path:** Browse to and select `Raspberry-Pi-CM5.kicad_sym`
   - **Plugin Type:** `KiCad`
7. Click **OK** to save and apply settings.
---
## 🛠️ Usage in Schematic Editor
1. Open your project's **Schematic Editor** (`.kicad_sch`).
2. Press **`A`** or click **Add Symbol** on the right toolbar.
3. In the search box, filter by `Raspberry-Pi-CM4` or `Raspberry-Pi-CM5`.
4. Select your module variant and place it on the schematic canvas.
---
## 🚨 Required Environment Path Setup
For associated footprint assignments and 3D models to link correctly when updating your PCB layout, ensure the base environment variable is configured:
1. Go to **Preferences** > **Configure Paths...**
2. Add an environment variable:
   - **Name:** `KICAD9_USER_RPICM_REPO_DIR`
   - **Path:** Absolute path to the repository root directory (e.g., `/path/to/Raspberry-Pi-Compute-Module-KiCad-main`)
3. Click **OK**.
---
## 📄 License & Attribution
Refer to the root [LICENSE](../../LICENSE) file for usage and distribution guidelines.

---

## Installation
TBC — full setup and assembly instructions will be added in the coming
months as the build progresses.

## Notes
- Likeness and voice: if this figure depicts a real, identifiable person
  and is intended for anything beyond private personal use, obtain
  permission for likeness and voice use.
- This is a prototype-stage project; specs and BOM quantities may change
  as parts are bench-tested.
