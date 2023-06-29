from telebot.types import CallbackQuery, Message

from actions import assign_ships, get_user_by_id, attack_cell
from bot_init import bot, parties
from helpers import cells_set, get_stage_ship_decks_1_text, stage_2_pl_1_text, stage_2_pl_2_text
from party import Party
from player_profile import PlayerProfile as Pl, PlayerNumber as Pl_num


def send_start_to_play_message(message: Message):
    if len(parties) == 0 or len(parties[len(parties) - 1].players) == 2:
        cur_party = Party()
        parties.append(cur_party)
    else:
        cur_party = parties[len(parties) - 1]

    if len(cur_party.players) == 0:
        bot.send_message(message.chat.id, 'Создание новой партии')
        pl_1 = Pl(message.chat.id)
        pl_1.party = cur_party
        cur_party.players.append(pl_1)
        pl_1.player_number = Pl_num.first
        bot.send_message(message.chat.id, 'Вы первый. Ожидайте второго игрока')
    elif len(cur_party.players) == 1:
        pl_2 = Pl(message.chat.id)
        pl_2.party = cur_party
        pl_2.enemy = cur_party.players[0]
        cur_party.players[0].enemy = pl_2
        cur_party.players.append(pl_2)
        pl_2.player_number = Pl_num.second
        bot.send_message(message.chat.id, 'Вы второй.')
        cur_party.stage.v = 1
        for p in cur_party.players:
            p.stage_assign_decks = 1

        # TODO асинхронно надо отправлять
        bot.send_message(
            cur_party.players[0].player_id,
            get_stage_ship_decks_1_text(cur_party.players[0]), parse_mode='html')
        bot.send_message(
            cur_party.players[1].player_id,
            get_stage_ship_decks_1_text(cur_party.players[0]), parse_mode='html')
    else:
        bot.send_message(message.chat.id, 'Создание новой партии')


@bot.message_handler(commands=['start'])  # handle the command "start"
def start_welcome(message):
    msg = "Привет, " + message.from_user.first_name + "!\n" + \
          "Это бот для игры в морской бой\n" + \
          "Ты можешь послать мне следующие команды:\n" + \
          "1) /info, чтобы узнать информацию о боте\n" + \
          "2) /play, чтобы поиграть с соперником"
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['info'])  # handle the command "info"
def send_info_message(message):
    msg = "Этого бота создал [этот](tg://user?id={416544613}) пользователь Telegram.\n" \
          "[VK](vk.com/id46566190)\n" \
          "[Instagram](instagram.com/dmitrygurylev/)"
    bot.send_message(message.chat.id, msg, parse_mode='Markdown')


@bot.message_handler(commands=['rules'])  # handle the command "rules"
def send_rules_message(message):
    msg = "Правила игры:\n" \
          "Игровое поле — квадрат 10×10.\n\n" \
          "Число кораблей:\n" \
          "1 корабль — ряд из 4 клеток («четырёхпалубный»)\n" \
          "2 корабля — ряд из 3 клеток («трёхпалубные»)\n" \
          "3 корабля — ряд из 2 клеток («двухпалубные»)\n" \
          "4 корабля — 1 клетка («однопалубные»)\n\n" \
          "Игрок, выполняющий ход, совершает выстрел — пишет координаты клетки, " \
          "в которой, по его мнению, находится корабль противника, например, «В1».\n" \
          "Если выстрел пришёлся в клетку, не занятую ни одним кораблём противника, " \
          "то следует ответ «Мимо!» и стрелявший игрок ставит на чужом квадрате в этом месте точку. " \
          "Право хода переходит к сопернику.\n" \
          "Если выстрел пришёлся в клетку, где находится многопалубный корабль (размером больше чем 1 клетка), " \
          "то следует ответ «Ранил(а)!». " \
          "Стрелявший игрок ставит на чужом поле в эту клетку крестик, " \
          "а его противник ставит крестик на своём поле также в эту клетку. " \
          "Стрелявший игрок получает право на ещё один выстрел.\n" \
          "Если выстрел пришёлся в клетку, где находится однопалубный корабль, " \
          "или последнюю непоражённую клетку многопалубного корабля, " \
          "то следует ответ «Убил(а)!». Оба игрока отмечают потопленный корабль на листе. " \
          "Стрелявший игрок получает право на ещё один выстрел.\n\n" \
          "Победителем считается тот, кто первым потопит все 10 кораблей противника"
    bot.send_message(message.chat.id, msg)


@bot.message_handler(commands=['play'])  # handle the command "play"
def start_welcome(message):
    send_start_to_play_message(message)


@bot.message_handler(content_types=['text'])  # handle with text
def handle_text(message):
    message_text_array = message.text.split()

    # match message_text_array[0]:
    player = get_user_by_id(message.chat.id)
    if player.stage_assign_decks != 0:
        assign_ships(message)
    elif message_text_array[0].lower() in cells_set:
        attack_cell(message)
    else:
        "ЗАГЛУШКА"


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: CallbackQuery):
    if call.data == "commit_ships":
        current_player = get_user_by_id(call.from_user.id)
        current_player.stage_assign_decks = 0
        current_player.ready_to_play = True
        current_player.turn = True
        cur_party = current_player.party

        enemy = current_player.enemy

        first_player = current_player if current_player.player_number == Pl_num.first else enemy

        if enemy.ready_to_play:
            cur_party.stage.v = 2
            bot.send_message(current_player.player_id, 'Принято')
            if current_player == first_player:
                # TODO асинхронно надо отправлять
                bot.send_message(current_player.player_id, stage_2_pl_1_text(current_player), parse_mode='html')
                bot.send_message(enemy.player_id, stage_2_pl_2_text(enemy), parse_mode='html')
            else:
                # TODO асинхронно надо отправлять
                bot.send_message(enemy.player_id, stage_2_pl_1_text(enemy), parse_mode='html')
                bot.send_message(current_player.player_id, stage_2_pl_2_text(current_player), parse_mode='html')
        else:
            if current_player == first_player:
                bot.send_message(current_player.player_id, 'Принято. Дождитесь второго игрока')
            else:
                bot.send_message(current_player.player_id, 'Принято. Дождитесь первого игрока')
    elif call.data == "reassign_ships":
        current_player = get_user_by_id(call.from_user.id)
        current_player.stage_assign_decks = 1
        current_player.remove_ship_assignation()
        bot.send_message(
            call.from_user.id,
            get_stage_ship_decks_1_text(current_player),
            parse_mode='html')


bot.polling(non_stop=True)
