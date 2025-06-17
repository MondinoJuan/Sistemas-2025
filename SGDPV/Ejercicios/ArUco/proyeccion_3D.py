import cv2
import numpy as np
import trimesh

# Función para cargar y procesar modelo 3D
def load_and_process_model(model_path, marker_size=0.05):
    """Cargar modelo 3D y adaptarlo para AR"""
    try:
        # Cargar modelo con materiales (.obj automáticamente carga .mtl)
        #model = trimesh.load(model_path, force='mesh', process=False)
        model = trimesh.load(model_path, process=True)
        print(f"Modelo cargado: {len(model.vertices)} vértices, {len(model.faces)} caras")
        
        # Información detallada sobre colores/materiales
        print("\n--- Información de colores/materiales ---")
        if hasattr(model.visual, 'vertex_colors') and len(model.visual.vertex_colors) > 0:
            print(f"✓ Colores por vértice: {len(model.visual.vertex_colors)} colores")
        
        if hasattr(model.visual, 'face_colors') and len(model.visual.face_colors) > 0:
            print(f"✓ Colores por cara: {len(model.visual.face_colors)} colores")
        
        if hasattr(model.visual, 'material'):
            if hasattr(model.visual.material, 'main_color'):
                print(f"✓ Material principal encontrado: {model.visual.material.main_color}")
            if hasattr(model.visual.material, 'materials'):
                print(f"✓ Múltiples materiales: {len(model.visual.material.materials)} materiales")
            if hasattr(model.visual.material, 'face_materials'):
                print(f"✓ Materiales por cara: {len(model.visual.material.face_materials)} asignaciones")
        
        if not any([
            hasattr(model.visual, 'vertex_colors') and len(model.visual.vertex_colors) > 0,
            hasattr(model.visual, 'face_colors') and len(model.visual.face_colors) > 0,
            hasattr(model.visual, 'material')
        ]):
            print("⚠ No se encontraron colores/materiales - usando colores por defecto")
        print("----------------------------------------\n")
        
        # Normalizar modelo
        model.vertices -= model.centroid  # Centrar
        max_dim = np.max(model.extents)
        scale = marker_size / max_dim
        model.vertices *= scale  # Escalar
        
        # Colocar sobre el marcador
        min_z = np.min(model.vertices[:, 2])
        model.vertices[:, 2] -= min_z
        
        return model
    except Exception as e:
        print(f"Error cargando modelo: {e}")
        print("Creando modelo por defecto...")
        return create_default_building()

def create_default_building():
    """Crear un edificio por defecto"""
    # Vértices de un edificio simple
    vertices = np.array([
        # Base (suelo)
        [0, 0, 0], [0.04, 0, 0], [0.04, 0.04, 0], [0, 0.04, 0],
        # Primer piso
        [0, 0, 0.02], [0.04, 0, 0.02], [0.04, 0.04, 0.02], [0, 0.04, 0.02],
        # Segundo piso  
        [0.005, 0.005, 0.02], [0.035, 0.005, 0.02], [0.035, 0.035, 0.02], [0.005, 0.035, 0.02],
        [0.005, 0.005, 0.035], [0.035, 0.005, 0.035], [0.035, 0.035, 0.035], [0.005, 0.035, 0.035],
        # Techo
        [0.02, 0.02, 0.045]
    ])
    
    faces = np.array([
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
    ])
    
    return trimesh.Trimesh(vertices=vertices, faces=faces)

def get_face_color(model, face_idx):
    """Obtener color de una cara específica"""
    try:
        # Prioridad 1: Materiales por cara (para archivos .obj con .mtl)
        if (hasattr(model.visual, 'material') and 
            hasattr(model.visual.material, 'face_materials') and
            len(model.visual.material.face_materials) > face_idx):
            
            material_idx = model.visual.material.face_materials[face_idx]
            if (hasattr(model.visual.material, 'materials') and 
                len(model.visual.material.materials) > material_idx):
                material = model.visual.material.materials[material_idx]
                if hasattr(material, 'diffuse') and material.diffuse is not None:
                    # Convertir de [0,1] a [0,255]
                    color = (material.diffuse[:3] * 255).astype(int)
                    return tuple(color)
        
        # Prioridad 2: Colores por cara
        if hasattr(model.visual, 'face_colors') and len(model.visual.face_colors) > face_idx:
            color = model.visual.face_colors[face_idx][:3]  # RGB sin alpha
            return tuple(map(int, color))
        
        # Prioridad 3: Colores por vértice (promedio de la cara)
        elif hasattr(model.visual, 'vertex_colors') and len(model.visual.vertex_colors) > 0:
            face_vertices = model.faces[face_idx]
            colors = model.visual.vertex_colors[face_vertices][:, :3]  # RGB sin alpha
            avg_color = np.mean(colors, axis=0)
            return tuple(map(int, avg_color))
        
        # Prioridad 4: Material principal
        elif hasattr(model.visual, 'material') and hasattr(model.visual.material, 'main_color'):
            color = model.visual.material.main_color[:3]  # RGB sin alpha
            return tuple(map(int, color))
        
        # Por defecto: color basado en el índice de la cara para variedad
        else:
            colors = [
                (100, 150, 200),  # Azul claro
                (150, 100, 200),  # Púrpura
                (200, 150, 100),  # Naranja claro
                (100, 200, 150),  # Verde claro
                (200, 100, 150),  # Rosa
                (150, 200, 100),  # Verde lima
            ]
            return colors[face_idx % len(colors)]
    
    except Exception as e:
        print(f"Error obteniendo color para cara {face_idx}: {e}")
        return (100, 150, 200)  # Color por defecto

