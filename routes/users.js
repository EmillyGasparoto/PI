const express = require("express");
const router = express.Router();
const db = require("../config/db");

// Criar usuário (Create)
router.post("/", (req, res) => {
    const { name, email, password, role } = req.body;
    const query = "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)";
    
    db.query(query, [name, email, password, role], (err, result) => {
        if (err) {
            console.error("❌ Erro ao criar usuário:", err.message);
            return res.status(500).send("Erro ao criar usuário!");
        }
        res.status(201).send("✅ Usuário criado com sucesso!");
    });
});

// Buscar todos os usuários (Read)
router.get("/", (req, res) => {
    db.query("SELECT id, name, email, role FROM users", (err, results) => {
        if (err) {
            console.error("❌ Erro ao buscar usuários:", err.message);
            return res.status(500).send("Erro ao buscar usuários!");
        }
        res.json(results);
    });
});

// Atualizar usuário (Update)
router.put("/:id", (req, res) => {
    const { name, email, password, role } = req.body;
    const query = "UPDATE users SET name=?, email=?, password=?, role=? WHERE id=?";
    
    db.query(query, [name, email, password, role, req.params.id], (err, result) => {
        if (err) {
            console.error("❌ Erro ao atualizar usuário:", err.message);
            return res.status(500).send("Erro ao atualizar usuário!");
        }
        res.send("✅ Usuário atualizado!");
    });
});

// Excluir usuário (Delete)
router.delete("/:id", (req, res) => {
    db.query("DELETE FROM users WHERE id=?", [req.params.id], (err, result) => {
        if (err) {
            console.error("❌ Erro ao excluir usuário:", err.message);
            return res.status(500).send("Erro ao excluir usuário!");
        }
        res.send("✅ Usuário excluído!");
    });
});

module.exports = router;
