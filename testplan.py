#
# Implementacao dos testes em https://gist.github.com/getupcloud/289a9193f7777deca6bc
#
# Para rodar os testes, execute:
#
#   $ ADMIN_TOKEN=XXXXXXXXXXXXXXXX py.test -v -x testplan.py
#

import os
import stat
import json
import shutil
import random
import subprocess
import mechanize
from hammock import Hammock

#
# Setup
#

assert 'ADMIN_TOKEN' in os.environ, 'Must set enviroment var $ADMIN_TOKEN'

CART_PHP    = 'php-5.3'
GITLAB      = 'https://git.getupcloud.com'
BROKER      = 'https://broker.getupcloud.com'
ADMIN_EMAIL = 'admin@getupcloud.com'
ADMIN_TOKEN = os.environ['ADMIN_TOKEN']

USER_EMAIL  = 'getuptest.{}@getupcloud.com'.format(os.getpid())
USER_PASS   = ''.join(random.sample('abcdefghijkl0123456789', 10))

USER_TOKEN  = '' # read after creation
KEY_RSA     = None
KEY_DSA     = None
APP         = 'testapp'
DOMAIN      = 'testdom'
PROJECT     = '{app}-{domain}'
GIT_URL     = 'git@git.getupcloud.com:{project_name}.git'
GIT_DIR     = '{project_name}.git'
DATA_DIR    = os.path.abspath('data-dir')

gitlab      = Hammock(GITLAB)

def setup_module():
	if os.path.isdir(DATA_DIR):
		shutil.rmtree(DATA_DIR)
	os.mkdir(DATA_DIR)

	global KEY_RSA, KEY_DSA
	KEY_RSA = create_rsa_key()
	KEY_DSA = create_dsa_key()


def teardown_module():
	pass

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

def create_project(name):
	'''Cria projeto no gitlab.
	'''
	data = json.dumps({'name': name})
	headers = {'Content-Type': 'application/json'}
	params = {'private_token': USER_TOKEN}
	project = gitlab.api.v2.projects.POST(verify=False, data=data, headers=headers, params=params)
	assert project.ok, 'Error creating project: data={data}, status_code={project.status_code}, response={project.content}'.format(data=data, project=project)
	return project.json()

def git(args, repo_dir='.', priv_key=None):
	assert isinstance(args, (list, tuple))
	assert os.path.isdir(repo_dir)
	if priv_key is not None:
		if isinstance(priv_key, (list, tuple)):
			priv_key = priv_key[0]
		assert os.path.isfile(priv_key)
	git_ssh = os.path.join(os.path.dirname(__file__), 'git-ssh')
	command = ['git'] + list(args)
	assert subprocess.call(command, cwd=repo_dir, env={'GIT_SSH': git_ssh, 'PRIV_KEY': priv_key or ''}) == 0

def clone_project(project_name, priv_key):
	'''Clona projeto do gitlab.
	'''
	git_url = GIT_URL.format(project_name=project_name)
	repo_dir = os.path.join(DATA_DIR, GIT_DIR.format(project_name=project_name))
	git(['clone', git_url, repo_dir], priv_key=priv_key)
	assert os.path.isdir(repo_dir) and os.path.isdir(os.path.join(repo_dir, '.git'))

def add_file_to_project(project_name, filename, content=None):
	'''Inclui arquivo no projeto, sobrescrevendo se o arquivo ja existe.
	'''
	repo_dir = os.path.join(DATA_DIR, GIT_DIR.format(project_name=project_name))
	_filename = os.path.join(repo_dir, filename)
	is_new = not os.path.isfile(_filename)
	with open(_filename, 'w') as f:
		if content is not None:
			f.write(str(content))
	git(['add', filename], repo_dir=repo_dir)
	log_mesg = '{mesg}: {filename}'.format(mesg='create' if is_new else 'updated', filename=filename)
	git(['commit', '-m', log_mesg, filename], repo_dir=repo_dir)

def push_project(project_name, priv_key):
	'''Execute git push no projeto
	'''
	repo_dir = os.path.join(DATA_DIR, GIT_DIR.format(project_name=project_name))
	git(['push', 'origin', 'master'], repo_dir=repo_dir, priv_key=priv_key)

