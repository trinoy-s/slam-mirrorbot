from telegram.ext import CommandHandler, run_async
from bot.helper import download_tools, gdriveTools, listeners
from bot import LOGGER, dispatcher
from bot.helper import fs_utils
from bot import download_dict, status_reply_dict, DOWNLOAD_STATUS_UPDATE_INTERVAL
from bot.helper.message_utils import *
from time import sleep
from bot.helper.bot_utils import get_readable_message, KillThreadException
LOGGER.info('mirror.py')


class MirrorListener(listeners.MirrorListeners):
    def __init__(self, context, update, reply_message):
        super().__init__(context, update, reply_message)

    def onDownloadStarted(self, link):
        LOGGER.info("Adding link: " + link)

    def onDownloadProgress(self, progress_status_list: list, index: int):
        msg = get_readable_message(progress_status_list)
        LOGGER.info("Editing message")
        try:
            editMessage(msg, self.context, self.reply_message)
        except BadRequest:
            raise KillThreadException('Message deleted. Terminate thread')

    def onDownloadComplete(self, progress_status_list, index: int):
        LOGGER.info("Download completed")
        gdrive = gdriveTools.GoogleDriveHelper(self)
        gdrive.upload(progress_status_list[index].name())

    def onDownloadError(self, error, progress_status_list: list, index: int):
        LOGGER.error(error)
        editMessage(error, self.context, self.reply_message)
        del download_dict[self.update.update_id]
        fs_utils.clean_download(progress_status_list[index].path())

    def onUploadStarted(self, progress_status_list: list, index: int):
        pass

    def onUploadComplete(self, link: str, progress_status_list: list, index: int):
        msg = '<a href="{}">{}</a>'.format(link, progress_status_list[index].name())
        try:
            deleteMessage(self.context, self.reply_message)
        except BadRequest:
            # This means that the message has been deleted because of a /status command
            pass
        sendMessage(msg, self.context, self.update)
        del download_dict[self.update.update_id]
        fs_utils.clean_download(progress_status_list[index].path())

    def onUploadError(self, error: str, progress_status: list, index: int):
        LOGGER.error(error)
        editMessage(error, self.context, self.reply_message)
        del download_dict[self.update.update_id]
        fs_utils.clean_download(progress_status[index].path())


@run_async
def mirror(update, context):
    message = update.message.text
    link = message.replace('/mirror', '')[1:]
    reply_msg = sendMessage('Starting Download', context, update)
    index = update.effective_chat.id
    if index in status_reply_dict.keys():
        deleteMessage(context, status_reply_dict[index])
    status_reply_dict[index] = reply_msg
    listener = MirrorListener(context, update, reply_msg)
    aria = download_tools.DownloadHelper(listener)
    aria.add_download(link)




@run_async
def cancel_mirror(update, context):
    pass


mirror_handler = CommandHandler('mirror', mirror)
dispatcher.add_handler(mirror_handler)
