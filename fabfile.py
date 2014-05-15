# coding: utf-8

import os

from fabric import colors
from fabric.decorators import task
from fabric.api import env, run, sudo, local
from fabric.contrib.files import exists
from fabric.operations import prompt, put
from fabric.context_managers import prefix, cd, settings, shell_env


### Start of config

APP_USER = APP_NAME = VENV_NAME = 'expensereport'
REPO_URL = 'git@github.com:seocam/expensereport.git'


environments = {
    'dev': {
        'hosts': ['127.0.0.1'],
        'key_filename': '~/.vagrant.d/insecure_private_key',
        'port': 2222,
        'is_vagrant': True,
        'superuser': 'vagrant',
    },
    'qa': {
        'hosts': [],
        'port': 22,
        'is_vagrant': False,
        'superuser': 'root',
    },
    'prod': {
        'hosts': ['162.243.230.194'],
        'port': 22,
        'is_vagrant': False,
        'superuser': 'root',
    },
}
DEFAULT_ENVIRONMENT = 'dev'

### End of config

env.user = APP_USER
env.use_shell = False

PROJECT_PATH = os.path.join(os.path.dirname(__file__))
REPO_PATH = '/home/{}/{}'.format(APP_USER, APP_NAME)
SOURCE_VENV = 'source /usr/local/bin/virtualenvwrapper.sh'
WORKON_ENV = '{} && workon {}'.format(SOURCE_VENV, VENV_NAME)
MANAGE_PATH = os.path.join(REPO_PATH, 'src')
SETTINGS_PATH = os.path.join(MANAGE_PATH, APP_NAME)


@task
def environment(name):
    """Set the environment where the tasks will be executed"""
    env.update(environments[name])
    env.environment = name
environment(DEFAULT_ENVIRONMENT)


def aptget_install(pkg):
    sudo('DEBIAN_FRONTEND=noninteractive apt-get install -y -q {}'.format(pkg))


def install_requirements():
    with cd(REPO_PATH), prefix(WORKON_ENV):
        run('pip install -U distribute')
        if not env.is_vagrant:
            run('pip install -r requirements.txt')
            return

        if exists('requirements-{}.txt'.format(env.environment)):
            run('pip install -r requirements-{}.txt'.format(env.environment))
        else:
            run('pip install -r requirements.txt')


def mkvirtualenv():
    if not exists('~/.virtualenvs/' + VENV_NAME):
        with prefix(SOURCE_VENV):
            run('mkvirtualenv ' + VENV_NAME)
            return True


def manage(command):
    django_settings = env.get('django_settings')
    env_vars = {}
    if django_settings:
        env_vars.update({'DJANGO_SETTINGS_MODULE': django_settings})

    with shell_env(**env_vars):
        with cd(MANAGE_PATH), prefix(WORKON_ENV):
            run('python manage.py {}'.format(command))


def syncdb():
    manage('syncdb')


def migrate():
    manage('migrate')


def collectstatic():
    sudo('mkdir -p /usr/share/nginx/{}'.format(APP_NAME))
    sudo('chown {} /usr/share/nginx/{}'.format(env.user, APP_NAME))
    manage('collectstatic --noinput')


def create_local_settings():
    with cd(SETTINGS_PATH), settings(user=env.superuser):
        env_local_settings = 'local_settings-{}.py'.format(env.environment)

        if not exists('local_settings.py') and exists(env_local_settings):
            run('ln -s {} {}'.format(env_local_settings, 'local_settings.py'))
            run('chown {} local_settings.py'.format(env.user))


def update_code():
    if env.is_vagrant:
        if not exists(REPO_PATH):
            run('ln -s /vagrant/ {}'.format(REPO_PATH))
        return

    if not exists(REPO_PATH):
        run('git clone {} {}'.format(REPO_URL, REPO_PATH))
    else:
        with cd(REPO_PATH):
            run('git pull')


@task
def bootstrap():
    """Bootstrap machine to run fabric tasks"""

    with settings(user=env.superuser):

        if not exists('/usr/bin/git'):
            aptget_install('git')

        if env.is_vagrant:
            groups = 'sudo,vagrant'
            local('chmod -fR g+w {}'.format(PROJECT_PATH))
        else:
            groups = 'sudo'

        sudo('useradd {} -G {} -m -s /bin/bash'.format(APP_USER, groups),
             quiet=True)
        ssh_dir = '/home/{0}/.ssh/'.format(APP_USER)
        if not exists(ssh_dir):
            sudo('mkdir -p {0}'.format(ssh_dir))
            sudo('chmod 700 {0}'.format(ssh_dir))
            sudo('cp ~{}/.ssh/authorized_keys /home/{}/.ssh/'.format(
                env.superuser,
                APP_USER
            ))
            sudo('chown -fR {0}:{0} {1}'.format(APP_USER, ssh_dir))

        sudoers_file = os.path.join('/etc/sudoers.d/', APP_USER)
        tmp_file = os.path.join('/tmp', APP_USER)
        if not exists(sudoers_file):
            sudo('echo "{} ALL=NOPASSWD: ALL" > {}'.format(APP_USER, tmp_file))
            sudo('chown root:root {}'.format(tmp_file))
            sudo('chmod 440 {}'.format(tmp_file))
            sudo('mv {} {}'.format(tmp_file, sudoers_file))


@task
def provision():
    """Run puppet"""

    update_code()

    puppet_path = os.path.join(REPO_PATH, 'puppet/')
    modules_path = os.path.join(puppet_path, 'modules')
    puppet_modules = '{}:/etc/puppet/modules'.format(modules_path)

    with cd(puppet_path):
        run('sudo python bootstrap.py')

    if env.is_vagrant:
        cmd = os.path.join(puppet_path, 'manifests', 'site.pp')
    else:
        cmd = '-e "include {}"'.format(APP_NAME)

    if not exists('/usr/bin/puppet'):
        print(colors.red('Please install `puppet` before continue.'))
        return

    sudo('puppet apply --modulepath={} {}'.format(puppet_modules, cmd))


@task
def ssh_keygen():
    """Create SSH credentials"""

    if not exists('~/.ssh/id_rsa'):
        run("ssh-keygen -f ~/.ssh/id_rsa -N '' -b 1024 -q")
    key = run('cat ~/.ssh/id_rsa.pub')

    print('Public key:')
    print(colors.yellow(key))
    print('')
    print('Add the key above to your github repository deploy keys')


@task
def deploy(noprovision=False):
    """Deploy and run the new code (master branch)"""

    if noprovision is False:
        provision()
    else:
        update_code()

    mkvirtualenv()

    sudo('supervisorctl stop all')

    install_requirements()
    create_local_settings()
    collectstatic()
    syncdb()
    migrate()

    sudo('supervisorctl start all')
