def get_avg_mark_by_tickets(tickets, lvls, target_mark):
    """
    tickets: {
        ticket_id: {
            local_task_idx: (task_id, lvl_name)
        }
    }
    lvls: {'Простые': 3, 'Усложнённые': 5, 'Сложные': 7}
    target_mark: целевая средняя сложность (например, 5)
    """
    tickets_stats = {}
    total_mark = 0
    total_error = 0
    max_error = 0

    for ticket_id, tasks in tickets.items():
        # считаем среднюю сложность билета
        total_mark_ticket = 0
        tasks_cnt = len(tasks)

        for _, (task_id, lvl_name) in tasks.items():
            task_mark = lvls[lvl_name]
            total_mark_ticket += task_mark

        ticket_mark = total_mark_ticket / tasks_cnt
        ticket_error = abs(target_mark - ticket_mark)

        tickets_stats[ticket_id] = {
            "mark": ticket_mark,
            "error": ticket_error,
        }

        total_mark += ticket_mark
        total_error += ticket_error
        max_error = max(max_error, ticket_error)

    tickets_cnt = len(tickets)

    return {
        "avg_mark": total_mark / tickets_cnt,
        "avg_error": total_error / tickets_cnt,
        "max_error": max_error,
        "tickets": tickets_stats,
    }
