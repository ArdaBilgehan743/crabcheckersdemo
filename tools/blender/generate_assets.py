from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "assets" / "blender" / "source"
MODEL_DIR = ROOT / "public" / "models"

SOURCE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def clean_blender_backups() -> None:
    for backup in SOURCE_DIR.glob("*.blend[0-9]"):
        backup.unlink(missing_ok=True)


def clean_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.view_settings.view_transform = "Filmic"
    bpy.context.scene.view_settings.look = "Medium High Contrast"


def mat(name: str, color: tuple[float, float, float, float], roughness: float = 0.75, metallic: float = 0.0, emission: bool = False):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        if emission:
            bsdf.inputs["Emission Color"].default_value = color
            bsdf.inputs["Emission Strength"].default_value = 1.4
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return material


def assign(obj, material):
    obj.data.materials.append(material)
    return obj


def shade(obj, bevel: float = 0.0):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    try:
        bpy.ops.object.shade_smooth()
    except RuntimeError:
        pass
    obj.select_set(False)
    if bevel:
        modifier = obj.modifiers.new("soft bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        modifier.affect = "EDGES"
        obj.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return obj


def sphere(name, loc, scale, material, segments: int = 32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(12, segments // 2), location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    assign(obj, material)
    shade(obj)
    return obj


def cube(name, loc, scale, material, bevel: float = 0.02):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, material)
    shade(obj, bevel)
    return obj


def cylinder(name, loc, radius, depth, material, vertices: int = 32, bevel: float = 0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    shade(obj, bevel)
    return obj


def cone(name, loc, radius1, radius2, depth, material, vertices: int = 32):
    bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius1, radius2=radius2, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    shade(obj, 0.01)
    return obj


def torus(name, loc, major, minor, material):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=48, minor_segments=10, location=loc)
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    shade(obj)
    return obj


def arm_between(name, start, end, radius, material):
    start_v = Vector(start)
    end_v = Vector(end)
    mid = (start_v + end_v) * 0.5
    depth = (end_v - start_v).length
    obj = cylinder(name, mid, radius, depth, material, vertices=16)
    direction = end_v - start_v
    obj.rotation_euler = direction.to_track_quat("Z", "Y").to_euler()
    return obj


def add_face(prefix, skin, ink, y=1.58, z=0.38, eye=0.045):
    for x in (-0.12, 0.12):
        sphere(f"{prefix}_eye_{x}", (x, y, z), (eye, eye * 0.62, eye * 0.42), ink, 16)
    sphere(f"{prefix}_nose", (0, y - 0.1, z + 0.025), (eye * 0.75, eye * 0.55, eye * 0.5), ink, 16)
    cube(f"{prefix}_mouth", (0, y - 0.18, z + 0.02), (0.16, 0.012, 0.012), ink, 0.003)


def add_table_hands(prefix, skin, cloth):
    arm_between(f"{prefix}_left_arm", (-0.34, 1.03, 0.08), (-0.82, 0.55, 0.56), 0.045, cloth)
    arm_between(f"{prefix}_right_arm", (0.34, 1.03, 0.08), (0.82, 0.55, 0.56), 0.045, cloth)
    sphere(f"{prefix}_left_hand", (-0.86, 0.52, 0.6), (0.13, 0.1, 0.1), skin, 20)
    sphere(f"{prefix}_right_hand", (0.86, 0.52, 0.6), (0.13, 0.1, 0.1), skin, 20)


def export_asset(name: str) -> None:
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE_DIR / f"{name}.blend"))
    bpy.ops.export_scene.gltf(
        filepath=str(MODEL_DIR / f"{name}.glb"),
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_materials="EXPORT",
        export_animations=True,
    )


def add_lights() -> None:
    bpy.ops.object.light_add(type="AREA", location=(0, 4, 3))
    bpy.context.object.name = "warm softbox"
    bpy.context.object.data.energy = 550
    bpy.context.object.data.size = 4
    bpy.ops.object.camera_add(location=(0, 2.4, 5.2), rotation=(math.radians(64), 0, 0))
    bpy.context.scene.camera = bpy.context.object


