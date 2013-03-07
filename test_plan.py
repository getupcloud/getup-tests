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
import pytest
import random
import requests
import mechanize
import subprocess
from functools import wraps
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
APP         = 'tstapp'
DOMAIN      = 'testdom{}'.format(os.getpid())
PROJECT     = '{app}-{domain}'
GIT_URL     = 'git@git.getupcloud.com:{project_name}.git'
GIT_DIR     = '{project_name}.git'
DATA_DIR    = os.path.abspath('data-dir')

gitlab      = Hammock(GITLAB, verify=False)
openshift   = None

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
	domain = openshift.broker.rest.domains.POST(data={'id': name})
	if error:
		assert domain.ok, 'Error creating domain {name}: {domain.status_code} {domain.reason}:\n{domain.text}'.format(**locals())
	return domain.json if domain.ok else False

def get_domain(name, error=True):
	'''Retorna dados de dominio. Se {error}=True, falha se ocorrer um
		erro na operacao, retornando True ou False.
	'''
	domain = openshift.broker.rest.domains(name).GET()
	if error:
		assert domain.ok, 'Invalid domain {name}: {domain.status_code} {domain.reason}:\n{domain.text}'.format(**locals())
	return domain.json if domain.ok else False

def update_domain(name, new_name, error=True):
	'''Altera o nome de um dominio. Se {error}=True, falha se nao conseguir
	renomear, retornando True ou False.
	'''
	# usa apenas o id se for um objeto ScopedDomain()
	try: name = name.id
	except AttributeError: pass

	domain = openshift.broker.rest.domains(name).PUT(data={'id': new_name})
	if error:
		assert domain.ok, 'Invalid domain {name}: {domain.status_code} {domain.reason}:\n{domain.text}'.format(**locals())
	return domain.json if domain.ok else False

def delete_domain(name, force=False, error=True):
	'''Remove um dominio. Se {error}=True, falha se nao conseguir
	remover, retornando True ou False.
	'''
	# usa apenas o id se for um objeto ScopedDomain()
	try: name = name.id
	except AttributeError: pass

	response = openshift.broker.rest.domains(name).DELETE(data={'force': str(force).lower()})
	if error:
		assert response.ok, 'Error deleting domain {name}: {response.status_code} {response.reason}:\n{response.text}'.format(**locals())
	return response.json if response.ok else False

#
# Operacoes de aplicacao
#

def create_app(name, domain, carts, scale=False):
	'''Cria uma aplicacao. Se {name} for falso, gera um nome aleatorio.
		Falha se ocorrer um erro na operacao.
	'''
	if not name:
		name = '{prefix}{suffix}'.format(prefix=APP, suffix=''.join(random.sample('abcdefghijkl0123456789', 4)))
	data = { 'name': name, 'scale': scale }
	if isinstance(carts, (list, tuple)):
		data['cartridges'] = carts
	else:
		data['cartridge'] = carts

	# usa apenas o id se for um objeto ScopedDomain()
	try: domain = domain.id
	except AttributeError: pass

	app = openshift.broker.rest.domains(domain).applications.POST(data=data)
	assert app.ok, 'Erro creating app {name}: {app.status_code} {app.reason}:\n{app.text}'.format(**locals())
	return app.json

def get_app(name, domain):
	'''Retorna dados de uma aplicacao. Falha se aplicacao nao existir.
	'''
	raise NotImplementedError()

def delete_app(name, domain, error=True):
	'''Remove uma aplicacao. Se {error}=True, falha se aplicacao
		nao existir ou ocorrer um error na operacao, retornando
		True ou False neste caso.
	'''
	# usa apenas o id se for um objeto ScopedDomain()
	try: domain = domain.id
	except AttributeError: pass

	response = openshift.broker.rest.domains(domain).applications(name).DELETE()
	if error:
		assert response.ok, 'Error deleting app {name}: {response.status_code} {response.reason}:\n{response.text}'.format(**locals())
	return response.json if response.ok else False

