import json
#import os
import logging
import traceback
import re
#import operator
#import random
#import requests

from config import TOKEN, DIR_DB, DIR_MAIN
#from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, BaseFilter, CallbackQueryHandler
#from telegram.ext import MessageFilter # for newer telegram python bot version

UPDATE_MESSAGE = 1

ADD_CHANNEL = 1

DELETE_CHANNEL = 1

class editFilter(BaseFilter): # for older telegram python bot version (right now on Linux)
#class editFilter(MessageFilter): # for newer telegram python bot version
    def filter(self, message):
        return len(re.findall(r'/edit (\d+)', str(message.text))) != 0

edit_filter = editFilter()

class deleteFilter(BaseFilter): # for older telegram python bot version (right now on Linux)
#class deleteFilter(MessageFilter): # for newer telegram python bot version
    def filter(self, message):
        return len(re.findall(r'/del (\d+)', str(message.text))) != 0

delete_filter = deleteFilter()

class pinFilter(BaseFilter):
#class pinFilter(MessageFilter):
    def filter(self, message):
        return len(re.findall(r'/pin (\d+)', str(message.text))) != 0

pin_filter = pinFilter()

class unpinFilter(BaseFilter):
#class unpinFilter(MessageFilter):
    def filter(self, message):
        return len(re.findall(r'/unpin (\d+)', str(message.text))) != 0 or len(re.findall(r'/unpin all', str(message.text))) != 0

unpin_filter = unpinFilter()

#service functions

def loadUserChannelMapping():
    with open(DIR_DB + 'DICT_USER_CHANNEL.json', 'r', encoding='utf-8') as fl:
        DICT_USER_CHANNEL = json.load(fl)
    return DICT_USER_CHANNEL

def updateUserChannelMapping(DICT_USER_CHANNEL):
    with open(DIR_DB + 'DICT_USER_CHANNEL.json', 'w', encoding='utf-8') as fl:
        json.dump(DICT_USER_CHANNEL, fl, indent=2, ensure_ascii=False)

#end service functions

#to do:
# 1. add db and sql lite for:
# 2. mapping table: user -> channel (one to many)
# 3. mapping table: user -> user info (derived automatically)
# 4. mapping table: channel -> channel info (entered by user)

dict_user_channel_run = loadUserChannelMapping()

#to do: extract user creation in Start to separate function in order to use in other functions

