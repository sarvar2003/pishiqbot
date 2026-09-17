from aiogram.fsm.state import State, StatesGroup


class TransactionStates(StatesGroup):
    waiting_amount = State()
    waiting_category = State()
    waiting_payment = State()
    waiting_note = State()
    waiting_datetime = State()
    confirming = State()


class EditTransactionStates(StatesGroup):
    choosing_field = State()
    waiting_new_amount = State()
    waiting_new_category = State()
    waiting_new_payment = State()
    waiting_new_note = State()


class TransferStates(StatesGroup):
    waiting_direction = State()
    waiting_amount = State()
    confirming = State()


class CategoryStates(StatesGroup):
    choosing_type = State()
    browsing_list = State()
    viewing_category = State()
    waiting_name_for_create = State()
    waiting_name_for_rename = State()


class ReportStates(StatesGroup):
    waiting_custom_date_from = State()
    waiting_custom_date_to = State()


class QuickEntryStates(StatesGroup):
    waiting_category_choice = State()
    waiting_payment_choice = State()


class HistoryStates(StatesGroup):
    waiting_filter_date_from = State()
    waiting_filter_date_to = State()
