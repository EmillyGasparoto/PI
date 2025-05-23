const mysql = require("mysql2");

const db = mysql.createConnection({
    host: "localhost",
    user: "root",
    password: "Laporine1940@", // ⚠️ Se seu banco não tem senha, deixe como ""
    database: "clinictech"
});

db.connect((err) => {
    if (err) {
        console.error("❌ Erro ao conectar ao banco de dados:", err.message);
        return;
    }
    console.log("✅ Conectado ao banco de dados MySQL!");
});

module.exports = db;
