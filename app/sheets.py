import json
import pygsheets

from datetime import date

gc = pygsheets.authorize(service_file='creds.json')
spreadsheet_id = '1DSXs_7YH51oNATfTlfjx2lJjaCsk95crOC7zJgM1TM8'


def get_dict_id():
    """
    Получает словарь в котором ключи это id техников, а значения - их инициалы.
    :return: словарь
    """
    with open('id.json', 'r', encoding='UTF-8') as f:
        dict_id = json.loads(f.read())

    return dict_id


def creat_total_json():
    """
    Создает файл total.json. Словарь из инициалов техников и присваивает каждому нулевое значение в начале дня.
    :return: True
    """
    dict_id_new = get_dict_id()
    total = {}
    for initial in dict_id_new.values():
        total.update({initial: [0, 0]})

    with open('total.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(total, ensure_ascii=False))

    return True


def append_worker(id_worker, initial):
    """
    Добавляет техника и его инициалы в файл id.json
    :param id_worker: str
    :param initial: str
    :return: True
    """
    with open('id.json', 'r', encoding='UTF-8') as f:
        dict_id = json.loads(f.read())
        dict_id.update({id_worker: initial})

    with open('id.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(dict_id, ensure_ascii=False))

    with open('total.json', 'r', encoding='UTF-8') as file:
        total = json.loads(file.read())
        total.update({initial: [0, 0]})

    with open('total.json', 'w', encoding='UTF-8') as file:
        file.write(json.dumps(total, ensure_ascii=False))

    return True


def delete_worker(id_worker):
    """
    Удаляет техника из файла id.json
    :param id_worker: str
    :return: True
    """
    with open('id.json', 'r', encoding='UTF-8') as f:
        dict_id = json.loads(f.read())
        dict_id.pop(id_worker)

    with open('id.json', 'w', encoding='UTF-8') as f:
        f.write(json.dumps(dict_id, ensure_ascii=False))

    return True


def show_workers():
    """
    Создает список текущих техников и файла id.json
    :return: dict
    """
    with open('id.json', 'r', encoding='UTF-8') as f:
        workers = json.loads(f.read())

    return workers


def get_cell(car):
    """
    Получает адрес ячейки для записи значени
    :param car: str
    :return: str адрес ячейки или False
    """
    today = date.today().strftime('%d.%m.%y')
    try:
        row = gc.get_range(spreadsheet_id, 'B1:B500', 'COLUMNS')[0].index(car) + 1
        col = gc.get_range(spreadsheet_id, 'A1:1')[0].index(today) + 1  
    except ValueError:
        return False
    cell = pygsheets.Address((row, col)).label

    return cell


def write_value(cell: str, val: str, initials: str):
    """
    Делает запись в таблицу о заправке или мойке машины. Также делает запись в файл total.json изменяя значение техника
    :param cell: str
    :param val: str
    :param initials: str
    :return: True or False
    """
    flg = False
    with open('total.json', 'r', encoding='UTF-8') as f:
        total = json.loads(f.read())
    if val == 'м':
        flg = True
    if initials in total:
        if val == 'м':
            total[initials][0] += 1
        else:
            total[initials][1] += float(val)

    else:
        if val == 'м':
            total.update({initials: [1, 0]})
        else:
            total.update({initials: [0, float(val)]})

    with open('total.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(total, ensure_ascii=False))

    data = gc.sheet.values_get(spreadsheet_id=spreadsheet_id,
                               value_range=f'{cell}:{cell}',
                               major_dimension='DIMENSION_UNSPECIFIED')
    if 'values' not in data:
        val = initials + ' ' + val
    else:
        init = data['values'][0][0].split(' ')[0]
        data_val = data['values'][0][0].split()[1]  # str
        if initials == init:
            if data_val.replace('.', '').isdigit():
                val = f'{init} м {data_val}'
            else:
                val = f'{init} м {val}'
        else:
            if data_val.replace('.', '').isdigit():
                val = f'{initials} м {init} {data_val}'
            else:
                val = f'{init} м {initials} {val}'

    gc.sheet.values_batch_update(spreadsheet_id=spreadsheet_id,
                                 body={'range': f'{cell}:{cell}',
                                       'majorDimension': 'DIMENSION_UNSPECIFIED',
                                       'values': [[val]]})

    if flg:
        sh = gc.open_by_key(spreadsheet_id)
        wks = sh[0]
        c = wks.cell(cell)
        c.unlink()
        c.color = (1.0, 1.0, 0.0, 1.0)
        c.link(wks, True)

    return True


def start_car(cell):
    sh = gc.open_by_key(spreadsheet_id)
    wks = sh[0]
    c = wks.cell(cell)
    c.unlink()
    c.color = (1.0, 0.0, 0.0, 1.0)
    c.link(wks, True)

    return True


def write_in_bak(cell: str, value: str, initials: str) -> bool:
    data = gc.sheet.values_get(spreadsheet_id=spreadsheet_id,
                               value_range=f'{cell}:{cell}',
                               major_dimension='DIMENSION_UNSPECIFIED')
    if 'values' not in data:
        value_for_write = initials + ' ' + value
    else:
        old_value = data['values'][0][0].split()[1]
        old_initials = data['values'][0][0].split()[0]
        value_for_write = f'{initials} {float(old_value) + float(value)}'
    gc.sheet.values_batch_update(spreadsheet_id=spreadsheet_id,
                                 body={'range': f'{cell}:{cell}',
                                       'majorDimension': 'DIMENSION_UNSPECIFIED',
                                       'values': [[value_for_write]]})

    with open('total.json', 'r', encoding='UTF-8') as f:
        total = json.loads(f.read())

    if initials in total:
        total[initials][1] += float(value)

        with open('total.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(total, ensure_ascii=False))

    return True


def get_cars_to_clear():
    """
    Создает список машин, которые необоходимо помыть. Берет машины которые не упоминались в течении 14 дней.
    :return: str
    """
    today = date.today().strftime('%d.%m.%y')
    try:
        col = gc.get_range(spreadsheet_id, 'A1:1')[0].index(today) + 1 
    except ValueError:
        return False
    cell = pygsheets.Address((150, col)).label
    if col > 14:
        cell2 = pygsheets.Address((4, col - 14)).label
    else:
        return 'Ошибка'
    data = gc.sheet.values_get(spreadsheet_id=spreadsheet_id,
                               value_range=f'{cell2}:{cell}',
                               major_dimension='DIMENSION_UNSPECIFIED')
    cars_in_table = gc.sheet.values_get(spreadsheet_id=spreadsheet_id,
                                        value_range='B4:B500')
    cnt = 0
    cars = []

    for list_values in data['values']:
        flg = 0
        for value in list_values:
            value = value.split()
            if value.count('м') > 0:  # если есть м
                flg = 1
                break
        if flg == 0:
            try:
                cars.append(cars_in_table['values'][cnt][0])
            except IndexError:
                pass
        cnt += 1

    result = 'Рекомендуется помыть машины: '
    for car in cars:
        result += f'{car}, '

    return result[:-2]


def get_fuel_and_clear():
    """
    Подсчитывает количество помытых машин и заправленного топлива
    :return: str or False
    """
    today = date.today().strftime('%d.%m.%y')

    try:
        col = gc.get_range(spreadsheet_id, 'A1:1')[0].index(today) + 1
    except ValueError:
        return False

    cell1 = pygsheets.Address((4, col)).label
    cell2 = pygsheets.Address((150, col)).label
    cell3 = pygsheets.Address((3, col)).label
    data = gc.sheet.values_get(spreadsheet_id=spreadsheet_id,
                               value_range=f'{cell1}:{cell2}',
                               major_dimension='COLUMNS')
    fuels = 0
    cnt = 0
    if 'values' in data:
        for val in data['values'][0]:
            val = val.split()
            if len(val) == 2:
                if val[-1].replace('.', '').isdigit():
                    fuels += float(val[1])
                else:
                    cnt += 1
            elif len(val) == 3:
                if val[-1].replace('.', '').isdigit():
                    fuels += float(val[-1])
                cnt += 1

            elif len(val) == 4:
                if val[-1].replace('.', '').isdigit():
                    fuels += float(val[-1])
                cnt += 1

    data1 = gc.sheet.values_get(spreadsheet_id=spreadsheet_id,
                                value_range=f'{cell3}:{cell3}',
                                major_dimension='COLUMNS')
    if 'values' in data1:
        tub = data1['values'][0][0]
    else:
        tub = 0
    result = f'Машин помыто {cnt}, заправлено {fuels:.2f}. Бак: {tub}'

    return result


def get_total_day():
    """
    Создает строку в которой перечисляет техников и их работу: сколько заправелнно и помыто машин.
    :return: str
    """
    with open('total.json', 'r', encoding='UTF-8') as f:
        dict_total = json.loads(f.read())

    total = 'Итог дня:'
    for worker, value in dict_total.items():
        total += f'\n{worker}: машин помыто {value[0]}, заправленно: {value[1]:.2f}'

    return total
