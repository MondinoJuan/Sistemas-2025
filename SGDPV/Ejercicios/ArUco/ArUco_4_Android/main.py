# main.py - Versión compatible con Android/Buildozer
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import *
from kivy.graphics.transformation import Matrix
from kivy.vector import Vector
import numpy as np
import math

class Simple3DModel:
    """Clase simple para manejar modelos 3D sin trimesh"""
    
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.colors = []
    
    @staticmethod
    def create_default_building():
        """Crear edificio por defecto"""
        model = Simple3DModel()
        
        # Vértices del edificio (escalados para visualización)
        model.vertices = np.array([
            # Base
            [-0.5, -0.5, 0], [0.5, -0.5, 0], [0.5, 0.5, 0], [-0.5, 0.5, 0],
            # Primer piso
            [-0.5, -0.5, 1], [0.5, -0.5, 1], [0.5, 0.5, 1], [-0.5, 0.5, 1],
            # Segundo piso
            [-0.3, -0.3, 1], [0.3, -0.3, 1], [0.3, 0.3, 1], [-0.3, 0.3, 1],
            [-0.3, -0.3, 1.8], [0.3, -0.3, 1.8], [0.3, 0.3, 1.8], [-0.3, 0.3, 1.8],
            # Techo
            [0, 0, 2.2]
        ], dtype=np.float32)
        
        # Caras del edificio
        model.faces = [
            # Base
            [0, 1, 2], [0, 2, 3],
            # Paredes primer piso
            [0, 1, 5], [0, 5, 4], [1, 2, 6], [1, 6, 5],
            [2, 3, 7], [2, 7, 6], [3, 0, 4], [3, 4, 7],
            # Techo primer piso
            [4, 5, 6], [4, 6, 7],
            # Paredes segundo piso
            [8, 9, 13], [8, 13, 12], [9, 10, 14], [9, 14, 13],
            [10, 11, 15], [10, 15, 14], [11, 8, 12], [11, 12, 15],
            # Techo piramidal
            [12, 13, 16], [13, 14, 16], [14, 15, 16], [15, 12, 16]
        ]
        
        # Colores para cada cara
        model.colors = [
            [0.6, 0.4, 0.2, 1],  # Base - marrón
            [0.6, 0.4, 0.2, 1],
            [0.8, 0.8, 0.9, 1],  # Paredes - gris claro
            [0.8, 0.8, 0.9, 1], [0.8, 0.8, 0.9, 1], [0.8, 0.8, 0.9, 1],
            [0.8, 0.8, 0.9, 1], [0.8, 0.8, 0.9, 1], [0.8, 0.8, 0.9, 1], [0.8, 0.8, 0.9, 1],
            [0.7, 0.7, 0.8, 1],  # Techo primer piso
            [0.7, 0.7, 0.8, 1],
            [0.9, 0.9, 1.0, 1],  # Paredes segundo piso - más claro
            [0.9, 0.9, 1.0, 1], [0.9, 0.9, 1.0, 1], [0.9, 0.9, 1.0, 1],
            [0.9, 0.9, 1.0, 1], [0.9, 0.9, 1.0, 1], [0.9, 0.9, 1.0, 1], [0.9, 0.9, 1.0, 1],
            [0.8, 0.2, 0.2, 1],  # Techo - rojo
            [0.8, 0.2, 0.2, 1], [0.8, 0.2, 0.2, 1], [0.8, 0.2, 0.2, 1]
        ]
        
        return model

class SimpleMarkerDetector:
    """Detector de marcadores simplificado para Android"""
    
    def __init__(self):
        self.marker_found = False
        self.marker_position = [0, 0]
        self.rotation = 0
        
    def detect_marker_simple(self, touch_pos, screen_size):
        """Simulación simple: usar toque como marcador"""
        if touch_pos:
            # Normalizar posición del toque
            x = (touch_pos[0] / screen_size[0] - 0.5) * 2
            y = (touch_pos[1] / screen_size[1] - 0.5) * 2
            self.marker_position = [x, -y]  # Invertir Y
            self.marker_found = True
            return True
        return False

class Simple3DRenderer:
    """Renderizador 3D simple usando Kivy Graphics"""
    
    def __init__(self):
        self.view_matrix = Matrix()
        self.projection_distance = 5
        
    def project_vertex(self, vertex, marker_pos, rotation, screen_size):
        """Proyectar vértice 3D a 2D"""
        # Aplicar transformación del marcador
        x = vertex[0] + marker_pos[0]
        y = vertex[1] + marker_pos[1]
        z = vertex[2] + 2  # Elevar modelo
        
        # Aplicar rotación simple
        cos_r = math.cos(rotation)
        sin_r = math.sin(rotation)
        new_x = x * cos_r - y * sin_r
        new_y = x * sin_r + y * cos_r
        
        # Proyección perspectiva simple
        if z > 0.1:  # Evitar división por cero
            screen_x = (new_x / z) * 200 + screen_size[0] / 2
            screen_y = (new_y / z) * 200 + screen_size[1] / 2
            return [screen_x, screen_y, z]
        return [0, 0, 10]  # Punto lejano si está detrás
    
    def is_face_visible(self, v1, v2, v3):
        """Determinar si una cara es visible (face culling)"""
        # Calcular normal usando producto cruzado
        edge1 = [v2[0] - v1[0], v2[1] - v1[1]]
        edge2 = [v3[0] - v1[0], v3[1] - v1[1]]
        cross = edge1[0] * edge2[1] - edge1[1] * edge2[0]
        return cross > 0  # Cara hacia adelante

