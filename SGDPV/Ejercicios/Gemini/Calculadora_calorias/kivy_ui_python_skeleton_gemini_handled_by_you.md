# Proyecto: Calculador de calorías (UI en Kivy + lógica en Python)

A continuación tenés **dos archivos** listos para usar:

- `app.kv` — Toda la interfaz con el usuario (Kivy language)
- `main.py` — Estructura de la app, variables, validaciones y *stubs* para conectar con Gemini (vos implementás esa parte)

---

## app.kv
```kv
#:kivy 2.3.0

<PrimaryButton@Button>:
    size_hint_y: None
    height: dp(48)
    bold: True

<HintLabel@Label>:
    color: .6, .6, .6, 1
    font_size: '12sp'

<TitleLabel@Label>:
    font_size: '20sp'
    bold: True

<Separator@Widget>:
    size_hint_y: None
    height: dp(1)
    canvas.before:
        Color:
            rgba: .85, .85, .85, 1
        Rectangle:
            pos: self.pos
            size: self.size

<Root>:
    HomeScreen:
        name: 'home'

<HomeScreen>:
    # Propiedades expuestas desde Python
    # result_calories, result_suggestions_text, loading

    FloatLayout:
        # Capa base con scroll para formularios largos
        ScrollView:
            size_hint: 1, 1
            do_scroll_x: False

            GridLayout:
                id: form_grid
                cols: 1
                size_hint_y: None
                padding: dp(16), dp(16)
                spacing: dp(12)
                height: self.minimum_height

                TitleLabel:
                    text: 'Calculador de calorías con Gemini'

                HintLabel:
                    text: 'Ingresá tus datos y qué comiste. Al tocar "Calcular", se llamará a Gemini (tu implementación) para estimar calorías y sugerir opciones.'

                Separator:

                Label:
                    text: 'Peso (kg)'
                    size_hint_y: None
                    height: self.texture_size[1]
                TextInput:
                    id: weight_input
                    hint_text: 'Ej.: 83'
                    input_filter: 'float'
                    write_tab: False
                    multiline: False
                    size_hint_y: None
                    height: dp(44)

                Label:
                    text: 'Edad (años)'
                    size_hint_y: None
                    height: self.texture_size[1]
                TextInput:
                    id: age_input
                    hint_text: 'Ej.: 28'
                    input_filter: 'int'
                    write_tab: False
                    multiline: False
                    size_hint_y: None
                    height: dp(44)

                Label:
                    text: 'Altura (cm)'
                    size_hint_y: None
                    height: self.texture_size[1]
                TextInput:
                    id: height_input
                    hint_text: 'Ej.: 185'
                    input_filter: 'int'
                    write_tab: False
                    multiline: False
                    size_hint_y: None
                    height: dp(44)

                Label:
                    text: '¿Qué comiste?'
                    size_hint_y: None
                    height: self.texture_size[1]
                TextInput:
                    id: food_input
                    hint_text: 'Ej.: 2 tostadas con palta, 200 ml de jugo de naranja, 1 café con leche...'
                    size_hint_y: None
                    height: dp(120)
                    text_validate_unfocus: False
                    multiline: True

                BoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(12)

                    PrimaryButton:
                        id: calc_btn
                        text: 'Calcular con Gemini'
                        on_release: root.on_submit()

                    Button:
                        text: 'Limpiar'
                        on_release: root.on_clear()

                Separator:

                TitleLabel:
                    text: 'Resultado'

                GridLayout:
                    cols: 2
                    size_hint_y: None
                    height: self.minimum_height
                    row_default_height: dp(28)
                    row_force_default: True
                    spacing: dp(6)

                    Label:
                        text: 'Calorías estimadas:'
                        halign: 'left'
                        valign: 'middle'
                        text_size: self.size
                    Label:
                        id: calories_label
                        text: root.result_calories if root.result_calories else '—'
                        halign: 'right'
                        valign: 'middle'
                        text_size: self.size

                Label:
                    text: 'Sugerencias para agregar:'
                    size_hint_y: None
                    height: self.texture_size[1]

                BoxLayout:
                    id: suggestions_box
                    orientation: 'vertical'
                    size_hint_y: None
                    spacing: dp(6)
                    padding: 0, 0
                    height: self.minimum_height

        # Overlay de carga
        BoxLayout:
            size_hint: 1, 1
            pos_hint: {"center_x": .5, "center_y": .5}
            canvas.before:
                Color:
                    rgba: (0,0,0,.3) if root.loading else (0,0,0,0)
                Rectangle:
                    pos: self.pos
                    size: self.size
            opacity: 1 if root.loading else 0

            BoxLayout:
                size_hint: None, None
                size: dp(160), dp(140)
                pos_hint: {"center_x": .5, "center_y": .5}
                padding: dp(16)
                spacing: dp(12)
                canvas.before:
                    Color:
                        rgba: 1,1,1,1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(12),]

                Image:
                    source: 'atlas://data/images/defaulttheme/loader'
                    anim_delay: .10
                    size_hint: None, None
                    size: dp(48), dp(48)
                Label:
                    text: 'Calculando...'
                    halign: 'center'
                    valign: 'middle'
                    text_size: self.size
```

