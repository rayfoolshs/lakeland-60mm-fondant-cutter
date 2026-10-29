# Lakeland 60 mm Fondant Cutter / Embosser

## Files

| File | Purpose |
|---|---|
| `lakeland_60mm_fondant_cutter_print.3mf` | **Use this for printing.** Pre-oriented with the flange on the bed and the logo facing up. |
| `lakeland_60mm_fondant_cutter_print.stl` | Same print orientation as the 3MF, if you prefer STL. |
| `lakeland_60mm_fondant_cutter.stl` | Design orientation (cutting edge down) for inspection/CAD. |
| `preview.png` | Logo layout, 3D print orientation, and cross-section. |
| `generation_report.txt` | Dimensions and mesh validation data. |

The 3MF is a **model-only** 3MF. Bambu Studio will slice it using the settings below; it is not a pre-sliced `.gcode.3mf`. If Bambu Studio does not import the 3MF for any reason, import `lakeland_60mm_fondant_cutter_print.stl` instead; it is already in the print orientation.

## Verified dimensions

- **60.0 mm cut diameter** (the fondant disc)
- **71.6 mm overall diameter** at the press flange
- **18.0 mm overall height**
- **1.8 mm wall**
- **3 mm fondant** design target
- **1.5 mm bird emboss**, **1.0 mm shield emboss**, **0.5 mm lime background emboss**
- Mesh is watertight and manifold; volume ≈ **19,844 mm³**
- Emblem clearance to the cutting ring: **2.0 mm**

The logo is the **bird + shield emblem only**. The full "LAKELAND SENIOR HIGH SCHOOL" wording was left off because it would be about 1.7 mm tall at 60 mm and would not print or emboss cleanly with a 0.4 mm nozzle.

## Material

**PETG is recommended** for durability, moisture resistance, and easier cleaning. Dry it before printing.

- PETG: 245 °C nozzle, 75 °C bed, 30–50 % part cooling
- PLA: 210–220 °C nozzle, 60 °C bed, 100 % cooling — prototype/display only, not recommended for repeated food contact

FDM parts are not inherently food-safe. See **Food safety** below.

## Bambu Studio settings (P1S, 0.4 mm nozzle)

| Setting | Value |
|---|---|
| Printer | Bambu Lab P1S 0.4 mm |
| Filament | Generic PETG (dry) |
| Process | 0.16 mm Optimal, or 0.12 mm Fine for sharper logo detail |
| Wall loops | 4 |
| Top/bottom layers | 5 top / 4 bottom |
| Infill | 20 % gyroid |
| Supports | Tree (auto), **build plate only**, 30° threshold |
| Support top Z distance | 0.2 mm |
| Support interface layers | 2 |
| Brim | 5 mm |
| Raft | None |
| Ironing | Optional; skip for the first print (it can soften the 0.5 mm feather grooves) |
| Nozzle temperature | 245 °C (first layer 250 °C) |
| Bed temperature | 75 °C |
| Outer wall speed | 50 mm/s |
| Inner wall speed | 90 mm/s |
| Infill speed | 120 mm/s |
| Travel speed | 300–500 mm/s |
| Retraction | 0.8–1.2 mm at 20–30 mm/s |
| Z-hop | 0.2 mm |
| Build plate | Textured PEI + glue stick as release agent |

Expected print time is roughly **2–3 hours** at 0.16 mm, or **3–4 hours** at 0.12 mm, depending on supports and speeds.

## Orientation and supports

The print file is already oriented:

- **Flange on the build plate**
- **Cutting edge at the top**
- **Logo features facing up inside the cutter**

Do **not** rotate it. This orientation puts the support material under the internal plate, where it is hidden inside the upper cavity. The logo contact faces are printed as top surfaces and are not supported.

Use **tree/organic supports with “support on build plate only.”** In print orientation, the only supported area should be under the internal plate (the side hidden inside the upper cavity). Do not paint supports onto the logo features.

The cutter has **two 0.8 mm air vents** through the internal plate. Keep them clear; they let air escape when the cutter is pressed into fondant.

## Bambu Studio workflow

