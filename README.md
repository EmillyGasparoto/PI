# ClinicTech 🏥💻 ## 
🚀 Sobre o Projeto ClinicTech é um sistema de gerenciamento para clínicas médicas, permitindo o cadastro e controle de pacientes, consultas e profissionais da saúde. 

## 🛠 Tecnologias Utilizadas - 
**Node.js** - Backend -
 **Express.js** - Framework -
  **MySQL** - Banco de dados - 
  **Postman** - Testes de API -
  **bcrypt** - Criptografia de senhas - 
  **JWT** - Autenticação segura 

📂 Estrutura do Projeto -
 **clinictech/** → Pasta principal do projeto. - **config/** → Contém arquivos de configuração, como o banco de dados. - `db.js` → Gerencia a conexão com o banco MySQL. - **routes/** → Contém as rotas da API (endpoints para comunicação). - `users.js` → Gerencia o CRUD de usuários (criar, listar, atualizar e excluir). - `server.js` → Arquivo principal que inicia o servidor e configura o backend.

   ⚙️ Como Instalar e Rodar o Projeto 
   1️⃣ **Clone o repositório** ```bash git clone https://github.com/seu-usuario/clinictech.git 2️⃣ Entre na pasta do projeto bash cd clinictech 
   3️⃣ Instale as dependências bash npm install 
   4️⃣ Configure o banco de dados Crie um banco de dados MySQL chamado clinitech. Verifique se config/db.js tem os dados corretos. 
   5️⃣ Inicie o servidor bash node server.js 
   ✅ Se tudo estiver correto, o terminal mostrará "Servidor rodando na porta 3000!".
    🔎 Testando APIs com Postman Criar usuário Método: POST URL: http://localhost:3000/users Body (JSON): json { "name": "João Silva", "email": "joao@example.com", "password": "123456", "role": "patient" } Listar usuários Método: GET URL: http://localhost:3000/users Atualizar usuário Método: PUT URL: http://localhost:3000/users/:id Excluir usuário Método: DELETE URL: http://localhost:3000/users/:id 
    🔮 Próximos Passos Finalizar instalação do MySQL e testar conexão
    🔄 Implementar autenticação JWT
    🔐 Melhorar segurança das senhas com bcrypt
    🔑 Criar um frontend em React.js 🎨