import re

import email
import smtplib
import mail_settings
import imaplib  ##вроде лучше чем pop3
import poplib
import base64
import quopri


class mail_bot:

    ##логиниться в __Init__ и использовать везде один объект?

    def __init__(self, email, password):
        self.email = email
        self.password = password

    def _get_mail_settings(self, server_name):
        """ Получить настройки почты. """
        mail_host = self.email.split('@')[1].strip()
        if mail_host in ['inbox.ru', 'list.ru', 'bk.ru', 'mail.ru']:
            return mail_settings.settings['mail.ru'][server_name]
        return mail_settings.settings[mail_host][server_name]

    def send_mail(self, to_addrs, subject, message):
        """ Отправить письмо. """
        smtp = smtplib.SMTP_SSL(self._get_mail_settings('smtp'))
        smtp.login(self.email, self.password)
        ## MIMEtype
        msg = email.message.EmailMessage()  ## Для работы с темой письма + русским языком
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = to_addrs
        msg.set_content(message.decode('utf-8'))  ##Декодим в байты с utf-8
        smtp.send_message(msg)
        smtp.close()

    def work_with_mail(self, impb, mails_numbers, amount_of_last_emails=5):
        """Парсер письма. Превращаем письмо в удобочитаемый вид, и возвращаем получивщийся результат.
        На данный момент возвращается в виде:
            -Отправитель письма
            -Дата письма
            -Тема письма
            -Тело письма
        """
        result_answer = ''
        if type(amount_of_last_emails) is list:  ## костыль - всегда передавать только int???
            from_number = len(amount_of_last_emails) * (-1)
        else:
            from_number = amount_of_last_emails * (-1)

        # from_number = int(len(amount_of_last_emails)) * (-1) ## amount_of_last_emails возвращает номера писем, поэтому кастим в len

        for _ in mails_numbers[from_number:][::-1]:
            ##Выдергиваем последние 5 значений, и сразу их переворачиваем, чтобы они отображались по дате писен сверху вниз(сверху новые, снизу старые).
            status, data = impb.fetch(_, '(RFC822)')
            email_message = email.message_from_bytes(data[0][1])
            result_answer += '\n'
            result_answer += ' '.join(
                ['To : ',
                 self.email if email_message['Delivered-To'] is None else str(email_message['Delivered-To']),
                 '\n'])
            from_mes = email_message['From']
            if from_mes.count('<') > 0 and from_mes.count('>') > 0:
                from_mes = from_mes.split('<')[1].split('>')[0]
            result_answer += ' '.join(['From : ', from_mes, '\n'])
            result_answer += ' '.join(['Date : ', email_message['Date'], '\n'])
            result_answer += ' '.join(['Subject : ', self.decode_mail_subject(email_message['Subject']), '\n'])
            result_answer += 'Message : '
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(
                            decode=True)  # to control automatic email-style MIME decoding (e.g., Base64, uuencode, quoted-printable)
                        body = body.decode()
                        result_answer += body[0:100] + '...(Остальной текст скрыт)\n'
                    elif part.get_content_type() == "text/html":
                        continue
            else:
                mail_content_type = email_message.get_content_type()
                if mail_content_type == "text/html":
                    result_answer += 'Это html сообщение.'
                elif mail_content_type == "text/plain":
                    result_answer += email_message.get_payload()[0:100] + '...(Остальной текст скрыт)\n'
                else:
                    result_answer += 'Не могу прочитать сообщение.'
        return result_answer

    def _reg_exp_ignorecase(self, pattern, text):
        """Возвращает список найденных соответствий без учета регистра."""
        return re.findall(pattern, text, re.IGNORECASE)

    def _decode_mail_subject_helper(self, mail_subject, base=False):
        """
        Декодим тему письма и приводим ее в обычный текст, т.к. тема письма приходит в нечитаемом виде.
        Если base=True, декодим с помощью base64.b64decode(_).decode(), иначе с помощью quopri.decodestring()
        """
        result = ''
        for _ in mail_subject.split(
                self._reg_exp_ignorecase('=\?UTF-8\?B\?', mail_subject)[0]
                if base
                else self._reg_exp_ignorecase('=\?UTF-8\?Q\?', mail_subject)[0]):

            if len(_) < 1: continue
            _ = _[:-2]  # Удаляем последние два символа - ?=
            result += base64.b64decode(_).decode('utf-8') if base else quopri.decodestring(_.encode('utf-8')).decode(
                'utf-8')
        return result

    def decode_mail_subject(self, mail_subject):
        """
        С помощью _decode_mail_subject_helper() приводим тему письма в читаемый вид.
        """
        if mail_subject.upper().count('=?UTF-8?B?') > 0:
            return self._decode_mail_subject_helper(mail_subject, base=True)
        elif mail_subject.upper().count('=?UTF-8?Q?') > 0:
            return self._decode_mail_subject_helper(mail_subject)
        else:
            return mail_subject

    def _login_in_imap(self):
        """
        Залогиниваемся в почтовике.
        """
        impb_mail_settings = self._get_mail_settings('imap').split(':')
        impb = imaplib.IMAP4_SSL(impb_mail_settings[0], int(impb_mail_settings[1]))
        impb.login(self.email, self.password)
        return impb

    # read docs
    def _get_mail_imap(self, mail_container, mail_container_filter, amount_of_last_emails=5,
                       read_mails=True, return_answer=True):
        """
        Получение писем и если read_mails=True и return_answer=True возвращаем текст писем, обработанный с помощью функции
        work_with_mail(). Если read_mails=False, просто возвращаем номера писем. !! Не читаем их. !!
        """
        impb = self._login_in_imap()
        impb.select(mail_container)
        status, data = impb.search(None, mail_container_filter)
        mails_numbers = data[0].split()
        if read_mails:
            if mail_container_filter == '(UNSEEN)':
                amount_of_last_emails = len(
                    self.get_mail_imap_inbox_unseen_mails())  ## Считываем кол-во непрочитанных сообщений прям тут из метода
            result_answer = self.work_with_mail(impb, mails_numbers, amount_of_last_emails)
        impb.close()
        impb.logout()
        if read_mails:
            if return_answer:
                return result_answer  ## Возвращает распарсенные сообщения
        else:
            return mails_numbers  ## Возвращает номера(id) сообщений

    def get_mails_number(self, mail_container, mail_container_filter):
        """
        Получить номера писем.
        """
        impb = self._login_in_imap()
        impb.select(mail_container)  ##INBOX ?
        status, data = impb.search(None, mail_container_filter)
        mails_numbers = data[0].split()
        return mails_numbers

    def work_with_mails_flags(self, mail_container, mail_container_filter, flags, cur_flag, expunge=False):
        """
        Работа с флагами писем.
        :mail_container: Папка писем -- Входящие , Удаленные письма и т.д.
        :mail_container_filter: Фильтр выбранной папки писем -- ALL, (UNSEEN) и т.д.
        :flags: Флаги писем --Если поставить +FLAGS, тогда указанное свойство в cur_flag добавится к каждому письму.
                                  Соответственно -FLAGS уберет свойство cur_flag у каждого письма.
        :cur_flag: Флаг(свойство) которое добавится/уберется у каждого письма.
        """
        impb = self._login_in_imap()
        mails_numbers = self.get_mails_number(mail_container, mail_container_filter)
        impb.select(mail_container)
        for _ in mails_numbers:
            impb.store(_, flags, cur_flag)
        if expunge: impb.expunge()  ## Только для удаленных сообщений (Очистка удаленных писем из ящика(mail_container))
        impb.close()
        impb.logout()

    def delete_mail_from_inbox(self):
        """
        Удалить почту из папки Входящие. !! Почта удаляется без попадания в папку Корзина !!.
        """
        self.work_with_mails_flags('INBOX', 'ALL', '+FLAGS', r'(\Deleted)', True)

    def seen_all_mail_imap_mails(self):
        """
        Ответить на всю непрочитанную почту сообщением от пользователя.
        """
        self.work_with_mails_flags('INBOX', '(UNSEEN)', '+FLAGS', r'(\Seen)')

    def get_mail_imap_inbox_all_mails(self, amount_of_last_emails=5):
        """
        Получить всю почту пользователя из папки "Входящие".
        Поставлено дефолтный вывод -- 5 писем.
        """
        return self._get_mail_imap('INBOX', 'ALL', amount_of_last_emails)

    def get_mail_imap_inbox_unseen_mails(self):
        """
        Получить всю непрочитанную почту пользователя из папки "Входящие".
        """
        return self._get_mail_imap('INBOX', '(UNSEEN)',
                                   read_mails=False)  # нужен флаг read_mails=False, иначе входит в цикл в _get_mail_imap()

    def answer_on_all_inbox_unseen_mails(self, message_template):  ##Сделать красиво
        """
        Ответить на всю непрочитанную почту сообщением от пользователя.
        """
        impb = self._login_in_imap()
        mails_numbers = self.get_mails_number('INBOX', '(UNSEEN)')
        impb.select()  ##Select INBOX
        for mail in mails_numbers:
            status, data = impb.fetch(mail, '(RFC822)')
            email_message = email.message_from_bytes(data[0][1])
            self.send_mail(email_message['Return-path'][1:-1], 'Автоматическое сообщение',
                           message_template.encode('utf-8'))
            # 'Добрый день, я получил Ваше сообщение. Отвечу Вам в ближайшее время.'.encode('utf-8'))

    def _get_mail_pop3(self):  ## нужно?
        """
        Не реализованный код - т.к. неизвестно нужен ли и pop3 и imap одновременно.
        Получение почты через POP3.
        """
        # print(self._get_mail_settings('imap'))
        pop = poplib.POP3_SSL('pop.mail.ru', 995)
        pop.user(self.email)
        pop.pass_(self.password)
        numMessages = len(pop.list()[1])
        for i in range(numMessages):
            for msg in pop.retr(i + 1)[1]:
                print(msg)
        pop.quit()
