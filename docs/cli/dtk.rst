dtk commands
===================

.. contents:: Available commands
    :local:

``analyze``
-------------

.. dtk-cmd:: analyze -i {exp_id|suite_id|name},... -a {config_name.py|built-in}

Analyzes the *most recent* experiment matched by specified **id** or **name** (or just the most recent) with the python script passed or the built-in analyzer.
Refer to the :dtk-cmd:`analyze-list` to see all available built-in analyzers.


.. dtk-cmd-option:: -bn, --batchName

When the analyze command is called on more than one experiment, a batch is automatically created. By default it will be called
`batch_id` with `id` being an automatically generated identification. This option allows to specify a batch name.
If the chosen batch already exists, the command will ask if you want to merge, override or cancel.


.. dtk-cmd-option:: -i, --ids

IDs of the items to analyze (can be suites, batches, experiments). This option supports a list of IDs separated by commas and the IDs can be:

* Experiment id
* Experiment name
* Batch id
* Batch name
* Suite id

.. dtk-cmd-option:: -a, --config_name

Python script or builtin analyzer name for custom analysis of simulations (see :dtk-cmd:`analyze-list`).

.. dtk-cmd-option:: --force, -f

Force analyzer to run even if jobs are not all finished.


``clean``
---------

.. dtk-cmd:: clean {none|id|name}

Hard deletes **ALL** experiments matched by the id or name (or literally all experiments if nothing is passed).

``clear_batch``
---------------

.. dtk-cmd:: clear_batch -bid <batch_id>

Clear the provided batch of all experiments or remove empty batches if no id provided.

.. dtk-cmd-option:: -bid

ID of the batch to clear.


``create_batch``
----------------

.. dtk-cmd:: create_batch -i <item_id,...> -bn <name>

Create a batch of experiments given the IDs of the items passed with the given name (or automatically generate a name if None is passed). The IDs supported are:

* Experiment id
* Experiment name
* Batch id
* Batch name
* Suite id

.. note::

    The batch creation will merge any overlapping items and ensure there will be no duplicates in the final batch.

.. dtk-cmd-option:: --ids -i

IDs of the items to group in the batch.

.. dtk-cmd-option:: --batchName, -bn

Name of the batch.


``delete``
----------

.. dtk-cmd:: delete {none|id|name}

Deletes the local metadata for the selected experiment (or most recent). This command will keep the experiment files (inputs and outputs) if the `--hard` flag is not used.

.. dtk-cmd-option:: --hard

Deletes the local metadata and the local working directory or marks the experimented as deleted in COMPS for the selected experiment (or most recent).


``exterminate``
---------------

.. dtk-cmd:: exterminate {none|id|name}

Kills ALL experiments matched by the id or name (or literally all experiments if nothing is passed).


``kill``
--------

.. dtk-cmd:: kill {none|id|name}

Kills all simulations in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --simIds, -s

Comma separated list of job IDs or simulations to kill in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

``list``
--------
.. dtk-cmd:: list {none|name}

list 20 *most recent* experiment containing specified **name** in the experiment name (or just the 20 most recent). For example::

    dtk list TestExperiment

.. dtk-cmd-option:: --<location>

list 20 *most recent* experiment by matched specified **location** in the experiment location. For example, to list experiments with HPC as a location::

    dtk list --HPC

.. dtk-cmd-option:: --number, -n

Use any number following by the command option to **limit** the number of *most recent* experiments to display. For example::

    dtk list -n 100

Use * to retrieve all experiments from local database. For example::

    dtk list -n *

``dtk list`` will only list experiments based on local database data that may not reflect the current status of the running experiments.

``list_batch``
--------------

.. dtk-cmd:: list_batch -bid <batch_id> -n <limit>

List the 20 (or `limit`) most recently created batches in the DB or the batch identified by `batch_id`.


.. dtk-cmd-option:: -bid

ID of the batch to list. If not provided, the command will list the `limit` batches present in the system.

.. dtk-cmd-option:: -n

Limit the number of batches to list.

``resubmit``
------------

.. dtk-cmd:: resubmit {none|id|name}

Resubmits all failed or canceled simulations in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --simIds, -s

Comma separated list of job IDs or process of simulations to resubmit in the *most recent* experiment matched by specified **id** or **name** (or just the most recent).

.. dtk-cmd-option:: --all, -a

Resubmit all failed or canceled simulations in selected experiments.

``run``
-------

.. dtk-cmd:: run {config_name}

Run the passed configuration python script for custom running of simulation. For example::

    dtk run example_sweep.py

.. dtk-cmd-option:: --<block_name>

Overrides which configuration block the simulation will be ran. Even if the python configuration passed defines the location ``LOCAL``, the simulations will be ran on the selected block::

    dtk run example_simulation.py --MY_CONFIG_BLOCK

