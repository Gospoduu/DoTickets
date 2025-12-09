from collections import defaultdict
import random as rn

def get_size_sorted_task(sorted_task, lvls):

    size_sorted_task = {}
    for task in sorted_task:
        avg_lvl = 0
        task_cnt = 0
        size_sorted_task[task] = {}
        for task_lvl in sorted_task[task]:
            ln = len(sorted_task[task][task_lvl])
            size_sorted_task[task][task_lvl] = ln
            task_cnt += ln
            avg_lvl += lvls[task_lvl] * ln
        size_sorted_task[task]["avg"] = round(avg_lvl / task_cnt, 3)
    return size_sorted_task


def get_ticket_list_by_avg(task_dict_cnt, lvls, tickets_cnt, avg):
    # Инициализация ошибок для каждой сложности
    task_dict_cnt = task_dict_cnt.copy()
    task_dict_cnt.pop("avg", None)
    total_available_tasks = sum(task_dict_cnt.values())
    if total_available_tasks < tickets_cnt:
        raise ValueError(f"Недостаточно задач! Всего доступно {total_available_tasks }, требуется {tickets_cnt}.")
    lvls = lvls.copy()


    abs_lvls_error = {lvl: abs(avg - lvls[lvl]) for lvl in lvls}
    lvls_error = {lvl: avg - lvls[lvl] for lvl in lvls}

    # Сортируем задачи по сложности (от меньшего отклонения от avg)
    sorted_error = sorted(lvls, key=lambda lvl: abs_lvls_error[lvl])
    not_chosen = tickets_cnt
    chosen_lvls = defaultdict(int)

    # Основной цикл
    while not_chosen > 0:
        # Печать текущего состояния для отладки
        # print(f"avg = {avg}, s_e = {sorted_error}")

        # Проверка на пустой список
        if not sorted_error:
            break

        # Берём задачу с минимальной ошибкой
        task = sorted_error[0]  # Берём первый элемент в отсортированном списке
        task_cnt = task_dict_cnt.get(task, 0)

        # Если задача исчерпана, удаляем её из всех структур данных
        if task_cnt == 0:
            sorted_error.pop(0)  # Убираем её из отсортированного списка
            lvls_error.pop(task, None)
            abs_lvls_error.pop(task, None)
            lvls.pop(task, None)  # Удаляем также из lvls, чтобы избежать выбора
            continue

        # Выбираем задачу и уменьшаем её количество
        chosen_lvls[task] += 1
        task_dict_cnt[task] -= 1
        not_chosen -= 1

        # Обновляем среднее значение, учитывая только выбранные задачи

        avg+=lvls_error[task]

        # Пересчитываем ошибки для всех уровней на основе обновленного среднего
        abs_lvls_error = {lvl: abs(avg - lvls[lvl]) for lvl in lvls}

        # Обновляем список уровней с минимальной ошибкой
        sorted_error = sorted(lvls, key=lambda lvl: abs_lvls_error[lvl])

    return chosen_lvls


def create_task_pack(lvls_tasks_cnt, all_tasks):
    lvls_tasks_cnt = lvls_tasks_cnt.copy()  # Копируем словарь lvls_tasks_cnt
    all_tasks = all_tasks.copy()  # Копируем словарь all_tasks
    task_pack = []

    # Проходим по каждому уровню сложности
    for task_lvl, task_cnt in lvls_tasks_cnt.items():
        task_lvl_pack = all_tasks[task_lvl][:]  # Создаём копию списка задач для текущего уровня сложности

        all_tasks_cnt = len(task_lvl_pack)
        print(f"all tasks cnt {all_tasks_cnt}")
        # Выбираем нужное количество задач
        for i in range(task_cnt):
            if all_tasks_cnt == 0:  # Если задач не осталось, пропускаем
                break
            rn_task_idx = rn.randint(0, all_tasks_cnt - 1)  # Генерируем случайный индекс
            chosen_task = task_lvl_pack.pop(rn_task_idx)  # Удаляем задачу из копии списка
            task_pack.append((chosen_task, task_lvl))  # Добавляем задачу и её уровень сложности в итоговый пакет
            all_tasks_cnt -= 1  # Обновляем количество оставшихся задач

    rn.shuffle(task_pack)  # Перемешиваем итоговый список задач
    return task_pack

def create_task_bank(mark, tickets_cnt, size_sorted_task, sorted_task, lvls):
    task_bank = {}
    for task in size_sorted_task:
        chosen_tasks_cnt = get_ticket_list_by_avg(size_sorted_task[task], lvls, tickets_cnt, mark)
        pack = create_task_pack(chosen_tasks_cnt, sorted_task[task])
        task_bank[task] = pack
    return task_bank


def create_tickets_balanced(task_bank, tickets_cnt, lvls, mark):
    # Инициализируем билеты
    tickets = {i + 1: {} for i in range(tickets_cnt)}
    # Текущая сумма сложности и кол-во задач в каждом билете
    sum_mark = {i + 1: 0 for i in range(tickets_cnt)}
    cnt_tasks = {i + 1: 0 for i in range(tickets_cnt)}

    # Идём по темам (группам заданий)
    for task in task_bank:
        candidates = task_bank[task]  # список [(task_id, lvl_name), ...], длины tickets_cnt

        # Посчитаем сложность для каждого кандидата
        candidates_with_mark = [
            (task_id, lvl_name, lvls[lvl_name]) for (task_id, lvl_name) in candidates
        ]

        # Сортируем билеты по текущей средней сложности (от самых "лёгких" к "тяжёлым")
        ticket_order = sorted(
            tickets.keys(),
            key=lambda t_id: (sum_mark[t_id] / cnt_tasks[t_id]) if cnt_tasks[t_id] > 0 else 0
        )

        # Сортируем задания по сложности (от сложных к простым)
        candidates_with_mark.sort(key=lambda x: x[2], reverse=True)

        # Раздаём: самым лёгким билетам — самые сложные задачи
        for (ticket_id, (task_id, lvl_name, task_mark)) in zip(ticket_order, candidates_with_mark):
            tickets[ticket_id][task] = (task_id, lvl_name)
            sum_mark[ticket_id] += task_mark
            cnt_tasks[ticket_id] += 1

    return tickets

def main_pipeline(tickets_cnt,mark, all_tasks, all_tasks_lvls_cnt, lvls):
    task_bank = create_task_bank(mark, tickets_cnt, all_tasks_lvls_cnt,all_tasks, lvls)
    tickets = create_tickets_balanced(task_bank, tickets_cnt, lvls, mark)
    return tickets


