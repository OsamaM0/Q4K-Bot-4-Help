from collections import defaultdict
from typing import DefaultDict, Optional, Set
from telegram.ext import ( Application, CallbackContext, ExtBot, TypeHandler, filters)
from telegram import Update

####################################################################################
################################## CUSTOM CONTEXT ##################################
####################################################################################

class ChatData:
  """Custom class for chat_data. Here we store data per message."""

  def __init__(self) -> None:
      self.clicks_per_message = defaultdict()
      self.user_current_state : DefaultDict[int, str] = defaultdict(str)




# The [ExtBot, dict, ChatData, dict] is for type checkers like mypy
class CustomContext(CallbackContext[ExtBot, dict, ChatData, dict]):
  """Custom class for context."""

  def __init__(
      self,
      application: Application,
      chat_id: Optional[int] = None,
      user_id: Optional[int] = None,
  ):
    super().__init__(application=application, chat_id=chat_id, user_id=user_id)
    self._message_id: Optional[str] = user_id


  @property
  def bot_user_ids(self) -> Set[int]:
    """Custom shortcut to access a value stored in the bot_data dict"""
    return self.bot_data.setdefault("user_ids", set())

  ############################ UPDATE USER CASH DATA ########################
  @property
  def message_clicks(self,) -> Optional[str]:
    """Access the number of clicks for the message this context object was built for."""
    if self._message_id:
      return self.chat_data.clicks_per_message[self._message_id]
    return None

  @message_clicks.setter
  def message_clicks(self, key:str, value: str) -> None:
    """Allow to change the count"""
    if not self._message_id:
      raise RuntimeError(
          "There is no message associated with this context object.")
    self.chat_data.clicks_per_message[self._message_id][key] = value

  def reset_mssage_clicks(self, default_keys) -> None:
    """
    Reset all values oef keys for the associated message to None.
    """
    if not self._message_id:
        raise RuntimeError("There is no message associated with this context object.")

    # Reset all values to None
    self.chat_data.clicks_per_message[self._message_id] = {key: None for key in default_keys}

  ############################ UPDATE USER CURRENT STATE ########################

  @property
  def current_state(self) -> Optional[str]:
      """Access the number of clicks for the message this context object was built for."""
      if self._message_id:
          return self.chat_data.user_current_state[self._message_id]
      return None

  @current_state.setter
  def current_state(self, value: str) -> None:
      """Allow to change the count"""
      if not self._message_id:
          raise RuntimeError("There is no message associated with this context object.")
      self.chat_data.user_current_state[self._message_id] = value
