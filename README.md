# 3DConsoleBridge

3DConsoleBridge lets you play native 3D console games (PS3, PS4, Xbox 360) on modern glasses-free 3D displays. Using off-the-shelf hardware and open tools, it converts 3D HDMI output for new screens, without modifying the console.

---

## Table of contents

- [Firmware patching guide](#firmware-patching-guide)
- [EDID emulator option](#edid-emulator-option)
- [ShaderGlass setup](#shaderglass-setup)
- [3DToElse_NTM3D details](#3dtoelse_ntm3d-details)
- [NTM3D EDID details](#ntm3d-edid-details)
- [Hardware connection](#hardware-connection)
- [Record using OBS](#record-using-obs)
- [Demo videos](#demo-videos)
- [3D TV size settings](#3d-tv-size-settings)
- [Hardware examples](#hardware-examples)
- [Credits](#credits)

---

## Firmware patching guide

> **⚠️ Warning:** Flashing any firmware is at your own risk. Make backups and verify hardware compatibility before proceeding!

### 0. Download ms213x_flash

Download the capture card firmware tool from [steve-m/ms213x_flash](https://github.com/steve-m/ms213x_flash).

### 1. Backup your capture card firmware
Run:
```
ms213x_flash.exe
```
This will create a backup of your capture card’s firmware (e.g. `backup.bin`).

### 2. Patch firmware using MS2130_edid_patcher.py
Run:
```
python3 MS2130_edid_patcher.py backup.bin NTM3D_edid.bin NTM3D_patched.bin
```
`backup.bin` is the firmware you just dumped.  
`NTM3D_edid.bin` is included in the repo.

### 3. Flash the patched firmware
Flash the patched firmware:
```
ms213x_flash.exe -w NTM3D_patched.bin
```

### Option: Use the premade firmware file
You can also use the premade firmware file `NTM3D_firmware.bin` provided in this repository.  
This file is based on the firmware from [this comment](https://github.com/awawa-dev/HyperHDR/discussions/499?sort=new#discussioncomment-15833082) that is itself based on the original from [awawa-dev/HyperHDR/discussions/729](https://github.com/awawa-dev/HyperHDR/discussions/729), with the EDID `NTM3D_edid.bin` patched in.

**Always read the linked threads for compatibility and risk information before flashing.**

---

## EDID emulator option

Using an EDID emulator like this, you can overwrite the EDID using ToastyX’s [EDID/DisplayID Writer tool](https://www.monitortests.com/forum/Thread-EDID-DisplayID-Writer).  
Flash `NTM3D_edid.bin`.

![EDID Emulator](Images/EDID_emulator.png)

---

## ShaderGlass setup

1. Follow the guide here:  
   [ShaderGlass Reddit Guide](https://www.reddit.com/r/Stereo3Dgaming/comments/1qibwpg/friendly_reminder_you_can_use_shaderglass_free_on/)

2. Add [`3DToElse_NTM3D.fx`](3DToElse_NTM3D.fx) from this repo to your ShaderGlass shader folder.

3. *(Insert video showing how to setup ReShade settings)*

---

## 3DToElse_NTM3D details

The modifications comprise support for frame packed input format. It will remove the blanking line and correctly scale each eye.

I also added support for half/full input and output for SBS (Side-by-Side) and TaB (Top-and-Bottom).  
However, keep in mind that ReShade cannot change the display aspect ratio, so the support uses letter and pillar boxes.

---

## NTM3D EDID details

`NTM3D_edid.bin` is based on the EDID from the HyperHDR firmware, with the 3D parts extracted from my LG 65UF852V. Some settings were adjusted to better suit the use of 3D.

If you want to inspect the EDID, make changes, or create your own, I can recommend [AW EDID Editor](https://www.analogway.com/products/aw-edid-editor).

---

## Hardware connection

**MS2130 capture card setup:**
```
PS3/PS4/Xbox 360 etc → HDMI splitter → MS2130 capture card
```

**EDID emulator setup:**
```
PS3/PS4/Xbox 360 etc → HDMI splitter → EDID emulator → Your capture card
```

---

## Record using OBS

To record or stream gameplay, start an additional ShaderGlass instance *without* 3DGameBridge activated.
Capture the output window of ShaderGlass using OBS.

1. **Enable multiple apps to use the camera:**  
   On Windows 11, you must enable multiple applications to access your capture card/camera device so you can start two instances of ShaderGlass.  
   See guide: [Enable or Disable Multiple Apps to Use Camera in Windows 11](https://www.elevenforum.com/t/enable-or-disable-multiple-apps-to-use-camera-in-windows-11.31199/)

2. **Use Game Capture in OBS:**  
   To ensure that ReShade shader effects are captured correctly, select **Game Capture** mode in OBS when grabbing the ShaderGlass window.

---

## Demo videos

YouTube demo video here (embed or link):

- *Placeholder for video 1*
- *Placeholder for video 2*

---

## 3D TV size settings

`NTM3D_edid.bin` presents as a 24 inch TV. This was chosen to match the original PS3 3D display size, the screen most developers probably made sure their games looked correct on. The PS3, and likely other consoles, use the TV screen size EDID value to scale 3D depth.

The following images show the difference between selecting 17 inch, 27 inch, and 47 inch respectively. No other settings have been changed.

**Previews:**

- **17 inch:**  
  ![17 Inch Freeview](Images/17inch_freeview.jpg)  
  [HSBS version](Images/17inch_hsbs.jpg)

- **27 inch:**  
  ![27 Inch Freeview](Images/27inch_freeview.jpg)  
  [HSBS version](Images/27inch_hsbs.jpg)

- **47 inch:**  
  ![47 Inch Freeview](Images/47inch_freeview.jpg)  
  [HSBS version](Images/47inch_hsbs.jpg)

Feel free to experiment with the TV size setting on the PS3. In my limited testing, going lower than around 17 inches can start introducing visual glitches or bugs.

---

## Hardware examples

Example MS2130-based capture card:  
![MS2130 Capture Card Example](Images/BENFEI_MS2130.jpg)

Example of a cheap HDMI splitter that will strip HDCP:  
![HDMI Splitter](Images/HDMI_splitter.png)

---

## Credits

- [3DToElse.fx (BlueSkyDefender)](https://github.com/BlueSkyDefender/Depth3D/blob/master/Other%20%20Shaders/3DToElse.fx)
- [ShaderGlass by mausimus](https://github.com/mausimus/ShaderGlass)
- [ShaderGlass guide discussion](https://www.reddit.com/r/Stereo3Dgaming/comments/1qibwpg/friendly_reminder_you_can_use_shaderglass_free_on/)
- [ms213x_flash](https://github.com/steve-m/ms213x_flash)
- [ms2130_patcher](https://github.com/steve-m/ms2130_patcher)
- [HyperHDR discussion #729](https://github.com/awawa-dev/HyperHDR/discussions/729)
- [HyperHDR discussion #499](https://github.com/awawa-dev/HyperHDR/discussions/499?sort=new#discussioncomment-15833082)
- [EDID DisplayID Writer](https://www.monitortests.com/forum/Thread-EDID-DisplayID-Writer)
- [Enable or Disable Multiple Apps to Use Camera in Windows 11](https://www.elevenforum.com/t/enable-or-disable-multiple-apps-to-use-camera-in-windows-11.31199/)
- [AW EDID Editor](https://www.analogway.com/products/aw-edid-editor)

---

For troubleshooting or questions, open an issue in this repository.