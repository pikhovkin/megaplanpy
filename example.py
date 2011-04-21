#-------------------------------------------------------------------------------
# Name:        example
# Purpose:
#
# Author:      Sergey Pikhovkin (s@pikhovkin.ru)
#
# Created:     04.02.2011
# Copyright:   (c) Sergey Pikhovkin 2011
# Licence:     MIT
#-------------------------------------------------------------------------------
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from megaplanpy import Megaplan


CODE = 'cp1251'

def PrintDict(D):
    tmpl1 = '{0}: {1}'
    tmpl2 = '    {0}: {1}'
    for key, value in D.iteritems():
        if isinstance(value, dict):
            print('{0}:'.format(key))
            for k, v in value.iteritems():
                if isinstance(v, (str, unicode)):
                    print(tmpl2.format(k, v.encode(CODE)))
                else:
                    print(tmpl2.format(k, v))
        else:
            if isinstance(value, (str, unicode)):
                print(tmpl1.format(key, value.encode(CODE)))
            else:
                print(tmpl1.format(key, value))

def main():
    account = 'my_account'
    login = 'my_login'
    password = 'my_password'

    self_id = '0000000' # <-- input self Id

    create_task = False
    edit_task = False

    mplan = Megaplan(account, login, password)

    print(' ' * 20 + 'TASK list view')
    obj = mplan.GetTasks()
    tasks = obj.data['tasks']
    for task in tasks:
        print('--------' * 10)
        PrintDict(task)


    print(' ' * 20 + 'TASK card view')
    if tasks:
        print('********' * 10)
        task_id = tasks[len(tasks) - 1]['Id']
        obj = mplan.GetTaskCard(task_id)
        task_card = obj.data['task']
        PrintDict(task_card)
        print('********' * 10)

    if create_task:
        print(' ' * 20 + 'TASK create')
        params = {
            'Model[Name]': 'New task',
            #'Model[Deadline]': '2011-02-05 12:00',
            #'Model[DeadlineDate]': '2011-02-05',
            #'Model[DeadlineType]': 'soft',
            'Model[Responsible]': self_id, # <-- input self Id
            #'Model[Executors]': '0',
            #'Model[Auditors]': '0',
            #'Model[Severity]': '1',
            #'Model[SuperTask]': '0',
            #'Model[Customer]': '0',
            #'Model[IsGroup]': '0',
            'Model[Statement]': 'Create new task from Python'
        }

        obj = mplan.SetTaskCreate(**params).data
        print(obj)

    if edit_task:
        print(' ' * 20 + 'TASK edit')
        task_id = obj['task']['Id']
        params = {
            'Model[Name]': 'New edit task',
            #'Model[Deadline]': '2011-02-05 12:00',
            #'Model[DeadlineDate]': '2011-02-05',
            #'Model[DeadlineType]': 'soft',
            'Model[Responsible]': self_id, # <-- input self Id
            #'Model[Executors]': '0',
            #'Model[Auditors]': '0',
            #'Model[Severity]': '1',
            #'Model[SuperTask]': '0',
            #'Model[Customer]': '0',
            #'Model[Owner]': '',
            'Model[Statement]': 'Edit new task from Python'
        }
        mplan.SetTaskEdit(task_id, **params)

    print(' ' * 20 + 'TASK available actions')
    obj = mplan.GetTaskAvailableActions(task_id)
    print(obj.actions)
    print(obj.params)
    print('--------' * 10)
    '''
    print(' ' * 20 + 'TASK action')
    obj = mplan.SetTaskAction(task_id, 'act_accept_task')
    print(obj.params)
    print('--------' * 10)

    print(' ' * 20 + 'TASK mark as favorite')
    mplan.SetTaskMarkAsFavorite(task_id, True)
    print('--------' * 10)
    '''

if __name__ == '__main__':
    main()