def make_bear() -> None:
    clean_scene()
    fur = mat("warm dense fur", (0.64, 0.53, 0.36, 1))
    muzzle = mat("cream muzzle", (0.92, 0.82, 0.62, 1))
    vest = mat("worn red vest", (0.48, 0.12, 0.08, 1))
    ink = mat("wet black ink", (0.02, 0.015, 0.012, 1), 0.45)
    shell = mat("polished shell buttons", (0.9, 0.72, 0.42, 1), 0.34)
    sphere("bear_body", (0, 0.78, 0), (0.62, 0.84, 0.5), vest)
    sphere("bear_belly_fur", (0, 0.73, 0.35), (0.42, 0.5, 0.12), fur)
    sphere("bear_head", (0, 1.56, 0.12), (0.58, 0.5, 0.5), fur)
    for x in (-0.35, 0.35):
        sphere("bear_ear", (x, 1.98, 0.06), (0.18, 0.18, 0.12), fur)
        sphere("bear_inner_ear", (x, 1.98, 0.13), (0.1, 0.09, 0.04), muzzle, 16)
    sphere("bear_muzzle", (0, 1.47, 0.56), (0.26, 0.16, 0.16), muzzle)
    sphere("bear_nose", (0, 1.51, 0.71), (0.08, 0.055, 0.045), ink, 16)
    for x in (-0.17, 0.17):
        sphere("bear_eye", (x, 1.66, 0.53), (0.045, 0.03, 0.025), ink, 16)
        sphere("bear_brow", (x, 1.75, 0.5), (0.12, 0.025, 0.018), ink, 16)
    for x in (-0.22, 0.22):
        sphere("bear_button", (x, 0.98, 0.49), (0.045, 0.045, 0.02), shell, 16)
    add_table_hands("bear", fur, vest)
    add_lights()
    export_asset("avatar-bear")


def make_hat() -> None:
    clean_scene()
    skin = mat("pale table skin", (0.78, 0.65, 0.5, 1))
    coat = mat("midnight coat", (0.04, 0.07, 0.16, 1))
    hatmat = mat("brushed black felt", (0.025, 0.02, 0.018, 1), 0.92)
    band = mat("dull blue hat band", (0.08, 0.12, 0.35, 1))
    ink = mat("ink", (0.01, 0.009, 0.008, 1))
    sphere("hat_body", (0, 0.82, 0), (0.43, 0.78, 0.34), coat)
    sphere("hat_head", (0, 1.55, 0.1), (0.34, 0.4, 0.32), skin)
    cylinder("hat_brim", (0, 1.92, 0.08), 0.55, 0.08, hatmat, 48)
    cylinder("hat_crown", (0, 2.18, 0.08), 0.34, 0.46, hatmat, 48)
    cylinder("hat_band", (0, 2.04, 0.08), 0.35, 0.06, band, 48)
    cube("hat_coat_split", (0, 0.82, 0.36), (0.035, 0.72, 0.035), ink, 0.003)
    add_face("hat", skin, ink, 1.58, 0.43, 0.038)
    add_table_hands("hat", skin, coat)
    add_lights()
    export_asset("avatar-hat")