#
# Operacoes de projeto
#

def create_project(name):
	'''Cria projeto no gitlab.
	'''
	data = json.dumps({'name': name})
	headers = {'Content-Type': 'application/json'}
	params = {'private_token': USER_TOKEN}
	project = gitlab.api.v2.projects.POST(data=data, headers=headers, params=params)
	assert project.ok, 'Error creating project: data={data}, status_code={project.status_code}, response={project.content}'.format(data=data, project=project)
	return project.json

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
	user = gitlab.api.v2.users.POST(data=json.dumps(data), headers=headers)
	assert user.ok, 'Error creating user: data={data}, status_code={user.status_code}, response={user.content}'.format(data=data, user=user)
	return user.json

def get_user(email, password):
	'''Busca dados de usuario.
	'''
	raise NotImplementedError()

def login_user(email, password):
	'''Realiza login no gitlab.
	'''
	b = mechanize.Browser()
	b.open(GITLAB) # pylint: disable=E1102
	b.select_form(nr=0) # pylint: disable=E1102
	b.form.set_value(value=email, id='user_email')
	b.form.set_value(value=password, id='user_password')
	r = b.submit() # pylint: disable=E1102
	assert r.geturl().rstrip('/') == GITLAB.rstrip('/')

def get_user_token(email, password):
	'''Busca private_token do usuario.
	'''
	data = json.dumps({'email': email, 'password': password})
	headers = {'Content-Type:': 'application/json'}
	session = gitlab.api.v2.session.POST(data=data, headers=headers)
	assert session.ok
	assert 'private_token' in session.json, 'Session token not found (invalid user or password?)'
	return session.json['private_token']

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
		session = gitlab.api.v2.user.keys.POST(data=data, headers=headers, params=params)
		assert session.ok

#
# Operacoes de url
#

def get_url(url, **kva):
	return requests.get(url, verify=False, **kva)

def get_url_status(url, **kva):
	return get_url(url, **kva).status_code

#
# Operacoes de accouting
#
def last_accounted(last_entry):
	# XXX: MOCK
	return True

################################################################################
################################################################################

#
# 1. Testes de usuario
#

class TestUsers:
	def test_create_user(self):
		'''1.1 Criacao de usuario
		'''
		create_user(name='Getup Cloud Test User {}'.format(os.getpid()), email=USER_EMAIL, password=USER_PASS)
		login_user(email=USER_EMAIL, password=USER_PASS)

	def test_user_auth_token(self):
		'''1.2 Autenticacao de usuario
		'''
		global USER_TOKEN, openshift
		USER_TOKEN = get_user_token(email=USER_EMAIL, password=USER_PASS)
		# atualiza objeto openshift com dados de autenticacao
		openshift = Hammock(BROKER, auth=(USER_EMAIL, USER_TOKEN), verify=False)

	def test_user_pub_key(self):
		'''1.3 Gerenciamento de chave ssh
		'''
		add_user_key('rsa-key', KEY_RSA[1])
		add_user_key('dsa-key', KEY_DSA[1])
		project_name = 'testuserpubkey-{}'.format(os.getpid())
		create_project(project_name)
		clone_project(project_name, KEY_DSA)
		add_file_to_project(project_name, 'README', 'hello world')
		push_project(project_name, KEY_RSA)

class TestBroker:
	def test_api_accessible(self):
		'''1.4 API Openshift acessivel
		'''
		url = Hammock(BROKER, verify=False).broker.rest.api
		api = url.GET()
		assert api.ok, 'Openshift API is unaccessible: {url}: {api.status_code} {api.reason}:\n{api.text}'.format(**locals())

