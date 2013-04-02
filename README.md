Getup - Test Plan
=================

Plano de testes funcionais da plataforma Getup.

As seguintes variaveis sao utilizadas para simplificar a execucao dos testes:

    $GITLAB      = https://git.getupcloud.com
    $BROKER      = https://broker.getupcloud.com
    $ADMIN_EMAIL = admin@getupcloud.com
    $ADMIN_TOKEN = <private_token do usuario admin>
    $USER_EMAIL  = getuptest@getupcloud.com
    $USER_PASS   = <definir valor temporario manualmente>
    $USER_TOKEN  = <private_token do usuario $USER_EMAIL>
    $APP         = testapp
    $DOMAIN      = testdom

Valores entre `<...>` devem ser devidamente substituidos de acordo com o contexto.

Nomenclatura
------------

- aplicacao simples: apenas um gear
- aplicacao composta: mais de um gear
- repositorio inicial: aplicacao criada a apartir de um repositorio git pre-existente (ex: [wordpress-example](https://github.com/openshift/wordpress-example))

1. Testes de usuario
--------------------

Dependencias:

 1. Usuario `$USER_EMAIL` nao pode existir

## 1.1. Criacao de usuario

Verificar se a plataforma consegue criar novos usuarios.

Executar:

    $ curl -v -k --user "$ADMIN_EMAIL:$ADMIN_TOKEN" $GITLAB/api/v2/users -X POST --data "name=Test User&email=$USER_EMAIL&password=$USER_PASS"

Resultados esperados:

1. Resposta HTTP 201
2. Resposta JSON com os dados do usuario criado
3. Verificar se o ususario consegue logar em [https://git.getupcloud.com](https://git.getupcloud.com)

## 1.2. Autenticacao de usuario

Verificar se é possivel acessar o token de autorizacao do usuario.

Executar:

    $ curl -v -k --user "$USER_EMAIL:$USER_PASS" $GITLAB/api/v2/session -X POST --data "{\"email\": \"$USER_EMAIL\", \"password\": \"$USER_PASS\"}"

Resultados esperados:

1. Resposta HTTP 201
2. Resposta JSON com o campo `private_token` preenchido

**O valor do campo `private_token` deve ser utilizado nos testes subsequentes setando a variavel `$USER_TOKEN`.**

    USER_TOKEN=<private_token>

## 1.3 Gerenciamento de chave ssh

Verificar se é possivel inserir e remover chaves ssh do usuario no gitlab.

### Adicionar 2 chaves (uma ssh e outra dsa) no gitlab
### Criar projeto no gitlab
### Clonar o projeto usando a chave rsa
### Incluir arquivo vazio no projeto e publicar usando chave dsa

## 1.4 API Openshift acessivel

Verifica se a API REST do openshift é acessivel

### Acessar e validar a url $BROKER/broker/rest/api

2. Testes de dominio
--------------------

Os testes abaixo devem ser realizados por ambas as interfaces: **REST** e **rhc**.

Dependencias:

- Usuario `$USER_EMAIL` deve existir
- Dominio `$DOMAIN` nao pode existir

## 2.1. Criacao e remocao de dominio novo

Verificar se é possivel criar e logo apos remover o dominio do usuario.

### Criar dominio usando API REST

Executar:

    $ curl -v -k $BROKER/broker/rest/domains -X POST --data 'id=$DOMAIN'

Resultados esperados:

1. Resposta HTTP 201
2. Resposta JSON com as informacoes do dominio recem criado

### Criar dominio usando rhc

Executar:

    $ rhc domain create `$DOMAIN`

Resultado esperado:

1. Mensagem confirmando a criacao do dominio (pode variar de acordo com a versao do rhc)

## 2.2. Alteracao de dominio

Verificar se é possivel renomear um dominio.

### Criar aplicacao simples
### Renomear o dominio
### Verificar nova URL da aplicacao
### Verificar account 'update-dom'
### Voltar o nome anterior do dominio

## 2.3 Remocao de dominio esvasiado

Verificar se é possivel remover um dominio sem aplicacões.

### Criar um dominio
### Verificar account 'create-dom'
### Criar uma aplicacao
### Verificar account 'create-app'
### Tentar remover o dominio ainda com a aplicacao
### Remover a aplicacao
### Verificar account 'delete-app'
### Remover o dominio
### Verificar account 'delete-dom'
### Verificar se o dominio nao existe

## 2.4 Remocao de dominio ocupado

Verificar se é possivel remover um dominio com aplicacao ativa, sem precisar remover a aplicacao.

### Criar um dominio
### Verificar account 'create-dom'
### Criar uma aplicacao
### Verificar account 'create-app'
### Tentar remover o dominio ainda com a aplicacao
### Verificar account 'delete-app' (nao deve existir)
### Remover o dominio forçadamente
### Verificar account 'delete-dom'
### Verificar se o dominio nao existe

3. Gerenciamento de aplicacao
-----------------------------

Dependencias:

- Usuario `$USER_EMAIL` deve existir
- Dominio `$DOMAIN` deve existir
- Chave ssh do usuario deve estar instalada no projeto (gitlab)criar

## 3.1 Criacao de aplicacao simples (producao)

Verificar se é possivel criar uma aplicacao.

### Criar aplicacao
### Verificar account 'create-app'
### Clonar repositorio da aplicacao
### Publicar novo arquivo na aplicacao
### Verificar estado da aplicacao

## 3.2 Remocao de aplicacao (producao)

Verificar se é possivel remover uma aplicacao.

### Criar aplicacao
### Verificar account 'create-app'
### Verificar estado da aplicacao
### Remover aplicacao
### Verificar account 'delete-app'
### Verificar se URL da aplicacao deixa de responder

## 3.3 Criacao de aplicacao simples com repositorio inicial (producao)

Verificar se é possivel criar uma aplicacao, utilizando o codigo de um repositorio existente.

### Criar aplicacao
### Verificar account 'create-app'
### Clonar repositorio da aplicacao
### Publicar novo arquivo na aplicacao
### Verificar estado da aplicacao

## 3.4 Criacao de aplicacao composta (producao)

Verificar se é possivel criar uma aplicacao com mais de um gear.

### Criar aplicacao com gear adicional
### Verificar account 'create-app' (todos os gears devem aparecer)
### Clonar repositorio da aplicacao
### Publicar arquivo de teste de gear (test.php)
### Verificar estado da aplicacao

## 3.5 Criacao de aplicacao composta com repositorio inicial (producao)

Verificar se é possivel criar uma aplicacao com mais de um gear, utilizando o codigo de um repositorio existente.

### Criar aplicacao composta com repositorio inicial
### Verificar account 'create-app' (todos os gears devem aparecer)
### Verificar estado da aplicacao (manual)

## 3.6 Criacao de aplicacao simples multi-branch (desenvolvimento)

Verificar se é possivel criar uma aplicacao com gear de desenvolvimento.

### Criar aplicacao de producao
### Verificar account 'create-app'
### Criar aplicacao de desenvolvimento
### Verificar account 'create-app'
### Verificar remotes configurados
### Clonar repositorio da aplicacao
### Publicar branches de desenvolvimento
### Verificar URLs dos branches

## 3.7 Remoção de branch (desenvolvimento)

Verificar se é possivel remover um branch do gear de desenvolvimento.

### Criar aplicacao de producao
### Verificar account 'create-app'
### Criar aplicacao de desenvolvimento
### Verificar account 'create-app'
### Verificar remotes configurados
### Clonar repositorio da aplicacao
### Publicar branches de desenvolvimento
### Verificar URLs dos branches
### Remover branch
### Verificar URL do branch removido
### Verificar URLs dos branches restantes

## 3.8 Criacao de aplicacao composta multi-branch (desenvolvimento)

Verificar se é possivel criar uma aplicacao de desenvolvimento com mais de um gear.

### Criar aplicacao composta de producao
### Verificar account 'create-app' (todos os gears devem aparecer)
### Criar aplicacao composta de desenvolvimento
### Verificar account 'create-app' (todos os gears devem aparecer)
### Verificar remotes configurados
### Clonar repositorio da aplicacao
### Publicar branches de desenvolvimento
### Verificar URLs dos branches

## 3.9 Criacao de aplicacao composta multi-branch com repositorio inicial (desenvolvimento)

Verificar se é possivel criar uma aplicacao de desenvolvimento com mais de um gear, utilizando o codigo de um repositorio existente.

### Criar aplicacao composta de producao com repositorio inicial
### Verificar account 'create-app' (todos os gears devem aparecer)
### Criar aplicacao composta de desenvolvimento
### Verificar account 'create-app' (todos os gears devem aparecer)
### Verificar remotes configurados
### Clonar repositorio da aplicacao
### Publicar branches de desenvolvimento
### Verificar estado da aplicacao (manual)
### Verificar URLs dos branches (manual)

## 3.10 Inclusao e exclusao de gears para aplicacao simples

Verificar se é possivel incluir e remover gears em uma aplicacao existente.

### Criar aplicacao simples de producao
### Verificar account 'create-app'
### Criar primeiro gear
### Verificar account 'create-gear'
### Verificar se o gear foi criado
### Criar segundo gear
### Verificar account 'create-gear'
### Verificar se o gear foi criado
### Remover primeiro gear
### Verificar account 'delete-gear'
### Verificar se o gear foi removido
### Remover segundo gear
### Verificar account 'delete-gear'
### Verificar se o gear foi removido

4. Escalabilidade de aplicacao
------------------------------

## 4.1 Escalar aplicacao simples manualmente

Verificar se a aplataforma consegue escalar uma aplicacao a partir da solicitacao do usuario.

### Criar aplicacao simples
### Verificar account 'create-app'
### Aplicar limites de gears da aplicacao
### Verificar quantidade de gears atual
### Escalar manualmente a aplicacao
### Verificar account 'scale-up'
### Verificar quantidade de gears atual
### Escalar manualmente a aplicacao ate o limite superior +1
### Verificar account 'scale-up' * N
### Verificar quantidade de gears atual
### Escalar manualmente a aplicacao ate o limite inferior -1
### Verificar account 'scale-down' * N
### Verificar quantidade de gears atual

## 4.2 Escalar aplicacao simples automaticamente

Verificar se a plataforma consegue escalar automaticamente uma aplicacao.
O teste consiste em criar uma aplicacao escalavel, disparar quantidade suficiente de
requisicoes para ela escalar ate o limite, cessar as requisicoes e verificar se esta
volta automaticamente a quantidade inicial de gears.

### Criar aplicacao simples
### Verificar account 'create-app'
### Publicar aplicacao com gargalo de conexoes
### Aplicar limites de gears da aplicacao
### Verificar quantidade de gears atual
### Disparar conexoes para a aplicacao
### Verificar account 'scale-up' * N
### Verificar quantidade de gears atual
### Encerrar as conexoes
### Verificar quantidade de gears atual
### Verificar account 'scale-down' * N

## 4.3 Escalar aplicacao composta manualmente

Verificar se a aplataforma consegue escalar uma aplicacao composta a partir da solicitacao do usuario.

### Criar aplicacao composta
### Verificar account 'create-app' (todos os gears devem aparecer)
### Aplicar limites de gears da aplicacao
### Verificar quantidade de gears atual
### Escalar manualmente a aplicacao
### Verificar account 'scale-up' + N
### Verificar quantidade de gears atual
### Escalar manualmente a aplicacao ate o limite superior +1
### Verificar account 'scale-up' * N
### Verificar quantidade de gears atual
### Escalar manualmente a aplicacao ate o limite inferior -1
### Verificar account 'scale-down' * N
### Verificar quantidade de gears atual

## 4.4 Escalar aplicacao composta automaticamente

Verificar se a plataforma consegue escalar automaticamente uma aplicacao composta.
O teste consiste em criar uma aplicacao composta escalavel, disparar quantidade suficiente de
requisicoes para ela escalar ate o limite, cessar as requisicoes e verificar se esta
volta automaticamente a quantidade inicial de gears.

### Criar aplicacao composta
### Verificar account 'create-app' (todos os gears devem aparecer)
### Publicar aplicacao com gargalo de conexoes
### Aplicar limites de gears da aplicacao
### Verificar quantidade de gears atual
### Disparar conexoes para a aplicacao
### Verificar account 'scale-up' * N
### Verificar quantidade de gears atual
### Encerrar as conexoes
### Verificar account 'scale-down' * N
### Verificar quantidade de gears atual

5. Deploy de aplicacao
----------------------

## 5.1 Hot deploy de aplicacao multi-branch

Verificar se a aplicacao consegue fazer hot-deploy.

### Criar aplicacao simples
### Incluir o arquivo .openshift/markers/hot_deploy e publicar
### Verificar se a aplicacao nao foi reiniciada (output do git push)
### Remover o arquivo .openshift/markers/hot_deploy e publicar
### Verificar se a aplicacao foi reiniciada (output do git push)

6. Referencias
--------------

https://access.redhat.com/knowledge/docs/en-US/OpenShift/2.0/html/User_Guide/sect-OpenShift-User_Guide-Hot_Deploying_Applications.html