def make_lantern() -> None:
    clean_scene()
    robe = mat("ochre robe", (0.55, 0.37, 0.12, 1))
    hood = mat("smoked hood", (0.18, 0.13, 0.08, 1))
    skin = mat("lamp warm skin", (0.82, 0.7, 0.48, 1))
    brass = mat("aged brass", (0.84, 0.56, 0.2, 1), 0.45, 0.35)
    glow = mat("lantern glow", (1.0, 0.64, 0.18, 1), 0.25, 0, True)
    ink = mat("ink", (0.02, 0.014, 0.01, 1))
    sphere("lantern_body", (0, 0.78, 0), (0.38, 0.78, 0.34), robe)
    cone("lantern_hood", (0, 1.62, 0.08), 0.48, 0.26, 0.62, hood, 40)
    sphere("lantern_face", (0, 1.51, 0.32), (0.24, 0.22, 0.1), skin, 24)
    add_face("lantern", skin, ink, 1.55, 0.4, 0.03)
    cylinder("lantern_frame", (0.55, 1.08, 0.46), 0.15, 0.34, brass, 6, 0.01)
    sphere("lantern_light", (0.55, 1.08, 0.46), (0.12, 0.12, 0.12), glow, 20)
    arm_between("lantern_arm", (0.25, 1.03, 0.12), (0.55, 1.08, 0.46), 0.04, robe)
    add_table_hands("lantern", skin, robe)
    add_lights()
    export_asset("avatar-lantern")


def make_diver() -> None:
    clean_scene()
    coat = mat("sea glass coat", (0.08, 0.44, 0.42, 1))
    skin = mat("sun touched skin", (0.78, 0.62, 0.44, 1))
    glass = mat("blue green glass", (0.45, 0.85, 0.92, 0.82), 0.18)
    leather = mat("old leather", (0.19, 0.1, 0.05, 1))
    pearl = mat("pearl", (0.92, 0.84, 0.6, 1), 0.25, 0.08)
    ink = mat("ink", (0.01, 0.01, 0.01, 1))
    sphere("diver_body", (0, 0.8, 0), (0.38, 0.78, 0.31), coat)
    sphere("diver_head", (0, 1.52, 0.1), (0.32, 0.38, 0.3), skin)
    for x in (-0.13, 0.13):
        cylinder("diver_goggle", (x, 1.6, 0.43), 0.105, 0.035, glass, 32)
        bpy.context.object.rotation_euler[0] = math.radians(90)
    cube("diver_goggle_bridge", (0, 1.6, 0.43), (0.12, 0.035, 0.03), leather, 0.003)
    torus("diver_pearl_bag_ring", (-0.32, 0.96, 0.42), 0.08, 0.012, pearl)
    sphere("diver_pearl", (-0.32, 0.96, 0.42), (0.075, 0.075, 0.075), pearl, 20)
    add_face("diver", skin, ink, 1.49, 0.38, 0.026)
    add_table_hands("diver", skin, coat)
    add_lights()
    export_asset("avatar-diver")


def make_widow() -> None:
    clean_scene()
    dress = mat("velvet violet dress", (0.23, 0.08, 0.3, 1))
    skin = mat("cool rose skin", (0.78, 0.58, 0.68, 1))
    hair = mat("black lacquer hair", (0.015, 0.012, 0.018, 1), 0.5)
    veil = mat("smoky veil", (0.05, 0.025, 0.06, 0.45), 0.9)
    ink = mat("ink", (0.01, 0.01, 0.012, 1))
    sphere("widow_body", (0, 0.82, 0), (0.34, 0.92, 0.3), dress)
    sphere("widow_head", (0, 1.58, 0.1), (0.29, 0.36, 0.28), skin)
    sphere("widow_hair", (0, 1.66, -0.02), (0.37, 0.4, 0.22), hair)
    cone("widow_veil", (0, 1.55, 0.12), 0.48, 0.16, 0.78, veil, 48)
    torus("widow_collar", (0, 1.12, 0.02), 0.32, 0.025, hair)
    add_face("widow", skin, ink, 1.58, 0.39, 0.03)
    add_table_hands("widow", skin, dress)
    add_lights()
    export_asset("avatar-widow")


