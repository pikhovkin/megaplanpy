megaplanpy
==========

The library support only JSON format.

Supports the API version of 2011.05+

Example usage
-------------

::

    #!/usr/bin/env python
    # -*- coding: UTF-8 -*-

    from megaplanpy import Megaplan

    def main():
        account = 'my_account'
        login = 'my_login'
        password = 'my_password'

        mplan = Megaplan(account, login, password)

        tasks = mplan.GetTasks().data['tasks']

    if __name__ == '__main__':
        main()