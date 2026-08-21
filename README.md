# ⚠️ BEFORE YOU EVEN START ⚠️
## DO NOT GO ON UNLESS YOU ARE A PROFESSIONAL AND YOU KNOW WHAT YOU ARE DOING!

---

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

This project uses two KiCad symbol/footprint libraries, covering the main
compute module and the microphone module. Both follow the same general
install pattern: add the library file(s) via **Preferences > Manage Symbol
Libraries...** (and **Manage Footprint Libraries...** where a footprint is
included), then verify in the Symbol/Footprint Editor before use.

| Library | Covers | KiCad Version |
| :--- | :--- | :--- |
| Raspberry Pi Compute Module | CM4, CM5 (symbols only) | KiCad 9 |
| INMP441ACEZ-R7 | Digital MEMS microphone (symbol + footprint) | KiCad 6+ |

---

## 1. Raspberry Pi Compute Module Library

Schematic symbol libraries (`.kicad_sym`) for the Raspberry Pi Compute
Module series (CM4 and CM5), for KiCad 9.

### 📦 Contents
| File Name | Description |
| :--- | :--- |
| `Raspberry-Pi-CM4.kicad_sym` | Schematic symbols for Raspberry Pi Compute Module 4 |
| `Raspberry-Pi-CM5.kicad_sym` | Schematic symbols for Raspberry Pi Compute Module 5 |

### ⚙️ Installation Guide
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

### 🛠️ Usage in Schematic Editor
1. Open your project's **Schematic Editor** (`.kicad_sch`).
2. Press **`A`** or click **Add Symbol** on the right toolbar.
3. In the search box, filter by `Raspberry-Pi-CM4` or `Raspberry-Pi-CM5`.
4. Select your module variant and place it on the schematic canvas.

### 🚨 Required Environment Path Setup
For associated footprint assignments and 3D models to link correctly when updating your PCB layout, ensure the base environment variable is configured:
1. Go to **Preferences** > **Configure Paths...**
2. Add an environment variable:
   - **Name:** `KICAD9_USER_RPICM_REPO_DIR`
   - **Path:** Absolute path to the repository root directory (e.g., `/path/to/Raspberry-Pi-Compute-Module-KiCad-main`)
3. Click **OK**.

### 📄 License & Attribution
Refer to the root [LICENSE](../../LICENSE) file for usage and distribution guidelines.

---

## 2. INMP441ACEZ-R7 Microphone Library

Official schematic symbol and PCB footprint library files for the
**INMP441ACEZ-R7** digital MEMS microphone, for KiCad 6 and newer.

### ⚠️ Important Download & Unzip Instructions
1. **Download:** Save the official `*.zip` archive.
2. **Extract:** Unzip the folder **as-is**. Do **NOT** rename the extracted folder.
3. **Structure:** Keep the internal file structure completely intact (including `.pretty`, `.kicad_mod`, and `.kicad_sym` files/folders).
> **Note:** Renaming the root extracted folder or altering internal directory paths will break absolute references and lead to footprint import errors in KiCad.

### 🛠️ KiCad Import Guide (V6 and Later)

#### Import Symbol (`.kicad_sym`)
1. Extract the contents of your downloaded `*.zip` file.
2. Launch KiCad and navigate to **Preferences** > **Manage Symbol Libraries...**
3. Select the **Global Libraries** tab (or **Project Specific Libraries** depending on your workflow).
4. Click **Browse Libraries** (the small folder icon at the bottom of the table).
5. Select the `*.kicad_sym` file from your extracted directory and click **Open**.
6. Verify the library appears in the table list, then click **OK**.
7. To verify, open the **Symbol Editor**, search for `INMP441ACEZ-R7` in the filter field, and double-click to view the component.

#### Import Footprint (`.pretty`)
1. Go to **Preferences** > **Manage Footprint Libraries...**
2. Select the **Global Libraries** tab.
3. Click **Browse Libraries** (the folder icon at the bottom).
4. Browse to and select the `.pretty` folder inside the extracted directory, then click **Open**.
5. Click **OK** to save and apply settings.

### 🔍 Verification Checklist
- [ ] Extracted folder name was **not** altered.
- [ ] Symbol displays correctly in the **Symbol Editor**.
- [ ] Footprint appears under library filter in **Footprint Editor**.
- [ ] Pin-out numbers on the schematic symbol match the physical pads on the footprint.

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
