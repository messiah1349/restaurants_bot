import pandas as pd
import matplotlib.pyplot as plt

from typing import Iterable

from telebot import types

def create_inline_keyboard(button_texts: Iterable[str], callback_values: Iterable[str]) -> types.InlineKeyboardMarkup:
    assert len(button_texts) == len(callback_values)
    keyboard = types.InlineKeyboardMarkup()
    for button, callback in zip(button_texts, callback_values):
        button = types.InlineKeyboardButton(text=button, callback_data=callback)
        keyboard.add(button)
    return keyboard


def create_keyboard(texts: Iterable[str]) -> types.ReplyKeyboardMarkup:
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=False, one_time_keyboard=True)
    for text in texts:
        keyboard.add(text)

    return keyboard


def save_table_as_image(df: pd.DataFrame,
                        plot_index: bool,
                        output_file: str) -> None:
    fig, ax = plt.subplots()

    fig.patch.set_visible(False)
    ax.axis('off')
    ax.axis('tight')

    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center',
        rowLabels=df.index if plot_index else None
    )

    table.set_fontsize(12)
    table.scale(1, 2)
    fig.tight_layout()

    plt.savefig(
        output_file,
        bbox='tight',
        edgecolor=fig.get_edgecolor(),
        facecolor=fig.get_facecolor(),
        dpi=250
    )
