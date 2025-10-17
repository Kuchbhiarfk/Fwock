import asyncio 
import re
from database import db
from translation import Translation
from pyrogram import Client, filters
from .test import get_configs, update_configs, CLIENT, parse_buttons
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CLIENT = CLIENT()

@Client.on_message(filters.command('settings'))
async def settings(client, message):
   await message.delete()
   await message.reply_text(
     "<b>⚙️ SETTINGS PANEL ⚙️</b>\n\n<i>Configure your bot settings below</i>",
     reply_markup=main_buttons()
     )
    
@Client.on_callback_query(filters.regex(r'^settings'))
async def settings_query(bot, query):
  user_id = query.from_user.id
  i, type = query.data.split("#")
  buttons = [[InlineKeyboardButton('↩ Back', callback_data="settings#main")]]
  
  if type=="main":
     await query.message.edit_text(
       "<b>⚙️ SETTINGS PANEL ⚙️</b>\n\n<i>Configure your bot settings below</i>",
       reply_markup=main_buttons())
       
  elif type=="bots":
     buttons = [] 
     _bot = await db.get_bot(user_id)
     if _bot is not None:
        buttons.append([InlineKeyboardButton(_bot['name'],
                         callback_data=f"settings#editbot")])
     else:
        buttons.append([InlineKeyboardButton('✚ Add bot ✚', 
                         callback_data="settings#addbot")])
        buttons.append([InlineKeyboardButton('✚ Add User bot ✚', 
                         callback_data="settings#adduserbot")])
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="settings#main")])
     await query.message.edit_text(
       "<b><u>🤖 MY BOTS</b></u>\n\n<b>You can manage your bots in here</b>",
       reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addbot":
     await query.message.delete()
     bot = await CLIENT.add_bot(bot, query)
     if bot != True: return
     await query.message.reply_text(
        "<b>✅ Bot token successfully added to database</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="adduserbot":
     await query.message.delete()
     user = await CLIENT.add_session(bot, query)
     if user != True: return
     await query.message.reply_text(
        "<b>✅ Session successfully added to database</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="channels":
     buttons = []
     channels = await db.get_user_channels(user_id)
     for channel in channels:
        buttons.append([InlineKeyboardButton(f"{channel['title']}",
                         callback_data=f"settings#editchannels_{channel['chat_id']}")])
     buttons.append([InlineKeyboardButton('✚ Add Channel ✚', 
                      callback_data="settings#addchannel")])
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="settings#main")])
     await query.message.edit_text( 
       "<b><u>🏷 MY CHANNELS</b></u>\n\n<b>You can manage your target chats here</b>",
       reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="addchannel":  
     await query.message.delete()
     try:
         text = await bot.send_message(user_id, "<b>❪ SET TARGET CHAT ❫\n\n📌 Forward a message from your target chat\n\n/cancel - cancel this process</b>")
         chat_ids = await bot.listen(chat_id=user_id, timeout=300)
         if chat_ids.text=="/cancel":
            await chat_ids.delete()
            return await text.edit_text(
                  "<b>❌ Process canceled</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
         elif not chat_ids.forward_date:
            await chat_ids.delete()
            return await text.edit_text("<b>❌ This is not a forwarded message</b>")
         else:
            chat_id = chat_ids.forward_from_chat.id
            title = chat_ids.forward_from_chat.title
            username = chat_ids.forward_from_chat.username
            username = "@" + username if username else "private"
         chat = await db.add_channel(user_id, chat_id, title, username)
         await chat_ids.delete()
         await text.edit_text(
            "<b>✅ Successfully updated</b>" if chat else "<b>⚠️ This channel is already added</b>",
            reply_markup=InlineKeyboardMarkup(buttons))
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('⏱ Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="editbot": 
     bot = await db.get_bot(user_id)
     TEXT = Translation.BOT_DETAILS if bot['is_bot'] else Translation.USER_DETAILS
     buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removebot")
               ],
               [InlineKeyboardButton('↩ Back', callback_data="settings#bots")]]
     await query.message.edit_text(
        TEXT.format(bot['name'], bot['id'], bot['username']),
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type=="removebot":
     await db.remove_bot(user_id)
     await query.message.edit_text(
        "<b>✅ Successfully updated</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("editchannels"): 
     chat_id = type.split('_')[1]
     chat = await db.get_channel_details(user_id, chat_id)
     buttons = [[InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removechannel_{chat_id}")
               ],
               [InlineKeyboardButton('↩ Back', callback_data="settings#channels")]]
     await query.message.edit_text(
        f"<b><u>📄 CHANNEL DETAILS</b></u>\n\n<b>- TITLE:</b> <code>{chat['title']}</code>\n<b>- CHANNEL ID:</b> <code>{chat['chat_id']}</code>\n<b>- USERNAME:</b> {chat['username']}",
        reply_markup=InlineKeyboardMarkup(buttons))
                                             
  elif type.startswith("removechannel"):
     chat_id = type.split('_')[1]
     await db.remove_channel(user_id, chat_id)
     await query.message.edit_text(
        "<b>✅ Successfully updated</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                               
  elif type=="caption":
     buttons = []
     data = await get_configs(user_id)
     caption = data['caption']
     remove_texts = data.get('remove_texts', [])
     
     if caption is None:
        buttons.append([InlineKeyboardButton('✚ Add Caption ✚', 
                      callback_data="settings#addcaption")])
     else:
        buttons.append([
            InlineKeyboardButton('👁 View Caption', callback_data="settings#seecaption"),
            InlineKeyboardButton('✏️ Edit', callback_data="settings#addcaption")
        ])
        buttons.append([
            InlineKeyboardButton('🗑️ Delete Caption', callback_data="settings#deletecaption")
        ])
     
     # Remove Texts Section
     if remove_texts:
        buttons.append([InlineKeyboardButton(f'✂️ Remove Texts ({len(remove_texts)})', 
                      callback_data="settings#manageremove")])
     else:
        buttons.append([InlineKeyboardButton('✂️ Add Remove Texts', 
                      callback_data="settings#addremove")])
     
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="settings#main")])
     
     remove_info = f"\n\n<b>🔴 Auto-Remove Texts: {len(remove_texts)}</b>" if remove_texts else ""
     
     await query.message.edit_text(
        f"<b><u>🖋️ CUSTOM CAPTION</b></u>\n\n<b>Set a custom caption for your files. The bot will automatically remove unwanted texts from original captions.</b>\n\n<b><u>📝 AVAILABLE FILLINGS:</b></u>\n- <code>{{filename}}</code> : File name\n- <code>{{size}}</code> : File size\n- <code>{{caption}}</code> : Cleaned original caption{remove_info}",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addremove":
     await query.message.delete()
     try:
         text = await bot.send_message(
             user_id, 
             "<b>✂️ ADD TEXTS TO AUTO-REMOVE</b>\n\n"
             "<b>📝 Send texts to remove from captions:</b>\n"
             "<code>'''Text1''', '''Text2''', '''Text3'''</code>\n\n"
             "<i>Example:</i>\n<code>'''Download Now''', '''Join Channel''', '''@username'''</code>\n\n"
             "/cancel - cancel process"
         )
         
         remove_input = await bot.listen(chat_id=user_id, timeout=300)
         if remove_input.text == "/cancel":
             await remove_input.delete()
             return await text.edit_text(
                 "<b>❌ Process canceled</b>",
                 reply_markup=InlineKeyboardMarkup(buttons)
             )
         
         # Parse texts to remove
         content = remove_input.text.strip()
         matches = re.findall(r"'''([^']+)'''", content)
         
         if not matches:
             await remove_input.delete()
             return await text.edit_text(
                 "<b>❌ Wrong format!</b>\n\nUse: <code>'''text1''', '''text2'''</code>",
                 reply_markup=InlineKeyboardMarkup(buttons)
             )
         
         # Get existing remove texts
         data = await get_configs(user_id)
         existing_texts = data.get('remove_texts', [])
         
         # Add new texts
         for match in matches:
             if match not in existing_texts:
                 existing_texts.append(match)
         
         await update_configs(user_id, 'remove_texts', existing_texts)
         await remove_input.delete()
         
         await text.edit_text(
             f"<b>✅ Successfully Added!</b>\n\n"
             f"<b>Total Remove Texts: {len(existing_texts)}</b>\n\n"
             f"<b>Added:</b>\n" + "\n".join([f"• <code>{t}</code>" for t in matches]),
             reply_markup=InlineKeyboardMarkup([
                 [InlineKeyboardButton('✂️ Manage', callback_data="settings#manageremove")],
                 [InlineKeyboardButton('↩ Back', callback_data="settings#caption")]
             ])
         )
         
     except asyncio.exceptions.TimeoutError:
         await text.edit_text(
             '<b>⏱ Process timed out!</b>',
             reply_markup=InlineKeyboardMarkup(buttons)
         )
  
  elif type=="manageremove":
     data = await get_configs(user_id)
     remove_texts = data.get('remove_texts', [])
     
     if not remove_texts:
         return await query.answer("No texts to manage!", show_alert=True)
     
     text_list = "\n".join([f"• <code>{t}</code>" for t in remove_texts])
     
     buttons = [
         [InlineKeyboardButton('➕ Add More', callback_data="settings#addremove")],
         [InlineKeyboardButton('🗑️ Clear All', callback_data="settings#clearremove")],
         [InlineKeyboardButton('↩ Back', callback_data="settings#caption")]
     ]
     
     await query.message.edit_text(
         f"<b><u>✂️ AUTO-REMOVE TEXTS</b></u>\n\n"
         f"<b>These texts will be automatically removed from original captions:</b>\n\n"
         f"{text_list}\n\n"
         f"<b>Total: {len(remove_texts)}</b>",
         reply_markup=InlineKeyboardMarkup(buttons)
     )
  
  elif type=="clearremove":
     await update_configs(user_id, 'remove_texts', [])
     await query.message.edit_text(
        "<b>✅ All remove texts cleared</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seecaption":   
     data = await get_configs(user_id)
     remove_texts = data.get('remove_texts', [])
     
     buttons = [
         [InlineKeyboardButton('✏️ Edit Caption', callback_data="settings#addcaption")],
         [InlineKeyboardButton('✂️ Manage Remove Texts', callback_data="settings#manageremove")],
         [InlineKeyboardButton('↩ Back', callback_data="settings#caption")]
     ]
     
     remove_info = ""
     if remove_texts:
         remove_info = f"\n\n<b>🔴 Auto-removing {len(remove_texts)} texts from captions</b>"
     
     await query.message.edit_text(
        f"<b><u>👁 YOUR CUSTOM CAPTION</b></u>\n\n<code>{data['caption']}</code>{remove_info}",
        reply_markup=InlineKeyboardMarkup(buttons))
    
  elif type=="deletecaption":
     await update_configs(user_id, 'caption', None)
     await query.message.edit_text(
        "<b>✅ Caption deleted successfully</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
                              
  elif type=="addcaption":
     await query.message.delete()
     try:
         text = await bot.send_message(
             query.message.chat.id, 
             "<b>📝 SEND YOUR CUSTOM CAPTION</b>\n\n"
             "<b>Available variables:</b>\n"
             "• <code>{filename}</code> - File name\n"
             "• <code>{size}</code> - File size\n"
             "• <code>{caption}</code> - Original caption (auto-cleaned)\n\n"
             "/cancel - cancel process"
         )
         caption_input = await bot.listen(chat_id=user_id, timeout=300)
         if caption_input.text == "/cancel":
             await caption_input.delete()
             return await text.edit_text(
                 "<b>❌ Process canceled!</b>",
                 reply_markup=InlineKeyboardMarkup(buttons)
             )
         try:
             caption_input.text.format(filename='', size='', caption='')
         except KeyError as e:
             await caption_input.delete()
             return await text.edit_text(
                f"<b>❌ Wrong variable {e} used in your caption</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
             )
         await update_configs(user_id, 'caption', caption_input.text)
         await caption_input.delete()
         await text.edit_text(
             "<b>✅ Caption updated successfully!</b>",
             reply_markup=InlineKeyboardMarkup(buttons)
         )
     except asyncio.exceptions.TimeoutError:
         await text.edit_text('⏱ Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="button":
     buttons = []
     button = (await get_configs(user_id))['button']
     if button is None:
        buttons.append([InlineKeyboardButton('✚ Add Button ✚', 
                      callback_data="settings#addbutton")])
     else:
        buttons.append([InlineKeyboardButton('👀 See Button', 
                      callback_data="settings#seebutton")])
        buttons[-1].append(InlineKeyboardButton('🗑️ Remove Button', 
                      callback_data="settings#deletebutton"))
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>⏹ CUSTOM BUTTON</b></u>\n\n<b>You can set inline buttons to your messages.</b>\n\n<b><u>📝 FORMAT:</b></u>\n<code>[Button Text][buttonurl:https://t.me/example]</code>",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="addbutton":
     await query.message.delete()
     try:
         txt = await bot.send_message(user_id, text="<b>📝 SEND YOUR CUSTOM BUTTON</b>\n\n<b>FORMAT:</b>\n<code>[Button Text][buttonurl:https://t.me/example]</code>\n\n/cancel - cancel")
         ask = await bot.listen(chat_id=user_id, timeout=300)
         
         if ask.text == "/cancel":
             await ask.delete()
             return await txt.edit_text(
                 "<b>❌ Process canceled</b>",
                 reply_markup=InlineKeyboardMarkup(buttons)
             )
         
         button = parse_buttons(ask.text.html)
         if not button:
            await ask.delete()
            return await txt.edit_text(
                "<b>❌ Invalid button format</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
         await update_configs(user_id, 'button', ask.text.html)
         await ask.delete()
         await txt.edit_text(
             "<b>✅ Button added successfully</b>",
             reply_markup=InlineKeyboardMarkup(buttons)
         )
     except asyncio.exceptions.TimeoutError:
         await txt.edit_text('⏱ Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seebutton":
      button = (await get_configs(user_id))['button']
      button = parse_buttons(button, markup=False)
      button.append([InlineKeyboardButton("↩ Back", "settings#button")])
      await query.message.edit_text(
         "<b>👀 YOUR CUSTOM BUTTON</b>",
         reply_markup=InlineKeyboardMarkup(button))
      
  elif type=="deletebutton":
     await update_configs(user_id, 'button', None)
     await query.message.edit_text(
        "<b>✅ Button deleted successfully</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
   
  elif type=="database":
     buttons = []
     db_uri = (await get_configs(user_id))['db_uri']
     if db_uri is None:
        buttons.append([InlineKeyboardButton('✚ Add URL ✚', 
                      callback_data="settings#addurl")])
     else:
        buttons.append([InlineKeyboardButton('👀 See URL', 
                      callback_data="settings#seeurl")])
        buttons[-1].append(InlineKeyboardButton('🗑️ Remove URL', 
                      callback_data="settings#deleteurl"))
     buttons.append([InlineKeyboardButton('↩ Back', 
                      callback_data="settings#main")])
     await query.message.edit_text(
        "<b><u>🗃 DATABASE</u></b>\n\n<b>Database is required to store duplicate messages permanently. Without it, stored data may disappear after bot restart.</b>",
        reply_markup=InlineKeyboardMarkup(buttons))

  elif type=="addurl":
     await query.message.delete()
     uri = await bot.ask(user_id, "<b>📝 SEND YOUR MONGODB URL</b>\n\n<i>Get your MongoDB URL from [mongodb.com](https://mongodb.com)</i>", disable_web_page_preview=True)
     if uri.text=="/cancel":
        return await uri.reply_text(
                  "<b>❌ Process canceled!</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
     if not uri.text.startswith("mongodb+srv://") and not uri.text.endswith("majority"):
        return await uri.reply("<b>❌ Invalid MongoDB URL</b>",
                   reply_markup=InlineKeyboardMarkup(buttons))
     await update_configs(user_id, 'db_uri', uri.text)
     await uri.reply("<b>✅ Database URL added successfully</b>",
             reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type=="seeurl":
     db_uri = (await get_configs(user_id))['db_uri']
     await query.answer(f"DATABASE URL: {db_uri}", show_alert=True)
  
  elif type=="deleteurl":
     await update_configs(user_id, 'db_uri', None)
     await query.message.edit_text(
        "<b>✅ Database URL deleted successfully</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type=="filters":
     await query.message.edit_text(
        "<b><u>💠 CUSTOM FILTERS 💠</b></u>\n\n<b>Configure the types of messages you want to forward</b>",
        reply_markup=await filters_buttons(user_id))
  
  elif type=="nextfilters":
     await query.edit_message_reply_markup( 
        reply_markup=await next_filters_buttons(user_id))
   
  elif type.startswith("updatefilter"):
     i, key, value = type.split('-')
     if value=="True":
        await update_configs(user_id, key, False)
     else:
        await update_configs(user_id, key, True)
     if key in ['poll', 'protect']:
        return await query.edit_message_reply_markup(
           reply_markup=await next_filters_buttons(user_id)) 
     await query.edit_message_reply_markup(
        reply_markup=await filters_buttons(user_id))
   
  elif type.startswith("file_size"):
    settings = await get_configs(user_id)
    size = settings.get('file_size', 0)
    i, limit = size_limit(settings['size_limit'])
    await query.message.edit_text(
       f'<b><u>📊 SIZE LIMIT</b></u>\n\n<b>Set file size limit for forwarding\n\nStatus: Files {limit} {size} MB will be forwarded</b>',
       reply_markup=size_button(size))
  
  elif type.startswith("update_size"):
    size = int(query.data.split('-')[1])
    if 0 < size > 2000:
      return await query.answer("❌ Size limit exceeded", show_alert=True)
    await update_configs(user_id, 'file_size', size)
    i, limit = size_limit((await get_configs(user_id))['size_limit'])
    await query.message.edit_text(
       f'<b><u>📊 SIZE LIMIT</b></u>\n\n<b>Set file size limit for forwarding\n\nStatus: Files {limit} {size} MB will be forwarded</b>',
       reply_markup=size_button(size))
  
  elif type.startswith('update_limit'):
    i, limit, size = type.split('-')
    limit, sts = size_limit(limit)
    await update_configs(user_id, 'size_limit', limit) 
    await query.message.edit_text(
       f'<b><u>📊 SIZE LIMIT</b></u>\n\n<b>Set file size limit for forwarding\n\nStatus: Files {sts} {size} MB will be forwarded</b>',
       reply_markup=size_button(int(size)))
      
  elif type == "add_extension":
    await query.message.delete() 
    ext = await bot.ask(user_id, text="<b>📝 SEND EXTENSIONS</b>\n\n<i>Separate by space</i>\n\nExample: <code>zip rar exe</code>\n\n/cancel - cancel")
    if ext.text == '/cancel':
       return await ext.reply_text(
                  "<b>❌ Process canceled</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
    extensions = ext.text.split(" ")
    extension = (await get_configs(user_id))['extension']
    if extension:
        for extn in extensions:
            if extn not in extension:
                extension.append(extn)
    else:
        extension = extensions
    await update_configs(user_id, 'extension', extension)
    await ext.reply_text(
        f"<b>✅ Successfully updated</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
      
  elif type == "get_extension":
    extensions = (await get_configs(user_id))['extension']
    btn = extract_btn(extensions)
    btn.append([InlineKeyboardButton('✚ ADD ✚', 'settings#add_extension')])
    btn.append([InlineKeyboardButton('🗑️ Remove All', 'settings#rmve_all_extension')])
    btn.append([InlineKeyboardButton('↩ Back', 'settings#main')])
    await query.message.edit_text(
        text='<b><u>💾 EXTENSIONS</u></b>\n\n<b>Files with these extensions will NOT be forwarded</b>',
        reply_markup=InlineKeyboardMarkup(btn))
  
  elif type == "rmve_all_extension":
    await update_configs(user_id, 'extension', None)
    await query.message.edit_text(text="<b>✅ Successfully deleted</b>",
                                   reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type == "add_keyword":
    await query.message.delete()
    ask = await bot.ask(user_id, text="<b>📝 SEND KEYWORDS</b>\n\n<i>Separate by space</i>\n\nExample: <code>movie video song</code>\n\n/cancel - cancel")
    if ask.text == '/cancel':
       return await ask.reply_text(
                  "<b>❌ Process canceled</b>",
                  reply_markup=InlineKeyboardMarkup(buttons))
    keywords = ask.text.split(" ")
    keyword = (await get_configs(user_id))['keywords']
    if keyword:
        for word in keywords:
            if word not in keyword:
                keyword.append(word)
    else:
        keyword = keywords
    await update_configs(user_id, 'keywords', keyword)
    await ask.reply_text(
        f"<b>✅ Successfully updated</b>",
        reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type == "get_keyword":
    keywords = (await get_configs(user_id))['keywords']
    btn = extract_btn(keywords)
    btn.append([InlineKeyboardButton('✚ ADD ✚', 'settings#add_keyword')])
    btn.append([InlineKeyboardButton('🗑️ Remove All', 'settings#rmve_all_keyword')])
    btn.append([InlineKeyboardButton('↩ Back', 'settings#main')])
    await query.message.edit_text(
        text='<b><u>♦️ KEYWORDS</b></u>\n\n<b>Files with these keywords in filename will be forwarded</b>',
        reply_markup=InlineKeyboardMarkup(btn))
      
  elif type == "rmve_all_keyword":
    await update_configs(user_id, 'keywords', None)
    await query.message.edit_text(text="<b>✅ Successfully deleted</b>",
                                   reply_markup=InlineKeyboardMarkup(buttons))
  
  elif type.startswith("alert"):
    alert = type.split('_')[1]
    await query.answer(alert, show_alert=True)


# HELPER FUNCTION: Clean caption by removing unwanted texts
async def clean_caption(original_caption, user_id):
    """Remove unwanted texts from original caption"""
    if not original_caption:
        return ""
    
    data = await get_configs(user_id)
    remove_texts = data.get('remove_texts', [])
    
    if not remove_texts:
        return original_caption
    
    cleaned = original_caption
    for text in remove_texts:
        cleaned = cleaned.replace(text, "")
    
    # Clean up extra spaces and newlines
    cleaned = re.sub(r'\n\s*\n+', '\n', cleaned)
    cleaned = re.sub(r' +', ' ', cleaned)
    cleaned = cleaned.strip()
    
    return cleaned
      

def main_buttons():
  buttons = [[
       InlineKeyboardButton('🤖 Bᴏᴛs',
                    callback_data=f'settings#bots'),
       InlineKeyboardButton('🏷 Cʜᴀɴɴᴇʟs',
                    callback_data=f'settings#channels')
       ],[
       InlineKeyboardButton('🖋️ Cᴀᴘᴛɪᴏɴ',
                    callback_data=f'settings#caption'),
       InlineKeyboardButton('⏹ Bᴜᴛᴛᴏɴ',
                    callback_data=f'settings#button')
       ],[
       InlineKeyboardButton('🗃 MᴏɴɢᴏDB',
                    callback_data=f'settings#database'),
       InlineKeyboardButton('🕵‍♀ Fɪʟᴛᴇʀs',
                    callback_data=f'settings#filters')
       ],[
       InlineKeyboardButton('🧪 Exᴛʀᴀ Sᴇᴛᴛɪɴɢs 🧪',
                    callback_data='settings#nextfilters')
       ],[      
       InlineKeyboardButton('⫷ Bᴀᴄᴋ', callback_data='back')
       ]]
  return InlineKeyboardMarkup(buttons)

def size_limit(limit):
   if str(limit) == "None":
      return None, ""
   elif str(limit) == "True":
      return True, "more than"
   else:
      return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
       for data in datas:
         if i >= 5:
            i = 0
         if i == 0:
            btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
            i += 1
            continue
         elif i > 0:
            btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
            i += 1
    return btn 

def size_button(size):
  buttons = [[
       InlineKeyboardButton('+',
                    callback_data=f'settings#update_limit-True-{size}'),
       InlineKeyboardButton('=',
                    callback_data=f'settings#update_limit-None-{size}'),
       InlineKeyboardButton('-',
                    callback_data=f'settings#update_limit-False-{size}')
       ],[
       InlineKeyboardButton('+1',
                    callback_data=f'settings#update_size-{size + 1}'),
       InlineKeyboardButton('-1',
                    callback_data=f'settings#update_size-{size - 1}')
       ],[
       InlineKeyboardButton('+5',
                    callback_data=f'settings#update_size-{size + 5}'),
       InlineKeyboardButton('-5',
                    callback_data=f'settings#update_size-{size - 5}')
       ],[
       InlineKeyboardButton('+10',
                    callback_data=f'settings#update_size-{size + 10}'),
       InlineKeyboardButton('-10',
                    callback_data=f'settings#update_size-{size - 10}')
       ],[
       InlineKeyboardButton('+50',
                    callback_data=f'settings#update_size-{size + 50}'),
       InlineKeyboardButton('-50',
                    callback_data=f'settings#update_size-{size - 50}')
       ],[
       InlineKeyboardButton('+100',
                    callback_data=f'settings#update_size-{size + 100}'),
       InlineKeyboardButton('-100',
                    callback_data=f'settings#update_size-{size - 100}')
       ],[
       InlineKeyboardButton('↩ Back',
                    callback_data="settings#main")
     ]]
  return InlineKeyboardMarkup(buttons)
       
async def filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('🏷️ Forward tag',
                    callback_data=f'settings_#updatefilter-forward_tag-{filter["forward_tag"]}'),
       InlineKeyboardButton('✅' if filter['forward_tag'] else '❌',
                    callback_data=f'settings#updatefilter-forward_tag-{filter["forward_tag"]}')
       ],[
       InlineKeyboardButton('🖍️ Texts',
                    callback_data=f'settings_#updatefilter-text-{filters["text"]}'),
       InlineKeyboardButton('✅' if filters['text'] else '❌',
                    callback_data=f'settings#updatefilter-text-{filters["text"]}')
       ],[
       InlineKeyboardButton('📁 Documents',
                    callback_data=f'settings_#updatefilter-document-{filters["document"]}'),
       InlineKeyboardButton('✅' if filters['document'] else '❌',
                    callback_data=f'settings#updatefilter-document-{filters["document"]}')
       ],[
       InlineKeyboardButton('🎞️ Videos',
                    callback_data=f'settings_#updatefilter-video-{filters["video"]}'),
       InlineKeyboardButton('✅' if filters['video'] else '❌',
                    callback_data=f'settings#updatefilter-video-{filters["video"]}')
       ],[
       InlineKeyboardButton('📷 Photos',
                    callback_data=f'settings_#updatefilter-photo-{filters["photo"]}'),
       InlineKeyboardButton('✅' if filters['photo'] else '❌',
                    callback_data=f'settings#updatefilter-photo-{filters["photo"]}')
       ],[
       InlineKeyboardButton('🎧 Audios',
                    callback_data=f'settings_#updatefilter-audio-{filters["audio"]}'),
       InlineKeyboardButton('✅' if filters['audio'] else '❌',
                    callback_data=f'settings#updatefilter-audio-{filters["audio"]}')
       ],[
       InlineKeyboardButton('🎤 Voices',
                    callback_data=f'settings_#updatefilter-voice-{filters["voice"]}'),
       InlineKeyboardButton('✅' if filters['voice'] else '❌',
                    callback_data=f'settings#updatefilter-voice-{filters["voice"]}')
       ],[
       InlineKeyboardButton('🎭 Animations',
                    callback_data=f'settings_#updatefilter-animation-{filters["animation"]}'),
       InlineKeyboardButton('✅' if filters['animation'] else '❌',
                    callback_data=f'settings#updatefilter-animation-{filters["animation"]}')
       ],[
       InlineKeyboardButton('🃏 Stickers',
                    callback_data=f'settings_#updatefilter-sticker-{filters["sticker"]}'),
       InlineKeyboardButton('✅' if filters['sticker'] else '❌',
                    callback_data=f'settings#updatefilter-sticker-{filters["sticker"]}')
       ],[
       InlineKeyboardButton('▶️ Skip duplicate',
                    callback_data=f'settings_#updatefilter-duplicate-{filter["duplicate"]}'),
       InlineKeyboardButton('✅' if filter['duplicate'] else '❌',
                    callback_data=f'settings#updatefilter-duplicate-{filter["duplicate"]}')
       ],[
       InlineKeyboardButton('⫷ back',
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons) 

async def next_filters_buttons(user_id):
  filter = await get_configs(user_id)
  filters = filter['filters']
  buttons = [[
       InlineKeyboardButton('📊 Poll',
                    callback_data=f'settings_#updatefilter-poll-{filters["poll"]}'),
       InlineKeyboardButton('✅' if filters['poll'] else '❌',
                    callback_data=f'settings#updatefilter-poll-{filters["poll"]}')
       ],[
       InlineKeyboardButton('🔒 Secure message',
                    callback_data=f'settings_#updatefilter-protect-{filter["protect"]}'),
       InlineKeyboardButton('✅' if filter['protect'] else '❌',
                    callback_data=f'settings#updatefilter-protect-{filter["protect"]}')
       ],[
       InlineKeyboardButton('🛑 Size limit',
                    callback_data='settings#file_size')
       ],[
       InlineKeyboardButton('💾 Extension',
                    callback_data='settings#get_extension')
       ],[
       InlineKeyboardButton('♦️ Keywords ♦️',
                    callback_data='settings#get_keyword')
       ],[
       InlineKeyboardButton('⫷ back', 
                    callback_data="settings#main")
       ]]
  return InlineKeyboardMarkup(buttons)

  
