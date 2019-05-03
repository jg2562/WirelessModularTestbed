.. _tutorial_antenna:

Antenna Tutorial
==================

In this tutorial, we will be showing how to write an echo antenna.


In order to write an antenna, you need to be able to specifiy what is needed for input arguments. The first thing that is taken in is the mode of the antenna. The next few items are the files to read and write from. After that, it is user defined arguments into the antenna.


.. code-block:: python
   :linenos:

    # Top of file
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('mode')
    parser.add_argument('in_filename')
    parser.add_argument('out_filename')
    args = parser.parse_args()
    mode = args.mode


In this tutorial, we will be using python's selectors package to handle file events.

.. code-block:: python
    :linenos:

    # Top of file
    import selectors

    sel = selectors.DefaultSelector()


Next you need to open up the files to interact with the user program. Due to use of selectors package, we are using the os open and close IMPORTANT - Make sure to open them in the order write file then read file.

.. code-block:: python
    :linenos:

    # Top of file
    import os

    try:
       fh_out = os.open(args.in_filename, os.O_WRONLY)
       fh_in = os.open(args.out_filename, os.O_RDONLY)
    finally:
       os.close(fh_in)
       os.close(fh_out)


Next we will expand the try statement to register and unregister the file handle with the selectors package. That way we can handle file events as they happen.

.. code-block:: python
    :emphasize-lines: 8,11
    :linenos:

    try:
       fh_out = os.open(args.in_filename, os.O_WRONLY)
       fh_in = os.open(args.out_filename, os.O_RDONLY)

       sel.register(fh_in, selectors.EVENT_READ)

    finally:
       sel.unregister(fh_in)
       os.close(fh_in)
       os.close(fh_out)


Lastly, we will process the event as it happens. Since this is a simple echo antenna, we will just assume the only event is the read file and direct that data to the output file

.. code-block:: python
    :emphasize-lines: 7-12
    :linenos:

    try:
       fh_out = os.open(args.in_filename, os.O_WRONLY)
       fh_in = os.open(args.out_filename, os.O_RDONLY)

       sel.register(fh_in, selectors.EVENT_READ)

       while True:
           events = sel.select()
           if events:
               buff = os.read(fh_in, 1024)
               if buff:
                    os.write(fh_out, buff)

    finally:
       sel.unregister(fh_in)
       os.close(fh_in)
       os.close(fh_out)


With that last addition we have a complete program. This antenna will use the two provided files and direct all data from the input file to the output file.

For the below program, I created an import protection with main function. This prevents problems with the doc generation program

Below if the full program:

.. code-block:: python
    :linenos:

    import argparse
    import os
    import selectors

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('mode')
        parser.add_argument('in_filename')
        parser.add_argument('out_filename')
        args = parser.parse_args()
        mode = args.mode

        sel = selectors.DefaultSelector()

        try:
            fh_out = os.open(args.in_filename, os.O_WRONLY)
            fh_in = os.open(args.out_filename, os.O_RDONLY)

            sel.register(fh_in, selectors.EVENT_READ)

            while True:
                events = sel.select()
                if events:
                    buff = os.read(fh_in, 1024)
                    if buff:
                        os.write(fh_out, buff)

        finally:
            sel.unregister(fh_in)
            os.close(fh_in)
            os.close(fh_out)

    if __name__ == "__main__":
        main()
