# Bed Visualizer

BlTouch UBL custom command (Create one with and without 5min wait):
```gcode
M140 S55            ; preheat bed
M104 S205 T0        ; preheat hotend
M190 S55            ; wait for bed to reach 55c
M109 S205 T0        ; wait for hotend to reach 205c
G4 P300000          ; wait 5 min for everything to get nice and toasty
G29 F 0             ; disable fade height
G28                 ; home all axes
G29 P1              ; automatic mesh probing using ABL
G29 P3 T            ; extrapolate unreachable mesh values
G29 P3 T            ; extrapolate unreachable mesh values
G29 P3 T            ; extrapolate unreachable mesh values
G29 P3 T            ; extrapolate unreachable mesh values
G29 S0              ; save mesh to slot 0
G29 F 5.0           ; re-enable fade height at 5.0mm
@BEDLEVELVISUALIZER ; tell the plugin to watch for reported mesh
M420 S0 V           ; enable and output updated mesh values
M500                ; save the new mesh to EEPROM
M155 S3             ; reset temperature reporting
```
test
