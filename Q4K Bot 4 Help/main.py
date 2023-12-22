# # Download the file
# from telegram import InputFile
#   file = await context.bot.get_file(update.message.document)
#   file_path = await file.download_to_drive(file_name)

#   # Optionally, you can resend the modified document to reflect the changes in the caption
#   with open(file_path, "rb") as modified_file:
#       await context.bot.send_document(
#           chat_id=update.effective_chat.id,
#           document=InputFile(modified_file),
#           caption=new_caption
#       )
#   # Remove the temporary downloaded file
#   os.remove(file_path)


#  Create Image
# async def stylize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#   user_message = update.message.text
#   if user_message is None:
#     await update.message.reply_text("Please send an image to stylize.")
#     return

#   img = Image.new('RGB', (500, 200), color=(73, 109, 137))
#   d = ImageDraw.Draw(img)
#   fnt = ImageFont.load_default()
#   d.text((50, 90), user_message, font=fnt, fill=(255, 255, 0))

#   img.save('styled_text.png')
#   with open('styled_text.png', 'rb') as photo:
#     await update.message.reply_photo(photo=photo)

import logging
import os
import re
import copy
import html

from telegram import __version__ as TG_VER
import pandas as pd
from csv_operations import (
    read_csv,
    write_csv,
    add_row_to_csv,
    get_row_from_csv,
    remove_row_from_csv,
    edit_row_in_csv,
    retrieve_data_advanced,
)
from dict_operations import (
    get_key_from_value,
    get_last_non_none_key_and_value,
    get_values_from_list_of_keys,
    create_nested_dict,
)
from customContext import CustomContext, ChatData
from datetime import datetime
from server import server
from dotenv import load_dotenv, find_dotenv


from collections import defaultdict
from typing import DefaultDict, Optional, Set

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    TypeHandler,
    filters,
)
from telegram import (
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio,
)

load_dotenv(find_dotenv())


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

# Get Bot Token From Environment
my_bot_token = os.environ["YOUR_BOT_TOKEN"]
chat_database_id = os.environ["CHAT_DATABASE_ID"]
chat_database_backup_id = os.environ["CHAT_DATABASE_BACKUP_ID"]
CHAT_DATABASES = [chat_database_id, chat_database_backup_id]

chat_database_username = os.environ["CHAT_DATABASE_USERNAME"]
ADMIN_LIST = {"Shrouk": 1135869415, "Osama": 5549398282}
shared_file_path = "Files/Shared_File_data.csv"
database_path = lambda chat_id: shared_file_path if chat_id == chat_database_id else "Files/Shared_File_data_Backup.csv"


