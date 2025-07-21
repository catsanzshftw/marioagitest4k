from ursina import *
import math, random

# ==== App/Window Setup ====
app = Ursina(title='Mario 3D Land - B3313 Tech Demo', vsync=True, development_mode=False)
window.fps_counter.enabled = True
window.exit_button.visible = False
window.title = 'Mario 3D Land - B3313 Tech Demo'
scene.fog_color = color.rgb(25, 25, 45)
scene.fog_density = 0.05
camera.fov = 80

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

# ==== Mario-like Controller ====
class MarioController(Entity):
    def __init__(self):
        super().__init__()
        self.speed = 8
        self.jump_height = 3
        self.jump_count = 0
        self.max_jumps = 2
        self.gravity = 40
        self.grounded = False
        self.velocity = Vec3(0, 0, 0)
        self.mouse_sensitivity = Vec2(100, 100)
        self.model = 'cube'
        self.color = color.rgb(200, 50, 50)
        self.scale = (1, 2, 1)
        self.position = (0, 5, 0)
        self.collider = BoxCollider(self, size=(1, 2, 1))
        camera.parent = self
        camera.position = (0, 8, -15)
        camera.rotation_x = 20
        mouse.locked = True

    def update(self):
        # Mouse look
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity.x * time.dt
        camera.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity.y * time.dt
        camera.rotation_x = clamp(camera.rotation_x, -90, 90)
        # Movement
        forward_amount = held_keys['w'] - held_keys['s']
        strafe_amount = held_keys['d'] - held_keys['a']
        direction = self.forward * forward_amount + self.right * strafe_amount
        if direction.length() > 0:
            direction = direction.normalized() * self.speed
            self.velocity.x = direction.x
            self.velocity.z = direction.z
        else:
            self.velocity.x = lerp(self.velocity.x, 0, time.dt * 10)
            self.velocity.z = lerp(self.velocity.z, 0, time.dt * 10)
        # Gravity
        if not self.grounded:
            self.velocity.y -= self.gravity * time.dt
        # Apply velocity
        self.position += self.velocity * time.dt
        # Ground check with snap
        hit_info = raycast(self.world_position + Vec3(0, -1 + 0.1, 0), Vec3(0, -1, 0), distance=0.5, ignore=(self,))
        if hit_info.hit:
            self.grounded = True
            self.position.y = hit_info.world_point.y + 1
            if self.velocity.y < 0: self.velocity.y = 0
            self.jump_count = 0
        else:
            self.grounded = False
        # Double Jump (pressed once per tap)
        if held_keys['space'] and self.jump_count < self.max_jumps:
            self.velocity.y = self.jump_height * 3
            self.jump_count += 1
            held_keys['space'] = 0 # prevent flight

player = MarioController()

# ==== Satellite HUD/Minimap ====
class SatelliteHUD(Entity):
    def __init__(self):
        super().__init__()
        self.minimap = Entity(parent=camera.ui, model='quad', color=color.rgba(20,20,40,200), scale=(0.3,0.3), position=(-0.65,0.35))
        self.border = Entity(parent=camera.ui, model='quad', color=color.rgb(100,100,150), scale=(0.32,0.32), position=(-0.65,0.35), z=-0.01)
        self.player_dot = Entity(parent=camera.ui, model='circle', color=color.rgb(255,100,100), scale=(0.02,0.02), position=(-0.65,0.35), z=-0.02)
        self.level_dots = []
    def update(self):
        map_scale = 0.005
        self.player_dot.position = (-0.65 + player.x * map_scale, 0.35 + player.z * map_scale)
        for i, obj in enumerate(level_objects):
            if i >= len(self.level_dots):
                dot = Entity(parent=camera.ui, model='circle', color=color.rgb(100,200,100), scale=(0.01,0.01), z=-0.02)
                self.level_dots.append(dot)
            self.level_dots[i].position = (-0.65 + obj.x * map_scale, 0.35 + obj.z * map_scale)
        # Hide unused
        for j in range(len(level_objects), len(self.level_dots)):
            self.level_dots[j].enabled = False

hud = SatelliteHUD()

# ==== B3313 Liminal Level ====
level_objects = []

for x in range(-50, 50, 10):
    for z in range(-50, 50, 10):
        height = random.uniform(-2, 2) if random.random() > 0.7 else 0
        Entity(model='cube', color=color.rgb(40,40,60) if height==0 else color.rgb(60,60,80),
               scale=(10, 0.5, 10), position=(x, height, z), texture='white_cube', collider='box')
for i in range(20):
    platform = Entity(model='cube', color=color.rgb(80,50,120), scale=(random.uniform(2,6),0.5,random.uniform(2,6)),
                      position=(random.uniform(-40,40),random.uniform(5,20),random.uniform(-40,40)), collider='box')
    level_objects.append(platform)
for i in range(15):
    Entity(model='cube', color=color.rgb(30,30,50), scale=(2,random.uniform(10,30),2),
           position=(random.uniform(-45,45),0,random.uniform(-45,45)), collider='box')
orbs = []
for i in range(10):
    orb = Entity(model='sphere', color=color.rgb(100,150,255), scale=0.5,
                 position=(random.uniform(-40,40),random.uniform(3,15),random.uniform(-40,40)))
    orb.unlit = True
    orb.base_y = orb.y
    orbs.append(orb)
mystery_cubes = []
for i in range(5):
    cube = Entity(model='cube', color=color.rgb(255,200,100), scale=1.5,
                  position=(random.uniform(-30,30),random.uniform(5,10),random.uniform(-30,30)))
    cube.unlit = True
    mystery_cubes.append(cube)
class Sky(Entity):
    def __init__(self):
        super().__init__(parent=scene, model='sphere', scale=500, texture='white_cube', double_sided=True)
        self.color = color.rgb(10, 10, 30)
sky = Sky()

# ==== Stats HUD ====
stats_text = Text(
    text='', position=(0.62, 0.44), scale=1.2, background=True, color=color.azure
)

# ==== Update Function (vibes central) ====
def update():
    # Animate orbs
    for i, orb in enumerate(orbs):
        orb.y = orb.base_y + math.sin(time.time() * 2 + i) * 0.02
        orb.color = color.rgb(
            100 + math.sin(time.time() + i) * 50,
            150 + math.sin(time.time() * 1.5 + i) * 50,
            255
        )
    # Rotate mystery cubes
    for cube in mystery_cubes:
        cube.rotation_y += 30 * time.dt
        cube.rotation_x += 20 * time.dt
    # Camera shake (occasionally)
    if random.random() > 0.99:
        camera.shake(duration=0.3, magnitude=0.05)
    # Minimap update
    hud.update()
    # Stats HUD update
    fps = int(1 / time.dt) if time.dt > 0 else 60
    vibe_level = "█" * int((math.sin(time.time() * 0.5) + 1) * 5)
    stats_text.text = f'FPS: {fps} | POS: {int(player.x)},{int(player.z)} | VIBE: {vibe_level}'

# ==== Onscreen Instructions ====
Text('WASD: Move | Space: Double Jump | Mouse: Look Around',
     position=(-0.8, -0.45), origin=(-1, -1), background=True)
Text('B3313 TECH DEMO - 60FPS',
     position=(0, 0.48), origin=(0, 0), background=True, scale=2)

app.run()
