import pygame, sys, math
import subprocess
import os # <-- 1. IMPORT OS

def run_menu() :
    pygame.init()
    WIDTH, HEIGHT = 1225, 692
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("City Racer Menu")

    # --- 2. FIND THE SCRIPT'S LOCATION ---
    # This will be '.../term-project'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # -------------------------------------

    # ==== โหลดทรัพยากร ====
    # --- 3. BUILD FULL PATHS FOR ALL ASSETS ---
    try:
        bg = pygame.image.load(os.path.join(script_dir, "menu_back.jpg")).convert()
        bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
        
        pygame.mixer.music.load(os.path.join(script_dir, "menu_music.mp3"))
        pygame.mixer.music.set_volume(0.3)
        pygame.mixer.music.play(-1)

        mouse_img = pygame.image.load(os.path.join(script_dir, "oiltank.png")).convert_alpha()
        mouse_img = pygame.transform.scale(mouse_img,(100,100))
        pygame.mouse.set_visible(False)

        btn_img = pygame.image.load(os.path.join(script_dir, "text_box.png")).convert_alpha()
        btn_img = pygame.transform.scale(btn_img,(200,80))

        car_img = pygame.image.load(os.path.join(script_dir, "car1_icon (2).png")).convert_alpha()
        car_img = pygame.transform.scale(car_img,(150,150))

        smoke_img = pygame.image.load(os.path.join(script_dir, "smoke_icon.png")).convert_alpha()
        smoke_img = pygame.transform.scale(smoke_img, (50,50))

        flag_img = pygame.image.load(os.path.join(script_dir, "flag_racing.png")).convert_alpha()
        flag_img = pygame.transform.scale(flag_img, (120,120))
    except pygame.error as e:
        print(f"Error loading asset: {e}")
        print("Please make sure all asset files are in the 'term-project' folder.")
        pygame.quit()
        sys.exit()
    # -----------------------------------------
    
    # --- Fonts (using built-in) ---
    try:
        logo_font = pygame.font.SysFont("glitch", 90)
    except:
        print("Warning: 'glitch' font not found, using default.")
        logo_font = pygame.font.SysFont(None, 100)
        
    try:
        btn_font = pygame.font.SysFont("Origami Mommy", 34)
    except:
        print("Warning: 'Origami Mommy' font not found, using default.")
        btn_font = pygame.font.SysFont(None, 40)


    smoke_part = []

    # ==== ตัวแปร ====
    bg_x = 0
    clock = pygame.time.Clock()
    start_scale = 1.0
    quit_scale = 1.0
    start_offset = 0
    quit_offset = 0
    time_float = 0
    car_y = 500
    car_start_x = 900
    car_end_x = 300
    car_x = car_start_x
    car_speed = -2
    smoke_timer = 0.5
    smoke_interval = 15 #ทุก 15 เฟรมสร้างควันใหม่
    flag_y = 210
    flag_x = 555
    start_hover = False
    quit_hover = False
    running = True

    # ==== ลูปหลัก ====
    while running:
        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_hover:
                    print("Start game!")  # ที่นี่ต่อเข้าโหมดเกมจริง
                    pygame.mixer.music.stop()
                    pygame.quit()
                    
                    # --- 4. FIX THE SUBPROCESS CALL ---
                    # Tell the subprocess to run 'main.py'
                    # and set its "working directory" (cwd) to our script's folder.
                    # This is CRITICAL for your Ursina game to find its assets.
                    main_py_path = os.path.join(script_dir, "main.py")
                    try:
                        subprocess.run([sys.executable, main_py_path], cwd=script_dir, check=True)
                    except subprocess.CalledProcessError as e:
                        print(f"Error running main.py: {e}")
                    except FileNotFoundError:
                        print(f"Error: 'main.py' not found at {main_py_path}")
                    # ----------------------------------
                    running = False 
                if quit_hover:
                    running = False

        # พื้นหลังเลื่อนเบา ๆ
        bg_x -= 0.5
        if bg_x <= -WIDTH:
            bg_x = 0
        screen.blit(bg, (bg_x, 0))
        screen.blit(bg, (bg_x + WIDTH, 0))

        # วาดชื่อเกม
        amplitude_y = 5
        amplitude_x = 3
        speed_float = 0.03
        offset_y = math.sin(time_float * speed_float) * amplitude_y
        offset_x = math.sin(time_float * speed_float * 0.5) * amplitude_x

        # Shadow
        shadow_color = (50, 50, 50)
        shadow_offset = 5
        title_text = "FAST BUT NOT FURIOUS"
        shadow = logo_font.render(title_text, True, shadow_color)
        screen.blit(shadow, ( WIDTH//2 - shadow.get_width()//2 + offset_x + shadow_offset,100 + offset_y + shadow_offset))

        # Main text
        main_color = (255, 255, 255)
        title = logo_font.render(title_text, True, main_color)
        screen.blit(title, (WIDTH//2 - title.get_width()//2 + offset_x,100 + offset_y))
        time_float += 1

        #smoke ตาม รถ
        smoke_timer += 1
        if smoke_timer >= smoke_interval :
            smoke_timer = 0
            smoke_part.append([car_x + 130, car_y + 60, 1.0, 255])

        for particle in smoke_part[:] :
            x, y, scale, alpha = particle
            smoke_surf = pygame.transform.rotozoom(smoke_img, 0, scale)
            smoke_surf.set_alpha(alpha)
            screen.blit(smoke_surf, (x,y))

            particle[1] -= 0.5
            particle[2] += 0.01
            particle[3] -= 5
            if particle[3] <= 0:
                smoke_part.remove(particle)
    
        #iconรถวิ่ง
        screen.blit(car_img, (car_x,car_y))
        car_x += car_speed
        if car_x <= car_end_x :
            car_x = car_start_x

        # วาดปุ่มstart
        start_rect = btn_img.get_rect(center=(WIDTH//2 ,370))
        start_hover = start_rect.collidepoint(mouse)

        target_scale = 1.2 if start_hover else 1.1
        start_scale += (target_scale - start_scale) * 0.1

        target_offset = -5 if start_hover else 0
        start_offset += (target_offset - start_offset) * 0.2

        scaled_start = pygame.transform.smoothscale(btn_img,(int(200 * start_scale),int(60 * start_scale)))
        scaled_start_rect = scaled_start.get_rect(center=start_rect.center)
        screen.blit(scaled_start, scaled_start_rect)

        color = (255,255,255) if start_hover else (220,220,215)
        label = btn_font.render("START!",True,color)
        screen.blit(label,(scaled_start_rect.centerx - label.get_width()//2, 360 + start_offset - 7)) # -7 to center text

        #วาดปุ่มquit
        quit_rect = btn_img.get_rect(center=(WIDTH//2 ,450))
        quit_hover = quit_rect.collidepoint(mouse)

        target_scale_q = 1.2 if quit_hover else 1.1
        quit_scale += (target_scale_q - quit_scale) * 0.1

        target_offset_q = -5 if quit_hover else 0
        quit_offset += (target_offset_q - quit_offset) * 0.2

        scaled_quit = pygame.transform.smoothscale(btn_img,(int(200 * quit_scale),int(60 * quit_scale)))
        scaled_quit_rect = scaled_quit.get_rect(center=quit_rect.center)
        screen.blit(scaled_quit, scaled_quit_rect)

        color_q = (255,255,255) if quit_hover else (220,220,215)
        label_q = btn_font.render("QUIT",True,color_q)
        screen.blit(label_q,(scaled_quit_rect.centerx - label_q.get_width()//2, 440 + quit_offset - 7)) # -7 to center text

        #flag
        screen.blit(flag_img, (flag_x, flag_y))

        #วาดmouse
        screen.blit(mouse_img, mouse)

        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == '__main__' :
    run_menu()