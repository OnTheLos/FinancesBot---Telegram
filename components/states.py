from aiogram.fsm.state import State, StatesGroup


class AddCategory(StatesGroup):
    type = State()
    name = State()

class AddOperation(StatesGroup):
    op = State()
    sum = State()
    id = State()
    cat = State()
    comm = State()
    next = State()

class History(StatesGroup):
    category = State()
    operation = State()
    period = State()
    page = State()

class DeleteOperation(StatesGroup):
    opid = State()

class Stats(StatesGroup):
    stats_type = State()
    stats_period = State()
    stats_id = State()

class Balance(StatesGroup):
    balance = State()


class EditCategory(StatesGroup):
    name1 = State()
    oldname = State()

class Distribution(StatesGroup):
    message = State()
    dist_text = State()
    dist_rm = State()
    dist_phid = State()

