from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


def extract_text_from_pdf(path_to_info: str) -> str:
    """
    Читает PDF и возвращает сырой текст.
    """
    output_string = StringIO()
    with open(path_to_info, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
    text = output_string.getvalue()
    return text


def build_sorted_task(info_text: str, lvls_titles) -> dict:
    """
    Парсит сырой текст из PDF и строит структуру:
    {
        1: {
            'Простые': [1, 11, 16, ...],
            'Усложнённые': [...],
            'Сложные': [...]
        },
        2: { ... },
        ...
    }
    """
    sorted_task = {}

    # на всякий случай уберём переносы строк
    info_text = info_text.replace("\n", " ")

    # режем по "Задания группы"
    for block in info_text.split("Задания группы"):
        txt = block.strip()
        if not txt:
            continue

        # первая "группа" до первого числа — это шлак, её пропускаем
        if not txt[0].isdigit():
            continue

        # номер группы (1, 2, 3, ...)
        parts = txt.split()
        try:
            task_group = int(parts[0])
        except ValueError:
            # если по каким-то причинам первый токен не число — пропускаем
            continue

        sorted_task[task_group] = {}
        current_lvl = None

        # остальные токены — слова вида "Простые:", номера задач "123," и т.п.
        task_elements = parts[1:]

        for token in task_elements:
            # убираем хвостовые запятые/точки и т.п.
            clean = token.strip()

            # пробуем распознать заголовок уровня сложности
            for lvl in lvls_titles:
                # в исходном тексте чаще всего "Простые:" — поэтому отрезаем последний символ
                if clean[:-1] == lvl:
                    current_lvl = lvl
                    sorted_task[task_group].setdefault(current_lvl, [])
                    break
            else:
                # если это не заголовок уровня
                if current_lvl and clean[0].isdigit():
                    # забираем только число до запятой
                    num_str = clean.split(",")[0]
                    try:
                        num = int(num_str)
                        sorted_task[task_group][current_lvl].append(num)
                    except ValueError:
                        # если вдруг там мусор — просто пропускаем
                        continue

    return sorted_task


def parse_tasks_from_pdf(path_to_info: str, lvls_titles) -> dict:
    """
    Высокоуровневая функция:
    - читает PDF
    - парсит его
    - возвращает готовый sorted_task
    """
    info_text = extract_text_from_pdf(path_to_info)
    sorted_task = build_sorted_task(info_text, lvls_titles)
    return sorted_task
