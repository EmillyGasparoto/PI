# projeto - integrador

# 1 - Baixe o repositório do Projeto

git clone https://github.com/EmillyGasparoto/PI.git

# 2 - Repositorio

dentro do Repositporio:

abra o arquivo app.py 
abra o terminal 
assegure que a pasta em que o terminal foi aberto se trata da pasta do repositório 
caso não seja, abra a pasta do repositorio copie o caminho e cole da seguinte maneira cd [cole aqui o caminho do repositorio]  

# 2. Criar e ativar um ambiente virtual
   
 python -m venv venv
 
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 4. Instalar dependências
   
pip install -r requirements.txt

# 6. Inicializar o banco de dados

# Apenas na primeira vez
flask db init             

# Cria uma migração
flask db migrate           

# Aplica as migrações ao banco
flask db upgrade          


# 8. Executar a aplicação
   
flask run
acessar (http://localhost:5000)

# Há outro branch com contribuições.