#
# Operacoes de usuario
#

def create_user(name, email, password):
	'''Cria usuario no gitlab. Verifica status HTTP=201 e
		dados retornados na resposta.
	'''
	data = {'name': name, 'email': email, 'password': password}
	headers = {
		'Private-Token': ADMIN_TOKEN,
		'Content-Type': 'application/json',
	}
	user = gitlab.api.v2.users.POST(verify=False, data=json.dumps(data), headers=headers)
	assert user.ok, 'Error creating user: data={data}, status_code={user.status_code}, response={user.content}'.format(data=data, user=user)
	return user.json()

def get_user(email, password):
	'''Busca dados de usuario.
	'''
	raise NotImplementedError()

def login_user(email, password): # pylint: disable=E1102
	'''Realiza login no gitlab.
	'''
	b = mechanize.Browser()
	b.open(GITLAB)      # pylint: disable=E1102
	b.select_form(nr=0) # pylint: disable=E1102
	b.form.set_value(value=email, id='user_email')
	b.form.set_value(value=password, id='user_password')
	r = b.submit()      # pylint: disable=E1102
	assert r.geturl().rstrip('/') == GITLAB.rstrip('/')

def get_user_token(email, password):
	'''Busca private_token do usuario.
	'''
	data = json.dumps({'email': email, 'password': password})
	headers = {'Content-Type:': 'application/json'}
	session = gitlab.api.v2.session.POST(verify=False, data=data, headers=headers)
	assert session.ok
	assert 'private_token' in session.json(), 'Session token not found (invalid user or password?)'
	return session.json()['private_token']

def create_ssh_key(key_type):
	'''Cria par de chaves ssh-{key_type} e retorna tupla (private, public).
	'''
	priv_key_filename = os.path.join(DATA_DIR, 'test_id_' + key_type)
	pub_key_filename  = priv_key_filename + '.pub'
	for f in [ priv_key_filename, pub_key_filename ]:
		try: os.unlink(f)
		except: pass
	assert subprocess.call(['env', 'ssh-keygen', '-t', key_type, '-N', '', '-f', priv_key_filename]) == 0
	assert os.path.isfile(priv_key_filename) and os.path.isfile(pub_key_filename)
	for f in [ priv_key_filename, pub_key_filename ]:
		os.chmod(f, stat.S_IRUSR | stat.S_IWUSR)
	return priv_key_filename, pub_key_filename

def create_rsa_key():
	'''Cria par de chaves ssh-rsa e retorna tupla (private_file, public_file).
	'''
	return create_ssh_key('rsa')

def create_dsa_key():
	'''Cria par de chaves ssh-dsa e retorna tupla (private_file, public_file).
	'''
	return create_ssh_key('dsa')

def add_user_key(title, public_key_file):
	'''Insere chave publica na conta do usuario
	'''
	with open(public_key_file) as key:
		data = json.dumps({'title': title, 'key': key.read()})
		headers = {'Content-Type:': 'application/json'}
		params = {'private_token': USER_TOKEN}
		session = gitlab.api.v2.user.keys.POST(verify=False, data=data, headers=headers, params=params)
		assert session.ok

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
	create_user(name='Getup Cloud Test User {}'.format(os.getpid()), email=USER_EMAIL, password=USER_PASS)
	login_user(email=USER_EMAIL, password=USER_PASS)

def test_user_auth_token():
	'''1.2 Autenticacao de usuario
	'''
	global USER_TOKEN
	USER_TOKEN = get_user_token(email=USER_EMAIL, password=USER_PASS)

def test_user_pub_key():
	'''1.3 Gerenciamento de chave ssh
	'''
	add_user_key('rsa-key', KEY_RSA[1])
	add_user_key('dsa-key', KEY_DSA[1])
	project_name = 'testuserpubkey-{}'.format(os.getpid())
	create_project(project_name)
	clone_project(project_name, KEY_DSA)
	add_file_to_project(project_name, 'README', 'hello world')
	push_project(project_name, KEY_RSA)

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
