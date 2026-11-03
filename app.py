"""Operacion Limpieza Tactica 3D - servidor Flask.
Python genera el mapa y las oleadas, controla el cambio de armas y guarda el ranking.
El navegador (three.js) dibuja la escena 3D y maneja el combate en tiempo real."""
import math
import os
import random

from flask import Flask, jsonify, request, send_file

app = Flask(__name__)


# ---------------- ESTRUCTURAS DE DATOS (clases propias) ----------------
class Nodo:
    def __init__(self, dato):
        self.dato = dato
        self.sig = None
        self.ant = None


class ListaCircular:
    """Lista circular doblemente enlazada: orden de las armas."""

    def __init__(self):
        self.actual = None
        self.tamano = 0

    def agregar(self, dato):
        nuevo = Nodo(dato)
        if self.actual is None:
            nuevo.sig = nuevo.ant = nuevo
            self.actual = nuevo
        else:
            ultimo = self.actual.ant
            ultimo.sig, nuevo.ant = nuevo, ultimo
            nuevo.sig, self.actual.ant = self.actual, nuevo
        self.tamano += 1

    def fijar(self, dato):
        nodo = self.actual
        for _ in range(self.tamano):
            if nodo.dato == dato:
                self.actual = nodo
                return True
            nodo = nodo.sig
        return False

    def siguiente(self):
        self.actual = self.actual.sig
        return self.actual.dato

    def anterior(self):
        self.actual = self.actual.ant
        return self.actual.dato


class Cola:
    """Cola FIFO: enemigos de una oleada, en el orden en que aparecen."""

    def __init__(self):
        self.frente = None
        self.final = None
        self.tamano = 0

    def encolar(self, dato):
        nodo = Nodo(dato)
        if self.final is None:
            self.frente = self.final = nodo
        else:
            self.final.sig = nodo
            self.final = nodo
        self.tamano += 1

    def desencolar(self):
        dato = self.frente.dato
        self.frente = self.frente.sig
        if self.frente is None:
            self.final = None
        self.tamano -= 1
        return dato


class Ranking:
    """Lista enlazada ordenada de mayor a menor puntaje (maximo 5)."""

    def __init__(self, limite=5):
        self.cabeza = None
        self.limite = limite

    def insertar(self, registro):
        nuevo = Nodo(registro)
        if self.cabeza is None or registro["puntaje"] > self.cabeza.dato["puntaje"]:
            nuevo.sig, self.cabeza = self.cabeza, nuevo
        else:
            act = self.cabeza
            while act.sig is not None and act.sig.dato["puntaje"] >= registro["puntaje"]:
                act = act.sig
            nuevo.sig, act.sig = act.sig, nuevo
        act, n = self.cabeza, 1          # recortar al limite
        while act is not None:
            if n == self.limite:
                act.sig = None
            act, n = act.sig, n + 1

    def lista(self):
        salida, act = [], self.cabeza
        while act is not None:
            salida.append(act.dato)
            act = act.sig
        return salida


ARMAS = ["rifle", "shotgun", "sniper", "smg"]
RANKING = Ranking()


# ---------------- LOGICA DEL JUEGO ----------------
def muros_edificio(cx, cz, w, d, puerta, alto=3.5, grosor=1.2, hueco=6.0):
    """Cuatro muros (centro x, z, ancho, profundidad, alto, tipo) con una puerta."""
    def lado(horizontal, cx_, cz_, largo, con_puerta):
        if not con_puerta:
            return [(cx_, cz_, largo, grosor, alto, "concrete")] if horizontal else [(cx_, cz_, grosor, largo, alto, "concrete")]
        seg, off = (largo - hueco) / 2, (largo + hueco) / 4
        if horizontal:
            return [(cx_ - off, cz_, seg, grosor, alto, "concrete"), (cx_ + off, cz_, seg, grosor, alto, "concrete")]
        return [(cx_, cz_ - off, grosor, seg, alto, "concrete"), (cx_, cz_ + off, grosor, seg, alto, "concrete")]
    return (lado(True, cx, cz - d / 2, w, puerta == "N") + lado(True, cx, cz + d / 2, w, puerta == "S")
            + lado(False, cx - w / 2, cz, d, puerta == "W") + lado(False, cx + w / 2, cz, d, puerta == "E"))