See :ref:`simtoolsoverlay` for more information.

.. dtk-cmd-option:: --ini <ini_file_path>

Overrides which overlay ini configuration file to use. Specifying this parameter will make the system ignore any ``simtools.ini`` file in the working directory::

    dtk run --ini folder/test.ini


.. dtk-cmd-option:: --priority

Overrides the :setting:`priority` setting of the :ref:`simtoolsini`.
Priority can take the following values:

    - ``Lowest``
    - ``BelowNormal``
    - ``Normal``
    - ``AboveNormal``
    - ``Highest``


For example, if we have a simulation supposed to run locally, we can force it to be HPC with lowest priority by using::

    dtk run example_local_simulation.py --HPC --priority Lowest

.. dtk-cmd-option:: --node_group <node_group>

Allows to overrides the :setting:`node_group` setting of the :ref:`simtoolsini`.

.. dtk-cmd-option:: --blocking, -b

If this flag is present, the tools will run the experiment and automatically display the status until done.

.. dtk-cmd-option:: --quiet, -q

If this flag is used, the tools will not generate console outputs while running.


``status``
----------

.. dtk-cmd:: status {none|id|name}

Returns the status of the *most recent* experiment matched by the specified **id** or **name**.


The ``experiment_id`` is displayed after issuing a ``dtk run`` command:

.. code-block:: doscon
    :linenos:
    :emphasize-lines: 8,12,13

    c:\dtk-tools\examples>dtk run example_sim.py

    Initializing LOCAL ExperimentManager from parsed setup
    Getting md5 for C:\Eradication\DtkTrunk\Eradication\x64\Release\Eradication.exe
    MD5 of Eradication.exe: a82da8d874e4fe6a5bd7acdf6cbe6911
    Copying Eradication.exe to C:\Eradication\bin...
    Copying complete.
    Creating exp_id = 2016_04_27_10_42_42_675000
    Saving meta-data for experiment:
    {
        "exe_name": "C:\\Eradication\\bin\\a82da8d874e4fe6a5bd7acdf6cbe6911\\Eradication.exe",
        "exp_id": "2016_04_27_10_42_42_675000",
        "exp_name": "ExampleSim",
        "location": "LOCAL",
        "sim_root": "C:\\Eradication\\simulations",
        "sim_type": "VECTOR_SIM",
        "sims": {
            "2016_04_27_10_42_42_688000": {
                "jobId": 12232
            }
        }
    }

In this example, the id is: ``2016_04_27_10_42_42_675000`` and we can poll the status of this experiment with::

    dtk status 2016_04_27_10_42_42_675000

In the same example, the name is: ``ExampleSim`` and can be polled with::

    dtk status ExampleSim

Which will return:

.. code-block:: doscon

    c:\dtk-tools\examples>dtk status 2016_04_27_10_42_42_675000
    Reloading ExperimentManager from: simulations\ExampleSim_2016_04_27_10_42_42_675000.json
    Job states:
    {
        "12232": "Success"
    }
    {'Success': 1}

Letting us know that the 1 simulation of our experiment completed successfully. You can learn more about the simulation states in the documentation related to the :ref:`experimentmanager`.


.. dtk-cmd-option:: --active, -a

Returns the status of all active experiments (mutually exclusive to any other parameters).

.. dtk-cmd-option:: --repeat, -r

Repeat status check until job is done processing. Without this option, the status command will only return the current state and return. With this option, the status of the experiment will be displayed at regular intervals until its completion.
For example:

.. code-block:: doscon

    c:\dtk-tools\examples>dtk status 2016_04_27_12_15_09_172000 --repeat
    Reloading ExperimentManager from: simulations\ExampleSim_2016_04_27_12_15_09_172000.json
    Job states:
    {
        "5900": "Running (40% complete)"
    }
    {'Running': 1}
    Job states:
    {
        "5900": "Running (81% complete)"
    }
    {'Running': 1}
    Job states:
    {
        "5900": "Running (97% complete)"
    }
    {'Running': 1}
    Job states:
    {
        "5900": "Finished"
    }
    {'Finished': 1}



``stdout``
----------

.. dtk-cmd:: stdout {none|id|name}

Prints ``StdOut.txt`` for the *first* simulation in the *most recent* experiment matched by specified id or name (or just the most recent).

.. dtk-cmd-option:: -e

Prints ``StdErr.txt`` for the *first* simulation in the *most recent* experiment matched by specified id or name (or just the most recent).

.. dtk-cmd-option:: --failed, --succeeded

Prints ``StdOut.txt`` for the *first* failed or succeeded (depending on flag) simulation in the *most recent* experiment matched by specified id or name (or just the most recent).

.. dtk-cmd-option:: --force, -f

``dtk stdout`` by default will only display simulations of a finished experiment. If you wish to display the outputs while the experiment is running, use this flag.

