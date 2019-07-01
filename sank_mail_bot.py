import threading
from telebot import types
from mail_ru_bot import mail_bot
import telebot

bot = telebot.TeleBot('telegram bot key')
global user_mail
global user_password
global message_chat  ##Для удобства, чтобы работать с чатом.
global mail_bot_r


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):  ##Стандартное меню
    """
    Обработчик команд виртуального меню. Меню вызывается командой /menu, в чате.
    """
    if call.data == "all_unread_messages":  # call.data это callback_data, которую мы указали при объявлении кнопки
        am_un = mail_bot_r.get_mail_imap_inbox_unseen_mails()
        get_messages(message_chat, amount_of_last_emails=am_un)
    elif call.data == "last_n_messages":  ##undone ???
        bot.send_message(message_chat.from_user.id, 'Введи нужное количество последних сообщений')
        bot.register_next_step_handler(message_chat, get_n_mail)
    elif call.data == "mark_all_letters_as_see":
        mail_bot_r.seen_all_mail_imap_mails()
        bot.send_message(message_chat.from_user.id, 'Сообщения были помечены как прочитанные.')
    elif call.data == 'answer_on_all_unread_messages':
        ##Вводить свое сообщение или использовать заготовку ??
        bot.send_message(message_chat.from_user.id, 'Напишите сообщение которое будет отправлено'
                                                    ' в отчет на каждое сообщение.')
        bot.register_next_step_handler(message_chat, get_answer_mail_template)
    elif call.data == 'send_message':
        #
        # Как вводить сообщение - по какой-то форме или как ?
        # Не знаю как правильно(красиво) сделать.
        #
        bot.send_message(message_chat.from_user.id, 'Введи почту получателя.')
        bot.register_next_step_handler(message_chat, get_mail_address_for_send_mail)


@bot.message_handler(commands=['start'])  ##В /help описать вкратце ?
def start_message(message):
    """
    /start - команда для начала работы с ботом.
    """
    global message_chat
    message_chat = message
    bot.send_message(message.chat.id, 'Помните - все данные всегда можно украсть.\n'
                                      'Вводите их на свой страх и риск\n'
                                      'Введите почту : mail_ru/google/yandex')
    threading.Thread(target=bot.register_next_step_handler, args=(message, get_mail,)).start()
    # bot.register_next_step_handler(message, get_mail)


@bot.message_handler(commands=['about'])
def about_text(message):
    """
    /about - Вывод информации о боте.
    """
    bot.send_message(message.chat.id,
                     '''
                     Добрый день - это Sank_mail_helper чат-бот.
                     Пока бот больше направлен на чтение почты, но уже есть возможности удалить/написать сообщения.
                     Бот пока работает только с почтой - mail.ru + yandex.ru. Планируется добавление gmail.com
                     Автор: Купырев Александр. https://vk.com/crendelb
                     ''')


@bot.message_handler(commands=['help'])
def help_menu(message):
    """
    /help - Вывод доступных команд.
    """
    bot.send_message(message.chat.id,
                     '''Доступные команды:
                     /start - залогиниться.
                     /menu - открыть главное меню. !!! menu - Работает только при залогиненном пользователе !!!
                     /about - описание чат-бота.
                     ''')


@bot.message_handler(commands=['menu'])
def main_menu(message):
    """
    /menu - Вывод главного меню, или вывод предупреждения, если пользователь еще не залогинен в почте.
    """
    try:
        if mail_bot_r is not None: show_virtual_options(message)
    except Exception:
        bot.send_message(message.chat.id, 'Ты еще не залогинен. Напиши /start')
        # message_chat ##Тоже может быть ошибка ? Т.к. если вырубался сервер, message_chat будет пустой.


def get_mail(message):
    """ Получение почты из чата. """
    global user_mail
    user_mail = message.text
    if user_mail.count('@') != 1 and user_mail.count('.') != 1:
        bot.send_message(message.from_user.id, 'Почта указана неправильно')
        return
    bot.send_message(message.from_user.id, 'Введите пароль от почты')
    bot.register_next_step_handler(message, get_password)


def get_answer_mail_template(message):
    """ Получение шаблона ответа из чата. """
    template = message.text
    mail_bot_r.answer_on_all_inbox_unseen_mails(template)
    bot.send_message(message_chat.from_user.id, 'На все сообщения был отправлен автоответ.')


