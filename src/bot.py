#!/usr/bin/env python

import data.config
import src.utils

import telegram
from telegram.ext import Updater, Dispatcher, JobQueue, CommandHandler


class TelechanBot:
    def __init__(self):
        self.token = data.config.telegram.setdefault("token", None)
        if not self.token:
            raise Exception("Token not found. Check config.py file in data folder.")
        self.test_mode = data.config.other.setdefault("test_mode", False)

        self.channels: list = src.utils.read_channels()

        self.updater: Updater = Updater(token=self.token, use_context=True)
        self.dispatcher: Dispatcher = self.updater.dispatcher
        self.job_queue: JobQueue = self.updater.job_queue

        self.setup_updater()

        self.updater.start_polling()
        pass

    def setup_updater(self):

        def start_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
            user_says = " ".join(context.args)
            update.message.reply_text("You said: " + user_says)
            pass

        def join_channel_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
            """This is callback function to join channels via bot

            To join channel, you should know two things: id and password (if given).
            If the given channel is not found in self.channels, then it will raise an error.

            Example call in Telegram:
            /join_channel @anontelechan
            /join_channel @testanontelechan z1on0101
            """

            raise NotImplementedError
            pass

        def leave_channel_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
            """This is callback function to leave joined channels via bot

            When you leave channel, you return to the default channel (@anontelechan).
            When in default channel, you can't leave it and thus an error will be raised.

            Example call in Telegram:
            ---Currently in @testanontelechan---
            /leave_channel # Works fine
            ---Currently in @anontelechan---
            /leave_channel # Won't work, as you can't leave default channel
            """

            raise NotImplementedError
            pass

        def add_channel_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
            """This is callback function to add channels to bot's list

            In order to add channel, you need to have this bot as administrator
            in channel (to be able to post messages is enough).
            As arguments you should add: id of channel, brief description (optional) and password (optional).

            Example call in Telegram:
            /add_channel @anontelechan "Main board of Telechan" "password"
            """

            bot: telegram.Bot = context.bot
            try:
                new_channel_id = context.args[0]
                new_channel_description = context.args[1]
                new_channel_password = context.args[2]
            except Exception as e:
                raise Exception("Something went wrong with arguments:", e)

            try:
                new_channel = bot.get_chat(new_channel_id)
            except Exception as e:
                raise Exception("There was an error trying to get chat by the given id:", e)

            new_channel_id = new_channel.id
            if new_channel_id in [current_channel["id"] for current_channel in self.channels]:
                raise Exception("This channel is already in the list.")

            try:
                is_channel_eligible = bot.get_chat_member(new_channel_id, bot.id).can_post_messages
            except Exception as e:
                raise Exception("There was an error reading bot information in channel:", e)
            if is_channel_eligible:
                self.channels.append(
                    {"id": new_channel_id, "description": new_channel_description, "password": new_channel_password}
                )
                src.utils.save_channels(self.channels)
                update.message.reply_text("Your channel was added in the list!")
            else:
                update.message.reply_text("It appears our bot is not able to post in your channel. "
                                          "Please, check bot's permissions.")

        self.dispatcher.add_handler(CommandHandler("start", start_callback))
        self.dispatcher.add_handler(CommandHandler("add_channel", add_channel_callback))
        self.dispatcher.add_handler(CommandHandler("join_channel", join_channel_callback))
        self.dispatcher.add_handler(CommandHandler("leave_channel", leave_channel_callback))

        pass

    def send_message(self, msg: telegram.Message):
        pass

    def receive_message(self, msg: telegram.Message):
        pass

    def process_message(self, msg: telegram.Message):
        pass