def make_crab(name: str, color: tuple[float, float, float, float]) -> None:
    clean_scene()
    shell = mat(f"{name} painted shell", color, 0.58)
    dark = mat(f"{name} dark shell edge", (color[0] * 0.45, color[1] * 0.45, color[2] * 0.45, 1), 0.72)
    eye = mat("ivory eye dots", (0.96, 0.9, 0.72, 1), 0.3)
    ink = mat("ink pupils", (0.01, 0.01, 0.01, 1))
    sphere("crab_body", (0, 0.15, 0), (0.34, 0.16, 0.28), shell, 32)
    for x in (-0.37, 0.37):
        sphere("crab_claw", (x, 0.13, 0.08), (0.16, 0.08, 0.11), shell, 20)
        arm_between("crab_arm", (x * 0.55, 0.12, 0.03), (x, 0.13, 0.08), 0.025, dark)
    for x in (-0.16, 0.16):
        arm_between("crab_eye_stalk", (x, 0.22, -0.1), (x, 0.36, -0.15), 0.014, dark)
        sphere("crab_eye", (x, 0.39, -0.16), (0.045, 0.045, 0.045), eye, 16)
        sphere("crab_pupil", (x, 0.4, -0.195), (0.016, 0.016, 0.01), ink, 12)
    for x in (-0.26, -0.13, 0.13, 0.26):
        arm_between("crab_leg", (x, 0.08, 0.05), (x * 1.25, 0.02, 0.25), 0.018, dark)
    add_lights()
    export_asset(f"crab-{name}")


def make_board() -> None:
    clean_scene()
    frame = mat("dark carved board frame", (0.12, 0.07, 0.045, 1), 0.84)
    light = mat("worn light squares", (0.72, 0.58, 0.46, 1), 0.88)
    dark = mat("oxblood squares", (0.36, 0.14, 0.12, 1), 0.88)
    line = mat("inked grid grooves", (0.035, 0.025, 0.02, 1), 0.7)
    cube("board_frame", (0, 0, 0), (7.1, 0.24, 7.1), frame, 0.05)
    for row in range(6):
        for col in range(6):
            x = (col - 2.5) * 1.04
            z = (row - 2.5) * 1.04
            cube("board_square", (x, 0.16, z), (0.98, 0.08, 0.98), light if (row + col) % 2 == 0 else dark, 0.012)
    for i in range(7):
        p = (i - 3) * 1.04 - 0.52
        cube("board_grid_x", (p, 0.23, 0), (0.025, 0.035, 6.24), line, 0.002)
        cube("board_grid_z", (0, 0.23, p), (6.24, 0.035, 0.025), line, 0.002)
    add_lights()
    export_asset("board-6x6")


def make_room() -> None:
    clean_scene()
    wood = mat("old walnut table", (0.34, 0.16, 0.09, 1), 0.8)
    cloth = mat("wine cloth", (0.17, 0.08, 0.06, 1), 0.95)
    brass = mat("lamp brass", (0.8, 0.52, 0.18, 1), 0.42, 0.3)
    shade = mat("blackened lamp shade", (0.035, 0.02, 0.016, 1), 0.82)
    glow = mat("warm bulb", (1.0, 0.64, 0.22, 1), 0.2, 0, True)
    cube("table_top", (0, 0, 0), (9.6, 0.34, 8.8), wood, 0.08)
    cube("table_cloth", (0, 0.22, 0), (7.75, 0.055, 7.2), cloth, 0.025)
    cylinder("lamp_cord", (-3.05, 3.4, -1.85), 0.018, 3.4, shade, 16)
    cone("lamp_shade", (-3.05, 1.55, -1.85), 0.82, 0.58, 0.56, shade, 48)
    sphere("lamp_bulb", (-3.05, 1.37, -1.85), (0.18, 0.18, 0.18), glow, 24)
    for i, x in enumerate((-3.6, 3.2, -1.1, 2.1)):
        sphere(f"shell_prop_{i}", (x, 0.34, 3.45 - i * 0.45), (0.16, 0.06, 0.1), brass, 20)
    add_lights()
    export_asset("table-room")


def main() -> None:
    clean_blender_backups()
    make_bear()
    make_hat()
    make_lantern()
    make_diver()
    make_widow()
    make_crab("red", (0.64, 0.09, 0.08, 1))
    make_crab("blue", (0.08, 0.15, 0.58, 1))
    make_board()
    make_room()
    clean_blender_backups()


if __name__ == "__main__":
    main()
