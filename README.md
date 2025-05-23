
🏥 ClinicTech - Backend
🔹 Um sistema de gestão para clínicas, integrado com MySQL e Node.js

🚀 Tecnologias utilizadas
Node.js

Express.js

MySQL

Git & GitHub

📌 Configuração do ambiente
1️⃣ Instalar dependências
bash
npm install express mysql2
2️⃣ Configurar o banco de dados MySQL
Crie um banco chamado clinictech

Configure os usuários e permissões corretamente

3️⃣ Configurar o arquivo db.js
javascript
const mysql = require("mysql2");

const db = mysql.createConnection({
    host: "localhost",
    user: "root",
    password: "SUA_SENHA_AQUI",
    database: "clinictech"
});

db.connect((err) => {
    if (err) {
        console.error("❌ Erro ao conectar ao banco:", err.message);
        return;
    }
    console.log("✅ Conectado ao banco de dados MySQL!");
});

module.exports = db;
💡 Troque "SUA_SENHA_AQUI" pela senha real do seu MySQL!

📌 Rotas da API
Usuários
✅ GET /usuarios → Listar usuários ✅ POST /usuarios → Criar usuário ✅ PUT /usuarios/:id → Atualizar usuário por ID ✅ DELETE /usuarios/:id → Excluir usuário por ID

Consultas
✅ GET /consultas → Listar consultas ✅ POST /consultas → Criar nova consulta

📌 Executar o servidor
1️⃣ Iniciar o backend
bash
node server.js
2️⃣ Testar APIs no navegador ou Postman
Acesse:

http://localhost:3000/usuarios
🔥 Git e versionamento
1️⃣ Enviar alterações ao GitHub
bash
git add .
git commit -m "Atualização do backend"
git push origin master
✅ Agora seu código está seguro no GitHub! 🚀