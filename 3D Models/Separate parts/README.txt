split_stl.py output — image-to-stl-1787233955901

Final assembled size : 646.68 x 442.27 x 1700.0 mm
Bed / gantry limit    : 175.0 x 175.0 x 175.0 mm
Grid                  : 4 (X) x 3 (Y) x 10 (Z)
Parts produced        : 81
Alignment pins        : yes, r=3.0mm, protrusion=4.0mm

Each STL is re-zeroed so its own bounding-box minimum sits at (0,0,0) —
they drop straight into a slicer with no repositioning.

File names encode grid position: part_x{col}_y{row}_z{layer}.
Where two pieces are grid-adjacent, the lower-index piece carries a
raised cylindrical peg and the higher-index neighbour carries a matching
blind socket (0.25mm radial clearance) — press them together
to self-align before gluing. Faces with no usable solid cross-section
(edges of thin/organic shapes) are left as plain glue joints.

See manifest.csv for exact per-part dimensions.