1. Install/open **Bambu Studio**.
2. Select the **Bambu Lab P1S 0.4 mm** printer and **Generic PETG** filament.
3. Import `lakeland_60mm_fondant_cutter_print.3mf`.
4. Confirm the flange is on the bed and the logo faces up.
5. Apply the settings in the table above.
6. Enable supports: **tree (auto)**, **build plate only**, 30° threshold, 0.2 mm top Z.
7. Add a **5 mm brim**.
8. Slice and preview:
   - First layer: the flange ring should be a clean circle.
   - Supports: only under the internal plate, not on the logo.
   - Top: the cutting edge and logo faces should be visible.
9. Send to the printer.

### LAN mode (P1S)

On the printer:

1. **Settings → Network → LAN Only Mode**.
2. Note the printer IP address and LAN access code.

In Bambu Studio:

1. Open the **Device** tab.
2. **Add Printer → LAN mode**.
3. Enter the IP address and access code.
4. Send the sliced print.

Alternatively, export the sliced `.gcode.3mf` and copy it to the SD card, then print from the printer screen. The computer and printer must be on the same network for LAN transfer.

## Post-processing

1. Remove the brim.
2. Remove the supports through the large opening on the flange side. Use needle-nose pliers; avoid touching the logo faces.
3. Trim any strings from the cutting edge with a sharp knife.
4. If the flange has elephant’s foot, sand the outside edge lightly with 400–800 grit. Do not round the cutting edge.
5. Wash with warm water and mild soap, rinse, and dry fully.
6. Check that both air vents are clear.

## Food safety

- FDM layer lines can harbour bacteria, and PETG/PLA filaments and colourants are not automatically food-safe.
- For occasional use, place a food-safe barrier (cling film or acetate) between the cutter and the fondant, or use a certified food-safe coating on the contact surfaces.
- Hand wash only. Do **not** put it in a dishwasher; PETG can deform.
- Do not use it with hot food or leave it in direct sunlight.
- If this cutter will be used commercially or repeatedly for food production, use a food-safe moulding process (for example, a silicone mould cast from this printed master) rather than bare FDM plastic.

## Using the cutter

1. Roll the fondant to **3 mm** thickness on a food-safe board.
2. Place the cutter with the cutting edge down and the logo inside.
3. Press down firmly and evenly on the flange until the rim reaches the board.
4. The rim cuts the 60 mm disc; the emblem presses into the top surface.
5. Lift the cutter carefully. The air vents help air escape during pressing. If the fondant sticks, push it out through the cutting-edge opening.
6. The bird is the deepest impression (1.5 mm), the shield is 1.0 mm, and the lime background is 0.5 mm. The feather lines and eye are raised details within the bird.

The logo is **not mirrored**. It is on the underside of the plate, so the fondant imprint reads correctly.

## Troubleshooting

| Problem | Fix |
|---|---|
| Logo details are soft or missing | Use 0.12 mm layers, dry the PETG, lower outer-wall speed to 35–45 mm/s, and confirm no supports touch the logo. |
| Stringing | Dry the filament, lower nozzle to 240 °C, increase retraction slightly, enable z-hop. |
| Supports are difficult to remove | Use tree supports, 0.2 mm top Z, 2 interface layers; remove through the flange opening. |
| First layer not sticking | Clean the PEI plate, apply glue stick, raise bed to 75–80 °C, keep the 5 mm brim. |
| Flange edge has a bulge (elephant’s foot) | Sand the outside of the flange; the cutting edge is at the top and is not affected. |
| Cutter does not cut cleanly | The edge is a 0.4 mm flat with a 45° outside chamfer. Press firmly; if the fondant is thicker than 3 mm, roll it thinner. Lightly sharpen only the outside chamfer with 800 grit. |
| Emboss is too shallow | Press until the rim touches the board. The design gives 1.5 mm maximum depth. |
| Emboss is too deep | The fondant is thicker than 3 mm; roll it to 3 mm. |
| Print is slightly undersized | PETG shrinkage is small. If needed, scale to 100.2–100.5 % in Bambu Studio and test on scrap fondant. |
| 3MF will not import | Import `lakeland_60mm_fondant_cutter_print.stl` instead; it has the same print orientation. |

## Regenerating or editing

The model was generated from `Lakeland - Transparent (1).dxf` with:

```bash
python scripts/generate_cutter.py
```

Run it from a Python environment that has the dependencies above installed.

The script uses `ezdxf`, `shapely`, `trimesh`, `manifold3d`, `numpy`, `matplotlib`, `scipy`, and `networkx`. Edit the constants at the top of the script to change the cut diameter, wall, height, emboss depths, or logo fit.
