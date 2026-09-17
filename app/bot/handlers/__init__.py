from aiogram import Router

from app.bot.handlers import balance, common, history, quick_entry, report, settings, start, transaction, transfer


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(common.router)
    root.include_router(start.router)
    root.include_router(transaction.router)
    root.include_router(transfer.router)
    root.include_router(report.router)
    root.include_router(balance.router)
    root.include_router(history.router)
    root.include_router(settings.router)
    root.include_router(quick_entry.router)
    return root
