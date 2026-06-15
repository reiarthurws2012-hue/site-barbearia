CREATE TABLE agendamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia TEXT NOT NULL,
    data TEXT NOT NULL,
    horario TEXT NOT NULL,
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    servico TEXT NOT NULL,
    UNIQUE(dia, data, horario)
);