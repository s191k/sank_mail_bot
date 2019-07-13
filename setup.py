#https://klen.github.io/create-python-packages.html
from setuptools import setup, find_packages

# Загружаем зависимости из файла
with open('requirements.txt') as f:
    required = f.read().splitlines()

# readme = open('README.md').read()
# with open('README.md') as r:
#     readme_file = r.read()

setup(
    name='sank_mail_bot',
    version=0.1,
    author='Sank(s191k) -- Kupyrev Alexander',
    author_email='solnushkoon@mail.ru',
    url='https://github.com/s191k/sank_mail_bot',
    description='Simple bot for work with emails in telegram chat', ## Summary
    # long_description=readme_file, ## Ругается на русский
    install_requires=required,
    packages=find_packages()
)