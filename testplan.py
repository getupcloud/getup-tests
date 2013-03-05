#
# Implementacao dos testes em https://gist.github.com/getupcloud/289a9193f7777deca6bc
#
# Para rodar os testes, execute:
#
#   $ ADMIN_TOKEN=XXXXXXXXXXXXXXXX py.test -v -x testplan.py
#

import os
import json
import random
import mechanize
from hammock import Hammock

#
# Setup
#

assert 'ADMIN_TOKEN' in os.environ, 'Must set enviroment var $ADMIN_TOKEN'

CART_PHP    = 'php-5.3'
GITLAB      = 'https://git.getupcloud.com/'
BROKER      = 'https://broker.getupcloud.com'
ADMIN_EMAIL = 'admin@getupcloud.com'
ADMIN_TOKEN = os.environ['ADMIN_TOKEN']

USER_EMAIL  = 'getuptest@getupcloud.com'
USER_PASS   = ''.join(random.sample('!@#$%&*()-_=+abcdefghijkl0123456789', 10))

USER_TOKEN  = '' # read after creation
KEY_RSA     = None
KEY_DSA     = None
APP         = 'testapp'
DOMAIN      = 'testdom'
PROJECT     = '{app}-{domain}'
GIT_URL     = 'git@git.getupcloud.com:{PROJECT}.git'

gitlab      = Hammock(GITLAB)

'''
def setup_module():
	global KEY_RSA, KEY_DSA
	KEY_RSA = create_rsa_key(USER_EMAIL + '-rsa')
	KEY_DSA = create_dsa_key(USER_EMAIL + '-dsa')

def teardown_module():
	pass
'''

#
# Operacoes de dominio
#

def create_domain(name, error=True):
	'''Cria um dominio. Se {error}=True, falha se dominio ja existe.
	'''
	raise NotImplementedError()

def get_domain(name, error=True):
	'''Retorna dados de dominio. Se {error}=True, falha se ocorrer um
		erro na operacao, retornando True ou False.
	'''
	raise NotImplementedError()

def update_domain(name, new_name, error=True):
	'''Altera o nome de um dominio. Se {error}=True, falha se nao conseguir
	renomear, retornando True ou False.
	'''
	raise NotImplementedError()

def delete_domain(name, force=False, error=True):
	'''Remove um dominio. Se {error}=True, falha se nao conseguir
	remover, retornando True ou False.
	'''
	raise NotImplementedError()

#
# Operacoes de aplicacao
#

def create_app(name, domain, carts, scale=False):
	'''Cria uma aplicacao. Falha se ocorrer um erro na operacao.
	'''
	raise NotImplementedError()

def get_app(name, domain):
	'''Retorna dados de uma aplicacao. Falha se aplicacao nao existir.
	'''
	raise NotImplementedError()

def delete_app(name, domain, error=True):
	'''Remove uma aplicacao. Se {error}=True, falha se aplicacao
		nao existir ou ocorrer um error na operacao, retornando
		True ou False neste caso.
	'''
	raise NotImplementedError()

#
# Operacoes de projeto
#

def create_project(project):
	'''Cria projeto no gitlab.
	'''
	raise NotImplementedError()

def clone_project(project, priv_key):
	'''Clona projeto do gitlab.
	'''
	raise NotImplementedError()

def add_file_to_project(project, filename, content=None):
	'''Comita arquivo no projeto. Adiciona se nao existir.
		Sobrescreve arquivo existente.
	'''
	raise NotImplementedError()

def push_project(project, priv_key):
	'''Execute git push no projeto
	'''
	raise NotImplementedError()

#
# Operacoes de usuario
#

def create_user(name, email, password):
	'''Cria usuario no gitlab. Verifica status HTTP=201 e
		dados retornados na resposta.
	'''
	data = {'name': name, 'email': email, 'password': password}
	headers = {'Private-Token': ADMIN_TOKEN}
	user = gitlab.api.v2.users.POST(verify=False, data=json.dumps(data), headers=headers)
	assert user.ok, 'Error creating user: data={data}, status_code={user.status_code}'.format(data=data, user=user)
	return user

def get_user(email, password):
	'''Busca dados de usuario.
	'''
	raise NotImplementedError()

def login_user(email, password):
	'''Realiza login no gitlab.
	'''
	b = mechanize.Browser()
	b.open(GITLAB)
	b.select_form(nr=0)
	b.form.set_value(value=email, id='user_email')
	b.form.set_value(value=password, id='user_password')
	r = b.submit()
	assert r.geturl() == GITLAB

def get_user_token(email, password):
	'''Busca private_token do usuario.
	'''
	raise NotImplementedError()

def _create_ssh_key(key_type, comment):
	'''Cria par de chaves ssh-{key_type} e retorna tupla (private, public).
	'''
	raise NotImplementedError()

