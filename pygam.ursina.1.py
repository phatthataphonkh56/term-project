from ursina import *

class Player(Entity): #รถ
    def __init__(self):
        super().__init__(model='apx_70_-_low_poly_model.glb',scale=(0.68, 0.9, 0.68),position=(0, 0.5, 0),rotation_y = -90)
        self.lane = 0  #center lane
        self.target_x = 0 #ตำแหน่งที่จะขยับ
        self.lane_distance = 2 #ขยับทีละ x หน่วย
        self.move_speed = 4 #ความเร็วที่ถนนคท

    def input(self, key):
        if key == 'a' and self.lane > -0.75:   # คท.ซ้าย
            self.lane -= 0.75
        if key == 'd' and self.lane < 0.75:    # คท.ขวา
            self.lane += 0.75
        #ตั้งค่าเป้าหมายใหม่
        self.target_x = self.lane * self.lane_distance 

    def update(self): #ทำให้เคลื่อนที่smooth
        self.x = lerp(self.x, self.target_x, time.dt*self.move_speed)

class Road(Entity): #ถนน
    def __init__(self, z):
        super().__init__(model='road_hd.glb',scale=0.3,position=(0, -1, z),rotation=(0,180,0))
    def update(self):
        self.z -= time.dt * 20
        if self.z < -ROAD_LENGTH * 0.3:
            self.z += ROAD_LENGTH * len(roads)

class Background(Entity): #พื้นหลัง
    def __init__(self, texture_n = 'city_backg.jpg'):
        super().__init__(model='quad', texture = texture_n, scale=(380,300), position = (0,-2.5,500))

    def update(self):
        pass #พื้นหลังไม่ขยับ



app = Ursina()

# ผู้เล่น
player = Player()

#ถนน
ROAD_LENGTH = 50
NUM_ROADS = 50
roads = [Road(z=i * ROAD_LENGTH) for i in range(NUM_ROADS)]

#พื้นหลัง
background_u = Background(texture_n='city_backg.jpg')
camera.position = (0, 3, -9)
camera.rotation_x = 9

#ไว้อัปเดตclassแต่ละอัน
def update():
    #ถนน
    for road in roads:
        road.update()

    #พื้นหลัง
    background_u.update()


app.run() 