---

## main.py
```python
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp

import threading

# ----------------------------
# Navegación raíz
# ----------------------------
class Root(ScreenManager):
    pass


# ----------------------------
# Pantalla principal
# ----------------------------
class HomeScreen(Screen):
    # Propiedades enlazadas a la UI
    result_calories = StringProperty("")
    loading = BooleanProperty(False)

    def on_kv_post(self, base_widget):
        """Se llama cuando el árbol KV ya está construido."""
        # Podés inicializar valores por defecto acá si querés
        pass

    # ----------------------------
    # Acciones de UI
    # ----------------------------
    def on_submit(self):
        """Valida el formulario y dispara el flujo para llamar a Gemini."""
        # Leer campos
        w = self.ids.weight_input.text.strip()
        a = self.ids.age_input.text.strip()
        h = self.ids.height_input.text.strip()
        food = self.ids.food_input.text.strip()

        # Validaciones simples
        errors = []
        if not w:
            errors.append("Peso requerido")
        if not a:
            errors.append("Edad requerida")
        if not h:
            errors.append("Altura requerida")
        if not food:
            errors.append("Descripción de comida requerida")

        # Tipos
        try:
            w_val = float(w)
            if w_val <= 0:
                errors.append("Peso inválido")
        except:
            errors.append("Peso debe ser numérico")

        try:
            a_val = int(a)
            if a_val <= 0:
                errors.append("Edad inválida")
        except:
            errors.append("Edad debe ser numérica entera")

        try:
            h_val = int(h)
            if h_val <= 0:
                errors.append("Altura inválida")
        except:
            errors.append("Altura debe ser numérica entera")

        if errors:
            self._show_errors(errors)
            return

        payload = {
            "weight_kg": w_val,
            "age_years": a_val,
            "height_cm": h_val,
            "food_description": food,
        }

        # Mostrar overlay de carga y desactivar botón
        self.update_loading(True)

        # Llamar a Gemini en un hilo aparte (vos implementás call_gemini_api)
        threading.Thread(target=self._call_gemini_thread, args=(payload,), daemon=True).start()

    def on_clear(self):
        self.ids.weight_input.text = ""
        self.ids.age_input.text = ""
        self.ids.height_input.text = ""
        self.ids.food_input.text = ""
        self.result_calories = ""
        self._populate_suggestions([])

    # ----------------------------
    # Conexión con Gemini (stubs)
    # ----------------------------
    def _call_gemini_thread(self, payload: dict):
        try:
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            # IMPLEMENTÁ ACÁ:
            # Reemplazá la siguiente línea por tu integración real con Gemini.
            # Debe retornar un dict con las claves: 'calories' (float/int) y
            # 'suggestions' (list[str]).
            # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
            result = self.call_gemini_api(payload)  # <-- tu implementación

            if not isinstance(result, dict):
                raise ValueError("La respuesta de Gemini debe ser un dict.")

            calories = result.get("calories")
            suggestions = result.get("suggestions", []) or []

            # Actualizar UI en el hilo principal
            Clock.schedule_once(lambda *_: self._apply_results(calories, suggestions))
        except Exception as e:
            Clock.schedule_once(lambda *_: self._on_api_error(str(e)))
        finally:
            Clock.schedule_once(lambda *_: self.update_loading(False))

    def call_gemini_api(self, payload: dict) -> dict:
        """
        STUB: Implementá la llamada a Gemini.
        Debe devolver: {"calories": <numero>, "suggestions": ["...", "..."]}
        """
        # EJEMPLO de formato esperado (BORRÁ esto cuando implementes):
        # raise NotImplementedError("Implementá la integración con Gemini acá.")
        # Para que puedas probar la UI sin la API, te dejo una simulación rápida:
        import time
        time.sleep(2.0)
        return {
            "calories": 540,
            "suggestions": [
                "Agregar una fruta (banana o manzana)",
                "Incluir una fuente de proteínas (yogur griego, huevo)",
                "Sumar frutos secos (nueces/almendras ~20g)",
            ],
        }

    # ----------------------------
    # Actualización de UI
    # ----------------------------
    def _apply_results(self, calories, suggestions):
        if calories is None:
            self.result_calories = "—"
        else:
            try:
                self.result_calories = f"{float(calories):.0f} kcal"
            except:
                self.result_calories = str(calories)
        self._populate_suggestions(suggestions)

    def _on_api_error(self, message: str):
        self.result_calories = "Error"
        self._populate_suggestions([f"Ocurrió un error: {message}"])

    def _populate_suggestions(self, items):
        box = self.ids.suggestions_box
        box.clear_widgets()
        from kivy.uix.label import Label
        if not items:
            box.add_widget(Label(text='—', size_hint_y=None, height=dp(24)))
            return
        for s in items:
            box.add_widget(Label(text=f"• {s}", size_hint_y=None, height=dp(24)))

    def _show_errors(self, errors):
        # Muestra errores en el panel de sugerencias para no abrir popups
        self.result_calories = "—"
        self._populate_suggestions([f"Error: {e}" for e in errors])

    def update_loading(self, value: bool):
        self.loading = bool(value)
        # Podés deshabilitar el botón durante la carga si querés
        self.ids.calc_btn.disabled = self.loading


class CaloriesApp(App):
    title = "Calculador de calorías"

    def build(self):
        # Cargá el archivo KV
        Builder.load_file('app.kv')
        return Root()


if __name__ == '__main__':
    CaloriesApp().run()
```

---

## Cómo usar

1. Guardá los archivos en la misma carpeta: `main.py` y `app.kv`.
2. Instalá Kivy (Python 3.9+ recomendado):
   ```bash
   pip install "kivy[base]" kivy-deps-angle
   ```
   > En Linux/macOS suele bastar `pip install kivy`. En Windows podés seguir [las guías de Kivy] y agregar `kivy-deps-*` si es necesario.
3. Ejecutá:
   ```bash
   python main.py
   ```
4. Implementá tu lógica en `call_gemini_api` para llamar a Gemini y devolver un dict con `calories` y `suggestions`.

## Notas de integración con Gemini
- En `on_submit` ya empaqueto el `payload` con `weight_kg`, `age_years`, `height_cm`, `food_description`.
- `call_gemini_api(payload)` se ejecuta en un **hilo** para no congelar la UI.
- Al completar, llamo `_apply_results(calories, suggestions)` en el hilo principal con `Clock.schedule_once`.
- Si algo falla, `_on_api_error(msg)` muestra el error en el área de sugerencias.

¿Querés que lo adapte a **KivyMD** con componentes Material y tema oscuro/ligero? También puedo agregar persistencia local (JSON) para recordar tus últimos datos.

