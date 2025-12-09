from collections import defaultdict
import random as rn

# сюда подключаешь свои функции:
from service.load_data import parse_tasks_from_pdf
from service.create_tickets_pack import  get_size_sorted_task
from service.create_tickets_pack import main_pipeline
from service.stats import get_avg_mark_by_tickets
# Я их ниже не дублирую, чтобы не засорять пример.


def help_command():
    rules = """Доступные команды:
  help
    Показать это сообщение.

  set_limits:<путь к файлу PDF с ограничениями>
    Пример: set_limits:Ограничения.pdf
    Запоминает путь к файлу с описанием задач.

  set_lvls:<описание уровней>
    Пример: set_lvls:Простые=3, Усложнённые=5, Сложные=7
    Задаёт уровни сложности и их численные значения.

  parse
    Читает файл ограничений (set_limits) и парсит задачи.
    Должны быть заданы и путь, и уровни сложности.

  create_tickets:<кол-во билетов>,<сложность>
    Пример: create_tickets:50,5
    Генерирует билеты и выводит базовую информацию.
  
  stats
    Показывает статистику сложности по последним сгенерированным билетам
    (использует последнюю целевую сложность).

  stats:<сложность>
    То же, но считает отклонения относительно указанной сложности.

  exit / quit
    Выход.
"""
    return rules


def unknown_command():
    return "Неизвестная команда. Введите 'help' для списка команд."


def parameters_error(e):
    return f"Некорректные параметры команды: {e}"


def read_command():
    line = input("Введите команду: ").strip()
    if not line:
        raise ValueError("Пустая команда")

    if ":" in line:
        command, params = line.split(":", 1)
        return command.strip(), params.strip()
    else:
        return line.strip(), ""


def parse_lvls(params: str):
    if not params:
        raise ValueError("Не переданы уровни сложности")
    parts = [p.strip() for p in params.split(",")]
    lvls = {}
    for part in parts:
        if "=" not in part:
            raise ValueError(f"Ожидается формат Имя=Число, получено: '{part}'")
        name, value = part.split("=", 1)
        name = name.strip()
        try:
            value = float(value.strip())
        except ValueError:
            raise ValueError(f"Не удалось преобразовать '{value}' к числу")
        lvls[name] = value
    lvls_titles = list(lvls.keys())
    return lvls_titles, lvls

def parse_stats_params(params: str, last_mark):
    """
    Если params пустой -> используем last_mark.
    Если указан параметр -> пытаемся распарсить float.
    """
    if not params:
        if last_mark is None:
            raise ValueError("Сложность не указана и нет последнего значения mark. Используйте stats:<сложность>")
        return last_mark

    try:
        mark = float(params.strip())
    except ValueError:
        raise ValueError(f"Некорректная сложность для stats: '{params}'")
    return mark


def parse_create_tickets_params(params: str):
    if not params:
        raise ValueError("Нужно указать: <кол-во билетов>,<сложность>")
    parts = [p.strip() for p in params.split(",")]
    if len(parts) != 2:
        raise ValueError("Ожидается два параметра: <кол-во билетов>,<сложность>")
    try:
        tickets_cnt = int(parts[0])
    except ValueError:
        raise ValueError(f"Некорректное число билетов: '{parts[0]}'")
    try:
        mark = float(parts[1])
    except ValueError:
        raise ValueError(f"Некорректная сложность: '{parts[1]}'")
    return tickets_cnt, mark


def main_loop():
    # состояние CLI
    state = {
        "limits_path": None,
        "lvls_titles": None,
        "lvls": None,
        "sorted_task": None,
        "size_sorted_task": None,
        "tickets": None,
        "last_mark": None,

    }

    print("CLI генератора билетов. Введите 'help' для списка команд.")
    while True:
        try:
            command, params = read_command()
        except Exception as e:
            print(parameters_error(e))
            continue

        cmd = command.lower()

        try:
            if cmd == "help":
                print(help_command())

            elif cmd == "set_limits":
                if not params:
                    raise ValueError("Не указан путь к файлу")
                state["limits_path"] = params
                print(f"Путь к файлу с ограничениями установлен: {params}")

            elif cmd == "set_lvls":
                lvls_titles, lvls = parse_lvls(params)
                state["lvls_titles"] = lvls_titles
                state["lvls"] = lvls
                print(f"Уровни сложности заданы: {lvls}")

            elif cmd == "parse":
                if not state["limits_path"]:
                    raise ValueError("Сначала задайте путь через set_limits")
                if not state["lvls_titles"] or not state["lvls"]:
                    raise ValueError("Сначала задайте уровни через set_lvls")

                # Здесь ты вызываешь свой реальный парсер PDF:
                sorted_task = parse_tasks_from_pdf(state["limits_path"], state["lvls_titles"])
                size_sorted_task = get_size_sorted_task(sorted_task, state["lvls"])
                # Для примера поставим заглушки:
                state["sorted_task"] = sorted_task
                state["size_sorted_task"] = size_sorted_task


                # TODO: заменить на реальные вызовы
                # state["sorted_task"] = ...
                # state["size_sorted_task"] = ...

            elif cmd == "create_tickets":
                if state["sorted_task"] is None or state["size_sorted_task"] is None:
                    raise ValueError("Сначала выполните команду parse")
                if state["lvls"] is None:
                    raise ValueError("Сначала задайте уровни через set_lvls")

                tickets_cnt, mark = parse_create_tickets_params(params)

                tickets = main_pipeline(
                    tickets_cnt=tickets_cnt,
                    mark=mark,
                    all_tasks=state["sorted_task"],
                    all_tasks_lvls_cnt=state["size_sorted_task"],
                    lvls=state["lvls"],
                )

                print(f"Сгенерировано {len(tickets)} билетов.")
                # Можно вывести краткую инфу по первым нескольким билетам:
                state["tickets"] = tickets  # <--- сохраняем
                state["last_mark"] = mark

                for t_id in list(tickets.keys()):
                    print(f"Билет {t_id}: {tickets[t_id]}")

            elif cmd == "stats":
                if state["tickets"] is None:
                    raise ValueError("Билеты ещё не сгенерированы. Сначала выполните create_tickets")
                if state["lvls"] is None:
                    raise ValueError("Сначала задайте уровни через set_lvls")

                target_mark = parse_stats_params(params, state["last_mark"])

                stats = get_avg_mark_by_tickets(
                    tickets=state["tickets"],
                    lvls=state["lvls"],
                    target_mark=target_mark,
                )

                print(f"Целевая сложность: {target_mark}")
                print(f"Средняя сложность по билетам: {stats['avg_mark']:.3f}")
                print(f"Средняя ошибка по билетам: {stats['avg_error']:.3f}")
                print(f"Максимальное отклонение сложности билета: {stats['max_error']:.3f}")

                print("Примеры билетов:")
                for ticket_id in list(stats["tickets"].keys())[:5]:
                    t = stats["tickets"][ticket_id]
                    print(f"  Билет {ticket_id}: сложность = {t['mark']:.3f}, ошибка = {t['error']:.3f}")

            elif cmd in ("exit", "quit"):
                print("Выход.")
                break

            else:
                print(unknown_command())

        except Exception as e:
            print(parameters_error(e))


if __name__ == "__main__":
    main_loop()
