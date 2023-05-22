from setuptools import setup, find_packages

required = [
    'pyTelegramBotAPI == 3.6.6',
    'requests == 2.31.0'
]

setup(
    name='sank_mail_bot_p',
    version=0.1,
    author='Sank(s191k) -- Kupyrev Alexander',
    author_email='solnushkoon@mail.ru',
    url='https://github.com/s191k/sank_mail_bot',
    description='Simple bot for work with emails in telegram chat',
    # long_description=readme_file, ## Ругается на русский
    install_requires=required,
    packages=find_packages()
)