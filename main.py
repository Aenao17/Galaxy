import random
import psycopg2
import json

from kivy.config import Config
from kivy.uix.button import Button

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '400')

from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.uix.relativelayout import RelativeLayout
from kivymd.uix.datatables import MDDataTable
from kivy import platform
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line, Quad, Triangle
from kivy.properties import NumericProperty, Clock, ObjectProperty, StringProperty

Builder.load_file("menu.kv")

class MainWidget(RelativeLayout):
    from transforms import  transform_perspective
    from user_actions import on_keyboard_down, on_keyboard_up, keyboard_closed

    perspective_point_x = NumericProperty(0)
    perspective_point_y = NumericProperty(0)
    menu_widget = ObjectProperty()
    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")
    score_txt = StringProperty("SCORE: 0")
    highscore_txt = StringProperty("HIGHSCORE: ")

    column_names = [("Name", dp(30)), ("Score", dp(30))]
    leaderbord_data = []

    highcore = 0
    name=""

    V_NB_LINES = 8
    V_LINES_SPACING = .3
    vertical_lines = []

    H_NB_LINES = 15
    H_LINES_SPACING = .3
    horizontal_lines = []

    SPEED = 0.5
    current_offset_y = 0
    current_y_loop = 0
    dificulty = 0

    SPEED_X = 1.3
    current_speed_x = 0
    current_offset_x = 0

    NR_TILES = 16
    tiles = []
    tiles_coordinates = []

    SHIP_WIDTH = .15
    SHIP_HEIGHT = 0.075
    SHIP_BASE_Y = 0.04
    ship = None
    ship_coordinates = [(0,0), (0,0), (0,0)]

    state_game_over = False
    state_game_has_started = False

    game_sound = None
    menu_music = None
    game_over_sound = None

    text_input=None
    button = None

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.load_leaderboard()
        self.init_audio()
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()
        self.reset_game()

        if self.is_desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)
        Clock.schedule_interval(self.update, 1 / 60)
        self.menu_music.play()

    def init_name(self):
        self.text_input = TextInput( size_hint=(0.2, 0.1), pos_hint={'x': 0.15, 'top': 0.6})
        self.button = Button(text="Save", size_hint=(0.1, 0.1), pos_hint={'x': 0.2, 'top': 0.45})
        self.button.bind(on_press=self.on_button_pressed1)
        self.text_input.opacity = 0
        self.button.opacity = 0
        MainWidget.add_widget(self, self.text_input)
        MainWidget.add_widget(self, self.button)

    def init_table(self):
        # Create the leaderboard table
        self.table = MDDataTable(
            size_hint=(0.5, 0.3),  # Adjust size
            pos_hint={'center_x': 0.5, 'center_y': 0.5},  # Center the table
            use_pagination=False,  # No pagination row
            rows_num=10,  # Max 10 rows visible
            check=False,  # ✅ Remove checkboxes
            column_data=self.column_names,
            row_data=self.leaderbord_data,

            # 🎨 Styling for blue rows
            background_color_header=(0, 0, 0.8, 1),  # ✅ Dark Blue Header
            background_color_cell=(0.3, 0.3, 1, 1),  # ✅ Blue background for rows
            background_color_selected_cell=(0.5, 0.5, 1, 1),  # Light blue for selected row
            elevation=0,  # Removes unwanted shadows
        )

        # ✅ Center header text
        centered_column_data = []
        for column in self.table.column_data:
            centered_column_data.append((column[0], column[1], lambda x: {'halign': 'center', 'valign': 'middle'}))

        self.table.column_data = centered_column_data

        # ✅ Refresh the table by re-assigning `row_data`
        self.table.row_data = self.leaderbord_data

        # Add the table directly to the widget
        self.add_widget(self.table)

    def get_highscore(self):
        try:
            f = open("highscore.txt",'r')
        except:
            f = open("highscore.txt",'w')
        finally:
            f.close()

        with open("highscore.txt",'r') as file:
            a = file.readline()
            if a == '':
                score = 0
            else:
                score = int(a.strip())
            file.close()
        return score

    def init_audio(self):
        self.game_sound = SoundLoader.load("music/Music.mp3")
        self.menu_music = SoundLoader.load("music/menu_music.mp3")
        self.game_over_sound = SoundLoader.load("music/game_over.mp3")

    def reset_game(self):

        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_offset_x = 0
        self.current_speed_x = 0

        self.tiles_coordinates = []
        self.pre_fill_tiles_coordinates()
        self.generate_tiles_coordinates()

        self.state_game_over = False
        self.score_txt = "SCORE: 0"
        self.highscore_txt = ""
        self.dificulty = 0

    def is_desktop(self):
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    def init_ship(self):
        with self.canvas:
            Color(0, 0, 0)
            self.ship = Triangle()

    def update_ship(self):
        center_x = self.width/2
        base_y = self.SHIP_BASE_Y * self.height
        ship_half_width = self.SHIP_WIDTH * self.width/2
        ship_height = self.SHIP_HEIGHT * self.height

        self.ship_coordinates[0] = (center_x - ship_half_width, base_y)
        self.ship_coordinates[1] = (center_x, base_y + ship_height)
        self.ship_coordinates[2] = (center_x + ship_half_width, base_y)

        x1, y1 = self.transform(*self.ship_coordinates[0])
        x2, y2 = self.transform(*self.ship_coordinates[1])
        x3, y3 = self.transform(*self.ship_coordinates[2])

        self.ship.points = [x1,y1, x2,y2, x3,y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x + 1, ti_y + 1)

        for i in range(0,3):
            px, py = self.ship_coordinates[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.NR_TILES):
                tile = Quad()
                self.tiles.append(tile)

    def pre_fill_tiles_coordinates(self):
        for i in range(0,10):
            self.tiles_coordinates.append((0,i))

    def generate_tiles_coordinates(self):
        last_x = 0
        last_y = 0

        for i in range(len(self.tiles_coordinates)-1,-1,-1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            last_x = last_coordinates[0]
            last_y = last_coordinates[1] + 1

        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index + self.V_NB_LINES - 1

        for i in range(len(self.tiles_coordinates), self.NR_TILES):
            r = random.randint(0,2)
            self.tiles_coordinates.append((last_x,last_y))
            if last_x-1 <= start_index:
                r = 1
            if end_index <= last_x+1:
                r = 2
            if r == 1:
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.V_NB_LINES):
                self.vertical_lines.append(Line())

    def get_line_x_from_index(self, index):
        center_x = self.perspective_point_x
        offset = index - 0.5
        spacing = int(self.V_LINES_SPACING * self.width)

        line_x = center_x + offset*spacing + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_y = int(self.H_LINES_SPACING * self.height)
        line_y = index * spacing_y - self.current_offset_y
        return line_y

    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_tiles(self):
        for i in range(0, self.NR_TILES):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinates[0] + 1, tile_coordinates[1] + 1)

            x1,y1 = self.transform(xmin, ymin)
            x2,y2 = self.transform(xmin, ymax)
            x3,y3 = self.transform(xmax, ymax)
            x4,y4 = self.transform(xmax, ymin)

            tile.points = [x1,y1, x2,y2, x3,y3, x4,y4]

    def update_vertical_lines(self):
        center_x = int(self.width / 2)
        offset = -int(self.V_NB_LINES / 2) + 0.5
        spacing = int(self.V_LINES_SPACING * self.width)

        start_index = -int(self.V_NB_LINES/2)+1

        for i in range(start_index, start_index + self.V_NB_LINES):
            line_x = self.get_line_x_from_index(i)

            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)

            self.vertical_lines[i].points = [x1, y1, x2, y2]

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.H_NB_LINES):
                self.horizontal_lines.append(Line())

    def update_horizontal_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index + self.V_NB_LINES - 1

        xmin = self.get_line_x_from_index(start_index)
        xmax = self.get_line_x_from_index(end_index)

        for i in range(0, self.H_NB_LINES):
            line_y = self.get_line_y_from_index(i)
            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]

    def transform(self, x, y):
        return self.transform_perspective(x, y)

    def update(self, dt):
        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()
        time_factor = dt * 60
        if not self.state_game_over and self.state_game_has_started:
            self.table.opacity=0
            self.table.disabled = True
            self.text_input.disabled = True
            self.button.disabled = True
            self.text_input.opacity=0
            self.button.opacity=0
            self.menu_music.stop()
            if self.current_y_loop % 50 == 0:
                self.dificulty += 1/200
            speed_y = (self.SPEED + self.dificulty) * self.height / 100
            self.current_offset_y += speed_y * time_factor
            spacing_y = self.H_LINES_SPACING * self.height
            speed_x = self.current_speed_x *  self.width / 100
            self.current_offset_x += speed_x * time_factor
            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.generate_tiles_coordinates()
            self.score_txt = "SCORE: " +  str(self.current_y_loop)

        if not self.check_ship_collision() and not self.state_game_over:
            self.state_game_over = True
            self.check_highscore()
            self.init_table()
            self.highscore_txt = "HIGHSCORE: " + str(self.get_highscore())
            self.menu_title = "G  A  M  E     O  V  E  R"
            self.menu_button_title = "RESTART"
            self.menu_widget.opacity = 1
            self.game_sound.stop()
            self.game_over_sound.play()
            self.table.opacity = 1


            if self.record():
                self.text_input.disabled = False
                self.button.disabled = False
                self.button.text = "Save"
                self.text_input.opacity = 1
                self.button.opacity = 1
                self.table.pos_hint = {'right': 0.9, 'center_y': 0.5}
                self.table.row_data=self.leaderbord_data
            else:
                self.button.text = "Save"
                self.table.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
                self.text_input.disabled = True
                self.button.disabled = True
                self.table.disabled = True

    def on_button_pressed1(self, event):
        self.name = self.text_input.text.strip()
        if self.name == "":
            self.name = "Player"

        self.check_leaderboard()
        self.text_input.text = ""

        # Disable and hide input fields
        self.text_input.disabled = True
        self.button.disabled = True
        self.text_input.opacity = 0
        self.button.opacity = 0

        # ✅ Do NOT restart the game here!
        # ✅ The game stays in "Game Over" state until the user presses the restart button

        # Ensure leaderboard updates visually
        self.table.opacity = 1
        self.table.row_data = self.leaderbord_data

    def on_menu_button_pressed(self):
        self.game_over_sound.stop()

        # ✅ Fully reset the game state
        self.reset_game()
        self.state_game_over = False
        self.state_game_has_started = True
        self.menu_widget.opacity = 0
        self.table.opacity = 0
        self.game_sound.play()

        # ✅ Ensure keyboard input is restored after restarting
        if self.is_desktop():
            if self._keyboard:
                self._keyboard.unbind(on_key_down=self.on_keyboard_down)
                self._keyboard.unbind(on_key_up=self.on_keyboard_up)

            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            if self._keyboard:
                self._keyboard.bind(on_key_down=self.on_keyboard_down)
                self._keyboard.bind(on_key_up=self.on_keyboard_up)

    def check_highscore(self):

        score = self.get_highscore()
        with open("highscore.txt", "w") as file:
            if score < self.current_y_loop:
                score = self.current_y_loop
            file.write(str(score))
            file.close()

    def record(self):
        if len(self.leaderbord_data) < 10:
            return True
        for i in self.leaderbord_data:
            if self.current_y_loop > i[1]:
                return True
        return False

    def check_leaderboard(self):
        """Update leaderboard, save to file, and keep top 10 scores."""
        self.leaderbord_data.append((self.name, self.current_y_loop))

        # Sort leaderboard in descending order
        self.leaderbord_data.sort(key=lambda x: x[1], reverse=True)

        # Keep only the top 10 scores
        self.leaderbord_data = self.leaderbord_data[:10]

        # Save the updated leaderboard to file
        self.save_leaderboard()

        # Refresh the table with new leaderboard
        self.table.row_data = self.leaderbord_data

    def load_leaderboard(self):
        """Load leaderboard data from a file."""
        try:
            with open("leaderboard.txt", "r") as file:
                self.leaderbord_data = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.leaderbord_data = []  # Start with an empty leaderboard

    def save_leaderboard(self):
        """Save leaderboard data to a file."""
        with open("leaderboard.txt", "w") as file:
            json.dump(self.leaderbord_data, file)


class GalaxyApp(MDApp):
    def on_start(self):
        self.root.init_table()
        self.root.init_name()
        self.root.table.opacity = 0
        self.root.table.pos_hint = {'right':2}

GalaxyApp().run()