import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.filechooser import FileChooserListView  # Asegúrate de usar el listado
from kivy.uix.filechooser import FileChooser
from kivy.uix.popup import Popup
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
import torch  # Para cargar el modelo YOLOv5
import cv2  # Para procesar la imagen
import os
import threading

print(cv2.__version__)

# Definir el tamaño de la ventana (opcional)
Window.size = (600, 700)

# Ventana emergente para seleccionar archivo
class FileChooserPopup(BoxLayout):
    def __init__(self, callback, **kwargs):
        super(FileChooserPopup, self).__init__(**kwargs)
        self.callback = callback
        self.orientation = 'vertical'

        # FileChooser con filtro, ruta inicial accesible y archivos ocultos desactivados
        self.filechooser = FileChooserListView(
            filters=["*.png", "*.jpg", "*.jpeg"],
            path=os.path.expanduser(r"C:\Users\ssdisco\Documents\IES N6\3 ano\proyecto\Proyectov3"),  # Directorio del usuario
            show_hidden=False,  # No mostrar archivos ocultos
            dirselect=False  # Solo seleccionar archivos, no directorios
        )

        self.add_widget(self.filechooser)

        # Botones
        button_layout = BoxLayout(size_hint=(1, 0.2), spacing=10, padding=10)

        cancel_btn = Button(text="Cancelar", size_hint=(0.5, 1))
        cancel_btn.bind(on_press=self.close_popup)
        button_layout.add_widget(cancel_btn)

        load_btn = Button(text="Cargar", size_hint=(0.5, 1))
        load_btn.bind(on_press=self.load_selected_file)
        button_layout.add_widget(load_btn)

        self.add_widget(button_layout)

    def close_popup(self, instance):
        self.parent.dismiss()

    def load_selected_file(self, instance):
        selected = self.filechooser.selection
        if selected:
            self.callback(selected[0])
            self.parent.dismiss()
        else:
            popup = Popup(title="Error", content=Label(text="No se seleccionó ningún archivo."), size_hint=(0.8, 0.4))
            popup.open()
# Pantalla principal (Home Screen)
class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super(HomeScreen, self).__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        instructions = Label(
            text="Bienvenido a la App de Detección de Enfermedades en Frutillas.\n\n" "Por favor, selecciona una opción abajo para continuar.",
            halign="center",
            valign="middle",
            size_hint=(1, 0.4),
            font_size='16sp'
        )
        layout.add_widget(instructions)

        capture_btn = Button(
            text="Capturar Foto",
            size_hint=(0.8, 0.3),
            pos_hint={'center_x': 0.5},
            background_color=(0.1, 0.6, 0.8, 1),
            font_size='20sp'
        )
        capture_btn.bind(on_press=self.go_to_camera_screen)
        layout.add_widget(capture_btn)

        load_image_btn = Button(
            text="Cargar Imagen",
            size_hint=(0.8, 0.3),
            pos_hint={'center_x': 0.5},
            background_color=(0.1, 0.6, 0.8, 1),
            font_size='20sp'
        )
        load_image_btn.bind(on_press=self.load_image)
        layout.add_widget(load_image_btn)

        self.add_widget(layout)

    def go_to_camera_screen(self, instance):
        self.manager.current = 'camera'

    def load_image(self, instance):
        popup_content = FileChooserPopup(self.load_image_callback)
        self.popup = Popup(title="Cargar Imagen", content=popup_content, size_hint=(0.9, 0.9))
        self.popup.open()

    def load_image_callback(self, file_path):
        if file_path:
            self.manager.get_screen('processing').image_path = file_path
            self.manager.current = 'processing'

# Pantalla de captura de imagen (Camera Screen)
class CameraScreen(Screen):
    def __init__(self, **kwargs):
        super(CameraScreen, self).__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.camera = Camera(play=True, resolution=(640, 480))
        layout.add_widget(self.camera)

        capture_btn = Button(
            text="Capturar",
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5},
            background_color=(0.1, 0.6, 0.8, 1),
            font_size='20sp'
        )
        capture_btn.bind(on_press=self.capture_photo)
        layout.add_widget(capture_btn)

        back_btn = Button(
            text="Volver",
            size_hint=(0.8, 0.2),
            pos_hint={'center_x': 0.5},
            background_color=(0.8, 0.1, 0.1, 1),
            font_size='20sp'
        )
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def capture_photo(self, instance):
        self.image_path = "captured_image.png"
        self.camera.export_to_png(self.image_path)

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup = Popup(title="Foto Capturada", size_hint=(0.8, 0.5))

        label = Label(text="¿Qué deseas hacer con la imagen?")
        layout.add_widget(label)

        save_btn = Button(text="Guardar", size_hint=(1, 0.3))
        save_btn.bind(on_press=self.save_image)
        layout.add_widget(save_btn)

        analyze_btn = Button(text="Analizar", size_hint=(1, 0.3))
        analyze_btn.bind(on_press=self.analyze_image)
        layout.add_widget(analyze_btn)

        cancel_btn = Button(text="Cancelar", size_hint=(1, 0.3))
        cancel_btn.bind(on_press=self.cancel_image)
        layout.add_widget(cancel_btn)

        popup.content = layout
        popup.open()

    def save_image(self, instance):
        # Crear la carpeta 'save_image' si no existe
        save_dir = os.path.join(os.path.dirname(__file__), "save_image")
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # Ruta final para guardar la imagen
        saved_image_path = os.path.join(save_dir, os.path.basename(self.image_path))

        # Mover la imagen capturada a la carpeta 'save_image'
        try:
            os.rename(self.image_path, saved_image_path)
            self.image_path = saved_image_path  # Actualizar la ruta al nuevo lugar

            # Mostrar mensaje de éxito
            popup = Popup(
                title="Imagen Guardada",
                content=Label(text=f"Imagen guardada en:\n{saved_image_path}"),
                size_hint=(0.8, 0.4)
            )
            popup.open()

            # Cerrar la ventana emergente después de unos segundos
            Clock.schedule_once(lambda dt: popup.dismiss(), 2)

        except Exception as e:
            print(f"Error al guardar la imagen: {e}")
            popup = Popup(
                title="Error",
                content=Label(text="No se pudo guardar la imagen."),
                size_hint=(0.8, 0.4)
            )
            popup.open()

    def analyze_image(self, instance):
        self.manager.current = 'processing'
        self.manager.get_screen('processing').image_path = self.image_path

    def cancel_image(self, instance):
        if os.path.exists(self.image_path):
            os.remove(self.image_path)
        popup = Popup(title="Imagen Eliminada", content=Label(text="La imagen ha sido eliminada."), size_hint=(0.8, 0.4))
        popup.open()

    def go_back(self, instance):
        self.manager.current = 'home'