def get_n_mail(message):
    """ Получение количества выводимой почты из чата. """
    amount_of_mails = message.text
    get_messages(message, amount_of_last_emails=int(amount_of_mails))


def get_password(message):
    """ Получение пароля из чата. """
    global user_password
    user_password = message.text
    show_virtual_options(message)


def get_mail_address_for_send_mail(message):
    """ Получение почты адресата из чата. """
    mail_send_map = {}
    mail_send_map['mail_address'] = message.text
    bot.send_message(message_chat.from_user.id, 'Введи тему сообщения.')
    bot.register_next_step_handler(message, get_mail_subject_for_send_mail, mail_send_map)


def get_mail_subject_for_send_mail(message, mail_send_map):
    """ Получение темы почты из чата. """
    mail_send_map['mail_subject'] = message.text
    bot.send_message(message_chat.from_user.id, 'Введи сообщение.')
    bot.register_next_step_handler(message, get_mail_message_for_send_mail, mail_send_map)


def get_mail_message_for_send_mail(message, mail_send_map):
    """ Получение сообщения почты из чата. """
    mail_message = message.text
    mail_bot_r.send_mail(mail_send_map['mail_address'], mail_message)


def show_virtual_options(message):  ##message не используется???
    """ Вывод виртуальной клавиатуры.
    Вывод главного меню пользователя. Меню представлено в виде визуальных кнопок.
    Вывод производится при написании команды /menu
    """
    keyboard = types.InlineKeyboardMarkup()  # наша клавиатура ++ есть еще ReplyKeyboard
    global mail_bot_r
    mail_bot_r = mail_bot(user_mail, user_password)
    unseen_messages = mail_bot_r.get_mail_imap_inbox_unseen_mails()

    bot.send_message(message_chat.from_user.id, 'Кол-во непрочитанной почты:  ' + str(len(unseen_messages)))

    if len(unseen_messages) > 0:  # Не показывать кнопку, если нет новых сообщений в INBOX
        key_get_all_unread_messages = types.InlineKeyboardButton(
            text='Все непрочитанные сообщений', callback_data='all_unread_messages')  # кнопка ----
        key_answer_all_unread_messages = types.InlineKeyboardButton(
            text='Ответить шаблоном на все непрочитанные сообщения',
            callback_data='answer_on_all_unread_messages')  # кнопка ----
        key_mark_down_all_letters = types.InlineKeyboardButton(
            text='Пометить все письма как прочитанные', callback_data='mark_all_letters_as_see')  # кнопка ----

    key_get_last_n_messages = types.InlineKeyboardButton(
        text='N последних сообщений', callback_data='last_n_messages')  # кнопка ----
    key_send_message = types.InlineKeyboardButton(
        text='Отправить сообщение', callback_data='send_message')  # кнопка ----

    current_vars = vars()
    for xx in current_vars:
        if xx.count('key_'):
            if xx == 'key_get_all_unread_messages' and len(unseen_messages) < 1:
                continue
            else:
                keyboard.add(current_vars[xx])
    question = 'Выбери пункт меню:\n Для повторного вызова меню пиши\n /menu'
    bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)


def get_messages(message, amount_of_last_emails=None):
    """ Получение почты пользователя и вывод в чат. """
    bot.send_message(message.from_user.id, 'Вывод почты')
    try:  ## Могут быть проблемы с получением почты.
        data = mail_bot_r.get_mail_imap_inbox_all_mails(amount_of_last_emails)
    except Exception as eexx:
        # raise eexx
        print(eexx)
        bot.send_message(message.chat.id, 'Ошибка получения почты.'
                                          ' Скорее всего неправильно указаны настройки почты.'
                                          ' Или серверы почты не отвечают.')
        return
    count = 0
    while True:
        try:
            print(data[1024 * count: 1024 * (count + 1)])
            bot.send_message(message.from_user.id, data[1024 * count: 1024 * (count + 1)])
            count += 1
        except:
            print('end')
            break


@bot.message_handler(content_types=['text'])
def send_text(message):
    """ Обработка любого текста.  Если текст не попадает под условия вышеописанных обработчиков, данный обработчик
     перехватает весь текст и выводит сообщение с подсказкой. """
    bot.send_message(message.chat.id, 'Привет, для начала работы напиши /start')


if __name__ == '__main__':
    bot.polling()