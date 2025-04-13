import kivy

from kivy.app import App

class calculadoraApp(App):
    def seven(self):
        self.root.ids.Screen.text += "7"

    def eight(self):
        self.root.ids.Screen.text += "8"

    def openPths(self):
        self.root.ids.Screen.text += "("

    def closePths(self):
        self.root.ids.Screen.text += ")"

    def addDot(self):
        self.root.ids.Screen.text += "."

    def addComa(self):
        self.root.ids.Screen.text += ","

    def nine(self):
        self.root.ids.Screen.text += "9"

    def divisionOp(self):
        self.root.ids.Screen.text += "/"

    def four(self):
        self.root.ids.Screen.text += "4"

    def five(self):
        self.root.ids.Screen.text += "5"

    def six(self):
        self.root.ids.Screen.text += "6"

    def multiplyOp(self):
        self.root.ids.Screen.text += "*"

    def one(self):
        self.root.ids.Screen.text += "1"

    def two(self):
        self.root.ids.Screen.text += "2"

    def three(self):
        self.root.ids.Screen.text += "3"

    def substractOp(self):
        self.root.ids.Screen.text += "-"

    def cero(self):
        self.root.ids.Screen.text += "0"

    def clean(self):
        self.root.ids.Screen.text = ""

    def equalOp(self):
        try:
            self.root.ids.Screen.text = str(eval(self.root.ids.Screen.text))
        except:
            self.root.ids.Screen.text = "Error"

    def plusOp(self):
        self.root.ids.Screen.text += "+"

if __name__ == '__main__':
    calculadoraApp().run()