# Pantalla de procesamiento y detección con YOLOv5
class ProcessingScreen(Screen):
    def __init__(self, **kwargs):
        super(ProcessingScreen, self).__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.progress_bar = ProgressBar(max=100, size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5})
        layout.add_widget(self.progress_bar)

        self.status_label = Label(text="Procesando imagen...", size_hint=(1, 0.2))
        layout.add_widget(self.status_label)

        self.add_widget(layout)

    def on_enter(self):
        Clock.schedule_once(self.process_image, 1)

    def process_image(self, dt):
        for i in range(1, 101):
            Clock.schedule_once(lambda dt: self.update_progress(i), i * 0.05)

    def update_progress(self, value):
        self.progress_bar.value = value
        if value == 100:
            self.detect_disease()

    def detect_disease(self):
        # Hacer la detección en un hilo separado
        def analyze():
            try:
                model_path = "strawberry_model_v2.pt"
                model = torch.load(model_path)  # Cargar el modelo YOLOv5
                model.eval()  # Cambiar el modelo a modo de evaluación

                # Cargar la imagen capturada
                img = cv2.imread(self.image_path)

                # Realizar detección
                results = model(img)

                # Procesar los resultados
                if results:
                    detected_disease = "Enfermedad detectada"
                else:
                    detected_disease = "Sano"

                # Cambiar a la pantalla de resultados
                result_screen = self.manager.get_screen('result')
                result_screen.image_path = self.image_path
                result_screen.disease = detected_disease
                self.manager.current = 'result'
            
            except Exception as e:
                # Manejar errores de carga del modelo o inferencia
                print(f"Error al detectar enfermedad: {e}")
                popup = Popup(title="Error", content=Label(text="Error al analizar la imagen."), size_hint=(0.8, 0.4))
                popup.open()

        # Ejecutar el análisis en un hilo
        analysis_thread = threading.Thread(target=analyze)
        analysis_thread.start()

# Pantalla de resultados
class ResultScreen(Screen):
    def __init__(self, **kwargs):
        super(ResultScreen, self).__init__(**kwargs)
        self.image_path = None
        self.disease = "Sano"
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.image_widget = Image(size_hint=(0.8, 0.5), pos_hint={'center_x': 0.5})
        layout.add_widget(self.image_widget)

        self.result_label = Label(text="", size_hint=(1, 0.2), font_size='20sp')
        layout.add_widget(self.result_label)

        new_detection_btn = Button(
            text="Nueva Detección", size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5}, background_color=(0.1, 0.6, 0.8, 1))
        new_detection_btn.bind(on_press=self.go_to_home)
        layout.add_widget(new_detection_btn)

        self.add_widget(layout)

    def on_pre_enter(self):
        self.image_widget.source = self.image_path
        self.result_label.text = f"Resultado: {self.disease}"

    def go_to_home(self, instance):
        self.manager.current = 'home'

# Ventana emergente para seleccionar archivo
class FileChooserPopup(BoxLayout):
    def __init__(self, callback, **kwargs):
        super(FileChooserPopup, self).__init__(**kwargs)
        self.callback = callback
        self.orientation = 'vertical'

        filechooser = FileChooser(size_hint=(1, 0.8))
        self.add_widget(filechooser)

        select_btn = Button(text="Seleccionar", size_hint=(0.8, 0.2), pos_hint={'center_x': 0.5})
        select_btn.bind(on_press=lambda instance: self.callback(filechooser.selection[0] if filechooser.selection else None))
        self.add_widget(select_btn)

# Manejo de pantallas
class DiseaseDetectionApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(CameraScreen(name='camera'))
        sm.add_widget(ProcessingScreen(name='processing'))
        sm.add_widget(ResultScreen(name='result'))
        return sm

if __name__ == '__main__':
    DiseaseDetectionApp().run()