import os
import csv
import urllib.request
import io
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.utils import get_color_from_hex

# 🌐 GOOGLE SHEET WEBLINK HUB
ONLINE_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJdUUlLlRZ49lBcKxR7QhUx-8Grh6iks1vR00BRiNXej4UUx3rfFQR1tikuZLX53aJLP8vb4kPyBgh/pub?gid=0&single=true&output=csv"
VERSION_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTJdUUlLlRZ49lBcKxR7QhUx-8Grh6iks1vR00BRiNXej4UUx3rfFQR1tikuZLX53aJLP8vb4kPyBgh/pub?gid=95776090&single=true&output=csv"

# 💾 INTERNAL DEVICE FILES FOR OFFLINE STORAGE
LOCAL_FILE = "tanks_data.csv"
VERSION_FILE = "local_version.txt"

# 📊 THE EXACT DATA MATRIX FROM YOUR SCREENSHOTS
DEFAULT_DATA_MATRIX = """Tank,IdealOutput,Correction
T500,0,-39
T500,4500,-39
T500,9000,-78
T500,13500,-117
T500,18000,-156
T510,0,-31
T510,4500,-32
T510,9000,-63
T510,13500,-97
T510,18000,-128
T520,0,-38
T520,4500,-38
T520,9000,-74
T520,13500,-113
T520,18000,-252
T530,0,-3
T530,4500,-24
T530,9000,-24
T530,13500,-24
T530,18000,-25
T540,0,0
T540,4500,0
T540,9000,0
T540,13500,0
T540,18000,0
T550,0,-40
T550,4500,-40
T550,9000,-79
T550,13500,-118
T550,18000,-154
T560,0,-55
T560,8500,-55
T560,17000,-54
T560,25500,-54
T560,34000,-56
T570,0,0
T570,8500,0
T570,17000,0
T570,25500,0
T570,34000,0
T580,0,-71
T580,8500,-71
T580,17000,-73
T580,25500,-72
T580,34000,-72
T590,0,0
T590,8500,0
T590,17000,0
T590,25500,0
T590,34000,0
T595,0,0
T595,8500,0
T595,17000,0
T595,25500,0
T595,34000,0"""

