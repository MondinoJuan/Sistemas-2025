from flask import Flask, render_template, request
import alchemy


app = Flask(__name__)

@app.route('/')
def inicio():
    return render_template('inicio.html')

@app.route('/tabla')
def tabla():
    return render_template('tabla.html')

@app.route('/formulario')
def formulario():
    return render_template('formulario.html')

if __name__ == '__main__':
    app.run(debug=True)