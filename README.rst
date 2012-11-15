=====
Modum
=====

Modum is a modular, asynchronous IRC bot written in python.

Installation
------------

It depends on `gevent <http://gevent.org>`_, which can be  downloaded `here <http://pypi.python.org/pypi/gevent#downloads>`_.

gevent below v1.0 depends on libevent, and above depends on libev.

Requirements can be installed with ``pip install -r requirements.txt``

At the moment I am using a v1.0 version of gevent, if you wish you can install it
beforehand from pypi using ``pip install gevent``

Usage
-----

Modum is configured with ``config.json`` in the ``data`` directory,
which you should edit with appropriate settings before you start it.

Modum can then be started simply with ``./modum`` or ``python modum``

You can find other options through ``./modum --help``

Extension
---------

You can add plugins in the obvious ``plugins`` directory.

Plugins should extend from the ``Plugin`` object, which provides many
convenience methods.

See ``plugins/ascii.py`` for an example plugin.

To allow for easy initialization, define this method:

``def setup(self, settings, botSettings):``

Please don't define ``__init__``, unless you call it on the parent as well.

``settings`` comes from the ``plugins`` section of the configuration file,
and ``botSettings`` comes from the client section of the configuration file.

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
