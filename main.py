import smtplib
import re
from email.mime.text import MIMEText
import ssl
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ConversationHandler
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

EMAIL, MESSAGE = range(2)


def is_valid_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None


def send_email_tls(recipient_email, message_text):
    msg = MIMEText(message_text)
    msg["Subject"] = "Сообщение от Telegram бота"
    msg["From"] = SMTP_EMAIL
    msg["To"] = recipient_email

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP("smtp.yandex.ru", 587) as server:
            server.starttls(context=context)
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, recipient_email, msg.as_string())
            print("Email отправлен успешно.")
    except Exception as e:
        print(f"Ошибка при отправке письма: {e}")


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text("Привет! Пожалуйста, введите свой email:")
    return EMAIL


async def email_handler(update: Update, context: CallbackContext):
    email = update.message.text.strip()
    print(f"Пользователь ввел email: {email}")
    if is_valid_email(email):
        context.user_data["email"] = email
        await update.message.reply_text("Email принят. Пожалуйста, введите текст сообщения:")
        return MESSAGE
    else:
        await update.message.reply_text("Некорректный email. Попробуйте снова:")
        return EMAIL


async def message_handler(update: Update, context: CallbackContext):
    message_text = update.message.text.strip()
    email = context.user_data.get("email")
    if email:
        send_email_tls(email, message_text)
        await update.message.reply_text("Сообщение отправлено!")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Ошибка: Email не был установлен.")
        return ConversationHandler.END


def main():
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, email_handler)],
            MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        },
        fallbacks=[],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
