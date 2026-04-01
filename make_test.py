import ezdxf

doc = ezdxf.new()
msp = doc.modelspace()

# Good hole
msp.add_circle((10, 10), radius=5.0)
# Bad hole (too small)
msp.add_circle((30, 10), radius=0.3)
# Two holes too close together
msp.add_circle((50, 10), radius=2.0)
msp.add_circle((53, 10), radius=2.0)  # only 1mm edge-to-edge gap

# Good arc
msp.add_arc((10, 40), radius=3.0, start_angle=0, end_angle=90)
# Bad arc (too tight)
msp.add_arc((30, 40), radius=0.2, start_angle=0, end_angle=90)

# Normal line
msp.add_line((0, 0), (100, 0))
# Suspiciously short line
msp.add_line((0, 60), (0.3, 60))

# Two horizontal lines very close (thin wall)
msp.add_line((0, 80), (50, 80))
msp.add_line((0, 80.4), (50, 80.4))  # 0.4mm gap = thin wall

doc.saveas("test_drawing.dxf")
print("Created test_drawing.dxf with test cases")
