import os
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import menu
import i18n
from lang import*
from telegram.helpers import escape_markdown

# Liste des produits avec leurs informations
def up(update:Update):
    user_lang=set_user_locale(update)
    PRODUITS = [
        {
            "nom": i18n.t("store.product_3_name"),
            "description": i18n.t("store.product_3_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/WhatsApp Image 2025-06-13 à 09.56.21_d571a595.jpg"
        },
        {
            "nom": i18n.t("store.product_4_name"),
            "description": i18n.t("store.product_4_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/WhatsApp Image 2025-06-13 à 09.56.23_af09acaf.jpg"
        },
        {
            "nom": i18n.t("store.product_5_name"),
            "description": i18n.t("store.product_5_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/WhatsApp Image 2025-06-13 à 09.56.23_ce71de6f.jpg"
        },
        {
            "nom": i18n.t("store.product_6_name"),
            "description": i18n.t("store.product_6_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/WhatsApp Image 2025-06-13 à 09.56.24_807b032e.jpg"
        },
        {
            "nom": i18n.t("store.product_7_name"),
            "description": i18n.t("store.product_7_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/WhatsApp Image 2025-06-13 à 09.56.25_0d675438.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/WhatsApp Image 2025-06-13 à 09.56.25_94505d3c.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/a.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/b.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/c.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/d.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/e.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/f.jpg"
        },
        {
            "nom": i18n.t("store.product_8_name"),
            "description": i18n.t("store.product_8_description"),
            "prix": i18n.t("store.product_price_placeholder"),
            "image": "images/g.jpg"
        },
    ]
    return PRODUITS


async def our_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    PRODUITS=up(update)
    user = update.effective_user
    user_lang=set_user_locale(update)
    await update.message.reply_text(
        i18n.t("store.store_header",langue=user_lang) + "\n\n" + i18n.t("store.store_intro",langue=user_lang),
        parse_mode="Markdown",
        reply_markup=menu.get_menu_markup(user.id)
    )

    media_group = []
    for i, produit in enumerate(PRODUITS):
        caption = i18n.t("store.gallery_caption",langue=user_lang) if i == 0 else ""
        try:
            if os.path.exists(produit["image"]):
                with open(produit["image"], 'rb') as photo_file:
                    media_group.append(
                        InputMediaPhoto(media=photo_file.read(), caption=caption)
                    )
        except Exception as e:
            print(f"Erreur image {produit['nom']}: {e}")

    if media_group:
        try:
            await context.bot.send_media_group(
                chat_id=update.effective_chat.id,
                media=media_group
            )
        except Exception:
            await envoyer_produits_individuellement(update, context)

    for produit in PRODUITS:
        msg = (
            f"\U0001F4E6 **{produit['nom']}**\n"
            f"\U0001F4DD {produit['description']}\n"
            f"{i18n.t('store.product_price_label',langue=user_lang)}\n"
            f"{i18n.t('store.product_separator',langue=user_lang)}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(i18n.t('store.btn_more_info'), callback_data=f"info_produit_{PRODUITS.index(produit)}"),
                # InlineKeyboardButton(i18n.t('store.btn_order'), callback_data=f"commander_produit_{PRODUITS.index(produit)}")
            ]
        ])

        await update.effective_chat.send_message(
            msg, parse_mode="Markdown", reply_markup=keyboard
        )

    await update.effective_chat.send_message(
        i18n.t("store.store_footer_header",langue=user_lang) + "\n" + i18n.t("store.store_footer_message",langue=user_lang),
        parse_mode="Markdown"
    )


async def envoyer_produits_individuellement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    PRODUITS=up(update)
    user_lang=set_user_locale(update)
    for produit in PRODUITS:
        if os.path.exists(produit["image"]):
            with open(produit["image"], 'rb') as photo_file:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo_file,
                    caption=f"\U0001F4E6 {produit['nom']}\n\U0001F4B0 {produit['prix']}"
                )


async def gerer_callback_produit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    PRODUITS=up(update)
    user_lang=set_user_locale(update)
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("info_produit_"):
        idx = int(data.split("_")[-1])
        p = PRODUITS[idx]
        nom = escape_markdown(p['nom'], version=1)
        description = escape_markdown(p['description'], version=1)
        prix = escape_markdown(p['prix'], version=1)

        msg = (
            f"\U0001F4E6 **{nom}**\n\n"
            f"{i18n.t('store.detailed_description_header',langue=user_lang)}\n{description}\n\n"
            f"{i18n.t('store.price_header',langue=user_lang)}, {prix}\n\n"
            f"{i18n.t('store.features_header',langue=user_lang)}\n"
            f"{i18n.t('store.feature_premium_quality',langue=user_lang)}\n"
            f"{i18n.t('store.feature_fast_delivery',langue=user_lang)}\n"
            f"{i18n.t('store.feature_warranty',langue=user_lang)}\n\n"
            f"{i18n.t('store.contact_more_info',langue=user_lang)}"
        )
        keyboard = InlineKeyboardMarkup([
            # [InlineKeyboardButton(i18n.t("store.btn_order_now",langue=user_lang), callback_data=f"commander_produit_{idx}")],
            [InlineKeyboardButton(i18n.t("store.btn_back_to_store",langue=user_lang), callback_data="retour_boutique")]
        ])
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=keyboard)

    elif data.startswith("commander_produit_"):
        idx = int(data.split("_")[-1])
        p = PRODUITS[idx]
            
        nom = escape_markdown(p['nom'], version=1)
        prix = escape_markdown(p['prix'], version=1)

        msg = (
            f"{i18n.t('store.order_header',langue=user_lang)}  {nom}\n\n"
            f"{i18n.t('store.price_header',langue=user_lang)} {prix}\n\n"
                f"{i18n.t('store.order_instructions_header',langue=user_lang)}\n"
            f"{i18n.t('store.order_step_1',langue=user_lang)}\n"
            f"{i18n.t('store.order_step_2',langue=user_lang)}\n"
            f"{i18n.t('store.order_step_3',langue=user_lang)}\n\n"
            f"{i18n.t('store.order_confirmation',langue=user_lang)}"
        )

        keyboard = InlineKeyboardMarkup([
            # [InlineKeyboardButton(i18n.t("store.btn_contact_support",langue=user_lang), callback_data="contact_support")],
            [InlineKeyboardButton(i18n.t("store.btn_back_to_store",langue=user_lang), callback_data="retour_boutique")]
        ])
        await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=keyboard)

    elif data == "retour_boutique":
        await query.edit_message_text(i18n.t("store.back_to_store_message"))

    elif data == "contact_support":
        msg = (
            f"{i18n.t('store.contact_support_header',langue=user_lang)}\n\n"
            f"{i18n.t('store.support_intro',langue=user_lang)}\n\n"
            f"{i18n.t('store.support_email',langue=user_lang)}\n"
            f"{i18n.t('store.support_telegram',langue=user_lang)}\n"
            f"{i18n.t('store.support_hours',langue=user_lang)}\n\n"
            f"{i18n.t('store.support_response',langue=user_lang)}\n"
        )
        await query.edit_message_text(msg, parse_mode="Markdown")