def draw_3d_model(frame, model, rvec, tvec, camera_matrix, dist_coeffs):
    """Dibujar modelo 3D proyectado en el frame con colores"""
    if model is None:
        return frame
    
    # Proyectar todos los vértices del modelo
    projected_vertices, _ = cv2.projectPoints(
        model.vertices, rvec, tvec, camera_matrix, dist_coeffs
    )
    projected_vertices = np.int32(projected_vertices).reshape(-1, 2)
    
    # Calcular qué caras son visibles (face culling básico)
    visible_faces = []
    for i, face in enumerate(model.faces):
        # Calcular normal de la cara en el espacio del mundo
        v1, v2, v3 = model.vertices[face]
        normal = np.cross(v2 - v1, v3 - v1)
        
        # Transformar normal al espacio de la cámara
        rotation_matrix, _ = cv2.Rodrigues(rvec)
        world_normal = rotation_matrix @ normal
        
        # Si la normal apunta hacia la cámara, la cara es visible
        if world_normal[2] < 0:  # En OpenCV, Z negativo es hacia adelante
            visible_faces.append((i, np.linalg.norm(v1 + tvec.flatten())))  # (índice, distancia)
    
    # Ordenar caras por distancia (más lejanas primero) para correcto z-buffering
    visible_faces.sort(key=lambda x: x[1], reverse=True)
    
    # Dibujar las caras visibles
    for face_idx, _ in visible_faces:
        face = model.faces[face_idx]
        face_vertices = projected_vertices[face]
        
        # Obtener color de la cara
        color = get_face_color(model, face_idx)
        
        # Color simple basado en el índice de la cara para variedad visual
        '''colors = [
            (100, 150, 200),  # Azul claro
            (150, 100, 200),  # Púrpura
            (200, 150, 100),  # Naranja claro
            (100, 200, 150),  # Verde claro
            (200, 100, 150),  # Rosa
            (150, 200, 100),  # Verde lima
        ]
        color = colors[face_idx % len(colors)]'''
        
        # Dibujar cara rellena
        cv2.fillPoly(frame, [face_vertices], color)
        
        # Dibujar contorno más oscuro
        border_color = tuple(max(0, c - 50) for c in color)
        cv2.polylines(frame, [face_vertices], True, border_color, 1)
    
    return frame

# Configuración principal
def main(model_path=None):
    # ArUco setup
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    
    # Cámara setup
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Calibración de cámara
    camera_matrix = np.array([[800, 0, 640], [0, 800, 360], [0, 0, 1]], dtype=np.float32)
    dist_coeffs = np.zeros((5, 1))
    marker_length = 0.05
    
    # Cargar modelo 3D
    if model_path:
        model = load_and_process_model(model_path, marker_length)
    else:
        model = create_default_building()
        print("Usando modelo de edificio por defecto")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)
        
        if ids is not None:
            # Dibujar marcadores detectados
            cv2.aruco.drawDetectedMarkers(frame, corners, ids)
            
            for corner in corners:
                img_points = corner[0].astype(np.float32)
                
                # Puntos del marcador en 3D
                obj_points = np.array([
                    [0, 0, 0],
                    [marker_length, 0, 0],
                    [marker_length, marker_length, 0],
                    [0, marker_length, 0],
                ], dtype=np.float32)
                
                # Resolver pose
                retval, rvec, tvec = cv2.solvePnP(
                    obj_points, img_points, camera_matrix, dist_coeffs
                )
                
                if retval:
                    # Dibujar ejes (opcional)
                    cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvec, tvec, 0.03)
                    
                    # Dibujar modelo 3D
                    frame = draw_3d_model(frame, model, rvec, tvec, camera_matrix, dist_coeffs)
        
        cv2.imshow("AR - Modelo 3D", frame)
        if cv2.waitKey(1) == 27:  # ESC para salir
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Para cargar tu modelo, usa una de estas opciones:
    
    # OPCIÓN 1: Ruta raw string (recomendado para Windows)
    #main(r"C:/Users/Admin/Desktop/Estudios/Sistemas-2025/SGDPV/Ejercicios/ArUco/Archivos3D/Church.obj")
    
    # OPCIÓN 2: Barras normales (también funciona en Windows)
    main("C:/Users/Admin/Desktop/Estudios/Sistemas-2025/SGDPV/Ejercicios/ArUco/Archivos3D/Safety_Cone.obj")
    
    # OPCIÓN 4: Para usar modelo por defecto, comenta la línea de arriba y descomenta esta:
    # main()