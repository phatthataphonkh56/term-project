class WordleGamePygame:
    def __init__(self, stats_file='wordle_stats_en.json'):
        self.WORD_LENGTH = 5
        self.MAX_GUESSES = 6
        self.stats_file = stats_file
        self.stats = self._load_stats()
        self.settings = load_settings()
        self.word_bank, self.target_word = [], ""
        self.guesses, self.results, self.current_guess = [], [], ""
        self.game_over, self.win = False, False
        self.current_mode = 'classic'
        self.message, self.message_timer = "", 0
        self.keyboard_colors = {chr(c): "KEY_DEFAULT" for c in range(ord('a'), ord('z') + 1)}
        self.key_rects = {} 
        self.sounds = {}

        self.timer_start_time = 0
        self.time_limit = 30000 
        self.time_remaining = 30.0 

        def load_sound(path):
            try:
                return pygame.mixer.Sound(path)
            except Exception as e:
                print(f"Could not load sound {path}: {e}")
                return None

        self.sounds = {
            "win": load_sound(os.path.join("sounds", "win.mp3")),
            "lose": load_sound(os.path.join("sounds", "lose.mp3")),
            "type": load_sound(os.path.join("sounds", "type.wav"))
        }
        
        try:
            pygame.mixer.music.load(os.path.join("sounds", "bg_music.mp3"))
        except Exception as e:
            print(f"Could not load bg music: {e}")

        self.apply_volume_settings()
        
        if self.settings.get("sound_enabled", True):
            try:
                pygame.mixer.music.play(-1)
            except Exception: pass

    def apply_volume_settings(self):
        bg_vol = self.settings.get("bg_volume", DEFAULT_SETTINGS["bg_volume"])
        fx_vol = self.settings.get("fx_volume", DEFAULT_SETTINGS["fx_volume"])
        try:
            pygame.mixer.music.set_volume(bg_vol)
        except Exception: pass
        for sname in ("win", "lose", "type"):
            if self.sounds.get(sname):
                self.sounds[sname].set_volume(fx_vol)

    def play_sound(self, name):
        if self.settings.get("sound_enabled", True) and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()

    def reset_game_state(self):
        self.guesses, self.results, self.current_guess = [], [], ""
        self.game_over, self.win = False, False
        self.message = ""
        self.keyboard_colors = {chr(c): "KEY_DEFAULT" for c in range(ord('a'), ord('z') + 1)}
        self.key_rects = {} 
        self.timer_start_time = 0
        self.time_remaining = 30.0

    def set_message(self, text, color_name="WHITE"):
        if isinstance(color_name, str):
            color = COLORS.get(color_name, COLORS["WHITE"])
        else:
            color = color_name
        self.message = (text, color)
        self.message_timer = pygame.time.get_ticks()

    def _load_words_from_file(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                words = [line.strip().lower() for line in f if len(line.strip()) == self.WORD_LENGTH and line.strip().isalpha()]
            if not words:
                print(f"Warning: Word file '{filename}' is empty or invalid. Using default list.")
                self.word_bank = ['apple', 'train', 'audio', 'house', 'world']
            else:
                self.word_bank = words
        except FileNotFoundError:
            print(f"Warning: Word file '{filename}' not found. Using default list and creating file.")
            self.word_bank = ['apple', 'train', 'audio', 'house', 'world']
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    pass 
            except Exception as e:
                print(f"Could not create file {filename}: {e}")

    def _load_stats(self):
        if not os.path.exists(self.stats_file):
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"played": 0, "wins": 0, "current_streak": 0, "max_streak": 0, "guess_dist": {}}

    def _save_stats(self):
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Could not save stats: {e}")

    def update_stats(self):
        self.stats["played"] += 1
        if self.win:
            self.stats["wins"] += 1
            self.stats["current_streak"] += 1
            self.stats["max_streak"] = max(self.stats["max_streak"], self.stats["current_streak"])
            guess_count = str(len(self.guesses))
            self.stats["guess_dist"][guess_count] = self.stats["guess_dist"].get(guess_count, 0) + 1
        else:
            self.stats["current_streak"] = 0
        self._save_stats()

    def check_guess(self, guess):
        result = ["GRAY"] * self.WORD_LENGTH
        target_counts = Counter(self.target_word)
        
        for i, letter in enumerate(guess):
            if letter == self.target_word[i]:
                result[i] = "GREEN"
                target_counts[letter] -= 1
        
        for i, letter in enumerate(guess):
            if result[i] != "GREEN" and letter in target_counts and target_counts[letter] > 0:
                result[i] = "YELLOW"
                target_counts[letter] -= 1
        
        for i, letter in enumerate(guess):
            if 'a' <= letter <= 'z':
                if result[i] == "GREEN":
                    self.keyboard_colors[letter] = "GREEN"
                elif result[i] == "YELLOW" and self.keyboard_colors[letter] != "GREEN":
                    self.keyboard_colors[letter] = "YELLOW"
                elif self.keyboard_colors[letter] == "KEY_DEFAULT":
                    self.keyboard_colors[letter] = "KEY_USED"
        return result

    def is_valid_guess(self, guess):
        if len(guess) != self.WORD_LENGTH:
            self.set_message(f"Guess must be {self.WORD_LENGTH} letters", "RED")
            return False
        return True

    def _render_end_screen(self):
        try:
            SCREEN.fill(BG_COLOR) 
            
            end_text_str, color = self.message
            
            if self.win and self.current_mode == 'unlimited':
                guess_count = len(self.guesses)
                end_text_str = f"YOU WIN! ({guess_count} guesses)"
            
            end_text_surf = FONTS["end_game"].render(end_text_str, True, color)
            SCREEN.blit(end_text_surf, end_text_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 - 30)))
            
            if not self.win:
                answer_surf = FONTS["message"].render(f"The word was: {self.target_word.upper()}", True, COLORS["WHITE"])
                SCREEN.blit(answer_surf, answer_surf.get_rect(center=(WIDTH / 2, HEIGHT / 2 + 15)))
                
            prompt_surf = FONTS["message"].render("Press Enter to return to menu", True, COLORS["WHITE"])
            SCREEN.blit(prompt_surf, prompt_surf.get_rect(center=(WIDTH / 2, HEIGHT - 50)))
            
            pygame.display.flip() 
        except Exception as e:
            print(f"Error rendering end screen: {e}")

    def _handle_end_game_sfx(self, sound_name):
        try:
            bg_pos = pygame.mixer.music.get_pos() 
            pygame.mixer.music.stop()
        except Exception:
            bg_pos = None
            
        if self.settings.get("sound_enabled", True) and self.sounds.get(sound_name):
            self.sounds[sound_name].play()
            pygame.time.wait(int(self.sounds[sound_name].get_length() * 1000))
        
        if self.settings.get("sound_enabled", True):
            try:
                if bg_pos is not None and bg_pos >= 0: 
                    pygame.mixer.music.play(-1, bg_pos / 1000.0) 
                else:
                    pygame.mixer.music.play(-1)
            except Exception:
                try:
                    pygame.mixer.music.play(-1) 
                except Exception:
                    pass 

    def handle_enter(self):
        if self.game_over: 
            return
        
        if self.is_valid_guess(self.current_guess):
            self.guesses.append(self.current_guess)
            self.results.append(self.check_guess(self.current_guess))
            self.current_guess = ""
            
            if self.guesses[-1] == self.target_word:
                self.win = self.game_over = True
                self.set_message("YOU WIN", "GREEN")
                
                self._render_end_screen() 
                pygame.time.wait(250)     
                self._handle_end_game_sfx("win") 
                
                if self.current_mode != 'unlimited':
                    self.update_stats()

            elif len(self.guesses) == self.MAX_GUESSES and self.current_mode != 'unlimited':
                self.game_over = True
                self.set_message("LOSE", "RED")
                
                self._render_end_screen() 
                pygame.time.wait(250)     
                self._handle_end_game_sfx("lose") 
                
                if self.current_mode != 'unlimited':
                    self.update_stats()

    def draw_board(self, surface):
        width, height = surface.get_size()
        
        board_area_h = height * 0.5
        padding_ratio = 0.1 
        grid_width_ratio = self.WORD_LENGTH + (self.WORD_LENGTH - 1) * padding_ratio
        box_size_w = (width * 0.8) / grid_width_ratio 
        
        grid_height_ratio = self.MAX_GUESSES + (self.MAX_GUESSES - 1) * padding_ratio
        box_size_h = board_area_h / grid_height_ratio
        
        box_size = min(box_size_w, box_size_h, 80) 
        padding = box_size * padding_ratio
        
        grid_width = (box_size * self.WORD_LENGTH) + (padding * (self.WORD_LENGTH - 1))
        start_x = (width - grid_width) / 2
        start_y = height * 0.1 

        if self.current_mode == 'unlimited' and not self.game_over:
            guesses_to_show = self.guesses[-1:-6:-1] 
            results_to_show = self.results[-1:-6:-1]
            num_history_rows_to_show = min(len(self.guesses), 5)
            total_rows_to_draw = 1 + num_history_rows_to_show 

            for i in range(total_rows_to_draw): 
                y_pos = start_y + i * (box_size + padding)
                
                if i == 0: 
                    for j in range(self.WORD_LENGTH):
                        box = pygame.Rect(start_x + j * (box_size + padding), y_pos, box_size, box_size)
                        letter, l_color = "", COLORS["WHITE"]
                        
                        if j < len(self.current_guess):
                            letter = self.current_guess[j]
                            pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                            pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 
                            l_color = COLORS["WHITE"] 
                        else:
                            pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                            pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 

                        if letter:
                            text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                            surface.blit(text_surf, text_surf.get_rect(center=box.center))
                            
                else: 
                    guess_idx = i - 1 
                    guess = guesses_to_show[guess_idx]
                    result = results_to_show[guess_idx]
                    
                    for j in range(self.WORD_LENGTH):
                        box = pygame.Rect(start_x + j * (box_size + padding), y_pos, box_size, box_size)
                        letter, color_key, l_color = guess[j], result[j], COLORS["WHITE"]
                        pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                        
                        text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                        surface.blit(text_surf, text_surf.get_rect(center=box.center))
            return 

        for i in range(self.MAX_GUESSES): 
            for j in range(self.WORD_LENGTH):
                box = pygame.Rect(start_x + j * (box_size + padding), start_y + i * (box_size + padding), box_size, box_size)
                letter, color_key, l_color = "", "BLACK", COLORS["WHITE"] 
                
                if i < len(self.guesses): 
                    letter, color_key, l_color = self.guesses[i][j], self.results[i][j], COLORS["WHITE"]
                    pygame.draw.rect(surface, COLORS[color_key], box, border_radius=5)
                elif i == len(self.guesses) and j < len(self.current_guess) and not self.game_over: 
                    letter = self.current_guess[j]
                    pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 
                    l_color = COLORS["WHITE"] 
                else: 
                    pygame.draw.rect(surface, COLORS["BLACK"], box, border_radius=5) 
                    pygame.draw.rect(surface, COLORS["GRAY"], box, 2, border_radius=5) 

                if letter:
                    text_surf = FONTS["letter"].render(letter.upper(), True, l_color)
                    surface.blit(text_surf, text_surf.get_rect(center=box.center))

    def draw_keyboard(self, surface):
        self.key_rects.clear() 
        width, height = surface.get_size()
        
        key_rows = [
            list("qwertyuiop"), 
            list("asdfghjkl"), 
            ["ENTER"] + list("zxcvbnm") + ["BACK"]
        ]
        
        keyboard_area_y = height * 0.25 
        key_h = (keyboard_area_y / 4) * 0.9 
        key_w = min(width * 0.08, key_h * 1.3) 
        padding = key_w * 0.15
        start_y = height * 0.7 

        for i, row in enumerate(key_rows):
            total_key_units = 0
            for key in row:
                total_key_units += 1 if len(key) == 1 else 1.5 
            
            row_width = (total_key_units * key_w) + ((len(row) - 1) * padding)
            current_x = (width - row_width) / 2
            current_y = start_y + i * (key_h + padding * 0.8)

            for key in row:
                current_key_w = key_w
                color_name = self.keyboard_colors.get(key, "KEY_DEFAULT") 
                
                if key == "ENTER" or key == "BACK":
                    current_key_w = key_w * 1.5
                    color_name = "KEY_DEFAULT"
                
                key_rect = pygame.Rect(current_x, current_y, current_key_w, key_h)
                self.key_rects[key] = key_rect 
                
                pygame.draw.rect(surface, COLORS[color_name], key_rect, border_radius=8)
                
                key_text_str = key.upper()
                if key == "BACK":
                    key_text_str = "<=" 
                
                key_text = FONTS["key"].render(key_text_str, True, COLORS["WHITE"])
                surface.blit(key_text, key_text.get_rect(center=key_rect.center))
                
                current_x += current_key_w + padding

    def draw_header(self, surface):
        width, height = surface.get_size()
        
        mode_text = f"Mode: {self.current_mode.replace('_', ' ').title()}"
        
        title_text = FONTS["menu"].render(mode_text, True, COLORS["WHITE"])
        surface.blit(title_text, title_text.get_rect(center=(width / 2, height * 0.04)))

        if self.current_mode == 'limited_time' and not self.game_over:
            timer_display = max(0, int(self.time_remaining + 0.99)) 
            timer_text = f"Time: {timer_display}"
            timer_color = COLORS["WHITE"] if self.time_remaining > 5 else COLORS["RED"]
            timer_surf = FONTS["stats"].render(timer_text, True, timer_color)
            timer_rect = timer_surf.get_rect(topright=(width - 20, height * 0.02))
            surface.blit(timer_surf, timer_rect)

    def draw_settings_gear(self, surface):
        width, height = surface.get_size()
        margin = 10
        gear_size = int(min(width, height) * 0.06)
        gear_rect = pygame.Rect(margin, height - gear_size - margin, gear_size, gear_size) 

        try:
            if not SETTING_IMG: raise ValueError("No setting image")
            img = pygame.transform.smoothscale(SETTING_IMG, (gear_size, gear_size))
            surface.blit(img, gear_rect)
        except Exception:
            gear_surf = FONTS["menu"].render("⚙", True, COLORS["WHITE"])
            surface.blit(gear_surf, gear_surf.get_rect(center=gear_rect.center))
        return gear_rect 
    
    def draw_return_button(self, surface):
        width, height = surface.get_size()
        margin = 10
        btn_size = int(min(width, height) * 0.06) 
        btn_rect = pygame.Rect(margin, margin, btn_size, btn_size) 

        try:
            if not RETURN_IMG: raise ValueError("No return image")
            img = pygame.transform.smoothscale(RETURN_IMG, (btn_size, btn_size))
            surface.blit(img, btn_rect)
        except Exception:
            fallback_text = FONTS["menu"].render("<-", True, COLORS["WHITE"])
            surface.blit(fallback_text, fallback_text.get_rect(center=btn_rect.center))
        return btn_rect
    
    def draw_message(self, surface):
        width, height = surface.get_size()
        if self.message and pygame.time.get_ticks() - self.message_timer < 2000 and not self.game_over:
            text, color = self.message
            msg_surface = FONTS["message"].render(text, True, color)
            surface.blit(msg_surface, msg_surface.get_rect(center=(width / 2, height * 0.95)))

    def start_new_game(self, mode):
        file_map = {'classic': 'words_medium.txt', 'unlimited': 'words_easy.txt', 'limited_time': 'words_hard.txt'}
        filename = file_map.get(mode, 'words_medium.txt')
        
        self._load_words_from_file(filename)
        self.reset_game_state()
        self.current_mode = mode
        if not self.word_bank:
            print("Error: Word bank is empty. Cannot start game.")
            return False 
        self.target_word = random.choice(self.word_bank)
        
        if self.current_mode == 'limited_time':
            self.timer_start_time = pygame.time.get_ticks()
            
        print(f"Starting {mode} mode. Hint: {self.target_word}")
        return True

    def run_game(self):
        global SCREEN, WIDTH, HEIGHT
        running = True
        clock = pygame.time.Clock()
        
        def get_ui_rects():
            gear_margin = 10
            gear_size = int(min(WIDTH, HEIGHT) * 0.06)
            gear_rect = pygame.Rect(gear_margin, HEIGHT - gear_size - gear_margin, gear_size, gear_size)
            
            return_margin = 10
            return_size = int(min(WIDTH, HEIGHT) * 0.06)
            return_rect = pygame.Rect(return_margin, return_margin, return_size, return_size)
            return gear_rect, return_rect

        gear_rect_for_events, return_rect_for_events = get_ui_rects()