class ARWidget(Widget):
    """Widget principal de AR"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Inicializar componentes
        self.model = Simple3DModel.create_default_building()
        self.detector = SimpleMarkerDetector()
        self.renderer = Simple3DRenderer()
        
        # Estado
        self.touch_pos = None
        self.rotation = 0
        
        # Programar actualización
        Clock.schedule_interval(self.update_ar, 1.0/30.0)  # 30 FPS
        
        # Bind touch events
        self.bind(on_touch_down=self.on_touch_down)
        self.bind(on_touch_move=self.on_touch_move)
        self.bind(on_touch_up=self.on_touch_up)
    
    def on_touch_down(self, touch):
        self.touch_pos = touch.pos
        return True
    
    def on_touch_move(self, touch):
        if self.touch_pos:
            # Usar movimiento para rotar
            dx = touch.pos[0] - self.touch_pos[0]
            self.rotation += dx * 0.01
            self.touch_pos = touch.pos
        return True
    
    def on_touch_up(self, touch):
        # Mantener última posición como marcador
        return True
    
    def update_ar(self, dt):
        """Actualizar AR cada frame"""
        self.canvas.clear()
        
        with self.canvas:
            # Fondo
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)
            
            # Detectar marcador (usar toque)
            if self.detector.detect_marker_simple(self.touch_pos, self.size):
                self.render_3d_model()
            
            # Instrucciones
            Color(1, 1, 1, 1)
    
    def render_3d_model(self):
        """Renderizar modelo 3D"""
        if not self.detector.marker_found:
            return
        
        # Proyectar todos los vértices
        projected_vertices = []
        for vertex in self.model.vertices:
            proj = self.renderer.project_vertex(
                vertex, 
                self.detector.marker_position,
                self.rotation,
                self.size
            )
            projected_vertices.append(proj)
        
        # Renderizar caras (ordenadas por profundidad)
        faces_with_depth = []
        for i, face in enumerate(self.model.faces):
            v1, v2, v3 = [projected_vertices[j] for j in face]
            
            # Verificar si la cara es visible
            if self.renderer.is_face_visible(v1, v2, v3):
                avg_depth = (v1[2] + v2[2] + v3[2]) / 3
                faces_with_depth.append((i, avg_depth, face))
        
        # Ordenar por profundidad (más lejano primero)
        faces_with_depth.sort(key=lambda x: x[1], reverse=True)
        
        # Dibujar caras
        for face_idx, _, face in faces_with_depth:
            vertices_2d = [projected_vertices[i][:2] for i in face]
            
            # Color de la cara
            if face_idx < len(self.model.colors):
                color = self.model.colors[face_idx]
            else:
                color = [0.5, 0.5, 0.8, 1]
            
            # Dibujar triángulo relleno
            Color(*color)
            Triangle(points=[
                vertices_2d[0][0], vertices_2d[0][1],
                vertices_2d[1][0], vertices_2d[1][1],
                vertices_2d[2][0], vertices_2d[2][1]
            ])
            
            # Dibujar contorno
            Color(0, 0, 0, 0.5)
            Line(points=[
                vertices_2d[0][0], vertices_2d[0][1],
                vertices_2d[1][0], vertices_2d[1][1],
                vertices_2d[2][0], vertices_2d[2][1],
                vertices_2d[0][0], vertices_2d[0][1]
            ], width=1)

class ARApp(App):
    def build(self):
        # Layout principal
        root = BoxLayout(orientation='vertical')
        
        # Instrucciones
        instructions = Label(
            text='Toca la pantalla para colocar modelo 3D\nArrastra para rotar',
            size_hint_y=None,
            height=80,
            color=[1, 1, 1, 1]
        )
        
        # Widget AR
        ar_widget = ARWidget()
        
        # Botón de salida
        exit_btn = Button(
            text='Salir',
            size_hint_y=None,
            height=50
        )
        exit_btn.bind(on_press=lambda x: App.get_running_app().stop())
        
        # Agregar widgets
        root.add_widget(instructions)
        root.add_widget(ar_widget)
        root.add_widget(exit_btn)
        
        return root

# Ejecutar app
if __name__ == '__main__':
    ARApp().run()