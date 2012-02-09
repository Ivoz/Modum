Modum
=====

Modum is a modular, multi-server, asynchronous IRC bot written in python.

Installation
-----------

It depends on gevent, which can be found [here](http://gevent.org), and downloaded [here](http://pypi.python.org/pypi/gevent#downloads).

gevent below v1.0 depends on libevent, and above depends on libev.

I recommend you install gevent using [pip](http://www.pip-installer.org/en/latest/installing.html) (`pip install gevent`).

Usage
-----

Modum is distributed with `config-example.json`, which should be copied
to `config.json` and configured appropriately before you start.

Modum can then be started simply with `python modum.py`.

Extension
---------

Credits
-------

![CC by-sa](http://i.creativecommons.org/l/by-sa/3.0/88x31.png "CC by-sa")

Modum by [Matthew Iversen](https://github.com/Ivoz/Modum) is licensed under a [Creative Commons Attribution-ShareAlike 3.0 Unported License](http://creativecommons.org/licenses/by-sa/3.0/).
Permissions beyond the scope of this license may be available at [notevencode.com](http://notevencode.com).

Copyright 2012, Matt Iversen

I would like to thank the following:

[zeekay](https://github.com/zeekay) - https://gist.github.com/1740951

[maxcountryman](https://github.com/maxcountryman) https://gist.github.com/676306

[gwik](https://github.com/gwik) - https://github.com/gwik/geventirc
