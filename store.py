import os
from telegram import Update, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import menu

# Liste des produits avec leurs informations
PRODUITS = [
    {
        "nom": "Produit 1",
        "description": "Description du produit 1",
        "prix": "-- USDT",
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.22_366dfb14.jpg"  # Utilisez / au lieu de \
    },
    {
        "nom": "Produit 2", 
        "description": "Description du produit 2",
        "prix": "-- USDT",
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.21_0566ebab.jpg"
    },
    {
        "nom": "Produit 3",
        "description": "Description du produit 3", 
        "prix": "-- USDT",
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.21_d571a595.jpg"
    },
    {
        "nom": "Produit 4",
        "description": "Description du produit 4",
        "prix": "-- USDT", 
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.23_af09acaf.jpg"
    },
    {
        "nom": "Produit 5",
        "description": "Description du produit 5",
        "prix": "-- USDT", 
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.23_ce71de6f.jpg"
    },
    {
        "nom": "Produit 6",
        "description": "Description du produit 6",
        "prix": "-- USDT", 
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.24_807b032e.jpg"
    },
    {
        "nom": "Produit 7",
        "description": "Description du produit 7",
        "prix": "-- USDT", 
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.25_0d675438.jpg"
    },
    {
        "nom": "Produit 8",
        "description": "Description du produit 8",
        "prix": "-- USDT", 
        "image": "images/WhatsApp Image 2025-06-13 à 09.56.25_94505d3c.jpg"
    },
]

async def our_store(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche la galerie de produits de l'entreprise."""
    user = update.effective_user
    
    # Message d'introduction
    intro_msg = (
        "🏪 **NOTRE BOUTIQUE**\n\n"
        "Découvrez notre sélection de produits de qualité !\n"
        "Voici notre galerie de produits disponibles :"
    )
    
    await update.message.reply_text(
        intro_msg, 
        parse_mode="Markdown",
        reply_markup=menu.get_menu_markup(user.id)
    )
    
    # Créer la galerie de photos avec descriptions
    media_group = []
    
    for i, produit in enumerate(PRODUITS):
        caption = ""
        if i == 0:  # Ajouter la caption seulement à la première image
            caption = "🛍️ Voici nos produits disponibles :"
            
        try:
            # Vérifier que le fichier existe
            if os.path.exists(produit["image"]):
                # Utiliser open() pour lire le fichier local
                with open(produit["image"], 'rb') as photo_file:
                    media_group.append(
                        InputMediaPhoto(
                            media=photo_file.read(),  # Lire le contenu du fichier
                            caption=caption if i == 0 else ""
                        )
                    )
            else:
                print(f"Fichier non trouvé : {produit['image']}")
                
        except Exception as e:
            print(f"Erreur lors de l'ajout de l'image {produit['nom']}: {e}")
    
    # Envoyer la galerie de photos
    if media_group:
        try:
            await context.bot.send_media_group(
                chat_id=update.effective_chat.id,
                media=media_group
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi de la galerie: {e}")
            # Fallback : envoyer les images une par une
            await envoyer_produits_individuellement(update, context)
    
    # Envoyer les détails de chaque produit
    for produit in PRODUITS:
        produit_msg = (
            f"📦 **{produit['nom']}**\n"
            f"📝 {produit['description']}\n"
            f"💰 Prix : {produit['prix']}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Boutons pour chaque produit
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("💬 Plus d'infos", callback_data=f"info_produit_{PRODUITS.index(produit)}"),
                InlineKeyboardButton("🛒 Commander", callback_data=f"commander_produit_{PRODUITS.index(produit)}")
            ]
        ])
        
        await update.effective_chat.send_message(
            produit_msg,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    # Message de fin
    footer_msg = (
        "📞 **CONTACT**\n"
        "Pour toute question ou commande, contactez notre support !\n\n"
        "🔔 Restez connectés pour découvrir nos nouveaux produits !"
    )
    
    await update.effective_chat.send_message(
        footer_msg,
        parse_mode="Markdown"
    )

async def envoyer_produits_individuellement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback pour envoyer les images une par une si la galerie échoue."""
    for produit in PRODUITS:
        try:
            if os.path.exists(produit["image"]):
                with open(produit["image"], 'rb') as photo_file:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=photo_file,
                        caption=f"📦 {produit['nom']}\n💰 {produit['prix']}"
                    )
            else:
                print(f"Fichier non trouvé : {produit['image']}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'image {produit['nom']}: {e}")

async def gerer_callback_produit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les callbacks des boutons de produits."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("info_produit_"):
        produit_index = int(data.split("_")[-1])
        produit = PRODUITS[produit_index]
        
        info_msg = (
            f"📦 **{produit['nom']}**\n\n"
            f"📝 **Description détaillée :**\n"
            f"{produit['description']}\n\n"
            f"💰 **Prix :** {produit['prix']}\n\n"
            f"✅ **Caractéristiques :**\n"
            f"• Qualité premium\n"
            f"• Livraison rapide\n"
            f"• Garantie incluse\n\n"
            f"📞 Contactez-nous pour plus d'informations !"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 Commander maintenant", callback_data=f"commander_produit_{produit_index}")],
            [InlineKeyboardButton("⬅️ Retour à la boutique", callback_data="retour_boutique")]
        ])
        
        await query.edit_message_text(
            info_msg,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    
    elif data.startswith("commander_produit_"):
        produit_index = int(data.split("_")[-1])
        produit = PRODUITS[produit_index]
        
        commande_msg = (
            f"🛒 **COMMANDE : {produit['nom']}**\n\n"
            f"💰 Prix : {produit['prix']}\n\n"
            f"📞 **Pour finaliser votre commande :**\n"
            f"1. Contactez notre support\n"
            f"2. Précisez le produit souhaité\n"
            f"3. Confirmez votre adresse de livraison\n\n"
            f"✅ Notre équipe vous contactera rapidement !"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Contacter le support", callback_data="contact_support")],
            [InlineKeyboardButton("⬅️ Retour à la boutique", callback_data="retour_boutique")]
        ])
        
        await query.edit_message_text(
            commande_msg,
            parse_mode="Markdown", 
            reply_markup=keyboard
        )
    
    elif data == "retour_boutique":
        await query.edit_message_text(
            "🏪 Retour à la boutique...\n\nUtilisez la commande /our_store pour voir à nouveau nos produits."
        )
    
    elif data == "contact_support":
        await query.edit_message_text(
            "📞 **CONTACT SUPPORT**\n\n"
            "Notre équipe est là pour vous aider !\n\n"
            "📧 Email : support@votreentreprise.com\n"
            "💬 Telegram : @votre_support\n"
            "⏰ Horaires : 9h-18h (Lun-Ven)\n\n"
            "Nous vous répondrons dans les plus brefs délais !"
        )