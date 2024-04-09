# Zero
Criando bot pra discord ...

## Instalação via Git

```git
git clone https://github.com/Zer0G0ld/Zero
```

# Ambiente Virtual - AV
Criando ...
```python
python3 -m venv venv

```

Ativando no Linux ou MacOS
```linux
source venv/bin/activate

```

Ativando no Windows
```cmd
.\venv\Scripts\Activate
```

Desativando ...
```linux
deactivate

```

### Instalando dependências

```
pip install -r requirements.txt
```

# Informações sobre o projeto
<p>Dividi o projeto em pastas para ficar mais facil de entender.</p>

### Arquivo principal
<p>O arquivo principal é o `app.py` então para rodar o bot você deve exceutar o comando `python3 app.py` </p>

![pyapp.py](src/README/Zero@Zer0G0ld.png)

<p>Isso significa que obviamente o bot está online.</p>
<br>

#### Chamar o bot
<p>Para chamar o bot é só usar o prefixo '$' ou você pode modificar ele aqui: </p>

```python
bot = commands.Bot(command_prefix="$", intents=intents, description=description)
```

<p>Se quiser alterar o `command_prefix`</p>

#### Eventos
<p>O bot tem dois eventos com o decorador `@bot.event` segue: </p>

```python
@bot.event
async def on_ready():   # Aqui ele vai detectar quando o bot está online e te alertará
    logger.info(f"Bot está online como {bot.user.name}") # gera log

    print(f"=================================")
    print(f"Estou Online como {bot.user.name}")
    print(f"=================================")

    for guild in bot.guilds: # Aqui ele va mandar um gif de saudação para as guildas ou servidores ( como preferir )
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                with open('src/saudacao.gif', 'rb') as f:
                    picture = discord.File(f)
                    await channel.send("Olá! Estou online e pronto para interagir.", file=picture)

    bot.add_cog(Economy(bot)) # Aqui ele chama o arquivo Economy que é uma classe que gerencia a economia do bot

    # Verifica se a cog Economy foi carregada corretamente
    cog = bot.get_cog('Economy')
    if cog:
        logger.info("Cog Economy carregada com sucesso.")
    else:
        logger.error("Erro ao carregar a cog Economy.")


@bot.event
async def on_message(message): # Aqui ele vai depurar as menssagens recebidas e vai ingnorar as que ele mesmo mandou 
    logger.info(f"Mensagem recebida de {message.author}: {message.content}") # ele gera um log
    print(f"Menssagem Recebida: {message.content} ") # Apenas para depuração, fora disso é anti ético

    if not message.author.bot:  # Certifica-se de que o autor da mensagem não seja um bot
        user_id = message.author.id
        data_manager = bot.get_cog('Economy').data_manager
        if not data_manager.user_exists(user_id):
            data_manager.register_new_user(user_id)
            await message.channel.send(f"Bem-vindo, {message.author.mention}! Uma nova conta foi criada para você com 100 moedas iniciais.")
    await bot.process_commands(message)
# essa parte de cima ele detecta os usuários que ainda não tem um saldo e adiciona 100 moedas
# para ver é só usar o comando '$saldo'
```

### Comandos
<p>Os comandos estão localizados no diretório `commands`. Lá estaram alguns arquivos de comandos separados por classe, ou seja, cada arquivo é uma classe diferente (pode haver casos de mais de uma classe em um arquivo). </p>

![CommandsPhoto](/src/README//CommandsPhoto.png)

<p>como podem ver além dos arquivos há também um diretório chamado `utils` que é onde eu deixo o banco de dados</p>

### Utils
<p>Como viram na pasta utils é onde fica o banco de dados para isso criei o `data.py` que é o que vai gerenciar o `data.db`</p>

![Utiulsdb](/src/README/Utiuls.png)

<p>Dentro de `data.py` há duas classes `Database` e `DataManager`. Ambas as classes utilizam a biblioteca sqlite3 para interagir com o banco de dados SQLite.</p>
<br>
<p>A classe Database é um gerenciador de contexto que abre uma conexão com o banco de dados SQLite quando o bloco with é iniciado e fecha a conexão quando o bloco with é concluído. Ela retorna um cursor para executar consultas SQL.</p>
<br>
<p>A classe DataManager é responsável por realizar operações no banco de dados, como criar tabelas, verificar se um usuário existe, registrar um novo usuário, adicionar ou remover moedas de um usuário, e assim por diante.</p>

# Licença
Sob a lincença [GNU](https://github.com/Zer0G0ld/Zero/blob/main/LICENSE)
