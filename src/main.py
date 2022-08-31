import enum
import sys
import requests
import logging
import os
import io
from urllib import request
from bs4 import BeautifulSoup
import telebot
from time import sleep
from loguru import logger
import json
from utils import (
    is_admin,
    get_id,
    get_hosts,
    get_templates,
    run_template_for_host,
    callback_data_dumps,
    confirm_action,
    get_stdout,
)
from telebot import types


class Commands(enum.Enum):
    UNSEE = 1
    NEXT = 2
    PREVIOUS = 3
    HOSTTEMPLATE = 4
    BACHTOSERVERLIST = 5
    RUNTEMPLATEFORHOST = 6
    GETSTDOUT = 7
    SELECTPLAYBOOKFORHOST = 8


class Main:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    awxReadToken = os.getenv("AWX_READ_TOKEN")
    awxWriteToken = os.getenv("AWX_WRITE_TOKEN", default="")
    awxUrl = os.getenv("AWX_URL")
    headers = {
        "Authorization": "Bearer " + awxWriteToken,
        "content-type": "application/json",
    }
    users = os.getenv("USERS").split(";")
    templates = os.getenv("TEMPLATES").split(";")

    page = 1

    def __init__(self):

        self.bot = telebot.TeleBot(self.token)

        logger.debug("Init")
        

    def startBot(self):

        logger.debug("__main__")

        @self.bot.message_handler(commands=["start"])
        def _proccess_command_start(msg):

            self.start(msg)

        @self.bot.message_handler(commands=["menu"])
        def _proccess_command_menu(msg):
            self.menu(msg)

        @self.bot.message_handler(commands=["getID"])
        def _proccess_command_printid(msg):
            self.print_id(msg)

        @self.bot.callback_query_handler(func=lambda call: True)
        def _proccess_callback_query(call):
            data = json.loads(call.data)
            queryHeader = data[0]
            

            match Commands(int(queryHeader)):
                case Commands.UNSEE:
                    logger.debug("unsee")
                    self.bot.delete_message(
                        call.message.chat.id, call.message.message_id
                    )
                case Commands.NEXT:
                    try:
                        self.page += 1
                        list_hosts = self.list_hosts(call, self.page)
                        self.bot.edit_message_text(
                            text=list_hosts.get("text"),
                            reply_markup=list_hosts.get("markup"),
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                        )
                    except Exception as e:
                        logger.error(e)
                        self.bot.send_message(
                            call.message.chat.id, "Не удаётся получить список хостов"
                        )
                        return
                case Commands.PREVIOUS:
                    try:
                        self.page -= 1
                        list_hosts = self.list_hosts(call, self.page)
                        self.bot.edit_message_text(
                            text=list_hosts.get("text"),
                            reply_markup=list_hosts.get("markup"),
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                        )
                    except Exception as e:
                        logger.error(e)
                        self.bot.send_message(
                            call.message.chat.id, "Не удаётся получить список хостов"
                        )
                        return
                case Commands.HOSTTEMPLATE:
                    try:

                        templates = self.select_template(call)

                        self.bot.edit_message_text(
                            text=templates.get("text"),
                            reply_markup=templates.get("markup"),
                            parse_mode="html",
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                        )
                    except Exception as e:
                        logger.error(e)
                        logger.trace(e)
                        self.bot.send_message(
                            call.message.chat.id, "Не удаётся получить список хостов"
                        )
                        return

                case Commands.BACHTOSERVERLIST:
                    try:
                        list_hosts = self.list_hosts(call, self.page)
                        self.bot.edit_message_text(
                            text=list_hosts.get("text"),
                            reply_markup=list_hosts.get("markup"),
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                        )
                    except Exception as e:
                        logger.error(e)
                        self.bot.send_message(
                            call.message.chat.id, "Не удаётся получить список хостов"
                        )
                        return
                case Commands.RUNTEMPLATEFORHOST:
                    self.run_template_for_host(call)
                case Commands.SELECTPLAYBOOKFORHOST:
                    self.hosts(call.message)
                case Commands.GETSTDOUT:
                    
                    
                    data = data[1]
                    html = get_stdout(
                        self.awxUrl,
                        headers=self.headers,
                        page_id=data.get("page_id")
                    )
                    soup = BeautifulSoup(html, "html.parser")

                    stdout = soup.findAll("div", {"class": "response-info"})

                    file_obj = io.BytesIO(stdout[0].encode())

                    file_obj.name = "stdout.html"
                    self.bot.send_document(data.get("chat_id"), file_obj)

        self.bot.polling(none_stop=True)

    def start(self, msg):
        if is_admin(msg.from_user.id, self.users):
            self.bot.send_message(msg.chat.id, "Вы <b>АДМИНИСТРАТОР</b>", "html")
            self.menu(msg)

        else:
            self.bot.send_message(msg.chat.id, "Вы не <b>АДМИНИСТРАТОР</b>", "html")
            self.bot.send_message(msg.chat.id, "/getID -  Получить ID")

    def menu(self, msg):
        if is_admin(not msg.from_user.id, self.users):
            self.bot.send_message(msg.chat.id, "Вы не администратор")
            self.print_id(msg)
            return
        menu_text = "Выберите действие"
        host_button = types.InlineKeyboardButton(
            text="Запустить Playbook для конкретного Хоста",
            callback_data=callback_data_dumps([Commands.SELECTPLAYBOOKFORHOST.value]),
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(host_button)
        self.bot.send_message(
            msg.chat.id, menu_text, reply_markup=markup, parse_mode="html"
        )

    def hosts(self, msg):
        if is_admin(not msg.from_user.id, self.users):
            return

        try:
            list_hosts = self.list_hosts(msg, self.page)
            self.bot.send_message(
                msg.chat.id,
                list_hosts.get("text"),
                reply_markup=list_hosts.get("markup"),
                parse_mode="html",
            )
        except Exception as e:
            logger.error(e)
            self.bot.send_message(msg.chat.id, "Не удаётся получить список хостов")
            return

    def list_hosts(self, msg, pg):
        buttons = []
        navButtons = []

        navButtons.append(
            types.InlineKeyboardButton(
                text="Закрыть",
                row_width=3,
                callback_data=callback_data_dumps([Commands.UNSEE.value]),
            )
        )

        markup = types.InlineKeyboardMarkup()
        try:
            results = get_hosts("GET", self.awxUrl, self.headers, page_id=pg)
        except Exception as e:
            logger.error(e)
            self.bot.send_message(msg.chat.id, "Не удаётся получить список хостов")
            return

        if results["next"] is not None:
            navButtons.append(
                types.InlineKeyboardButton(
                    text="Вперёд",
                    callback_data=callback_data_dumps([Commands.NEXT.value]),
                )
            )
        if results["previous"] is not None:
            navButtons.append(
                types.InlineKeyboardButton(
                    text="Назад",
                    callback_data=callback_data_dumps([Commands.PREVIOUS.value]),
                )
            )

        text = f"Всего хостов: <b>{results['count']}</b>\nСписок хостов:\n"
        for host in results["results"]:

            text += f'{host["id"]}. {host["name"]}\n'
            callback_dict = [
                Commands.HOSTTEMPLATE.value,
                {"h_i": host["id"], "h_n": host["name"]},
            ]
            buttons.append(
                types.InlineKeyboardButton(
                    text=f'{host["name"]}', callback_data=str(json.dumps(callback_dict))
                )
            )

        markup.add(*navButtons, *buttons)
        return {"text": text, "markup": markup}

    def select_template(self, call):
        if is_admin(not call.from_user.id, self.users):
            self.bot.send_message(call.chat.id, "Вы не администратор")
            return

        data = json.loads(call.data)
        host = data[1]
        text = f"""Вы выбрали Хост: <b>{host['h_n']}</b>\nСписок шаблонов
ID  NAME\n"""
        callback_dict = []

        buttons = []
        templates = self.templates
        try:
            markup = types.InlineKeyboardMarkup()
            back_button = types.InlineKeyboardButton(
                text="Вернуться",
                callback_data=str(json.dumps([Commands.BACHTOSERVERLIST.value])),
            )

            for template in get_templates("GET", self.awxUrl, headers=self.headers)[
                "results"
            ]:

                if str(template["id"]) in templates:

                    text += f"{str(template['id'])} {template['name']}\n"
                    callback_dict = [
                        Commands.RUNTEMPLATEFORHOST.value,
                        {"h_n": host["h_n"], "t_i": template["id"]},
                    ]

                    buttons.append(
                        types.InlineKeyboardButton(
                            text=f'{template["id"]}',
                            callback_data=str(json.dumps(callback_dict)),
                        )
                    )

            markup.add(*buttons, back_button)

            return {"text": text, "markup": markup}
        except Exception as e:
            logger.error(e)
            self.bot.send_message(call.message.chat.id, "Не удаётся выбрать шаблон")
            return

    def run_template_for_host(self, data):

        if is_admin(not data.from_user.id, self.users):
            self.bot.send_message(data.message.chat.id, "Вы не администратор")
            return

        template_data = json.loads(data.data)
        chat_id = data.message.chat.id
        try:
            requests.request("GET", self.awxUrl, headers=self.headers)
        except Exception as e:
            logging.error(e)
            self.bot.send_message(chat_id, "Не удаётся подключиться к серверу")
            return

        obj = confirm_action()

        img = self.bot.send_photo(chat_id, obj.get("capcha_img"))

        self.bot.register_next_step_handler(
            img, lambda m: self.run(m, data, template_data, obj)
        )

    def run(self, m, data, template_data, obj):

        chat_id = data.message.chat.id
        template_id = template_data[1].get("t_i")
        host_name = template_data[1].get("h_n")
        host = {"limit": host_name}

        try:
            if obj.get("capcha_num") == str(m.text):
                res = run_template_for_host(
                    "POST",
                    template_id,
                    self.awxUrl,
                    headers=self.headers,
                    data=host,
                ).text
                page_id = json.loads(res).get("id")
                markup = types.InlineKeyboardMarkup()
                stdout = types.InlineKeyboardButton(
                    text="Получить Лог",
                    callback_data=str(json.dumps([Commands.GETSTDOUT.value, {"page_id": page_id, "chat_id": chat_id}])),
                )
                markup.add(stdout)
                
                self.bot.send_message(
                    chat_id, "Шаблон Выполнился Успешно\n", reply_markup=markup
                )

                logger.debug(
                    f"Пользователь {data.from_user.username} запустил шаблон {template_id} на хосте {host_name}"
                )

            else:

                self.bot.send_message(
                    chat_id, "Капча введена не верно\nШаблон Не выполнился\n"
                )
        except Exception as e:
            print(e)
            self.bot.send_message(chat_id, "Произошла ошибка")

    def print_id(self, msg):
        self.bot.send_message(msg.chat.id, "ID Пользователя - " + str(msg.from_user.id))


Main().startBot()