#
# 2. Testes de domino
#
@pytest.fixture                    # pylint: disable=E1101
def scoped_domain(request):
	'''Cria um dominio exclusivo para o teste.
		Os atributos do dominio (response['data][*]) podem ser acessados
		como propriedades da instancia. Ex: domain.id == 'mydomain'.
		Para acessar a resposta completa, use scoped_domain.domain['data'|'status'|...]
	'''
	class ScopedDomain:
		def __init__(self):
			self.name = ''.join(random.sample('abcdefghijklmnopqrwstuvwxyz', 8))
			self.domain = None
			self.deleted = False

		def create(self):
			self.domain = create_domain(self.name)
			return self.domain

		def delete(self):
			return True if self.deleted else delete_domain(self.name, force=True)

		def __getitem__(self, name):
			return self.domain[name]

		def __getattr__(self, name):
			try:
				return self['data'][name]
			except:
				raise AttributeError('\'{klass}\' object has no attribute \'{name}\''.format(klass=self.__class__.__name__, name=name))

	sd = ScopedDomain()
	sd.create()
	request.addfinalizer(sd.delete)
	return sd

class TestDomain:
	def test_create_remove_new_domain(self):
		'''2.1. Criacao e remocao de dominio novo
		'''
		name = ''.join(random.sample('abcdefghijklmnopqrwstuvwxyz', 8))
		assert not get_domain(name, error=False)
		try:
			create_domain(name)
			get_domain(name)
		finally:
			delete_domain(name)

	@pytest.mark.usefixtures('scoped_domain') # pylint: disable=E1101
	def test_update_domain(self, scoped_domain):
		'''2.2. Alteracao de dominio
		'''
		new_domain =  scoped_domain.id[1:-1]
		update = False
		try:
			update_domain(scoped_domain.id, new_domain)
			update = True
			last_accounted('update-dom')
			get_domain(new_domain)
		finally:
			if update:
				update_domain(new_domain, scoped_domain['data']['id'])

	@pytest.mark.usefixtures('scoped_domain') # pylint: disable=E1101
	def test_remove_emptied_domain(self, scoped_domain):
		'''2.3 Remocao de dominio esvasiado
		'''
		app = create_app(None, scoped_domain, CART_PHP)
		last_accounted('create-app')
		assert not delete_domain(scoped_domain, force=False, error=False)
		delete_app(app['data']['name'], scoped_domain)
		last_accounted('delete-app')
		delete_domain(scoped_domain, force=False)
		scoped_domain.deleted = True
		last_accounted('delete-dom')
		assert get_url_status(scoped_domain.links['GET']['href'], auth=(USER_EMAIL, USER_TOKEN)) == 404

	@pytest.mark.usefixtures('scoped_domain') # pylint: disable=E1101
	def test_remove_busy_domain(self, scoped_domain):
		'''2.4 Remocao de dominio ocupado
		'''
		create_app(None, scoped_domain, CART_PHP)
		last_accounted('create-app')
		assert not delete_domain(scoped_domain, force=False, error=False)
		delete_domain(scoped_domain, force=True)
		last_accounted('delete-dom')
		scoped_domain.deleted = True
		assert get_url_status(scoped_domain.links['GET']['href'], auth=(USER_EMAIL, USER_TOKEN)) == 404

#
# 3. Gerenciamento de aplicacao
#

class TestApp:
	@pytest.mark.usefixtures('scoped_domain') # pylint: disable=E1101
	def test_create_app_simple_prod(self, scoped_domain):
		'''3.1 Criacao de aplicacao simples (producao)
		'''
		app = create_app(None, scoped_domain.id, CART_PHP)
		last_accounted('create-app')
		project = PROJECT.format(app=app['data']['name'], domain=scoped_domain.id)
		clone_project(project, KEY_RSA)
		add_file_to_project(project, 'php/new-file.txt', 'hello world')
		push_project(project, KEY_RSA)
		res = get_url(app['data']['app_url'] + '/new-file.txt')
		assert res.status_code == 200
		assert res.content == 'hello world'
