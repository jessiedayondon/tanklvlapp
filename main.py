import os
import csv
import urllib.request
import io
import ssl
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

# 🌐 GOOGLE SHEET WEBLINK HUB
# Update these placeholders with your actual published Google Sheet CSV web links!
ONLINE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJdUUlLlRZ49lBcKxR7QhUx-8Grh6iks1vR00BRiNXej4UUx3rfFQR1tikuZLX53aJLP8vb4kPyBgh/pub?gid=0&single=true&output=csv"
VERSION_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJdUUlLlRZ49lBcKxR7QhUx-8Grh6iks1vR00BRiNXej4UUx3rfFQR1tikuZLX53aJLP8vb4kPyBgh/pub?gid=95776090&single=true&output=csv"

# 💾 INTERNAL DEVICE FILES FOR OFFLINE STORAGE
LOCAL_FILE = "tanks_data.csv"
VERSION_FILE = "local_version.txt"

# 📊 DATA MATRIX REPLICATING THE PROVIDED FILE FORMAT
DEFAULT_DATA_MATRIX = """Tank,IdealOutput,Correction
T500,0,0
,4500,0
,9000,0
,13500,0
,18000,0
T510,0,-31
,4500,-32
,9000,-63
,13500,-97
,18000,-126
T520,0,-36
,4500,-38
,9000,-74
,13500,-113
,18000,-252
T530,0,-3
,4500,-24
,9000,-24
,13500,-24
,18000,-25
T540,0,0
,4500,0
,9000,0
,13500,0
,18000,0
T550,0,-40
,4500,-40
,9000,-79
,13500,-118
,18000,-154
T560,0,-55
,8500,-55
,17000,-54
,25500,-54
,34000,-56
T570,0,0
,8500,0
,17000,0
,25500,0
,34000,0
T580,0,-71
,8500,-71
,17000,-73
,25500,-72
,34000,-72
T590,0,0
,8500,0
,17000,0
,25500,0
,34000,0
T595,0,0
,8500,0
,17000,0
,25500,0
,34000,0"""

