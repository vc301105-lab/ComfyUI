# MJH-style horror scene - Blender (bpy) script
# Haunted house + graveyard + ghost + moon, night lighting
import bpy, math, random

random.seed(13)

# ---------- clean scene ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def new_mat(name, color, emission=0.0, emit_color=None, roughness=0.9):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    if emission > 0:
        ec = emit_color or color
        bsdf.inputs["Emission Color"].default_value = (*ec, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    return m

def add_cube(name, loc, scale, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    return o

# ---------- materials ----------
mat_ground = new_mat("ground", (0.02, 0.03, 0.02))
mat_house  = new_mat("house",  (0.05, 0.035, 0.03))
mat_roof   = new_mat("roof",   (0.02, 0.015, 0.015))
mat_window = new_mat("window", (1.0, 0.45, 0.05), emission=14.0)
mat_stone  = new_mat("stone",  (0.18, 0.18, 0.20))
mat_tree   = new_mat("tree",   (0.03, 0.02, 0.015))
mat_moon   = new_mat("moon",   (1.0, 0.97, 0.85), emission=6.0)
mat_ghost  = new_mat("ghost",  (0.75, 0.9, 1.0), emission=2.2, emit_color=(0.6, 0.85, 1.0), roughness=0.3)
mat_eyes   = new_mat("eyes",   (0.0, 0.0, 0.0), roughness=0.2)

# ---------- ground ----------
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
bpy.context.object.data.materials.append(mat_ground)

# ---------- haunted house ----------
add_cube("house_body", (0, 9, 2.2), (3.2, 2.6, 2.2), mat_house)
# roof (pyramid-ish)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=4.4, depth=2.8, location=(0, 9, 5.8))
roof = bpy.context.object
roof.rotation_euler[2] = math.radians(45)
roof.data.materials.append(mat_roof)
# tower
add_cube("tower", (-3.4, 8.2, 3.4), (0.9, 0.9, 3.4), mat_house)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1.5, depth=1.8, location=(-3.4, 8.2, 7.7))
tcone = bpy.context.object
tcone.rotation_euler[2] = math.radians(45)
tcone.data.materials.append(mat_roof)
# glowing windows
for (x, z) in [(-1.5, 2.6), (1.5, 2.6), (0, 1.2), (-3.4, 4.6)]:
    add_cube(f"win_{x}_{z}", (x, 9 - 2.65, z), (0.45, 0.05, 0.6), mat_window)

# ---------- graveyard ----------
for i in range(9):
    x = random.uniform(-7, 7)
    y = random.uniform(1.0, 6.0)
    if abs(x) < 2.5 and y > 4:  # keep path clear
        x += 4 * (1 if x >= 0 else -1)
    g = add_cube(f"grave_{i}", (x, y, 0.55), (0.35, 0.09, 0.55), mat_stone)
    g.rotation_euler = (random.uniform(-0.08, 0.08), random.uniform(-0.12, 0.12), random.uniform(-0.3, 0.3))

# ---------- dead trees (simple) ----------
def dead_tree(loc, h=4.5):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.16, depth=h, location=(loc[0], loc[1], h / 2))
    trunk = bpy.context.object
    trunk.data.materials.append(mat_tree)
    for a in range(4):
        ang = random.uniform(0, 6.28)
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.06, depth=1.8,
            location=(loc[0] + 0.7 * math.cos(ang), loc[1] + 0.7 * math.sin(ang), h * 0.72 + a * 0.25))
        br = bpy.context.object
        br.rotation_euler = (random.uniform(0.6, 1.2), 0, ang)
        br.data.materials.append(mat_tree)

dead_tree((-6.5, 6.5)); dead_tree((6.8, 5.2), h=5.2)

# ---------- ghost ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75, location=(2.6, 4.2, 1.5), segments=24, ring_count=16)
ghost = bpy.context.object
ghost.name = "ghost"
ghost.scale = (1, 1, 1.5)
ghost.data.materials.append(mat_ghost)
bpy.ops.object.shade_smooth()
for dx in (-0.26, 0.26):  # eyes
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.11, location=(2.6 + dx, 4.2 - 0.62, 1.85))
    e = bpy.context.object
    e.data.materials.append(mat_eyes)
    e.parent = ghost
    e.matrix_parent_inverse = ghost.matrix_world.inverted()

# ghost floating animation
scene.frame_start, scene.frame_end = 1, 36
for f, z in [(1, 1.5), (18, 2.1), (36, 1.5)]:
    ghost.location.z = z
    ghost.keyframe_insert(data_path="location", frame=f)

# ---------- moon ----------
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.8, location=(-9, 38, 16))
moon = bpy.context.object
moon.data.materials.append(mat_moon)

# ---------- lights ----------
bpy.ops.object.light_add(type='SUN', location=(0, 0, 20))
sun = bpy.context.object
sun.data.energy = 3.5
sun.data.color = (0.55, 0.68, 1.0)
sun.rotation_euler = (math.radians(55), 0, math.radians(200))

bpy.ops.object.light_add(type='AREA', location=(0, -4, 8))  # soft fill
fill = bpy.context.object
fill.data.energy = 300
fill.data.size = 12
fill.data.color = (0.5, 0.6, 1.0)
fill.rotation_euler = (math.radians(30), 0, 0)

bpy.ops.object.light_add(type='POINT', location=(2.6, 4.2, 2.2))  # ghost glow
gl = bpy.context.object
gl.data.energy = 60
gl.data.color = (0.55, 0.8, 1.0)

# ---------- world (dark night sky) ----------
world = bpy.data.worlds.new("night")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.002, 0.004, 0.012, 1)
bg.inputs[1].default_value = 1.0

# ---------- camera (slow push-in) ----------
bpy.ops.object.camera_add(location=(0, -14, 3.2), rotation=(math.radians(87), 0, 0))
cam = bpy.context.object
cam.data.lens = 24
scene.camera = cam
cam.keyframe_insert(data_path="location", frame=1)
cam.location = (0, -11, 3.0)
cam.keyframe_insert(data_path="location", frame=36)

# ---------- render settings ----------
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.fps = 12
scene.view_settings.look = 'AgX - Punchy'

print("Scene ready:", len(bpy.data.objects), "objects")
