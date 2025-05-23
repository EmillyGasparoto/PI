const express = require("express");
const mysql = require("mysql2");

const app = express();
const PORT = 3000;

// Configuração do banco de dados
const db = mysql.createConnection({
    host: "localhost",
    user: "root",
    password: "SUA_SENHA_AQUI", // 🛠️ Troque pela senha correta
    database: "clinictech"
});

db.connect((err) => {
    if (err) {
        console.error("❌ Erro ao conectar ao banco:", err.message);
        return;
    }
    console.log("✅ Conectado ao banco de dados MySQL!");
});

app.use(express.json()); // Middleware para aceitar JSON

// 📌 Rota GET - Listar usuários
app.get("/usuarios", (req, res) => {
    db.query("SELECT * FROM usuarios", (err, results) => {
        if (err) {
            return res.status(500).json({ erro: "Erro ao buscar usuários" });
        }
        res.json(results);
    });
});

// 📌 Rota POST - Criar usuário
app.post("/usuarios", (req, res) => {
    const { nome, email } = req.body;
    db.query("INSERT INTO usuarios (nome, email) VALUES (?, ?)", [nome, email], (err, results) => {
        if (err) {
            return res.status(500).json({ erro: "Erro ao criar usuário" });
        }
        res.json({ mensagem: "Usuário criado com sucesso!", id: results.insertId });
    });
});

// 📌 Rota PUT - Atualizar usuário por ID
app.put("/usuarios/:id", (req, res) => {
    const { nome, email } = req.body;
    const { id } = req.params;
    db.query("UPDATE usuarios SET nome = ?, email = ? WHERE id = ?", [nome, email, id], (err) => {
        if (err) {
            return res.status(500).json({ erro: "Erro ao atualizar usuário" });
        }
        res.json({ mensagem: "Usuário atualizado com sucesso!" });
    });
});

// 📌 Rota DELETE - Excluir usuário por ID
app.delete("/usuarios/:id", (req, res) => {
    const { id } = req.params;
    db.query("DELETE FROM usuarios WHERE id = ?", [id], (err) => {
        if (err) {
            return res.status(500).json({ erro: "Erro ao excluir usuário" });
        }
        res.json({ mensagem: "Usuário excluído com sucesso!" });
    });
});

// 📌 Rota GET - Listar consultas
app.get("/consultas", (req, res) => {
    db.query("SELECT * FROM consultas", (err, results) => {
        if (err) {
            return res.status(500).json({ erro: "Erro ao buscar consultas" });
        }
        res.json(results);
    });
});

// 📌 Rota POST - Criar consulta
app.post("/consultas", (req, res) => {
    const { paciente_id, medico_id, data_hora, status, observacoes } = req.body;
    db.query(
        "INSERT INTO consultas (paciente_id, medico_id, data_hora, status, observacoes) VALUES (?, ?, ?, ?, ?)",
        [paciente_id, medico_id, data_hora, status, observacoes],
        (err, results) => {
            if (err) {
                return res.status(500).json({ erro: "Erro ao criar consulta" });
            }
            res.json({ mensagem: "Consulta criada com sucesso!", id: results.insertId });
        }
    );
});

// Inicia o servidor
app.listen(PORT, () => {
    console.log(`✅ Servidor rodando na porta ${PORT}`);
});