# Enable logging
logging.basicConfig(
    filename="logfile.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


####################################################################################
##################################### IMPORT DATA ##################################
####################################################################################

g = pd.read_csv("Files/ge.csv")
cs = pd.read_csv("Files/cs.csv")
it = pd.read_csv("Files/it.csv")
i_s = pd.read_csv("Files/is.csv")
mm = pd.read_csv("Files/mm.csv")
data = pd.concat([g, cs, it, i_s, mm]).iloc[:, :-1].drop_duplicates()

# Define the lambda function
# Update Chat & Backup
def backup_from_original (chat_id, key):
    df = pd.read_csv("Files/database_backup_con.csv")
    if chat_id == chat_database_backup_id:
        return dict(zip(df["Original Database"], df["Backup Database"])).get(key,"")
    return key




course_start_with = lambda specific_letter: [
    [course]
    for course in list(
        data[data["Course Name"].str.startswith(specific_letter)]["Course Name"]
    )
]

# KEYBOARD
keyboards = {
    "Year": [["2024"], ["2023"], ["2022"], ["2021"], ["2020"], ["2019"]],
    "Academic year": [
        ["First Year"],
        ["Second Year"],
        ["Third Year"],
        ["Fourth Year"],
        ["Back", "Back to Start"],
    ],
    "Department": [["CS"], ["IT"], ["IS"], ["MM"], ["Back", "Back to Start"]],
    "Semester": [["First Semester", "Second Semester"], ["Back", "Back to Start"]],
    "Course Name": course_start_with(""),
    "Course Type": [["Lectures", "Sections", "Exams"], ["Back", "Back to Start"]],
    "Material Type": [
        ["Slide", "Book", "Summary"],
        ["Video", "Record", "Link"],
        ["OutsideRescource"],
        ["Back", "Back to Start"],
    ],
    "Lecture": [
        ["Lec0", "Lec1", "Lec2", "Lec3"],
        ["Lec4", "Lec5", "Lec6", "Lec7"],
        ["Lec8", "Lec9", "Lec10", "Lec11"],
        ["Lec12", "Lec13", "Lec14", "Lec15"],
        ["Adding Lectures Manually"],
        ["Back", "Back to Start"],
    ],
    "Exams Type": [["Practical", "Midterm", "Final"], ["Back", "Back to Start"]],
}
Material_info = [
    "Year",
    "Department",
    "Academic year",
    "Semester",
    "Course Name",
    "Course Type",
    "Material Type",
    "Lecture",
    "Exams Type",
]


course_lock_info = ["Department", "Course Lettar", "Course Name"]
course_lock_keyboard = {
    "Department": [["GE"], ["CS"], ["IT"], ["IS"], ["MM"], ["Back", "Back to Start"]],
    "Course Lettar": [
        ["3", "A", "B", "C", "D", "E", "F"],
        ["G", "H", "I", "K", "M", "N", "O"],
        ["P", "Q", "R", "S", "T", "V", "W"],
        ["Back", "Back to Start"],
    ],
    "Course Name": course_start_with(""),
}


edited_material_info = ["File ID"] + Material_info


####################################################################################
####################################################################################
################################## BOT FUNCTIONS ###################################
####################################################################################
####################################################################################


################################################################################
########################## CALLBACK FUNCTION ###################################
################################################################################


# Function to handle Inline button clicks
async def button_click(update: Update, context: CustomContext) -> None:
    # Get the callback data from the clicked button
    query = update.callback_query
    button_id = query.data
    await update.callback_query.answer()

    # =========Start Methods Buttons==============
    if button_id == "Start_btn":
        await start(update, context)
    elif button_id == "Start_btnShare":
        await share(update, context)
    elif button_id == "Start_btnSearch":
        await search(update, context)
    elif button_id == "Start_btnInfo":
        await info(update, context)
    elif button_id == "Start_btnEdit":
        await edit(update, context)
    elif button_id == "Start_btnDelete":
        await delete(update, context)

    # =========== SEARCH METHOD BUTTONS =================
    # Search Manual
    elif button_id == "Search_btnManual":
        new_action(update, context, "Search_Manual")
        await update.effective_message.reply_html(
            """You clicked <b>Manual Search</b>\n write name of Material and any other filtter with:
                                        \n\n * '&' like Database&2023 => get all Material for Database only at 2023 
                                        \n\n * '|' like Database|2023 => get all Material for Database and all material at 2023 
                                        \n\n * '-' like Database-2023 => get all Material for Database Except at 2023 """
        )

    # --------Search Automatic------
    elif button_id == "Search_btnAutomatic":
        await update.effective_message.reply_text(
            "Automatic Search is ON", reply_markup=ReplyKeyboardRemove(selective=True)
        )
        await search_automatic(update, context)
    elif button_id == "Search_btnCreate_Message":
        await retrieve_material(update, context, "Message")
    elif button_id == "Search_btnRetreive_Materials":
        await retrieve_material(update, context, "Material")

    # ============ SHARE METHOD BUTTONS ==============
    # ----------------Share Manual ------------------
    elif button_id == "Share_btnManual":
        context.current_state = "Share_Manual"
        await update.effective_message.reply_text(
            "You clicked Manual Share \nSend Message of Hashtags You Want to assign to Material"
        )
    # ------------ Confirm Share Manuaal -------------
    elif button_id == "Share_btnManualConfirmeTrue":
        context.current_state = "receive_data"
        await update.effective_message.reply_text("Send Your Material Now")
    # ----------- Not Confirm Share Manuaal ----------
    elif button_id == "Share_btnManualConfirmeFalse":
        await update.effective_message.reply_text("Send Your Hashtags Again")
    # -------------- Share Automatic ------------------
    elif button_id == "Share_btnAutomatic":
        context.current_state = "Share_Auto"
        await update.effective_message.reply_text(
            "Automatic Share is ON", reply_markup=ReplyKeyboardRemove(selective=True)
        )
        await share_automatic(update, context)

    # ============ EDIT Method Buttons ===============
    # First Stage
    # --------------- Edit Manual --------------
    elif button_id == "Edit_btnCaption":
        context.current_state = "Edit_Caption"
        await choose_edit_caption_type(update, context)
    # Second Stage
    # --------------- Edit Content -------------
    elif button_id == "Edit_btnContent":
        context.current_state = "Edit_Content"
        await update.effective_message.reply_html(
            "You clicked <b>Edit Material Content</b> \nSend New Material"
        )
    # --------- Edit Caption Auton - Manual ---------
    elif button_id == "Edit_btnCaption_Manual":
        context.current_state = "Edit_Caption_Manual"
        await update.effective_message.reply_html(
            "You clicked <b>Edit Material Caption Manually</b>\nSend You Caption Hashtags"
        )
    elif button_id == "Edit_btnCaption_Auto":
        context.current_state = "Edit_Caption_Auto"
        await edit_caption_auto(update, context)
    # Third Stage
    # ------------ Confirm Edit Caption -------------
    elif button_id == "Edit_btnCaption_Confirm":
        await edit_material_caption(update, context)
    elif button_id == "Edit_btnCaption_Resend":
        await update.effective_message.reply_html("Resend New Hashtags")

    # =============== REMOVE METHOD =====================
    elif button_id == "Start_btnRemove":
        await remove(update, context)

    # =============== GPA METHOD BOTTONS ================
    elif button_id == "Start_btnGPACalc":
        await GPACalc(update, context)

    # =========== COURSE LOCK METHOD BOTTONS ===========
    elif button_id == "Start_btnCourseLock":
        await courseLock(update, context)


####################################################################################
################################ MASSAGE HANDELR ###################################
####################################################################################

############################### TEXT MESSAGE #######################################


async def textHandler(update: Update, context: CustomContext) -> None:
    """Handel Text User Send and Forwared them to Spacfic Program according to state"""
    # If Share Option was used
    state = context.current_state
    print(state)
    # ------------------- Share ------------------
    # Share Manual
    if state == "Share_Manual":
        await share_manual(update, context)
    # Share Automatic
    elif state == "Share_Auto":
        await share_automatic(update, context)

    # ------------------- Search ------------------
    # Search Manual
    elif state == "Search_Manual":
        await search_manual(update, context)
    # Search Automatic
    elif state == "Search_Auto":
        await search_automatic(update, context)
    elif state == "receive_data":
        await receive_materials_send_database(update, context)

    # --------------------- EDIT ------------------
    elif state == "Edit":
        await choose_edit_type(update, context)
    elif state == "Edit_Caption_Auto":
        await edit_caption_auto(update, context)
    elif state == "Edit_Caption_Manual":
        await edit_caption_manualy(update, context)
    # ------------------- SHARE ------------------------
    # Share Manual
    elif state == "Share_Manual":
        await share_manual(update, context)
    # Share Automatic
    elif state == "Share_Auto":
        await share_automatic(update, context)
    # -------------------- REMOVE ----------------------
    elif state == "Remove":
        await remove_messages(update, context)
    # ------------------ GPA CALC --------------------
    elif state == "GPACalc":
        await calculate_gpa(update, context)
    # ------------------ COURSE LOCK ------------------
    elif state == "CourseLock":
        await find_locked_course(update, context)

    else:
        await start(update, context)


############################### ATTACH MESSAGE #######################################
async def attachHandelr(update: Update, context: CustomContext) -> None:
    """Handel Attachiment User Send and Forwared them to Spacfic Program according to state"""

    # ------------------- Auto Search or Share------------------
    if context.current_state == "receive_data":
        await receive_materials_send_database(update, context)
    elif context.current_state == "Edit_Content":
        await edit_material_content(update, context)

    # ------------------- IF No state------------------
    else:
        await start(update, context)

####################################################################################
############################## COMMANDS FUNCTIONS ##################################
####################################################################################


############################## Handel New Action ###################################
def new_action(update: Update, context: CustomContext, action_name: str):
    # log the user share action
    logger.info(
        action_name
        + " command requested by {} in chat {}.".format(
            update.effective_message.from_user.first_name,
            update.effective_message.chat_id
        )
    )
    # Update current state
    context.current_state = action_name
    # Delete all saved Data to get new data
    action_keys = {
        "Share": Material_info,
        "Search": Material_info,
        "Edit": edited_material_info,
        "CourseLock": course_lock_info,
    }
    if action_name in action_keys:
        context.reset_user_cache_data(action_keys[action_name])


############################### START COMMAND #######################################
async def start(update: Update, context: CustomContext) -> None:
    """Starts the conversation and asks the user"""
    # New action
    new_action(update, context, "Start")
    # Reply to user to choose next action
    msg_header = """Hi! My name is <b>Q4K Help Bot</b>🤖.\nI will hold a conversation with you. 
  \n\n How can I Help You Today <b>{}</b>?""".format(
        update.effective_message.from_user.first_name
    )
    msg_btn = [
        ["Share 📨", "Search 🔎"],
        ["Edit 📝", "Remove 🗑️"],
        ["GPA Calculator 🧮", "Course Lock 🔏"],
        ["How Bot Work ℹ️"],
    ]
    btn_id = [
        ["Start_btnShare", "Start_btnSearch"],
        ["Start_btnEdit", "Start_btnRemove"],
        ["Start_btnGPACalc", "Start_btnCourseLock"],
        ["Start_btnInfo"],
    ]

    await send_inline_keyboard_message(update, context, msg_header, msg_btn, btn_id)


############################### SHARE COMMAND #######################################
async def share(update: Update, context: CustomContext) -> None:
    """
    SHARE function.
    * Create Hashtags
    * Modifiy Attachment by new Hashtags & Send to group
    """
    # New acation
    new_action(update, context, "Share")
    # Reply to user to
    msg_header = "You are about to send us materials. Thx 🥰"
    msg_btn = [["Manual Share", "Automatic Share"], ["Back to Start"]]
    btn_id = [["Share_btnManual", "Share_btnAutomatic"], ["Start_btn"]]
    await send_inline_keyboard_message(update, context, msg_header, msg_btn, btn_id)


############################### SEARCH COMMAND #######################################
async def search(update: Update, context: CustomContext) -> None:
    """
    Search for Material
    * Search by typing Manual
    * Search by buttons Aautomatic
    """
    # New action
    new_action(update, context, "Search")
    # Create a list of buttons
    # Reply to user to
    msg_header = "You Want to search for Material, Choose Your Search Method:"
    msg_btn = [["Manual Search ✍️", "Automatic Search ⌨️"], ["Back to Start 🔙"]]
    btn_id = [["Search_btnManual", "Search_btnAutomatic"], ["Start_btn"]]
    await send_inline_keyboard_message(update, context, msg_header, msg_btn, btn_id)


############################### EDIT COMMAND #######################################
async def edit(update: Update, context: CustomContext) -> None:
    """
    Edit Material
    * Edit by typing Manual
    * Edit by buttons Aautomatic
    """
    # New action
    new_action(update, context, "Edit")
    await update.effective_message.reply_text("Send Link of Message you want to Edit")


############################### REMOVE COMMAND #######################################
async def remove(update: Update, context: CustomContext) -> None:
    """Remove Messages"""
    # New action
    new_action(update, context, "Remove")
    await update.effective_message.reply_text("Send Link of Message you want to Delete")


#################################### GPA CALCUATOR #############################
async def GPACalc(update: Update, context: CustomContext):
    """
    Calculator
    * Calcuate GPA
    * Calcuate Percentage
    """
    # New action
    new_action(update, context, "GPACalc")

    await update.effective_message.reply_html(
        "Send Your GPA like This:"
        "\n<b>C 1</b>\n<b>A+ 3</b>\n"
        "Lettars = Grade \n"
        "Numbers = Course Hours"
    )


##################################### COURSE LOCK ##############################
async def courseLock(update: Update, context: CustomContext):
    """
    Search for courses that git locked by other course
    """
    # New action
    new_action(update, context, "CourseLock")
    # Start Find new courses
    await update.effective_message.reply_html(
        "You Now Search for Courses that Lock By Other Course",
        reply_markup=ReplyKeyboardRemove(selective=True),
    )
    # Start Course Lock Discover
    await find_locked_course(update, context)


########################### print_users COMMAND ###############################
async def print_users(update: Update, context: CustomContext) -> None:
    """Show which users have been using this bot."""
    await update.message.reply_text(
        f"The following user IDs have used this bot: {', '.join(map(str, context.bot_user_ids))}"
    )

async def print_files(update: Update, context: CustomContext) -> None:
    """Show which users have been using this bot."""
    print(update.effective_message.user.id in admin_ids)
    if update.effective_message.user.id in admin_ids:
        # Send the CSV file
        for files_path in database_path+["Files/users.csv"]:
            with open(files_path, 'rb') as file:
                await context.bot.send_document(chat_id=update.effective_message.chat_id,
                                                document=InputFile(file))
                
# async def print_static(update: Update, context: CustomContext):
#     """Show which users have been using this bot."""
#     if update.effective_message.user.id in admin_ids:
#         # Send the CSV file
        


################################ INFO #########################################
async def info(update: Update, context: CustomContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton(
                "Listen To Explain Video",
                url="https://youtu.be/bcYEX_I88VY?si=f2SN6bY6yozc6EJF",
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_html(
        "\nHI Iam <b>Q4K Help Bot 🤖</b>"
        "\ncreated to help you in your studying\n\n<b>So How can i help you</b>"
        "\n\n*  <b>Share materials 📨</b>\nusing /share command by typing/selecting type(Hashtags)"
        "for your Materials then send Materials Anonymously "
        "\n\n* <b>Search for materials 🔎</b>\nusing /search command by typing/selecting type of Materials you want then bot send Materials."
        "\n\n* <b>Edit materials 📝</b>\nusing /edit command by send message link and then choose change message contenet or message caption (Hashtags)."
        "\n\n* <b>Remove materials 🗑️</b>\nusing /remove command by send material link you want to remove."
        "\n\n* <b>Calculate Your GPA 🧮</b>\nCalculate Your GPA and Percetange use /calc command"
        "\n\n* <b>Courses Get Locked 🚫</b>\nknow what Courses Get Locked by spacific course by use /lock command "
        "\n\nThis work is for God only, please pray for me 💖"
        "\nWant Some Help? ask Developer @Osama_Mo7",
        reply_markup=reply_markup,
    )



        ####################################################################################
        ################################### BOT PROGRAMS ###################################
        ####################################################################################


# Hashtags Common Functions
def user_cache_data_to_hashtag(user_data_dict):
    values_list = get_values_from_list_of_keys(user_data_dict, Material_info)
    return "#" + "\n#".join(
        [
            str(value).replace(" ", "_").replace("/", "\n#")
            for value in values_list
            if value not in [None, "nan"]
        ]
    )


async def extract_material_info_from_hashtags(update: Update, context: CustomContext):
    correct_hashtag = {}
    false_hashtag = []

    # Extract Hashtags
    matches = re.findall(r"#(\w+)", update.message.text)
    # Validate Hashtags
    for hashtag in matches:
        material_info = hashtag.replace("_", " ")
        selected_key, i = get_key_from_value(keyboards, material_info)

        # Extract Correcte and Wrong Hashtags
        if selected_key != None:
            correct_hashtag.update({selected_key: material_info})
            context.user_cache_data.update({selected_key: material_info})
        else:
            false_hashtag.append(hashtag)

    # Check if there is any Important Hashtag Not exsits
    if len(correct_hashtag) > 0:
        if any(
            i not in correct_hashtag.keys() for i in ["Course Name", "Course Type"]
        ) or not any(
            i in correct_hashtag.keys() for i in ["Material Type", "Exams Type"]
        ):
            return -1, -1
        else:
            # Auto Complite Elective Keys if has no hashtags
            time = str(datetime.now()).split("-")
            if int(time[1]) > 8:
                year = int(time[0]) + 1
                sem = "First Semester"
            else:
                year = int(time[0])
                sem = "First Semester" if int(time[1]) < 3 else "Second Semester"

            if "Year" not in correct_hashtag.keys():
                correct_hashtag["Year"] = year
                context.user_cache_data.update({"Year": year})
            if "Semester" not in correct_hashtag.keys():
                correct_hashtag["Semester"] = sem
                context.user_cache_data.update({"Semester": sem})

            return correct_hashtag, false_hashtag
    else:
        return None, None


###############################################################################
############################### EDIT MATERIAL #################################
###############################################################################


async def choose_edit_type(update: Update, context: CustomContext):
    # Check if link is valied
    group_username = update.message.text.split("/")[-2]
    msg_id = int(update.message.text.split("/")[-1])
    msg_data = get_row_from_csv(shared_file_path, "File ID", msg_id)
    if (msg_data != None) and (group_username == chat_database_username):
        if update.effective_user.id in [msg_data["User ID"], *ADMIN_LIST.values()]:
            # Update user cacha data
            file_data = {
                "File ID": msg_id,
                **{k: v for k, v in msg_data.items() if k in edited_material_info},
            }
            for i, j in file_data.items():
                context.user_cache_data[i] = j

            # Choose Type of update
            msg_header = "You Want to Edit Material, Choose What does you want to change"
            msg_btn = [
                ["Material Content 🖼️", "Material Caption 💬"],
                ["Back to Start 🔙"],
            ]
            btn_id = [["Edit_btnContent", "Edit_btnCaption"], ["Start_btn"]]
            await send_inline_keyboard_message(
                update, context, msg_header, msg_btn, btn_id
            )
        else:
            await update.effective_message.reply_html(
                "You Can't Edit this file cause you don't share it"
            )
    else:
        await update.effective_message.reply_html(
            "The Message You want to Edit does not Exist"
        )


# Material Content Selected
async def edit_material_content(update: Update, context: CustomContext):
    """Edit Material Content"""
    # Check the type of media in the update
    media = None
    if update.message.photo:
        # Image
        file_id = update.message.photo[-1].file_id
        media = InputMediaPhoto(media=file_id)
    elif update.message.video:
        # Video
        file_id = update.message.video.file_id
        media = InputMediaVideo(media=file_id)
    elif update.message.document:
        # PDF or any other document
        file_id = update.message.document.file_id
        media = InputMediaDocument(media=file_id)
    elif update.message.audio:
        # Music or audio
        file_id = update.message.audio.file_id
        media = InputMediaAudio(media=file_id)
    else:
        # Unsupported media type
        await update.effective_message.reply_text("Unsupported media type")

    # Update Chat & Backup
    for chat_id in CHAT_DATABASES:
        msg_id = backup_from_original(chat_id, context.user_cache_data["File ID"])
        print(msg_id)
        # Edit the old media message with the new media
        await context.bot.edit_message_media(
            chat_id=chat_id,
            message_id=msg_id,
            media=media,
        )

        # Update Material Caption
        caption = user_cache_data_to_hashtag(context.user_cache_data)
        await context.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=msg_id,
            caption=caption,
        )

    await update.effective_message.reply_html(
        "You Edited Material Content Successfully"
    )


# Material Caption Selected
async def choose_edit_caption_type(update: Update, context: CustomContext):
    # Choose Type of update
    msg_header = "You Want to Edit Material Caption, Choose Which way you want to "
    msg_btn = [["Edit Caption Manualy ✍️", "Edit Caption Auto ⌨️"], ["Back to Edit 🔙"]]
    btn_id = [["Edit_btnCaption_Manual", "Edit_btnCaption_Auto"], ["Start_btnEdit"]]
    await send_inline_keyboard_message(update, context, msg_header, msg_btn, btn_id)


# Edit Caption Manualy Selected
async def edit_caption_manualy(update: Update, context: CustomContext):
    """Edit Material Caption Manualy"""
    correct_hashtags, false_hashtags = await extract_material_info_from_hashtags(
        update, context
    )

    if correct_hashtags:
        await confirm_edit_caption(update, context, correct_hashtags, false_hashtags)
    else:
        await update.effective_message.reply_html(
            "Please Enter Correct Hashtags Caption"
        )


# Edit Caption Auto Selected
async def edit_caption_auto(update: Update, context: CustomContext):
    """Edit Material Caption Manualy"""
    # New Action
    new_action(update, context, "Edit_Caption_Auto")
    # Show Keyboards
    end_page = await keyboard_button_control(update, context, keyboards)
    # You Reach to end page
    if end_page == -1:
        await confirm_edit_caption(
            update, context, correct_hashtags=context.user_cache_data
        )


async def confirm_edit_caption(
    update: Update, context: CustomContext, correct_hashtags: dict, false_hashtags=[]
):
    msg_header = "<b>True hashtags</b>\n\n*" + "\n*".join(
        [f"<b>{i}</b> : {j}" for i, j in correct_hashtags.items()]
    )
    if len(false_hashtags) > 0:
        msg_header += "\n\n<b>False hashtags Are</b>\n\n*" + "\n*".join(false_hashtags)
    msg_header += "\nAre You Sure You Want To Edit Material Caption>"
    msg_btn = [["Yes ✅", "No ❌"], ["Back to Edit 🔙"]]
    btn_id = [["Edit_btnCaption_Confirm", "Edit_btnCaption_Resend"], ["Start_btnEdit"]]
    await send_inline_keyboard_message(update, context, msg_header, msg_btn, btn_id)


async def edit_material_caption(update: Update, context: CustomContext) -> None:
    """Edit Messages"""
    # Get New Captions
    caption = user_cache_data_to_hashtag(context.user_cache_data)
    # Edit Database
    # Update Chat & Backup
    for chat_id in CHAT_DATABASES:  
        msg_id = backup_from_original(chat_id, context.user_cache_data["File ID"])
        # Edit Caption
        await context.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=msg_id,
            caption=caption,
        )
        edit_row_in_csv(
            database_path(chat_id),
            "File ID",
            msg_id,
            context.user_cache_data,
        )

    await update.effective_message.reply_text("Edit Material Caption Done")


################################################################################
############################## REMOVE MATERIAL #################################
################################################################################

async def remove_messages(update: Update, context: CustomContext) -> None:
    """Remove Messages"""
    data_path = shared_file_path
    file_id = int(update.message.text.split("/")[-1])
    group_username = update.message.text.split("/")[-2]

    # Check if the msg Exist
    msg_data = get_row_from_csv(data_path, "File ID", file_id)
    if (msg_data != None) and (group_username == chat_database_username):
        # Check if user want to send is sender of the file or admin
        if update.effective_user.id in [msg_data["User ID"], *ADMIN_LIST.values()]:
            # Delete the original message from telegram databse
            # Update Chat & Backup
            for chat_id in CHAT_DATABASES:
                msg_id = backup_from_original(chat_id, file_id)
                await context.bot.delete_message(
                    chat_id=chat_id,
                    message_id=msg_id
                )
                # Delete the original message from CSV file
                deleted = remove_row_from_csv(database_path(chat_id), "File ID", msg_id)
            # Remove Connection too
            remove_row_from_csv("Files/database_backup_con.csv", "Original Database", file_id)
            await update.effective_message.reply_text(deleted)
        else:
            await update.effective_message.reply_html(
                "You Can't Delete this file cause you don't share it and you don't admin"
            )
    else:
        await update.effective_message.reply_html(
            "The Message You want to Delete does not Exist"
        )


################################################################################
############################### SHARE MATERIAL #################################
################################################################################


async def share_automatic(update: Update, context: CustomContext) -> None:
    """Automatic Share Material Method"""
    # New Action
    new_action(update, context, "Share_Auto")

    # Show Keyboards
    end_page = await keyboard_button_control(update, context, keyboards)

    # You Reach to end page
    if end_page == -1:
        hashtags = user_cache_data_to_hashtag(context.user_cache_data)
        await update.message.reply_text(
            f"You Select Those hashtags\n {hashtags}\nPlease Send Material"
        )
        context.current_state = "receive_data"


async def share_manual(update: Update, context: CustomContext) -> None:
    """Manual Share Material Method"""
    # New Action
    new_action(update, context, "Share_Manual")
    correct_hashtags, false_hashtags = await extract_material_info_from_hashtags(
        update, context
    )

    if correct_hashtags:
        if correct_hashtags == -1:
            await update.message.reply_text(
                "There must be Course Name, Course Type and at least Material Type or Exams Type "
            )
        else:
            final_message = (
                f"Correct Hashtags \n{user_cache_data_to_hashtag(correct_hashtags)}"
            )
            final_message += (
                "False Hashtags\n#" + "\n#".join(false_hashtags)
                if "*" in false_hashtags
                else ""
            )
            final_message += "\n\nDo you want to send material with these hashtags?"
            await send_inline_keyboard_message(
                update,
                context,
                final_message,
                [["Yes ✅", "no ❌"]],
                [["Share_btnManualConfirmeTrue", "Share_btnManualConfirmeFalse"]],
            )
    else:
        await update.effective_message.reply_html(
            "There is no Correct Hashtags Founded, Please Resend Correct Hashtags Again!!!"
        )


################################################################################
################################### SEARCH MATERIAL ############################
################################################################################

async def search_automatic(update: Update, context: CustomContext) -> None:
    """Automatic Search for Material Method"""
    # New action
    new_action(update, context, "Search_Auto")
    # Show Keyboards
    end_page = await keyboard_button_control(update, context, keyboards)
    # You Reach to end page
    if end_page == -1:
        # Remove Department when search cause common courses
        context.user_cache_data["Department"] = None
        quire = "&".join(
            [value for value in context.user_cache_data.values() if value is not None]
        )
        await retrieve(update, context, quire=quire)


async def search_manual(update: Update, context: CustomContext) -> None:
    """Manualy Search for Material Method"""

    await retrieve(update, context, quire=update.message.text)


async def retrieve(update: Update, context: CustomContext, quire: str):
    """Send Messages that user retrive while search for matiral"""

    # Iterate through the list of messages and send
    message_id_list = retrieve_data_advanced(shared_file_path, quire)

    # Check if it retrive data
    if len(message_id_list) == 0:
        await update.message.reply_text("No Material Founded !!!")
    # Check if
    else:
        # Updata user cash data
        context.reset_user_cache_data({"message_id_list": message_id_list})
        context.user_cache_data["message_id_list"] = message_id_list

        msg_header = "How would you like me to send you your materials?"
        msg_btn = [["Retrive Materials 🗂️", "Create Message of Materials 📜"]]
        btn_id = [["Search_btnRetreive_Materials", "Search_btnCreate_Message"]]
        await send_inline_keyboard_message(update, context, msg_header, msg_btn, btn_id)


# ========================= COMMON SEARCH and SHARE METHODS ======================

async def keyboard_button_control(update: Update, context: CustomContext, keyboards) -> int:
    """Show Buttons Keyboard Accoridng to Use input Text"""

    message = update.message
    # Show Start Page of keyboard if No Message before
    if message is None or message.text[0] == "/":
        await dict_to_keyboard(update, context, next(iter(keyboards)), keyboards)
    else:
        # -------------------------- HANDEL CONSTANT CASES -----------------------
        message_text = message.text.split("(")[0]
        print(message_text)
        # If Back button Selected
        if message_text == "Back":
            # Remove Last hashtag
            prev_key, prev_value = get_last_non_none_key_and_value(
                context.user_cache_data
            )
            context.user_cache_data[prev_key] = None
            # Move to prevoise page
            await dict_to_keyboard(update, context, prev_key, keyboards)
        # If Back to Start button Selected
        elif message_text == "Back to Start":
            await share(update, context)
        # If Course Latter Choosen
        elif message_text == "Search by Course Lettar":
            await dict_to_keyboard(
                update, context, "Course Lettar", course_lock_keyboard
            )
        elif message_text in [
            element
            for sup_list in course_lock_keyboard["Course Lettar"]
            for element in sup_list
        ]:
            await dict_to_keyboard(
                update, context, "Course Lettar Course Name", keyboards
            )

        # -------------------------- HANDEL DYNAMIC CASES -----------------------
        else:
            # Retrive key of value if not licture
            selected_key, i = (
                ("Lecture", 12)
                if check_lectures_pattern(message_text)
                else get_key_from_value(keyboards, message_text)
            )

            # If Key is None
            if selected_key is None:
                await update.message.reply_text(
                    f"Please Select Element from Buttons"
                    f"\n\n{message_text} is not a valid option"
                )

            else:
                # Show Next Keyboard page put not for last pages
                if (
                    selected_key == "Lecture"
                    and message_text == "Adding Lectures Manually"
                ):
                    await update.message.reply_html(
                        "<b>Send Lecture for this materail</b>"
                        "\n*<b> New Line </b> = New Materails "
                        "\n*<b> New Space</b> = New Lectures  "
                        "\n\n<b>Example: </b>"
                        "\n\none Lecture for all material\nLec1 "
                        "\n\none material for more than one Lecture  \nLec1/Lec2/Lec3 "
                        "\n\nmore than one lecature each lecture has one material \nLec1\nLec2\nLec3 "
                        "\n\nmore than one lecature each lecture has more than one material\nLec1/Lec2\nLec3/Lec4 "
                    )

                else:
                    # Add value to user keyboard
                    context.user_cache_data[selected_key] = str(message_text)

                    if selected_key not in [
                        "Lecture",
                        list(context.user_cache_data.keys())[-1],
                    ] and str(message_text) != "Book":
                        # Update keyboards with new values and move to new page
                        next_key = list(keyboards.keys())[i + 1]

                        # Check Department if it General or not
                        if next_key == "Department" and str(message_text) in [
                            "First Year",
                            "Second Year",
                        ]:
                            context.user_cache_data[next_key] = "GE"
                            next_key = "Semester"

                        await dict_to_keyboard(update, context, next_key, keyboards)
                        # Key founded
                        return 1

                    else:
                        print(selected_key)
                        # Reached to the End
                        return -1

    # Nothing Happend
    return 0


def check_lectures_pattern(text):
    # Define the pattern using regular expression
    pattern = re.compile(r"\bLec\d+\b")
    # Check if all words match the pattern
    match_result = all(pattern.match(word) for word in text.split())

    return match_result


##############################################################################
################################## DATABASE ##################################
##############################################################################


#-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- SEND MESSAGES _-_-_-_-_-_-_-_-_-_-_-_-_-_

async def retrieve_material(update: Update, context: CustomContext, type):
    """Send Messages that user retrieve while searching for material"""
    message_id_list = context.user_cache_data["message_id_list"]
    material_dict_info = create_nested_dict(message_id_list.to_dict(orient="records"))
    message = ""

    for course_name, years in material_dict_info.items():
        message += await create_message(course_name, years, type, update, context)

    await update.effective_message.reply_html(message, disable_web_page_preview=True)


async def create_message(course_name, years, type, update, context):
    material_type_to_emoji = {
        "slide": "📚",
        "exam": "📄",
        "video": "📺",
        "record": "🔊",
        "summary": "📝",
        "link": "🔗",
        "other": "📖"
    }

    message = f"{'-_' * 22}\n✨✨✨  <b>{course_name}</b>  ✨✨✨"

    for year, course_types in years.items():
        message += f"\n\n{'-' * 60}\n🗓️ <b>Year: {year}</b>"

        for course_type, material_types in course_types.items():
            message += f"\n\n                   🏫 <b>{course_type}</b> 🏫\n"

            for material_type, lectures in material_types.items():
                emoji = material_type_to_emoji.get(material_type.lower(), "📖")
                message += f"\n{emoji}<b> {material_type.lower()} </b>{emoji}\n"

                if type == "Material": 
                    await update.effective_message.reply_html(message, disable_web_page_preview=True)
                    message = ""

                lecture_messages = [
                    await create_lecture_message(lecture, type, update, context)
                    for lecture in lectures
                ]
                grouped_messages = ["".join(lecture_messages[i:i+4]) for i in range(0, len(lecture_messages), 4)]
                message += "\n".join(grouped_messages)

    return message + "\n\n\n"

async def create_lecture_message(lecture, type, update, context):
    message = ""
    for name, link in lecture.items():
        if type == "Material":
            await send_message_based_on_content_type(update, context, update.effective_message.chat_id, name, link.split("/")[-1])

        elif type == "Message":
            message += f"<a href='{html.escape(link)}'>{html.escape(name)}</a>       "

    return message


#-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_- RETRIVE MESSAGES _-_-_-_-_-_-_-_-_-_-_-_-_-_

async def receive_materials_send_database(update: Update, context: CustomContext) -> None:
    """Modify Attachment Caption and send it directly to a specific group"""
    

    lectures = context.user_cache_data.get("Lecture", None)
    if lectures :
        print(lectures)
        lectures = lectures.split("\n")
        context.user_cache_data["Lecture"] = lectures.pop(0) 

    new_caption = user_cache_data_to_hashtag(context.user_cache_data)
    file_ids = []
    for chat_id in CHAT_DATABASES:
        
        file_id, link = await send_message_based_on_content_type(update, context, chat_id ,new_caption)
    
        if file_id:
            attachment_user_info = {
                "File ID": file_id,
                "File Link": link,
                "User ID": update.effective_user.id,
                "Username": update.effective_user.username,
                "Current Date": datetime.now(),
            }
    
            # Update Attachment Database
            add_row_to_csv(
                database_path(chat_id),
                {**attachment_user_info, **context.user_cache_data},
            )
    
            file_ids.append(file_id)
    
        else:
            await update.message.reply_text("Please send a supported attachment (document, photo, video, audio, text) or a valid URL to modify its caption.")
    add_row_to_csv(
        "Files/database_backup_con.csv",
        {"Original Database":file_ids[0],"Backup Database":file_ids[1]},
    )
    if lectures:
        context.user_cache_data["Lecture"] = "\n".join(lectures)
    await update.message.reply_text("Done!")




async def send_message_based_on_content_type(update: Update, context: CustomContext, chat_id, new_caption, file_id=None):

    content_type_to_function = {
        'document': context.bot.send_document,
        'photo': context.bot.send_photo,
        'video': context.bot.send_video,
        'audio': context.bot.send_audio,
    }

    message = None
    if file_id is not None:
        message = await context.bot.forward_message(chat_id=chat_id,
                                              from_chat_id= chat_database_id, message_id = file_id)
    else:
       message = update.message

    new_file_id = None
    for content_type, function in content_type_to_function.items():
        content = getattr(message, content_type)
        if content:
            new_file_id = content.file_id if content_type != 'photo' else content[0].file_id
            file_send = await function(chat_id=chat_id, **{content_type: new_file_id, 'caption': new_caption})
            return file_send.message_id, "https://t.me/Q4K_Database/"+str(file_send.message_id)
    else:
        file_send = await context.bot.send_message(chat_id, f"{message.text}\n\nCaption:\n{new_caption}")

        urls = re.findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", message.text)
        link = urls[0] if urls else "https://t.me/Q4K_Database/"+str(file_send.message_id)
        return file_send.message_id, link

    if file_id is not None: 
        await context.bot.delete_message(
            chat_id=chat_id,
            message_id=message.message_id,
        )

################################################################################
############################## GPA CALCULATUR ##################################
################################################################################

async def calculate_gpa(update: Update, context: CustomContext):
    grade_points = {
        "A+": 4.0,
        "A": 3.7,
        "A-": 3.3,
        "B+": 3,
        "B": 2.8,
        "C+": 2.6,
        "C": 2.3,
        "D+": 2,
        "D": 1.7,
        "D-": 1.4,
        "F": 0.0,
    }

    total_credit_hours = 0
    total_grade_points = 0
    # Extract Grade and course hours from user message
    grades_and_hours = update.message.text
    for entry in grades_and_hours.split("\n"):
        if entry:
            try:
                # Calculate user GPA and Percentage
                grade, hours = entry.split()
                total_credit_hours += int(hours)
                total_grade_points += grade_points[grade] * int(hours)
            except Exception as e:
                await update.message.reply_text(
                    "Please Send Your Degree Like this \n"
                    "\n Grade Hours \n A 3 \n B 2"
                )
                break
    else:
        # If For loop done correctly without any break caclaute GPA
        if total_credit_hours == 0:
            gpa = 0.0
            percentage = 0.0
        else:
            gpa = round(total_grade_points / total_credit_hours, 2)
            percentage = round((total_grade_points / (4 * total_credit_hours)) * 100, 2)

        # Send user message
        message = "Hi {} Your GPA is <b>{}</b> and percentage is <b>{}</b>% ".format(
            update.message.from_user.first_name, gpa, percentage
        )
        if percentage > 80:
            message += "Congratulations 🎉🥳"
        elif percentage > 50:
            message += "Good Job 💖"
        else:
            message += "Keep Trying Not End of the world ♥️"
        await send_inline_keyboard_message(
            update, context, message, [["Back to Start"]], [["Start_btn"]]
        )

################################################################################
############################ FIND COURSE THAT LOCKED ###########################
################################################################################

async def find_locked_course(update: Update, context: CustomContext):
    # Show Keyboards
    end_page = await keyboard_button_control(update, context, course_lock_keyboard)

    # You Reach to end page
    if end_page == -1:
        department, course_letter, course_name = context.user_cache_data.values()
        file_path = "Files/" + department.lower() + ".csv"
        df = pd.read_csv(file_path)
        course_code = df.loc[df["Course Name"] == course_name, "Code"]

        if len(course_code) == 0:
            await update.message.reply_html(
                f"Courses <b>{course_name}</b> Not for <b>{department}</b> Department",
                reply_markup=ReplyKeyboardRemove(selective=True),
            )
        else:
            course_code = course_code.values[0]
            locked_courses = list(
                retrieve_data_advanced(file_path, course_code, None, 100)["Course Name"]
            )
            locked_courses.remove(course_name)
            if len(locked_courses) > 0:
                await update.message.reply_html(
                    f"Courses That Locked by Course <b>{course_name}</b> with code <b>{course_code}</b> are\n\n* "
                    + "\n* ".join(locked_courses),
                    reply_markup=ReplyKeyboardRemove(selective=True),
                )
            else:
                await update.message.reply_html(
                    f"No Courses Founded That Locked by Course <b>{course_name}</b> with code <b>{course_code}</b>",
                    reply_markup=ReplyKeyboardRemove(selective=True),
                )

                ####################################################################################
                ############################## BOT COMMON FUNCTIONS ################################
                ####################################################################################


async def track_users(update: Update, context: CustomContext) -> None:
    """Store the user id of the incoming update, if any."""
    if update.effective_user:
        if update.effective_user.id not in context.bot_user_ids:
            add_row_to_csv(
                "Files/users.csv",
                {
                    "First Name": update.effective_user.first_name,
                    "Last Name": update.effective_user.last_name,
                    "User ID": update.effective_user.id,
                    "Username": update.effective_user.username,
                    "Login Date": datetime.now(),
                },
            )

            context.bot_user_ids.add(update.effective_user.id)


async def send_inline_keyboard_message(
    update: Update,
    custom: CustomContext,
    messageHeader: str,
    buttonsName: list,
    buttonsID: list,
):
    """Send Inline Keyboard Message using Nested List of Buttons Name and ID"""
    # Create Buttons
    buttons = [
        [
            InlineKeyboardButton(text=name, callback_data=id)
            for name, id in zip(buttonsName[i], buttonsID[i])
        ]
        for i in range(len(buttonsName))
    ]
    # Create an InlineKeyboardMarkup with the list of buttons
    reply_markup = InlineKeyboardMarkup(buttons)
    # Send a message with the buttons
    try:
        await update.effective_message.edit_html(
            messageHeader, reply_markup=reply_markup
        )
    except Exception as e:
        await update.effective_message.reply_html(
            messageHeader, reply_markup=reply_markup
        )


async def dict_to_keyboard( update: Update, context: CustomContext, page_key, dict_keyboards):
    """Convert List Value of Dict for spacific Key to Keyboard in python"""
    kb = {}
    msg = update.message.text.split("(")[0] if update.message else ""
    # Get Next Keyboard Values
    # Handel Exams Keyboard
    if msg == "Exams":
        kb = copy.deepcopy(dict_keyboards["Exams Type"])
    # Handel Cours Name Keyboard
    elif page_key == "Course Name":
        udict = context.user_cache_data
        file_path = "Files/" + udict["Department"].lower() + ".csv"
        quire = udict["Academic year"] + "&" + udict["Semester"]
        kb = [
            [i]
            for i in retrieve_data_advanced(file_path, quire)["Course Name"].tolist()
        ]
        kb += [["Search by Course Lettar"], ["Back", "Back to Start"]]
    # Handle Course Lettar Keyboard
    elif page_key == "Course Lettar Course Name":
        kb = course_start_with(msg) + [["Back", "Back to Start"]]
    else:
        kb = copy.deepcopy(dict_keyboards[page_key])

    # Add Number of Material in dict_keyboard Except for Lettars
    if page_key != "Course Latter":
        for i, key in enumerate(kb):
            for j, value in enumerate(key):
                d = [i for i in context.user_cache_data.values() if i != None]
                value_num = len(
                    retrieve_data_advanced(
                        shared_file_path, value + "&" + "&".join(d), None, 100
                    )
                )
                if value_num > 100 : value = "100+"
                kb[i][j] = (
                    kb[i][j]
                    if kb[i][j] in ["Back", "Back to Start"]
                    else kb[i][j] + f"({value_num})"
                )

    # Update Keyboard value
    reply_markup = ReplyKeyboardMarkup(
        kb,
        one_time_keyboard=True,
        resize_keyboard=True,
        input_field_placeholder=f"Select Your {page_key}",
    )

    await update.effective_message.reply_text(
        f"Select Your {page_key}", reply_markup=reply_markup
    )


####################################################################################
####################################### MAIN #######################################
####################################################################################


def main() -> None:
    """Run the bot."""
    context_types = ContextTypes(context=CustomContext, chat_data=ChatData)
    application = (
        Application.builder().token(my_bot_token).context_types(context_types).build()
    )

    # run track_users in its own group to not interfere with the user handlers
    application.add_handler(TypeHandler(Update, track_users), group=-1)

    # Commands
    application.add_handler(CommandHandler("start", start), group=1)
    application.add_handler(CommandHandler("share", share), group=1)
    application.add_handler(CommandHandler("search", search), group=1)
    application.add_handler(CommandHandler("calc", GPACalc), group=1)
    application.add_handler(CommandHandler("lock", courseLock), group=1)
    application.add_handler(CommandHandler("edit", edit), group=1)
    application.add_handler(CommandHandler("remove", remove), group=1)
    application.add_handler(CommandHandler("info", info), group=1)
    application.add_handler(CommandHandler("edit_msg", edit), group=1)
    application.add_handler(CommandHandler("print_users", print_users), group=1)
    application.add_handler(CommandHandler("print_files", print_files), group=1)

    # Callbacks
    application.add_handler(CallbackQueryHandler(button_click), group=2)

    # Messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, textHandler), group=3
    )
    application.add_handler(MessageHandler(filters.ATTACHMENT, attachHandelr), group=3)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    server()
    main()
