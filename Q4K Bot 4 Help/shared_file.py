import pandas as pd
from telegram import Update
from customContext import CustomContext 
import os

class SharedFile:
      def __init__(self):
            self._file_path = "Files/Shared_File_data.csv"
            self._admin_list =  {"Shrouk":1135869415,"Osama":5549398282}
            self.chat_database_id = os.os.environ['CHAT_DATABASE_ID']
            self.data = pd.read_csv(self._file_path)

      def _message_user_sender_id(self, message_id ):
            
            msg_id = self.data[self.data["File ID"] == message_id]
            # Check if the msg Exist
            if len(msg_id) > 0:
              return msg_id["User ID"].tolist()
            else:
              return None
              
      #======================= USER CASHDATA and HASHTAGS ====================#

      def _user_cache_material_hashtags(update:Update, context:CustomContext, keyboards): 
        return "#" + "\n#".join([value.replace(" ", "_") for value in context.user_cache_data.values() if value is not None])

      def _msg_hashtags_to_user_cache(update:Update, context:CustomContext):
        # Get Hashtags from users 
        hashtags_message = update.message.text 
        correct_hashtag = "You Selecte This Hashtags: \n"
        false_hashtag = "\nThose Hashtags are Not Correct: "

        # Extract Validate Hashtags
        matches = re.findall(r'#(\w+)', hashtags_message)

        # Validate Each Hashtags and show correct and not correct hashtags
        for hashtag in matches: 
          material_info = " ".join(hashtag.split("_"))
          selected_key, i = get_key_from_value(keyboards, material_info)
          
          # Check if the key exist in the keyboards dict
          if selected_key != None: 
            correct_hashtag += "\n* "+selected_key+" : "+hashtag
            context.user_cache_data[selected_key] = hashtag.replace("_"," ")
          else:
            false_hashtag += "\n* "+hashtag

        # Send Message with Correct Hashtags to user
        if "*" in correct_hashtag: 
          final_message = f"{correct_hashtag}{'*' + false_hashtag if '*' in false_hashtag else ''}\n\nDo you want to send material with these hashtags?"
          return final_message
        else:
          return None
          
        #   await send_inline_keyboard_message(update, context, final_message,[["Yes","no"]],
        #                                      [["Share_btnManualConfirmeTrue","Share_btnManualConfirmeFalse"]]  )

        # # In case there no correct Hashtags
        # else: 
        #   await update.message.reply_text("There is no Correct Hashtags Founded, Please Resend Correct Hashtags Again!!!")


  

      #======================= DATABASE MATERIAL FUNCTIONS ====================#
  
      async def retrive_material(update:Update, context:CustomContext, retrive_quire:str):
        """Send Messages that user retrive while search for matiral"""   

        # Iterate through the list of messages and send
        messaage_id_list = retrieve_data_advanced(self._file_path, retrive_quire)["File ID"]

        if len(messaage_id_list) == 0: 
            await update.message.reply_text("No Material Founded !!!")
        else:
            for message_id in messaage_id_list: 
                try:
                  await context.bot.forward_message(chat_id=update.message.chat_id,
                                                    from_chat_id='-1002081981357',
                                                    message_id=message_id)
                except Exception as e:
                  logger.info(f"Error When retrive message id: {message_id}, for user: {update.effective_message.from_user.id}")
                  
      
      async def store_material(update:Update, context:CustomContext):
        """Store Materials that user shared"""
        
        # Store the Materials
        user_id = update.effective_message.from_user.id
        
        # Check if the caption is valid
        if not self._validate_material_caption(update.effective_message.caption):
          await update.message.reply_text("Invalid Caption !!!")
          return
        
        # Store the Materials
        store_data(self._file_path, quire, update.effective_message.caption, update.effective_message.document.file_id, user_id)
        
        await update.message.reply_text("Material Stored !!!")






  
        
      async def edit_message_caption(self, update: Update, context: CustomContext,new_caption:str, chat_id = self.chat_database_id) -> None:
        """ Edit Caption of Messages """

        file_id = int(update.message.text.split("/")[-1])
        send_id = self._message_user_sender_id(self, file_id )
        
        if send_id:
          # Check if user is the sender of the file or admin
          if update.effective_user.id in [*send_id, *self.ADMIN_LIST.values()]:
              # Edit the original message in the telegram database with new caption
              await context.bot.edit_message_text(
                  chat_id=chat_id,
                  message_id=file_id,
                  text=new_caption
              )
              # Edit the original message in the CSV file with new caption
              data.loc[data["File ID"] == file_id, "Caption"] = new_text
              data.to_csv(self.data_path, index=False)
  
              await update.effective_message.reply_text("Caption edited successfully.")
          else:
              await update.effective_message.reply_html("You don't have permission to edit this caption.")
        else:
          await update.effective_message.reply_html("This file doesn't exist.")
            


      async def modify_message(self, update: Update, context: CustomContext, message_id): 
            
          # Iterate through different types of attachments
          if update.message.document:
            file_id = update.message.document.file_id
            replied_message = await update.message.reply_document(document=file_id, caption=new_caption)

          elif update.message.photo:
            file_id = update.message.photo[0].file_id
            replied_message = await update.message.reply_photo(photo=file_id,caption=new_caption)

          elif update.message.video:
            file_id = update.message.video.file_id
            replied_message = await update.message.reply_video(video=file_id, caption=new_caption)

          elif update.message.audio:
            file_id = update.message.audio.file_id
            replied_message = await update.message.reply_audio(audio=file_id, caption=new_caption)

      async def modify_caption_and_forward(self, update: Update, context: CustomContext) -> None:
        """Modify Attachiment Caption then forwared This Attachiment to spacific group"""
        # Check if the message contains a document, photo, video, or audio
        if update.message.document or update.message.photo or update.message.video or update.message.audio:
          # Get the file ID based on the type of attachment
          file_id = None
          replied_message = None
          # New caption
          new_caption = "#"+"\n#".join([value.replace(" ","_") for value in context.message_clicks.values() if value is not None])

          # Iterate through different types of attachments
          if update.message.document:
            file_id = update.message.document.file_id
            replied_message = await update.message.reply_document(document=file_id, caption=new_caption)

          elif update.message.photo:
            file_id = update.message.photo[0].file_id
            replied_message = await update.message.reply_photo(photo=file_id,caption=new_caption)

          elif update.message.video:
            file_id = update.message.video.file_id
            replied_message = await update.message.reply_video(video=file_id, caption=new_caption)

          elif update.message.audio:
            file_id = update.message.audio.file_id
            replied_message = await update.message.reply_audio(audio=file_id, caption=new_caption)

          if file_id:

            # Forward the replied message to another chat
            forwared_message = await context.bot.forward_message(chat_id = chat_database_id,
                                              from_chat_id=update.message.chat_id,
                                              message_id=replied_message.message_id)

            attachment_user_info = {"File ID":forwared_message.message_id,"User ID":update.effective_user.id,
                                    "Username":update.effective_user.username,"Current Date":datetime.now()}

            # Update Attachiment Database
            add_row_to_csv("Files/Shared_File_data.csv",{**attachment_user_info,**context.message_clicks})

            # Delete the original message
            await context.bot.delete_message(chat_id=update.message.chat_id, message_id=replied_message.message_id)

        else:
          # Handle the case when the message doesn't contain a supported attachment
          await update.message.reply_text(
              "Please send a supported attachment (document, photo, video, audio) to modify its caption."
          )


                  