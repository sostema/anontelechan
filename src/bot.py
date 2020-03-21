#!/usr/bin/env python

import telegram
from telegram.ext import Updater, Dispatcher, JobQueue, CommandHandler, PicklePersistence, MessageHandler, Filters

import data.config
import src.utils


class TelechanBot:
    def __init__(self):
        self.token = data.config.telegram.setdefault("token", None)
        if not self.token:
            raise Exception("Token not found. Check config.py file in data folder.")
        self.test_mode = data.config.other.setdefault("test_mode", False)

        self.channels: list = src.utils.read_channels()
        self.default_channel = int(self.channels[0]["id"])

        self.persistence = PicklePersistence(filename='../data/persistence.data')

        self.updater: Updater = Updater(token=self.token, persistence=self.persistence, use_context=True)
        self.dispatcher: Dispatcher = self.updater.dispatcher
        self.job_queue: JobQueue = self.updater.job_queue

        self.setup_updater()

        self.updater.start_polling()
        pass

    def setup_updater(self):

        class Commands:
            @staticmethod
            def start_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
                context.user_data["current_channel"] = self.default_channel
                update.message.reply_text("Hello! This is bot for anonymous communication via channels!\n"
                                          "You're currently in a default channel {0}, but you can feel free to join "
                                          "any other channel (as long as they are added to this bot)."
                                          .format(self.default_channel))
                pass

            @staticmethod
            def join_channel_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
                """This is callback function to join channels via bot

                To join channel, you should know two things: id and password (if given).
                If the given channel is not found in self.channels, then it will raise an error.

                Example call in Telegram:
                /join_channel @anontelechan
                /join_channel @testanontelechan z1on0101
                """

                try:
                    new_channel_id = context.bot.get_chat(context.args[0]).id
                    new_channel_password = None
                    if len(context.args) > 1:
                        new_channel_password = context.args[1]

                    try:
                        new_channel = context.bot.get_chat(new_channel_id)
                    except Exception as e:
                        update.message.reply_text("It appears that this id is non-existent.")
                        raise Exception("There was an error trying to get chat by the given id:", e)

                    channel_obj = None
                    new_channel_id = new_channel.id
                    for current_channel in self.channels:
                        if current_channel["id"] == new_channel_id:
                            channel_obj = current_channel

                    if not channel_obj:
                        update.message.reply_text("No such channel exists in our list.")
                        raise Exception("No such channel {0} exists in the list.".format(new_channel_id))
                    else:
                        if not channel_obj["password"] or channel_obj["password"] == new_channel_password:
                            context.user_data["current_channel"] = channel_obj["id"]
                            update.message.reply_text("You've joined new channel!")
                        elif channel_obj["password"] != new_channel_password:
                            update.message.reply_text("Wrong password.")

                except Exception as e:
                    update.message.reply_text("Something went wrong :(")
                    raise Exception(e)

                pass

            @staticmethod
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

                if context.user_data["current_channel"] != self.default_channel:
                    context.user_data["current_channel"] = self.default_channel
                    reply_text = "You've left channel. Now you're in default channel {0}.".format(self.default_channel)
                else:
                    reply_text = "You're in default channel {0}, you can't leave it!".format(self.default_channel)
                update.message.reply_text(reply_text)
                pass

            @staticmethod
            def add_channel_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
                """This is callback function to add channels to bot's list

                In order to add channel, you need to have this bot as administrator
                in channel (to be able to post messages is enough).
                As arguments you should add: id of channel and password (optional).

                Example call in Telegram:
                /add_channel @anontelechan password
                """

                bot: telegram.Bot = context.bot
                new_channel_id, new_channel_password = None, None
                try:
                    new_channel_id = context.args[0]
                    if len(context.args) >= 2:
                        new_channel_password = context.args[1]
                except Exception as e:
                    update.message.reply_text("You didn't specify channel id as argument.")
                    raise Exception("Something went wrong with arguments:", e)

                try:
                    new_channel = bot.get_chat(new_channel_id)
                except Exception as e:
                    update.message.reply_text("It appears that this id is non-existent.")
                    raise Exception("There was an error trying to get chat by the given id:", e)

                new_channel_id = new_channel.id
                if new_channel_id in [current_channel["id"] for current_channel in self.channels]:
                    update.message.reply_text("This channel is already in the list.")
                    raise Exception("{0} is already in the list.".format(new_channel_id))

                try:
                    is_channel_eligible = bot.get_chat_member(new_channel_id, bot.id).can_post_messages and \
                                          bot.get_chat_member(new_channel_id, bot.id).can_delete_messages
                except Exception as e:
                    update.message.reply_text("Bot wasn't able to read information about channel.")
                    raise Exception("There was an error reading bot information in channel:", e)
                if is_channel_eligible:
                    self.channels.append(
                        {"id": new_channel_id,
                         "author": update.message.from_user.id,
                         "password": new_channel_password if new_channel_password else ""}
                    )
                    src.utils.save_channels(self.channels)
                    update.message.reply_text("Your channel was added in the list! "
                                              "We've automatically added you in this channel.")
                    Commands.join_channel_callback(update, context)
                else:
                    update.message.reply_text("It appears our bot is not able to post and delete in your channel. "
                                              "Please, check bot's permissions.")

                pass

            @staticmethod
            def delete_channel_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
                """This is callback function to delete channels from bot's list

                In order to delete channel, you should be the one, who added it to the list (smart, right?).

                Example call in Telegram:
                /delete_channel @anontelechan
                """

                bot: telegram.Bot = context.bot

                try:
                    channel_id = context.args[0]
                except Exception as e:
                    update.message.reply_text("You haven't specified channel id in arguments.")
                    raise Exception(e)

                try:
                    channel_id = bot.get_chat(channel_id).id
                except Exception as e:
                    update.message.reply_text("No such channel was found in Telegram.")
                    raise Exception(e)

                channel_obj = None
                for current_channel in self.channels:
                    if current_channel["id"] == channel_id:
                        channel_obj = current_channel

                if not channel_obj:
                    update.message.reply_text("This channel is not in the list!")
                else:
                    if channel_obj["author"] == update.message.from_user.id:
                        self.channels.remove(channel_obj)
                        src.utils.save_channels(self.channels)
                        update.message.reply_text("Channel was successfully removed from our list.")
                    else:
                        update.message.reply_text(
                            "You're not an author of this channel, and as such you can't delete it.")

                pass

        class Messages:
            @staticmethod
            def text_callback(update: telegram.Update, context: telegram.ext.CallbackContext):
                user_channel = context.user_data['current_channel']
                user_channel_str = str(user_channel)[4::] \
                    if not context.bot.get_chat(user_channel).username else context.bot.get_chat(user_channel).username

                current_message_id = context.chat_data.setdefault('last_id', -1) + 1
                if current_message_id == 0:
                    message_id = context.bot.send_message(user_channel, "foobar")
                    current_message_id = message_id.message_id + 1
                    context.bot.delete_message(user_channel, message_id.message_id)

                message: telegram.Message = update.message

                message_text = f'<a href="https://t.me/{user_channel_str}/{current_message_id}">' \
                               f'{current_message_id}</a>' + "\n---\n" + message.text_html

                message_id = context.bot.send_message(user_channel, message_text,
                                                      parse_mode=telegram.ParseMode.HTML, disable_web_page_preview=True)
                context.chat_data['last_id'] = message_id.message_id

                user_message = f'<a href="https://t.me/{user_channel_str}/{current_message_id}">' \
                               f"Link to your message.</a>"
                context.bot.send_message(update.message.from_user.id, user_message, parse_mode=telegram.ParseMode.HTML)
                pass

        self.dispatcher.add_handler(CommandHandler("start", Commands.start_callback))
        self.dispatcher.add_handler(CommandHandler("add_channel", Commands.add_channel_callback))
        self.dispatcher.add_handler(CommandHandler("join_channel", Commands.join_channel_callback))
        self.dispatcher.add_handler(CommandHandler("leave_channel", Commands.leave_channel_callback))
        self.dispatcher.add_handler(CommandHandler("delete_channel", Commands.delete_channel_callback))

        self.dispatcher.add_handler(MessageHandler(Filters.text & Filters.update.message, Messages.text_callback))

        pass
