=====
Modum
=====

Modum is a modular, multi-server, asynchronous IRC bot written in python.

Installation
------------

It depends on `gevent <http://gevent.org>`_, which can be  downloaded `here <http://pypi.python.org/pypi/gevent#downloads>`_.

gevent below v1.0 depends on libevent, and above depends on libev.

I recommend you install gevent using `pip <http://www.pip-installer.org/en/latest/installing.html>`_ (``pip install gevent``).

Usage
-----

Modum is configured with ``config.json``, in the ``data`` directory
which you should edit with appropriate settings before you start it.

Modum can then be started simply with ``./modum`` or ``python modum``.

Extension
---------

You can add plugins in the obvious ``plugins`` directory.

Credits
-------

|CC by-sa|

.. |CC by-sa| image:: http://i.creativecommons.org/l/by-sa/3.0/88x31.png

Modum by `Matthew Iversen <https://github.com/Ivoz/Modum>`_ is licensed under a `Creative Commons Attribution-ShareAlike 3.0 Unported License <http://creativecommons.org/licenses/by-sa/3.0/>`_.
You can ask for permissions beyond the scope of this license by contacting me.

Copyright 2012, Matt Iversen

I would like to thank the following:

`zeekay <https://github.com/zeekay>`_ - https://gist.github.com/1740951

`maxcountryman <https://github.com/maxcountryman>`_ - https://gist.github.com/676306

`gwik <https://github.com/gwik>`_ - https://github.com/gwik/geventirc
