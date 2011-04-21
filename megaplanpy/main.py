#-------------------------------------------------------------------------------
# Name:        main
# Purpose:
#
# Author:      Sergey Pikhovkin (s@pikhovkin.ru)
#
# Created:     27.01.2011
# Copyright:   (c) Sergey Pikhovkin 2011
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import md5, hmac
from hashlib import sha1
import base64
from datetime import datetime
from rfc822 import formatdate, mktime_tz, parsedate_tz
from urllib import urlencode

from client import APIClient
from data import JSON2Obj


class AttributeError(Exception):
    pass


class ClientError(Exception):
    pass


class Megaplan(object):
    """
    """
    debug = False

    HOST = '{account}.megaplan.ru/'
    SIGNATURE = '{method}\n{md5content}\n{contenttype}\n{date}\n{host}{uri}'

    _CommonApi = 'BumsCommonApiV01/'
    _ProjectApi = 'BumsProjectApiV01/'
    _StaffApi = 'BumsStaffApiV01/'
    _TaskApi = 'BumsTaskApiV01/'

    AUTHORIZE = _CommonApi + 'User/'
    COMMENT = _CommonApi + 'Comment/'
    DEPARTMENT = _StaffApi + 'Department/'
    EMPLOYEE = _StaffApi + 'Employee/'
    FAVORITE = _CommonApi + 'Favorite/'
    INFORMER = _CommonApi + 'Informer/'
    PROJECT = _ProjectApi + 'Project/'
    SEARCH = _CommonApi + 'Search/'
    SEVERITY = _TaskApi + 'Severity/'
    TASK = _TaskApi + 'Task/'

    code = 'utf-8'

    _FolderType = ('incoming', 'responsible', 'executor', 'owner', 'auditor',
        'all',)
    _StatusType = ('actual', 'inprocess', 'new', 'overdue', 'done', 'delayed',
        'completed', 'failed', 'any',)
    _ActionType = ('act_accept_task', 'act_reject_task', 'act_accept_work',
        'act_reject_work', 'act_done', 'act_pause', 'act_resume', 'act_cancel',
        'act_expire', 'act_renew',)
    _SubjectType = ('task', 'project',)
    _OrderType = ('asc', 'desc',)

    @property
    def Account(self):
        return self._Account

    @Account.setter
    def Account(self, account):
        self._Account = account
        self._host = self.HOST.format(account=account)
        self._MPQuery = 'https://{host}{uri}'.format(host=self._host, uri='{uri}')

    @property
    def Login(self):
        return self._Login

    @Login.setter
    def Login(self, login):
        self._Login = login

    @property
    def Password(self):
        return self._Password

    @Password.setter
    def Password(self, password):
        self._Password = password

    def __init__(self, account='', login='', password=''):
        self.Account, self.Login, self.Password = account, login, password

        self._client = APIClient()
        self._data = str()

        self._AccessId = str()
        self._SecretKey = str()
    # / def __init__(self):

    def _TimeAsRfc822(self, dt):
        return formatdate(mktime_tz(parsedate_tz(dt.strftime('%a, %d %b %Y %H:%M:%S'))))
    # /

    def _GetResponseObject(f):
        """
        Decorator
        """
        def wrapper(self):
            obj = JSON2Obj(self._data)
            if 'error' == obj.status['code']:
                if 'message' in obj.status:
                    raise Exception(obj.status['message'])
            return f(self, obj)

        return wrapper
    # / def _GetResponseObject(f):

    @_GetResponseObject
    def _AuthorizeHandle(self, obj):
        self._AccessId = obj.data['AccessId']
        self._SecretKey = obj.data['SecretKey']

        if self.debug:
            self._MPQuery = 'http://{host}'.format(host=self._host) + '{uri}'
    # /

    def _Authorize(self):
        uri = self.AUTHORIZE + 'authorize.api'
        md5pass = md5.new(self.Password).hexdigest()
        params = {'Login': self.Login, 'Password': md5pass}
        self._data = \
            self._client.Request(self._MPQuery.format(uri=uri), params)
        self._AuthorizeHandle()

    def _Auth(f):
        def wrapper(self, *args, **kwargs):
            if (self._AccessId == '') or (self._SecretKey == ''):
                self._Authorize()
            return f(self, *args, **kwargs)
        return wrapper
    # /

    def _GetSignature(self, method, uri, params={}):
        self._rfcdate = self._TimeAsRfc822(datetime.now())
        self._md5content = ''
        contenttype = ''
        if 'POST' == method:
            self._md5content = md5.new(urlencode(params)).hexdigest()
            contenttype = 'application/x-www-form-urlencoded'
        sign = {
            'method': method,
            'md5content': self._md5content,
            'contenttype': contenttype,
            'date': self._rfcdate,
            'host': self._host,
            'uri': uri
        }
        q = self.SIGNATURE.format(**sign)
        h = hmac.HMAC(self._SecretKey.encode(self.code), q, sha1)
        return base64.encodestring(h.hexdigest()).strip()
    # /

    def _GetHeaders(self, uri, params={}):
        method = 'GET'
        if params:
            method = 'POST'
        signature = self._GetSignature(method, uri, params)
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru,en-us;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '300',
            'Connection': 'keep-alive',
            'Date': self._rfcdate,
            'X-Authorization': '{0}:{1}'.format(self._AccessId, signature)
        }
        if method == 'GET':
            header['Accept'] = 'application/json'
        elif method == 'POST':
            header['Content-MD5'] = self._md5content
        return header
    # /

    @_GetResponseObject
    def _ResponseHandle(self, obj):
        return obj
    # /

    @_Auth
    def _GetData(self, uri, params={}):
        headers = self._GetHeaders(uri, params)
        self._data = self._client.Request(
            self._MPQuery.format(uri=uri), params=params, headers=headers)
        if self._client.Status in (400, 401, 403, 404, 500):
            raise ClientError(
                '{0} {1}'.format(self._client.Status, self._client.Reason))
        return self._ResponseHandle()
    # /

    def Tasks(self, Folder='all', Status='any', FavoritesOnly=False, Search=''):
        """
        input:
            Folder='all': string = ('incoming' (входящие),
                'responsible' (ответственный), 'executor' (соисполнитель),
                'owner' (исходящие), 'auditor' (аудируемые),
                'all' (все)) # Папка
            Status='any': string = ('actual' (актуальные),
                'inprocess' (в процессе), 'new' (новые),
                'overdue' (просроченные), 'done' (условно завершенные),
                'delayed' (отложенные), 'completed' (завершенные),
                'failed' (проваленные), 'any' (любые)) # Статус
            FavoritesOnly=0: integer = (0, 1) # Только избранное
            Search='': string = 'любая строка' # Строка поиска
        output:
            tasks<array>:
                Id: integer # ID задачи
                Name: string # Название
                Status: string # Статус
                Deadline: datetime # Дедлайн
                Owner: object(Id, Name) # Постановщик (сотрудник)
                Responsible: object(Id, Name) # Ответственный (сотрудник)
                Severity: object(Id, Name) # Важность
                SuperTask: object(Id, Name) # Надзадача
                Project: object(Id, Name) # Проект
                Favorite: integer # В избранном
                TimeCreated: datetime # Время создания
        """
        if (Folder not in self._FolderType) or (Status not in self._StatusType):
            raise AttributeError('Invalid parameter value')

        uri = '{0}list.api?Folder={1}&Status={2}&FavoritesOnly={3}&Search={4}'
        uri = uri.format(self.TASK, Folder, Status, int(FavoritesOnly), Search)
        return self._GetData(uri)
    # /

    def TaskCard(self, Id):
        """
        input:
            Id: integer # ID задачи. Обязательный параметр
        output:
            task:
                Id: integer # ID задачи
                Name: string # Название
                Statement: string # Суть задачи
                Status: string # Статус
                Deadline: datetime # Дедлайн
                DeadlineType: string # Тип дедлайна
                Owner: object (Id, Name) # Постановщик (сотрудник)
                Responsible: object (Id, Name) # Ответственный (сотрудник)
                Executors: array<object> (Id, Name) # Соисполнители (сотрудники)
                Auditors: array<object> (Id, Name) # Аудиторы (сотрудники)
                Severity: object (Id, Name) # Важность
                SuperTask: object (Id, Name) # Надзадача
                Project: object (Id, Name) # Проект
                SubTasks: array<object>(Id, Name, Owner, Responsible, Deadline,
                    Favorite (версия 2011.02+)) # Подзадачи
                Favorite: integer # В избранном
                TimeCreated: datetime # Время создания
                Customer: object(Id, Name, Status, Type) # Заказчик
                    (код, название, статус, тип)
        """
        uri = '{0}card.api?Id={1}'.format(self.TASK, Id)
        return self._GetData(uri)
    # /

    def TaskCreate(self, **kwargs):
        """
        input:
            kwargs:
                Model[Name]: string # Название
                Model[Deadline]: datetime # Дедлайн (дата со временем)
                Model[DeadlineDate]: date # Дедлайн (только дата)
                Model[DeadlineType]: string # Тип дедлайна
                Model[Responsible]: integer # Код ответственного
                Model[Executors]: array<integer> # Коды соисполнителей
                Model[Auditors]: array<integer> # Коды аудиторов
                Model[Severity]: integer # Код важности
                Model[SuperTask]: string # Код надзадачи (если число) или
                    код проекта (если строка в формате ‘p<код проекта>’
                Model[Customer]: integer # Код заказчика
                Model[IsGroup]: integer = (0, 1) # Массовая задача
                    (каждому соисполнителю будет создана своя задача)
                Model[Statement]: string # Суть задачи
        output:
            Id: integer # ID задачи
            Name: string # Название задачи
        """
        uri = '{0}create.api'.format(self.TASK)
        return self._GetData(uri, kwargs)
    # /

    def TaskEdit(self, Id, **kwargs):
        """
        input:
            Id: integer # ID задачи. Обязательный параметр
            kwargs:
                Model[Name]: string # Название
                Model[Deadline]: datetime # Дедлайн (дата со временем)
                Model[DeadlineDate]: date # Дедлайн (только дата)
                Model[DeadlineType]: string # Тип дедлайна
                Model[Owner]: integer # Код постановщика
                Model[Responsible]: integer # Код ответственного
                Model[Executors]: array<integer> # Коды соисполнителей
                Model[Auditors]: array<integer> # Коды аудиторов
                Model[Severity]: integer # Код важности
                Model[SuperTask]: string # Код надзадачи (если число) или
                    код проекта (если строка в формате ‘p<код проекта>’
                Model[Customer]: integer # Код заказчика
                Model[Statement]: string # Суть задачи
        output:
            None
        """
        uri = '{0}edit.api'.format(self.TASK)
        kwargs['Id'] = str(Id)
        self._GetData(uri, kwargs)
    # /

    def TaskAction(self, Id, Action):
        """
        input:
            Id: integer # ID задачи. Обязательный параметр
            Action: string = ('act_accept_task' (принять задачу),
                'act_reject_task' (отклонить задачу),
                'act_accept_work' (принять работу),
                'act_reject_work' (отклонить работу),
                'act_done' (завершить задачу), 'act_pause' (поставить на паузу),
                'act_resume' (возобновить задачу), 'act_cancel' (снять задачу),
                'act_expire' (провалить задачу),
                'act_renew' (возобновить задачу))
        output:
            None
        """
        if (Action not in self._ActionType):
            raise AttributeError('Invalid parameter value')

        uri = '{0}action.api'.format(self.TASK)
        params = {'Id': str(Id), 'Action': Action}
        return self._GetData(uri, params)
    # /

    def TaskAvailableActions(self, Id):
        """
        input:
            Id: integer # ID задачи. Обязательный параметр
        output:
            actions: array

        act_accept_task - исполнитель принимает задачу
        act_reject_task - исполнитель отклоняет задачу
        act_accept_work - постановщик принимает выполненную задачу
        act_reject_work - постановщик отклоняет выполненную задачу
        act_done - исполнитель заканчивает работу, задача условно завершена
        act_pause - временно приостановить выполнение задачи
        act_resume - продолжить выполнение приостановленной задачи
        act_cancel - отменить задачу
        act_expire - провалить задачу
        act_renew - принять ранее отклоненную задачу
        """
        uri = '{0}availableActions.api?Id={1}'.format(self.TASK, Id)
        return self._GetData(uri)
    # /

    def TaskMarkAsFavorite(self, Id, Value=True):
        """
        input:
            Id: integer # ID задачи. Обязательный параметр
            Value: integer = (1 (пометить как избранное),
                0 (убрать из избранного))
        output:
            None
        """
        if Value:
            self.FavoriteAdd('task', Id)
        else:
            self.FavoriteRemove('task', Id)
    # /

    def Projects(self, Folder='all', Status='any', FavoritesOnly=False, Search=''):
        """
        input:
            Folder='all': string = ('incoming' (входящие),
                'responsible' (ответственный), 'executor' (соисполнитель),
                'owner' (исходящие), 'auditor' (аудируемые),
                'all' (все)) # Папка
            Status='any': string = ('actual' (актуальные), 'inprocess' (в процессе),
                'new' (новые), 'overdue' (просроченные),
                'done' (условно завершенные), 'delayed' (отложенные),
                'completed' (завершенные), 'failed' (проваленные),
                'any' (любые)) # Статус
            FavoritesOnly=0: integer = (0, 1) # Только избранное
            Search='': string = 'любая строка' # Строка поиска
        output:
            projects<array>:
                Id: integer # ID проекта
                Name: string # Название
                Status: string # Статус
                Deadline: datetime # Дедлайн
                Owner: object(Id, Name) # Владелец (сотрудник)
                Responsible: object(Id, Name) # Менеджер (сотрудник)
                Severity: object(Id, Name) # Важность
                SuperProject: object(Id, Name) # Надпроект
                Favorite: integer # В избранном
                TimeCreated: datetime # Время создания
        """
        if (Folder not in self._FolderType) or (Status not in self._StatusType):
            raise AttributeError('Invalid parameter value')

        uri = '{0}list.api?Folder={1}&Status={2}&FavoritesOnly={3}&Search={4}'
        uri = uri.format(self.PROJECT, Folder, Status, int(FavoritesOnly), Search)
        return self._GetData(uri)
    # /

    def ProjectCard(self, Id):
        """
        input:
            Id: integer # ID проекта. Обязательный параметр
        output:
            project:
                Id: integer # ID проекта
                Name: string # Название
                Statement: string # Описание проекта
                Status: string # Статус
                Deadline: datetime # Дедлайн
                DeadlineType: string # Тип дедлайна
                Owner: object(Id, Name) # Создатель (сотрудник)
                Responsible: object(Id, Name) # Менеджер (сотрудник)
                Executors: array<object> (Id, Name) # Команда проекта
                    (сотрудники)
                Auditors: array<object> (Id, Name) # Аудиторы (сотрудники)
                Severity: object(Id, Name) # Важность
                SuperProject: object(Id, Name) # Надпроект
                SubProjects: array<object>(Id, Name, Owner, Responsible,
                    Deadline, Favorite (версия 2011.02+)) # Подпроекты
                Tasks: array<object> (Id, Name, Owner, Responsible, Deadline,
                    Favorite (версия 2011.02+)) # Задачи проекта
                TimeCreated: datetime # Время создания
                Customer: object(Id, Name, Status, Type) # Заказчик
                    (код, название, статус, тип)
        """
        uri = '{0}card.api?Id={1}'.format(self.PROJECT, Id)
        return self._GetData(uri)
    # /

    def ProjectCreate(self, **kwargs):
        """
        input:
            kwargs:
                Model[Name]: string # Название
                Model[Deadline]: datetime # Дедлайн (дата со временем)
                Model[DeadlineDate]: date # Дедлайн (только дата)
                Model[DeadlineType]: string # Тип дедлайна
                Model[Responsible]: integer # Код менеджера
                Model[Executors]: array<integer> # Коды участников проекта
                Model[Auditors]: array<integer> # Коды аудиторов
                Model[Severity]: integer # Код важности
                Model[SuperProject]: integer # Код надпроекта
                Model[Customer]: integer # Код заказчика
                Model[Statement]: string # Описание проекта
        output:
            Id: integer # ID проекта
            Name: string # Название проекта

        У сотрудника может не быть прав на создание проекта. В этом случае команда вернет 403-ю ошибку и
        следующий ответ:
        {
          "status":
          {
            "code":"error",
            "message":"You can not create projects"
          }
        }
        Таким образом, эту команду можно использовать не только для создания проекта,
        но и для проверки наличия прав на создание проекта
        (например, чтобы решить, показывать в приложении кнопку "Создать проект" или нет).
        """
        uri = '{0}create.api'.format(self.PROJECT)
        return self._GetData(uri, kwargs)
    # /

    def ProjectEdit(self, Id, **kwargs):
        """
        input:
            Id: integer # ID проекта. Обязательный параметр
            kwargs:
                Model[Name]: string # Название
                Model[Deadline]: datetime # Дедлайн (дата со временем)
                Model[DeadlineDate]: date # Дедлайн (только дата)
                Model[DeadlineType]: string # Тип дедлайна
                Model[Owner]: integer # Код постановщика
                Model[Responsible]: integer # Код менеджера
                Model[Executors]: array<integer> # Коды участников проекта
                Model[Auditors]: array<integer> # Коды аудиторов
                Model[Severity]: integer # Код важности
                Model[SuperProject]: integer # Код надпроекта
                Model[Customer]: integer # Код заказчика
                Model[Statement]: string # Описание проекта
        output:
            None
        """
        uri = '{0}edit.api'.format(self.PROJECT)
        kwargs['Id'] = str(Id)
        self._GetData(uri, kwargs)
    # /

    def ProjectAction(self, Id, Action):
        """
        input:
            Id: integer # ID проекта. Обязательный параметр
            Action: string = ('act_accept_work' (принять работу),
                'act_reject_work' (отклонить работу),
                'act_done' (завершить проект), 'act_pause' (поставить на паузу),
                'act_resume' (возобновить проект), 'act_cancel' (снять проект),
                'act_expire' (провалить проект),
                'act_renew' (возобновить проект))
        output:
            None
        """
        if (Action not in self._ActionType):
            raise AttributeError('Invalid parameter value')

        uri = '{0}action.api'.format(self.PROJECT)
        params = {'Id': str(Id), 'Action': Action}
        return self._GetData(uri, params)
    # /

    def ProjectAvailableActions(self, Id):
        """
        input:
            Id: integer # ID проекта. Обязательный параметр
        output:
            actions: array

        actions:
            act_accept_work - постановщик принимает выполненный проект
            act_reject_work - постановщик отклоняет выполненный проект
            act_done - исполнитель заканчивает работу, проект условно завершен
            act_pause - временно приостановить выполнение проекта
            act_resume - продолжить выполнение приостановленного проекта
            act_cancel - отменить проект
            act_expire - провалить проект
            act_renew - открыть проект заново
        """
        uri = '{0}availableActions.api?Id={1}'.format(self.PROJECT, Id)
        return self._GetData(uri)
    # /

    def ProjectMarkAsFavorite(self, Id, Value=True):
        """
        input:
            Id: integer # ID проекта. Обязательный параметр
            Value: integer = (1 (пометить как избранное),
                0 (убрать из избранного))
        output:
            None
        """
        if Value:
            self.FavoriteAdd('project', Id)
        else:
            self.FavoriteRemove('project', Id)
    # /

    def Severities(self):
        """
        input:
            None
        output:
            Id: integer # ID важности
            Name: string # Название
        """
        uri = '{0}list.api'.format(self.SEVERITY)
        return self._GetData(uri)
    # /

    def Employees(self, Department=0, OrderBy='name', OrderDir='asc'):
        """
        input:
            Department=0: integer # Id отдела
            OrderBy='name': string = ('name', 'department',
                'position') # Параметр для сортировки
            OrderDir='asc': string = ('asc', 'desc') # Направление сортировки
        output:
            employees<array>:
                Id: integer # ID сотрудника
                Name: string # Полное имя
                LastName: string # Фамилия
                FirstName: string # Имя
                MiddleName: string # Отчество
                Position: object(Id, Name) # Должность
                Department: object(Id, Name) # Отдел
                Phones: array # Телефоны
                Email: string # E-mail
                Status: object(Id, Name) # Статус
                TimeCreated: datetime # Время создания
        """
        uri = '{0}list.api?Department={1}&OrderBy={2}&OrderDir={3}'
        uri = uri.format(self.EMPLOYEE, Department, OrderBy, OrderDir)
        return self._GetData(uri)
    # /

    def EmployeeCard(self, Id):
        """
        input:
            Id: integer # ID сотрудника
        output:
            employee:
                Id: integer # ID сотрудника
                Name: string # Полное имя
                LastName: string # Фамилия
                FirstName: string # Имя
                MiddleName: string # Отчество
                Gender: string # Пол
                Position: object(Id, Name) # Должность
                Department: object(Id, Name) # Отдел
                Birthday: date # Дата рождения
                HideMyBirthday: boolean # Скрывать дату рождения
                Age: integer # Возраст
                Phones: array # Телефоны
                Email: string # E-mail
                Icq: string # ICQ
                Skype: string # Skype
                Jabber: string # Jabber
                Address: object(Id, City, Street, House) # Адрес
                Behaviour: string # График работы
                Inn: string # ИНН
                PassportData: string # Паспортные данные
                AboutMe: string # О себе
                ChiefsWithoutMe: array<object>(Id, Name) # Начальники
                SubordinatesWithoutMe: array<object>(Id, Name) # Подчиненные
                Coordinators: array<object>(Id, Name) # Координаторы
                Status: object(Id, Name) # Статус
                AppearanceDay: date # Дата принятия на работу
                FireDay: date # Дата увольнения
                TimeCreated: datetime # Время создания
                Avatar: string # Адрес аватара сотрудника
                Photo: string # Адрес большого фото сотрудника
        """
        uri = '{0}card.api?Id={1}'.format(self.EMPLOYEE, Id)
        return self._GetData(uri)
    # /

    def EmployeeCreate(self, **kwargs):
        """
        input:
            kwargs:
                Model[LastName]: string # Фамилия
                Model[FirstName]: string # Имя
                Model[MiddleName]: string # Отчество
                Model[Gender]: string = ('male', 'femail') # Пол
                Model[Position]: string # Должность. Обязательный параметр
                Model[Birthday]: date # Дата рождения
                Model[HideMyBirthday]: boolean # Скрывать дату рождения
                Model[Email]: string # E-mail
                Model[Icq]: string # ICQ
                Model[Skype]: string # Skype
                Model[Jabber]: string # Jabber
                Model[Behaviour]: string # График работы
                Model[PassportData]: string # Паспортные данные
                Model[Inn]: string # ИНН
                Model[AboutMe]: string # О себе
                Model[Status]: string = ('in-office', 'out-of-office') # Статус
                Model[AppearanceDay]: date # Дата принятия на работу
                Address[City]: string # Город
                Address[Street]: string # Улица
                Address[House]: string # Дом
        output:
            Id: integer # ID сотрудника
            Name: string # Имя сотрудника
        """
        uri = '{0}create.api'.format(self.EMPLOYEE)
        return self._GetData(uri, kwargs)
    # /

    def EmployeeEdit(self, Id, **kwargs):
        """
        input:
            Id: integer # ID сотрудника. Обязательный параметр
            kwargs:
                Model[LastName]: string # Фамилия
                Model[FirstName]: string # Имя
                Model[MiddleName]: string # Отчество
                Model[Gender]: string = ('male', 'femail') # Пол
                Model[Position]: string # Должность
                Model[Birthday]: date # Дата рождения
                Model[HideMyBirthday]: boolean # Скрывать дату рождения
                Model[Email]: string # E-mail
                Model[Icq]: string # ICQ
                Model[Skype]: string # Skype
                Model[Jabber]: string # Jabber
                Model[Behaviour]: string # График работы
                Model[PassportData]: string # Паспортные данные
                Model[Inn]: string # ИНН
                Model[AboutMe]: string # О себе
                Model[Status]: string = ('in-office', 'out-of-office') # Статус
                Model[AppearanceDay]: date # Дата принятия на работу
                Address[City]: string # Город
                Address[Street]: string # Улица
                Address[House]: string # Дом
        output:
            None
        """
        uri = '{0}edit.api'.format(self.EMPLOYEE)
        kwargs['Id'] = str(Id)
        self._GetData(uri, kwargs)
    # /

    def EmployeeAvailableActions(self, Id):
        """
        input:
            Id: integer # ID сотрудника. Обязательный параметр
        output:
            actions: array

        actions:
            act_can_fire - уволить
            act_edit - редактировать
        """
        uri = '{0}availableActions.api?Id={1}'.format(self.EMPLOYEE, Id)
        return self._GetData(uri)
    # /

    def Departments(self):
        """
        input:
            None
        output:
            departments<array>:
                Id: integer # ID отдела
                Name: string # Название отдела
                Head: object(Id, Name) # Начальник отдела
                Employees: array<object(Id, Name)> # Список сотрудников отдела
                EmployeesCount: integer # Количество сотрудников в отделе
        """
        uri = '{0}list.api'.format(self.DEPARTMENT)
        return self._GetData(uri)
    # /

    def Comments(self, SubjectType, SubjectId, Order='asc'):
        """
        input:
            SubjectType: string = ('task' (задача),
                'project' (проект)) # Тип комментируемого объекта
            SubjectId: integer # ID комментируемого объекта
            Order='asc': string = ('asc' (по возрастанию), 'desc' (по убыванию))
                # Направление сортировки по дате (по умолчанию asc)
        output:
            comments<array>:
                Id: integer # ID комментария
                Text: string # Текст комментария
                Work: integer # Кол-во потраченных минут, которое приплюсовано
                    к комментируемому объекту (задаче или проекту)
                WorkDate: date # Дата, на которую списаны потраченные часы
                TimeCreated: datetime # Время создания
                Author: object(Id, Name) # Автор комментария (сотрудник)
                Avatar: string # Адрес аватара автора
        """
        if (SubjectType not in self._SubjectType) or \
            (Order not in self._OrderType):
            raise AttributeError('Invalid parameter value')

        uri = '{0}list.api?SubjectType={1}&SubjectId={2}&Order={3}'
        uri = uri.format(self.COMMENT, SubjectType, SubjectId, Order)
        return self._GetData(uri)
    # /

    def CommentCreate(self, SubjectType, SubjectId, **kwargs):
        """
        input:
            SubjectType: string = ('task' (задача),
                'project' (проект)) # Тип комментируемого объекта
            SubjectId: integer # ID комментируемого объекта
            kwargs:
                Model[Text]: string # Текст комментария
                Model[Work]: integer # Кол-во потраченных часов, которое
                    приплюсуется к комментируемому объекту (задача или проект)
                Model[WorkDate]: date # Дата, на которую списывать
                    потраченные часы
                Model[Attaches]: array # Приложенный файл,
                    должен передаваться POST-запросом
                Model[Attaches][Content]: string # Данные(контент файла),
                    закодированные с использованием MIME base64
                Model[Attaches][Name]: string # Имя файла (будет фигурировать
                    при выводе комментария)

        output:
            Id: integer # ID комментария
            Text: string # Текст комментария
            Work: integer # Кол-во потраченных минут, которое приплюсуется
                к комментируемому объекту (задача или проект)
            WorkDate: date # Дата, на которую списывать потраченные часы
            TimeCreated: datetime # Время создания
        """
        if SubjectType not in self._SubjectType:
            raise AttributeError('Invalid parameter value')

        uri = '{0}create.api'.format(self.COMMENT)
        kwargs['SubjectId'] = str(SubjectId)
        kwargs['SubjectType'] = SubjectType
        return self._GetData(uri, kwargs)
    # /

    def Favorites(self):
        """
        input:
            None
        output:
            Tasks<array>:
                Tasks: array # Список задач, см. структуру в "Список задач"
                Projects: array # Список проектов,
                    см. структуру в "Список проектов"
        """
        uri = '{0}list.api'.format(self.FAVORITE)
        return self._GetData(uri)
    # /

    def FavoriteAdd(self, SubjectType, SubjectId):
        """
        input:
            SubjectType: string = ('task' (задача),
                'project' (проект)) # Тип объекта
            SubjectId: integer # ID объекта
        output:
            None
        """
        if SubjectType not in self._SubjectType:
            raise AttributeError('Invalid parameter value')

        uri = '{0}add.api'.format(self.FAVORITE)
        params = {'SubjectId': str(SubjectId), 'SubjectType': SubjectType}
        self._GetData(uri, params)
    # /

    def FavoriteRemove(self, SubjectType, SubjectId):
        """
        input:
            SubjectType: string = ('task' (задача),
                'project' (проект)) # Тип объекта
            SubjectId: integer # ID объекта
        output:
            None
        """
        if SubjectType not in self._SubjectType:
            raise AttributeError('Invalid parameter value')

        uri = '{0}remove.api'.format(self.FAVORITE)
        params = {'SubjectId': str(SubjectId), 'SubjectType': SubjectType}
        self._GetData(uri, params)
    # /

    def Search(self, qs):
        """
        input:
            qs: string # Текст для поиска
            # Если параметр qs не указан либо пустой, то будет возвращена ошибка
            # "Empty query". Если же, результатов соответствующих запросу
            # не найдено, то в выходных данных будет возвращена ошибка
            # "No results".
        output:
            Employees: array # Список сотрудников,
                см. структуру в "Список сотрудников"
            Tasks: array # Список задач, см. структуру в "Список задач"
            Projects: array # Список проектов, см. структуру в "Список проектов"
        """
        uri = '{0}quick.api'.format(self.SEARCH)
        params = {'qs': qs}
        return self._GetData(uri, params)
    # /

    def Notifications(self):
        """
        input:
            None
        output:
            notifications<array>:
                Id: integer # ID уведомления
                Subject: object(Id,Name,Type) # Предмет уведомления
                    (см. пояснение ниже)
                Content: string или object(Subject,Text,Author) # Содержимое
                    уведомления (см. пояснение ниже)
                TimeCreated: datetime # Время создания уведомления

            # см. http://wiki.megaplan.ru/API_notifications

        Subject - это модель данных, с которой связано уведомление
            (задача, проект, сотрудник или комментарий). Если, например,
            уведомление о том, что поставлена задача, то в Subject будет
            идентификатор задачи. Subject содержит следующие аттрибуты:
                Id - идентификатор модели
                Name - название модели
                Type - тип модели (task/project/employee/comment).
        Структура Content зависит от типа Subject. Для всех типов, кроме
            комментариев, это простой текст уведомления. В случае
            с комментариями Content содержит следующие аттрибуты:
                Subject - предмет комментирования (задача или проект)
                    с вложенной структурой, аналогичной Subject
                    в самом уведомлении
                Text - текст комментария
                Author - автор комментария (Id и Name)
        """
        uri = '{0}notifications.api'.format(self.INFORMER)
        return self._GetData(uri)
    # /

    def NotificationDeactivate(self, Id):
        """
        input:
            Id: integer # ID уведомления. Обязательный параметр
        output:
            None
        """
        uri = '{0}deactivateNotification.api'.format(self.INFORMER)
        params = {'Id': str(Id)}
        self._GetData(uri, params)
    # /

    def Approvals(self):
        """
        input:
            None
        output:
            Tasks: array # Список задач, см. структуру в "Список задач"
            Projects: array # Список проектов, см. структуру в "Список проектов"
        """
        uri = '{0}approvals.api'.format(self.INFORMER)
        return self._GetData(uri)
    # /

# / class Megaplan(object):


def main():
    pass

if __name__ == '__main__':
    main()