class SmartCheckingInterface(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 30
        self.spacing = 10
        
        # Load database files into the phone's engine memory
        self.calibration_db, self.status_message = self.initialize_database()
        
        # --- PROPORTIONAL FULL-SCREEN SCALING INTERFACE ---
        self.add_widget(Label(
            text="SS/FS VOLUME CORRECTION", 
            font_size='22sp', bold=True, color=get_color_from_hex('#FFFFFF'),
            size_hint_y=0.08
        ))
        
        self.add_widget(Label(
            text=self.status_message, 
            font_size='12sp', italic=True, color=get_color_from_hex('#B0B0B0'),
            size_hint_y=0.05
        ))
        
        # 1. Tank Selector Menu Dropdown
        self.add_widget(Label(text="TANK:", color=get_color_from_hex('#A2EF7C'), bold=True, size_hint_y=0.04))
        tank_options = tuple(self.calibration_db.keys()) if self.calibration_db else ('No Data Found',)
        self.tank_spinner = Spinner(
            text='Select Tank', values=tank_options,
            background_color=get_color_from_hex('#385723'), color=get_color_from_hex('#FFFFFF'),
            size_hint_y=0.10
        )
        self.tank_spinner.bind(text=self.trigger_calculation)
        self.add_widget(self.tank_spinner)
        
        # 2. Level Input Typing Box (Optimized Input Profile)
        self.add_widget(Label(text="TANK VOLUME:", color=get_color_from_hex('#E0E0E0'), bold=True, size_hint_y=0.04))
        self.volume_input = TextInput(
            text='0', multiline=False, input_filter='float',
            input_type='number', # 📱 Forces Android to trigger a native number pad layout
            size_hint_y=0.10, font_size='20sp'
        )
        self.volume_input.bind(text=self.trigger_calculation)
        self.add_widget(self.volume_input)
        
        # 3. New Dedicated Action Execution Button
        self.compute_btn = Button(
            text="✅ COMPUTE CORRECTION",
            font_size='18sp', bold=True,
            background_normal='', # Clears default gray Kivy skin gradients
            background_color=get_color_from_hex('#2E7D32'), # Industrial High-Contrast Green Accent
            color=get_color_from_hex('#FFFFFF'),
            size_hint_y=0.12
        )
        self.compute_btn.bind(on_press=self.trigger_calculation)
        self.add_widget(self.compute_btn)
        
        # 4. Dynamic Mid-point Volume Correction Output Area
        self.add_widget(Label(text="VOLUME CORRECTION:", color=get_color_from_hex('#A2EF7C'), bold=True, size_hint_y=0.04))
        self.correction_lbl = Label(text="0.00", font_size='26sp', bold=True, color=get_color_from_hex('#FF4D4D'), size_hint_y=0.08)
        self.add_widget(self.correction_lbl)
        
        # 5. Final Aggregated Corrected Tank Volume Output Area
        self.add_widget(Label(text="CORRECTED VOLUME:", color=get_color_from_hex('#A2EF7C'), bold=True, size_hint_y=0.04))
        self.corrected_lbl = Label(text="0.00", font_size='32sp', bold=True, color=get_color_from_hex('#00FFCC'), size_hint_y=0.12)
        self.add_widget(self.corrected_lbl)
        
        # Bottom flexible buffer balancing space layout block
        self.add_widget(BoxLayout(size_hint_y=0.13))

    def initialize_database(self):
        """ Automatically verifies active files and pulls cloud sheet logs when online """
        should_download = False
        status = ""
        
        local_version = "0"
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r") as f:
                local_version = f.read().strip()
                
        if not os.path.exists(LOCAL_FILE):
            should_download = True

        # Try connection web check
        try:
            response = urllib.request.urlopen(VERSION_CSV_URL, timeout=2)
            version_data = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(version_data))
            online_version = "0"
            for row in reader:
                online_version = row['Version'].strip()
                break
            
            if online_version != local_version:
                should_download = True
                local_version = online_version
            else:
                status = "🔒 Up to Date: Operating offline using active cache."
        except Exception:
            should_download = False
            status = "✈️ Offline Mode: Operating smoothly using cached matrix numbers"

        # Update cache file if network indicates version shift
        if should_download:
            try:
                response = urllib.request.urlopen(ONLINE_CSV_URL, timeout=4)
                cloud_content = response.read().decode('utf-8')
                with open(LOCAL_FILE, mode='w', encoding='utf-8') as f:
                    f.write(cloud_content)
                with open(VERSION_FILE, mode='w', encoding='utf-8') as f:
                    f.write(local_version)
                status = "🔄 Database Updated! Saved new calibration parameters."
            except Exception:
                if not os.path.exists(LOCAL_FILE):
                    with open(LOCAL_FILE, mode='w', encoding='utf-8') as f:
                        f.write(DEFAULT_DATA_MATRIX)
                    with open(VERSION_FILE, mode='w', encoding='utf-8') as f:
                        f.write("1")
                status = "✈️ Engine Ready: Initialized offline fallback parameters"

        # Organize data logs into active structural lookup frames
        data_matrix = {}
        if os.path.exists(LOCAL_FILE):
            with open(LOCAL_FILE, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    tank = row.get('Tank', '').strip()
                    if not tank:
                        continue
                    ideal_out = float(row['IdealOutput'])
                    correction = float(row['Correction'])
                    if tank not in data_matrix:
                        data_matrix[tank] = []
                    data_matrix[tank].append((ideal_out, correction))
            
            # Ensure proper linear sort by IdealOutput order
            for tank in data_matrix:
                data_matrix[tank] = sorted(data_matrix[tank], key=lambda x: x[0])
                
        return data_matrix, status

    def trigger_calculation(self, *args):
        """ Core math engine. Runs linear proportional curve scaling on interactions """
        tank = self.tank_spinner.text
        if tank not in self.calibration_db:
            return
        try:
            current_vol = float(self.volume_input.text) if self.volume_input.text else 0.0
        except ValueError:
            current_vol = 0.0
            
        points = self.calibration_db[tank]
        correction = 0.0
        
        # --- Linear Curve Interpolation Formula Engine ---
        if current_vol <= points[0][0]:
            correction = points[0][1]
        elif current_vol >= points[-1][0]:
            correction = points[-1][1]
        else:
            for i in range(len(points) - 1):
                x0, y0 = points[i]
                x1, y1 = points[i+1]
                if x0 <= current_vol <= x1:
                    # Mathematical Formula: y = y0 + ((x - x0) * (y1 - y0)) / (x1 - x0)
                    correction = y0 + ((current_vol - x0) * (y1 - y0)) / (x1 - x0)
                    break
                    
        corrected_vol = current_vol + correction
        
        # Update UI layout views with clean structural string format markers
        self.correction_lbl.text = f"{correction:+.2f}"
        self.corrected_lbl.text = f"{corrected_vol:,.2f}"

class TankInterpolationApp(App):
    def build(self):
        return SmartCheckingInterface()

if __name__ == '__main__':
    TankInterpolationApp().run()
