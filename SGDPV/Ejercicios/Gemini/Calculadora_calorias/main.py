from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.metrics import dp

import google.generativeai as genai
import json
import os
import re
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
            err_msg = str(e)                             # <-- congela el valor ahora
            Clock.schedule_once(lambda dt: self._on_api_error(err_msg))
        finally:
            Clock.schedule_once(lambda dt: self.update_loading(False))

    def call_gemini_api(self, payload: dict) -> dict:
        # Configurar API_KEY
        genai.configure(api_key='AIzaSyDYm3CM1vnyj2V5OZij43LeHjPadrT5tN0')

        # Crear el modeloo especifico
        modelo = genai.GenerativeModel('gemini-2.5-flash')

        prompt = (
                    "Eres un nutricionista. Devuelve SOLO un JSON válido (sin explicaciones, "
                    "sin bloques de código, sin texto extra). Formato EXACTO:\n"
                    '{ "calories": <numero>, "suggestions": ["...", "..."] }\n'
                    f"Usuario: {payload['age_years']} años, {payload['weight_kg']} kg, {payload['height_cm']} cm.\n"
                    f"Comida: {payload['food_description']}."
                )
        
        def _extract_json_block(text: str):
            text = text.strip()

            # 1) Entre ```json ... ```
            m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
            if m:
                return json.loads(m.group(1))

            # 2) Entre ``` ... ```
            m = re.search(r"```+\s*(\{.*?\})\s*```+", text, flags=re.DOTALL)
            if m:
                return json.loads(m.group(1))

            # 3) Primer '{' hasta el último '}' (balance simple)
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = text[start:end+1]
                return json.loads(candidate)

            # Si todo falla, lanzar error para que lo capture tu except
            raise json.JSONDecodeError("No se pudo extraer JSON", text, 0)
        
        resp = modelo.generate_content(prompt)
        text = resp.text.strip()
        try:
            data = _extract_json_block(text)
        except json.JSONDecodeError:
            # Fallback: calorías y sin sugerencias
            m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
            calories = float(m.group(1)) if m else None
            data = {"calories": calories, "suggestions": []}

        # Validación mínima
        if not isinstance(data, dict) or "calories" not in data:
            raise ValueError("Respuesta de Gemini inválida: se esperaba JSON con 'calories' y 'suggestions'.")

        if "suggestions" not in data or not isinstance(data["suggestions"], list):
            data["suggestions"] = []

        return data

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
            lbl = Label(
                text=f"• {s}",
                size_hint_y=None,
                halign='left',
                valign='top'
            )
            # Hacer wrap al ancho disponible y ajustar altura al contenido
            lbl.bind(
                width=lambda inst, w: setattr(inst, "text_size", (w, None)),
                texture_size=lambda inst, ts: setattr(inst, "height", ts[1])
            )
            box.add_widget(lbl)

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
        Builder.load_file('calc_cal.kv')
        return Root()


if __name__ == '__main__':
    CaloriesApp().run()