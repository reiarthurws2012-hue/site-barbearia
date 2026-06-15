from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'

SENHA_ADMIN = "1234"
@app.route("/admin/login", methods=["GET", "POST"])
def login_admin():
    if request.method == "POST":
        senha = request.form["senha"]

        if senha == SENHA_ADMIN:
            session["admin"] = True
            return redirect("/admin")
        else:
            return "Senha incorreta"

    return render_template("adm.html")


@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin/login")

    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        SELECT id, dia, data, horario, nome, telefone, servico
        FROM agendamentos
                ORDER BY data, horario
    """)

    agendamentos = cursor.fetchall()
    banco.close()

    return render_template("admi.html", agendamentos=agendamentos)


@app.route("/admin/sair")

def sair_admin():
    session.pop("admin", None)
    return redirect("/")
def conectar():
    return sqlite3.connect("barbearia.db")

def gerar_horarios(dia):
    if dia in ["segunda", "terca", "quarta", "quinta", "sexta"]:
        return ["18:30", "19:15", "20:00"]
    elif dia == "sabado":
        return [
            "09:00", "09:45", "10:30", "11:15", "12:00", "12:45",
            "13:30", "14:15", "15:00", "15:45", "16:30", "17:15", "18:00"
        ]
    return []

def dia_da_semana(data_str):
    try:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

    nomes = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]
    return nomes[data_obj.weekday()]


def criar_banco():
    banco = conectar()
    cursor = banco.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL,
            data TEXT NOT NULL,
            horario TEXT NOT NULL,
            nome TEXT NOT NULL,
            telefone TEXT NOT NULL,
            servico TEXT NOT NULL,
            UNIQUE(dia, data, horario)
        )
    """)

    banco.commit()
    # Migração simples: se a tabela já existia sem a coluna 'data', adicioná-la.
    cursor.execute("PRAGMA table_info(agendamentos)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'data' not in cols:
        try:
            cursor.execute("ALTER TABLE agendamentos ADD COLUMN data TEXT DEFAULT ''")
            banco.commit()
        except sqlite3.OperationalError:
            # Em caso de erro (raridade), ignorar para não quebrar a inicialização
            pass

    banco.close()

def horarios_ocupados(dia, data=None):
    banco = conectar()
    cursor = banco.cursor()

    if data:
        cursor.execute("SELECT horario FROM agendamentos WHERE data = ?", (data,))
    else:
        cursor.execute("SELECT horario FROM agendamentos WHERE dia = ?", (dia,))

    ocupados = [linha[0] for linha in cursor.fetchall()]

    banco.close()
    return ocupados

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/agendar", methods=["POST"])
def agendar():
    dia = request.form.get("dia")
    data = request.form.get("data")

    if not dia and not data:
        return "Por favor selecione um dia ou informe uma data.", 400

    if not dia:
        dia = dia_da_semana(data)
        if not dia:
            return "Data inválida.", 400

    if data:
        return redirect(f"/agendar/{dia}?data={data}")
    return redirect(f"/agendar/{dia}")

@app.route("/agendar/<dia>", methods=["GET", "POST"])
def agendar_dia(dia):
    data = request.args.get("data")
    if request.method == "POST":
        # prefer form-supplied data (hidden field) over query param
        data_form = request.form.get("data") or data

        horario = request.form["horario"]
        nome = request.form["nome"]
        telefone = request.form["telefone"]
        servico = request.form["servico"]

        banco = conectar()
        cursor = banco.cursor()

        try:
            cursor.execute("""
                INSERT INTO agendamentos (dia, data, horario, nome, telefone, servico)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dia, data_form, horario, nome, telefone, servico))

            banco.commit()
            banco.close()

            return render_template(
                "confirmar.html",
                dia=dia,
                data=data_form,
                horario=horario,
                nome=nome,
                servico=servico
            )

        except sqlite3.IntegrityError:
            banco.close()
            return "Esse horário já foi agendado. Volte e escolha outro."

    todos_horarios = gerar_horarios(dia)
    ocupados = horarios_ocupados(dia, data)

    horarios = []

    for horario in todos_horarios:
        if horario not in ocupados:
            horarios.append(horario)

    return render_template("agendar.html", dia=dia, horarios=horarios, data=data)
@app.route("/confirmar")
def confirmar():
    return render_template("confirmar.html")

if __name__ == "__main__":
    criar_banco()
    app.run(debug=True)