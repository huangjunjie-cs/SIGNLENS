=====
Usage
=====



Command line usage 
-------------------------

After finish the :doc:`installation`, it can be invoked from the command line by:


.. code-block:: bash

    $ signlens -f tests/test_datas/bitcoin_alpha.edgelist


It will output the metrics report table for a signed networks

::

    +---------------------------------------+----------------------------------+
    |                Metrics                |              Value               |
    +=======================================+==================================+
    | The number of nodes                   | 22650                            |
    +---------------------------------------+----------------------------------+
    | The number of edges                   | 1536                             |
    +---------------------------------------+----------------------------------+
    | Sign distribution (+)                 | 0.936                            |
    +---------------------------------------+----------------------------------+
    | Balanced triangle distribution        | 0.881                            |
    +---------------------------------------+----------------------------------+
    | Unbalanced triangle distribution      | 0.119                            |
    +---------------------------------------+----------------------------------+
    | Signed triangle  (+++, ++-, +--, ---) | (0.8413, 0.1166, 0.0393, 0.0028) |
    +---------------------------------------+----------------------------------+
    | In-degreeoutput                       | output/In-degree.pdf             |
    +---------------------------------------+----------------------------------+
    | In-degree sign output                 | output/In-degree-sign.pdf        |
    +---------------------------------------+----------------------------------+
    | Out-degreeoutput                      | output/Out-degree.pdf            |
    +---------------------------------------+----------------------------------+
    | Out-degree sign output                | output/Out-degree-sign.pdf       |
    +---------------------------------------+----------------------------------+
    | Hop sign output                       | output/Hop.pdf                   |
    +---------------------------------------+----------------------------------+
    | Singular value distribution           | output/Top-K.pdf                 |
    +---------------------------------------+----------------------------------+

.. note::

    This file (e.g, ``bitcoin_alpha.edgelist``) needs to be a signed edgelist file, including ``source_node``, ``target_node``, and ``sign`` fields. like:




For signed bipartite networks, you can run it by:

.. code-block:: bash

    signlens -f tests/test_datas/senate1to10.edgelist -t bipartite

::

    +--------------------------------------+------------------------------------+
    | Metrics                              | Value                              |
    +======================================+====================================+
    | The number of nodes                  | (145, 1056)                        |
    +--------------------------------------+------------------------------------+
    | The number of edges (+, -, total)    | (14979, 12104, 27083)              |
    +--------------------------------------+------------------------------------+
    | Sign distribution (+)                | 0.553                              |
    +--------------------------------------+------------------------------------+
    | Balanced butterfly distribution      | 0.798                              |
    +--------------------------------------+------------------------------------+
    | Unbalanced butterfly distribution    | 0.202                              |
    +--------------------------------------+------------------------------------+
    | Signed butterfly                     | [0.262, 0.108, 0.11, 0.184, 0.133, |
    | (++++,+--+,++--,+-+-,----,+++-,+---) | 0.122, 0.081]                      |
    +--------------------------------------+------------------------------------+



Package usage
---------------

You can use it by importing some class you want to use.

.. code-block:: python

    from sign_lens import SignLens
    model = SignLens('./xxx.edgelist')
    model.report_signed_metrics()