class SmartCheckingInterface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 30
        self.spacing = 12
        
        # Canvas light backdrop background configuration
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_background, pos=self._update_background)
        
        # Load database files into active memory
        self.calibration_db, self.status_message = self.initialize_database()
        
        # --- TOP HEADER PANEL AREA (DARK DESIGN BLOCK) ---
        self.header_panel = BoxLayout(orientation='vertical', size_hint_y=0.38, padding=15, spacing=8)
        with self.header_panel.canvas.before:
            Color(0.06, 0.06, 0.07, 1) # #101012 Deep dark matte
            self.header_bg = RoundedRectangle(size=self.header_panel.size, pos=self.header_panel.pos, radius=[18])
        self.header_panel.bind(size=self._update_header, pos=self._update_header)
        
        # Header string widgets in Capitalize Each Word format
        self.header_panel.add_widget(Label(
            text="Ss/Fs Volume Correction", 
            font_size='18sp', bold=True, color=get_color_from_hex('#F40009'),
            size_hint_y=0.15
        ))
        
        self.header_panel.add_widget(Label(
            text=self.status_message, 
            font_size='11sp', color=get_color_from_hex('#666668'),
            size_hint_y=0.10
        ))
        
        # Minimalist smooth liquid tank graphics element
        self.tank_widget = BoxLayout(size_hint_y=0.75, size_hint_x=None, width=130, pos_hint={'center_x': 0.5})
        with self.tank_widget.canvas.before:
            Color(0.15, 0.15, 0.17, 1) # Stainless steel metallic hue outline
            self.tank_shell = RoundedRectangle(size=self.tank_widget.size, pos=self.tank_widget.pos, radius=[12])
            Color(0.21, 0.13, 0.08, 1) # Smooth caramel fluid visualization fill color
            self.fluid_rect = Rectangle(size=(124, 0), pos=(self.tank_widget.pos[0]+3, self.tank_widget.pos[1]+3))
        self.tank_widget.bind(size=self._update_tank, pos=self._update_tank)
        self.header_panel.add_widget(self.tank_widget)
        self.add_widget(self.header_panel)
        
        # --- MANUAL DATA CONTROLS SECTION ---
        # 1. Dropdown Tank Options Selection Box
        self.add_widget(Label(text="Tank Selection", color=get_color_from_hex('#555558'), font_size='13sp', bold=True, size_hint_y=0.04, halign='left', text_size=(Window.width-80, None)))
        tank_options = tuple(self.calibration_db.keys()) if self.calibration_db else ('No Data Found',)
        self.tank_spinner = Spinner(
            text='T500', values=tank_options,
            background_normal='', background_color=get_color_from_hex('#F3F4F6'), 
            color=get_color_from_hex('#111111'), size_hint_y=0.07, font_size='14sp'
        )
        self.tank_spinner.bind(text=self.trigger_calculation)
        self.add_widget(self.tank_spinner)
        
        # 2. Level Volume Text Entry Input Box Row + Inline Compute Action
        self.add_widget(Label(text="Tank Volume Level", color=get_color_from_hex('#555558'), font_size='13sp', bold=True, size_hint_y=0.04, halign='left', text_size=(Window.width-80, None)))
        
        input_row = BoxLayout(orientation='horizontal', size_hint_y=0.07, spacing=10)
        self.volume_input = TextInput(
            text='8700', multiline=False, input_filter='float', input_type='number',
            background_normal='', background_color=get_color_from_hex('#F3F4F6'),
            foreground_color=get_color_from_hex('#111111'), font_size='15sp', padding=[10, 12, 10, 12]
        )
        input_row.add_widget(self.volume_input)
        
        self.compute_btn = Button(
            text="Compute", font_size='13sp', bold=True,
            background_normal='', background_color=get_color_from_hex('#F40009'),
            color=get_color_from_hex('#FFFFFF'), size_hint_x=0.3
        )
        self.compute_btn.bind(on_press=self.trigger_calculation)
        input_row.add_widget(self.compute_btn)
        self.add_widget(input_row)
        
        # --- OUTPUT RESULT ROW DISPLAY CARDS ---
        # 3. Capitalized Volume Correction Row Card
        self.card_corr = BoxLayout(orientation='horizontal', size_hint_y=0.11, padding=20)
        with self.card_corr.canvas.before:
            Color(0.97, 0.98, 0.98, 1) # Slate gray canvas tint
            self.bg_corr = RoundedRectangle(size=self.card_corr.size, pos=self.card_corr.pos, radius=[14])
        self.card_corr.bind(size=self._update_card_corr, pos=self._update_card_corr)
        
        self.card_corr.add_widget(Label(text="Volume Correction", font_size='14sp', bold=True, color=get_color_from_hex('#374151'), halign='left', text_size=(Window.width, None)))
        self.correction_lbl = Label(text="0.00", font_size='22sp', bold=True, color=get_color_from_hex('#EF4444'), halign='right', text_size=(Window.width, None))
        self.card_corr.add_widget(self.correction_lbl)
        self.add_widget(self.card_corr)
        
        # 4. Capitalized Corrected Volume Row Card
        self.card_res = BoxLayout(orientation='horizontal', size_hint_y=0.11, padding=20)
        with self.card_res.canvas.before:
            Color(0.95, 0.98, 0.96, 1) # Green calculation tint
            self.bg_res = RoundedRectangle(size=self.card_res.size, pos=self.card_res.pos, radius=[14])
        self.card_res.bind(size=self._update_card_res, pos=self._update_card_res)
        
        self.card_res.add_widget(Label(text="Corrected Volume", font_size='14sp', bold=True, color=get_color_from_hex('#166534'), halign='left', text_size=(Window.width, None)))
        self.corrected_lbl = Label(text="8,700.00 L", font_size='22sp', bold=True, color=get_color_from_hex('#16A34A'), halign='right', text_size=(Window.width, None))
        self.card_res.add_widget(self.corrected_lbl)
        self.add_widget(self.card_res)
        
        self.trigger_calculation()

    # --- CANVAS COORDINATE UPDATES ---
    def _update_background(self, instance, value): self.bg_rect.size = instance.size; self.bg_rect.pos = instance.pos
    def _update_header(self, instance, value): self.header_bg.size = instance.size; self.header_bg.pos = instance.pos
    def _update_card_corr(self, instance, value): self.bg_corr.size = instance.size; self.bg_corr.pos = instance.pos
    def _update_card_res(self, instance, value): self.bg_res.size = instance.size; self.bg_res.pos = instance.pos
    
    def _update_tank(self, instance, value):
        self.tank_shell.size = instance.size
        self.tank_shell.pos = instance.pos
        self.update_fluid_visual()

    def update_fluid_visual(self):
        """ Scales fluid height smoothly based on calculation ratios """
        tank = self.tank_spinner.text
        if tank not in self.calibration_db or not self.volume_input.text:
            self.fluid_rect.size = (124, 0)
            return
        try:
            current_vol = float(self.volume_input.text)
        except ValueError:
            current_vol = 0.0
            
        points = self.calibration_db[tank]
        max_capacity = points[-1][0] if points else 1.0
        if max_capacity <= 0:
            max_capacity = 1.0
            
        # Keep visual percentage capped securely between 0% and 100%
        ratio = min(max(current_vol / max_capacity, 0.0), 1.0)
        max_visual_height = self.tank_widget.height - 6
        visual_height = ratio * max_visual_height
        
        self.fluid_rect.pos = (self.tank_widget.pos[0] + 3, self.tank_widget.pos[1] + 3)
        self.fluid_rect.size = (self.tank_widget.width - 6, visual_height)

    def initialize_database(self):
        """ Automatically verifies active files and pulls cloud sheet logs when online """
        should_download = False
        status = ""
        context = ssl._create_unverified_context() # Safe SSL bridge passing for native Android environments
        
        local_version = "0"
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                local_version = f.read().strip()
                