EDIFICIOS = [(-50, -50, 18, 14, "S"), (0, -58, 16, 12, "S"), (50, -48, 18, 14, "W"), (-58, 0, 14, 18, "E"),
             (58, 5, 14, 18, "W"), (-48, 52, 18, 14, "N"), (0, 58, 16, 12, "N"), (50, 50, 18, 14, "N"),
             (-30, -26, 10, 8, "E")]

NOMBRES = ["ALMACÉN", "CUARTEL", "TALLER", "HANGAR", "OFICINAS", "FÁBRICA", "SILO", "PUERTO", "TORRE"]


def generar_mapa():
    # formato de cada obstaculo: (x, z, ancho, profundidad, alto, tipo)
    obst = [(-12, -8, 8, 2, 3, "concrete"), (12, -8, 8, 2, 3, "concrete"),
            (-12, 8, 8, 2, 2, "sandbag"), (12, 8, 8, 2, 2, "sandbag")]          # base inicial
    barriles = [(-8, -4), (8, 4)]
    for e in EDIFICIOS:
        obst += muros_edificio(*e)
        barriles.append((e[0], e[1]))
    intentos = 0
    while len(obst) < 62 and intentos < 500:                                   # coberturas sueltas
        intentos += 1
        x, z = random.uniform(-68, 68), random.uniform(-68, 68)
        horiz = random.random() < 0.5
        w, d = (random.uniform(5, 9), 1.5) if horiz else (1.5, random.uniform(5, 9))
        if math.hypot(x, z) < 22 or any(abs(x - o[0]) < (w + o[2]) / 2 + 3 and abs(z - o[1]) < (d + o[3]) / 2 + 3 for o in obst):
            continue
        obst.append((x, z, w, d, 2, random.choice(["sandbag", "concrete"])))
    for _ in range(10):
        x, z = random.uniform(-68, 68), random.uniform(-68, 68)
        if math.hypot(x, z) > 20:
            barriles.append((x, z))
    lugares = [{"nombre": "BASE", "x": 0, "z": 0}] + [{"nombre": n, "x": e[0], "z": e[1]} for e, n in zip(EDIFICIOS, NOMBRES)]
    return {"obstaculos": obst, "barriles": barriles, "lugares": lugares}


def generar_oleada(n):
    """Cola con el orden de aparicion de los enemigos de la oleada n."""
    cola = Cola()
    for i in range(6 + 3 * n):
        cola.encolar("HEAVY" if i % 4 == 3 else ("FAST" if n >= 3 and i % 5 == 4 else "NORMAL"))
    if n % 5 == 0:
        cola.encolar("BOSS")
    return [cola.desencolar() for _ in range(cola.tamano)]


# ---------------- RUTAS ----------------
@app.get("/")
def inicio():
    return send_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"))


@app.get("/salud")
def salud():
    return "ok"


@app.get("/api/info")
def api_info():
    return jsonify({"estado": "Running", "armas": ARMAS, "estructuras": ["ListaCircular", "Cola", "Ranking"]})


@app.get("/api/mapa")
def api_mapa():
    return jsonify(generar_mapa())


@app.get("/api/oleada")
def api_oleada():
    return jsonify({"enemigos": generar_oleada(max(1, request.args.get("n", 1, type=int)))})


@app.post("/api/arma")
def api_arma():
    d = request.get_json(force=True)
    lista = ListaCircular()
    for a in ARMAS:
        lista.agregar(a)
    lista.fijar(d.get("actual", "rifle"))
    nueva = lista.siguiente() if d.get("dir", 1) > 0 else lista.anterior()
    return jsonify({"arma": nueva, "orden": ARMAS})


@app.post("/api/puntaje")
def api_puntaje():
    d = request.get_json(force=True)
    RANKING.insertar({"nombre": str(d.get("nombre", "Jugador"))[:16], "puntaje": int(d.get("puntaje", 0)),
                      "bajas": int(d.get("bajas", 0)), "oleada": int(d.get("oleada", 1))})
    return jsonify({"ranking": RANKING.lista()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