def create_rsa_key(comment):
	'''Cria par de chaves ssh-rsa e retorna tupla (private_file, public_file).
	'''
	raise NotImplementedError()

def create_dsa_key(comment):
	'''Cria par de chaves ssh-dsa e retorna tupla (private_file, public_file).
	'''
	raise NotImplementedError()

def add_user_key(public_key_file):
	'''Insere chave publica na conta do usuario
	'''
	raise NotImplementedError()

#
# Operacoes de url
#

def get_url(url):
	raise NotImplementedError()

def get_url_status(url):
	raise NotImplementedError()

#
# Operacoes de accouting
#
def get_accounting():
	raise NotImplementedError()

################################################################################
################################################################################

#
# 1. Testes de usuario
#

def test_create_user():
	'''1.1 Criacao de usuario
	'''
	create_user(name='Test User', email=USER_EMAIL, password=USER_PASS)
	login_user(email=USER_EMAIL, password=USER_PASS)

def test_user_auth_token():
	'''1.2 Autenticacao de usuario
	'''
	global USER_TOKEN
	USER_TOKEN = get_user_token(email=USER_EMAIL, password=USER_PASS)

def test_user_pub_key():
	'''1.3 Gerenciamento de chave ssh
	'''
	add_user_key(KEY_RSA)
	add_user_key(KEY_DSA)
	project = 'testuserpubkey'
	create_project(project)
	clone_project(project, KEY_DSA)
	add_file_to_project(project, 'new-file.txt', 'hello world')
	push_project(project, KEY_RSA)

#
# 2. Testes de domino
#

def test_create_domain():
	'''2.1. Criacao de dominio
	'''
	assert not get_domain(DOMAIN, error=False)
	create_domain(DOMAIN)
	get_domain(DOMAIN, error=False)

def test_update_domain():
	'''2.2. Alteracao de dominio
	'''
	app_a = create_app(APP, DOMAIN, CART_PHP)
	assert get_url_status(app_a['data']['url']) == 200
	update_domain(DOMAIN, DOMAIN + 'new')
	app_b = get_app(APP, DOMAIN + 'new')
	assert app_a['data']['url'] != app_b['data']['url']
	assert get_url_status(app_b['data']['url']) == 200
	assert get_accounting()[-1] == 'update-dom'
	update_domain(DOMAIN + 'new', DOMAIN)
	app_c = get_app(APP, DOMAIN)
	assert app_a['data']['url'] == app_c['data']['url']
	assert get_url_status(app_c['data']['url']) == 200
	assert get_accounting()[-1] == 'update-dom'

def test_remove_empty_domain():
	'''2.3 Remocao de dominio vazio
	'''
	if get_domain(DOMAIN, error=False):
		delete_domain(DOMAIN, force=True, error=False)
		assert get_accounting()[-1] == 'delete-dom'
	dom = create_domain(DOMAIN)
	assert get_accounting()[-1] == 'create-dom'
	create_app(APP, DOMAIN, CART_PHP)
	assert get_accounting()[-1] == 'create-app'
	assert not delete_domain(DOMAIN, force=False, error=False)
	delete_app(APP, DOMAIN)
	assert get_accounting()[-1] == 'delete-app'
	delete_domain(DOMAIN, force=False)
	assert get_accounting()[-1] == 'delete-dom'
	assert get_url_status(dom['data']['links']['GET']['href']) == 404

def test_remove_busy_domain():
	'''2.4 Remocao de dominio ocupado
	'''
	if get_domain(DOMAIN, error=False):
		delete_domain(DOMAIN, force=True, error=False)
		assert get_accounting()[-1] == 'delete-dom'
	dom = create_domain(DOMAIN)
	assert get_accounting()[-1] == 'create-dom'
	create_app(APP, DOMAIN, CART_PHP)
	assert get_accounting()[-1] == 'create-app'
	assert not delete_domain(DOMAIN, force=False, error=False)
	assert get_accounting()[-1] != 'delete-dom'
	assert delete_domain(DOMAIN, force=True)
	assert get_accounting()[-1] == 'delete-dom'
	assert get_url_status(dom['data']['links']['GET']['href']) == 404

#
# 3. Gerenciamento de aplicacao
#

def test_create_app_simple_prod():
	'''3.1 Criacao de aplicacao simples (producao)
	'''
	create_domain(DOMAIN)
	app = create_app(APP, DOMAIN, CART_PHP)
	assert get_accounting()[-1] == 'create-app'
	clone_project(PROJECT, KEY_RSA)
	add_file_to_project(PROJECT, 'php/new-file.txt', 'hello world')
	push_project(PROJECT, KEY_RSA)
	res = get_url(app['data']['app_url'] + '/new-file.txt')
	assert res.status_code == 200
	assert res.content == 'hello world'