def createUser(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    context.bot.send_message(chat_id = chat_id, text = 'Hello. I am your helper for channel management.\nYou can <b>add</b>, <b>edit</b>, <b>delete</b>, <b>pin</b> or <b>unpin</b> messages or posts in your channel.\n\nIn order to operate, you should add me to your channel and make me admin.\n\n/addchannel - add your channel\n/delchannel - delete your channel\n/mychannels - show your channels', parse_mode = 'HTML')
    if not str(chat_id) in dict_user_channel_run.keys():
        dict_user_channel_run[str(chat_id)] = "0"
        updateUserChannelMapping(dict_user_channel_run)
        print('User ' + str(chat_id) + ' has been added to the DICT_USER_CHANNEL table.')

def addChannelStart(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id = chat_id, text = 'Enter Channel Id in the following format: <code>-123456789</code>.', parse_mode = 'HTML')
    return ADD_CHANNEL

def addChannelEnd(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    if len(re.findall(r'^-\d+$', str(msg))) == 0:
        context.bot.send_message(chat_id = chat_id, text = 'Incorrect format.\nEnter Channel Id in the following format: <code>-123456789</code>.', parse_mode = 'HTML')
        return ADD_CHANNEL
    else:
        dict_user_channel_run[str(chat_id)] = str(msg)
        updateUserChannelMapping(dict_user_channel_run)
        context.bot.send_message(chat_id = chat_id, text = 'Channel has been added.', parse_mode = 'HTML')
        print('User ' + str(chat_id) + ' has added channel ' + str(msg) + '.')
        return ConversationHandler.END

def delChannelStart(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id = chat_id, text = 'Enter Channel Id in the following format: <code>-123456789</code>.', parse_mode = 'HTML')
    return DELETE_CHANNEL

def delChannelEnd(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    if len(re.findall(r'^-\d+$', str(msg))) == 0:
        context.bot.send_message(chat_id = chat_id, text = 'Incorrect format.\nEnter Channel Id in the following format: <code>-123456789</code>.', parse_mode = 'HTML')
        return DELETE_CHANNEL
    else:
        #to be updated such as it goes through all channels and if finds one - deletes it
        if dict_user_channel_run[str(chat_id)] == str(msg):
            dict_user_channel_run[str(chat_id)] = "0"
            updateUserChannelMapping(dict_user_channel_run)
            context.bot.send_message(chat_id = chat_id, text = 'Channel has been deleted.', parse_mode = 'HTML')
            print('User ' + str(chat_id) + ' has deleted channel ' + str(msg) + '.')
            return ConversationHandler.END
        else:
            context.bot.send_message(chat_id = chat_id, text = 'You don\'t have such channel.\nEnter Channel Id in the following format: <code>-123456789</code>.', parse_mode = 'HTML')
            return DELETE_CHANNEL

def myChannels(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    context.bot.send_message(
        chat_id = chat_id, 
        text = 'Your channels are:\n<code>' + dict_user_channel_run[str(chat_id)] + '</code>', 
        parse_mode = 'HTML')

def sendToChannel(update, context):
    chat_id = update.effective_chat.id
    if update.message.reply_to_message is None:
        context.bot.send_message(chat_id, 'You have to reply to a message in order to send it to the channel.')
    else:
        replied_info = update.message.reply_to_message
        try:
            msg_id = context.bot.send_message(chat_id = dict_user_channel_run[str(chat_id)], text = replied_info.text, parse_mode = 'HTML')
            context.bot.send_message(chat_id = chat_id, text = 'Message ID is: <b>'+str(msg_id['message_id'])+'</b>.', parse_mode = 'HTML')
            #context.bot.copy_message(chat_id = CHANNEL_ID, from_chat_id = chat_id, message_id = replied_info.message_id)
        except Exception:
            logging.error(traceback.format_exc())

def editMsg_start(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    channelMessageId = re.search(r'/edit (\d+)', msg).group(1)
    context.user_data[str(chat_id) + 'channelMessageId'] = channelMessageId
    context.bot.send_message(chat_id, text = 'MessageId you want to modify: <b>'+str(channelMessageId)+'</b>. Send the updated message.', parse_mode = 'HTML')
    return UPDATE_MESSAGE

def editMsg_update(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    channelMessageId = context.user_data[str(chat_id) + 'channelMessageId']
    print('--> '+str(channelMessageId)+' is being modified.')
    try:
        context.bot.editMessageText(
            chat_id = dict_user_channel_run[str(chat_id)]
            , message_id = channelMessageId
            , text = msg
            , parse_mode = 'HTML'
        )
        context.bot.send_message(chat_id = chat_id, text = 'Message <b>'+str(channelMessageId)+'</b> has been edited.', parse_mode = 'HTML')
        return ConversationHandler.END
    except Exception:
        logging.error(traceback.format_exc())
        return ConversationHandler.END

def deleteMsg(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    try:
        channelMessageId = re.search(r'/del (\d+)', msg).group(1)
        print('--> '+str(channelMessageId)+' is being deleted.')
        context.bot.delete_message(
            chat_id = dict_user_channel_run[str(chat_id)]
            , message_id = channelMessageId
        )
        context.bot.send_message(chat_id = chat_id, text = 'Message <b>'+str(channelMessageId)+'</b> has been deleted.', parse_mode = 'HTML')
    except Exception:
        logging.error(traceback.format_exc())

def pinMsg(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    try:
        channelMessageId = re.search(r'/pin (\d+)', msg).group(1)
        print('--> '+str(channelMessageId)+' is being pinned.')
        context.bot.pin_chat_message(chat_id = dict_user_channel_run[str(chat_id)], message_id = channelMessageId)
        context.bot.send_message(chat_id = chat_id, text = 'Message <b>'+str(channelMessageId)+'</b> has been pinned.', parse_mode = 'HTML')
    except Exception:
        logging.error(traceback.format_exc())

def unpinMsg(update, context):
    chat_id = update.effective_chat.id
    msg = update.message.text
    try:
        if msg == '/unpin all':
            print('All messages are being unpinned.')
            context.bot.unpin_all_chat_messages(chat_id = dict_user_channel_run[str(chat_id)])
            context.bot.send_message(chat_id = chat_id, text = 'All messages have been unpinned.')
        else:
            channelMessageId = re.search(r'/unpin (\d+)', msg).group(1)
            print('--> '+str(channelMessageId)+' is being unpinned.')
            context.bot.unpin_chat_message(chat_id = dict_user_channel_run[str(chat_id)], message_id = channelMessageId)
            context.bot.send_message(chat_id = chat_id, text = 'Message <b>'+str(channelMessageId)+'</b> has been unpinned.', parse_mode = 'HTML')
    except Exception:
        logging.error(traceback.format_exc())

def cancel(update, context):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id, 'Operation cancelled.', parse_mode = 'HTML')
    return ConversationHandler.END

def main():

    updater = Updater(token=TOKEN, use_context = True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', createUser)
    dispatcher.add_handler(start_handler)

    my_channels_handler = CommandHandler('mychannels', myChannels)
    dispatcher.add_handler(my_channels_handler)

    add_channel_start_handler = CommandHandler('addchannel', addChannelStart)
    add_channel_end_handler = MessageHandler(Filters.regex(r'^-\d+$'), addChannelEnd)
    cancel_handler = CommandHandler('cancel', cancel)

    add_channel_conv_handler = ConversationHandler(
        entry_points=[add_channel_start_handler],
        states={
            ADD_CHANNEL: [add_channel_end_handler]
        },
        fallbacks=[cancel_handler]
    )

    dispatcher.add_handler(add_channel_conv_handler)


    del_channel_start_handler = CommandHandler('delchannel', delChannelStart)
    del_channel_end_handler = MessageHandler(Filters.regex(r'^-\d+$'), delChannelEnd)

    del_channel_conv_handler = ConversationHandler(
        entry_points=[del_channel_start_handler],
        states={
            ADD_CHANNEL: [del_channel_end_handler]
        },
        fallbacks=[cancel_handler]
    )

    dispatcher.add_handler(del_channel_conv_handler)


    edit_message_start_handler = MessageHandler(edit_filter, editMsg_start)
    edit_message_update_handler = MessageHandler(Filters.text, editMsg_update)

    edit_message_conv_handler = ConversationHandler(
        entry_points = [edit_message_start_handler],
        states={
            UPDATE_MESSAGE: [edit_message_update_handler]
        },
        fallbacks=[cancel_handler]
    )

    dispatcher.add_handler(edit_message_conv_handler)

    pin_message_handler = MessageHandler(pin_filter, pinMsg)
    dispatcher.add_handler(pin_message_handler)

    unpin_message_handler = MessageHandler(unpin_filter, unpinMsg)
    dispatcher.add_handler(unpin_message_handler)

    send_to_channel_handler = CommandHandler('send', sendToChannel)
    dispatcher.add_handler(send_to_channel_handler)

    delete_message_handler = MessageHandler(delete_filter, deleteMsg)
    dispatcher.add_handler(delete_message_handler)

    updater.start_polling()
    
    updater.idle()


if __name__ == '__main__':
    main()
