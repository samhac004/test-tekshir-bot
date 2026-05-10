from html import escape

def make_channels_list(channels: list) -> str:
    matn = "<b>📢 Majiburiy Obuna</b>\n\n"
    matn += f"<b>Ulangan kanallar:</b> {len(channels)} ta\n\n"
    matn += "➖➖➖➖➖➖➖➖➖➖\n"
    
    for i, channel in enumerate(channels, 1):
        title = escape(channel[1])
        channel_id = channel[2]
        link = channel[3]
        id_link = f"https://t.me/c/{str(channel_id).replace('-100', '')}/1"

        matn += f"{i}. <a href='{link or id_link}'>{title or f'Kanal {i}'}</a>\n"

    return matn


def make_admins_list(admins: list) -> str:
    matn = "<b>👨‍💻 Adminlar</b>\n\n"
    matn += f"<b>Adminlar:</b> {len(admins)} ta\n\n"
    matn += "➖➖➖➖➖➖➖➖➖➖\n"
    
    for i, admin in enumerate(admins, 1):
        full_name = escape(admin[1])
        admin_id = admin[2]

        matn += f"{i}. <a href='tg://user?id={admin_id}'>{full_name}</a>\n"

    return matn


def make_results_list(results: list) -> str:
    matn = ''
    
    for i, result in enumerate(results, 1):
        _, name, res, percent = result

        matn += f"{i}. {name} - {res} ({percent}%)\n"

    return matn

def format_answers(answers_str):
    # answers_str: "abcd" -> "1-a, 2-b, 3-c, 4-d"
    formatted = [f"{i+1}-{char}" for i, char in enumerate(answers_str.lower())]
    return ", ".join(formatted)