.. _tutorial_user_program:

User Program Tutorial
========================

In this tutorial, we will be creating a simple increment program that communicates through the echo command.


The first thing we will be writing, is a few variables to hold the network socket data

.. code-block:: python
   :linenos:

    server_address = "network_command"
    port = 65432


Next create a function that sends a given command to the network server. First, it opens the socket and sends the encoded command through the socket with an null byte. Then it waits for a reply and decodes it and returns it.

.. code-block:: python
   :linenos:

    def send_command(command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(server_address)
            sock.send(command.encode('utf-8') + b'\0')
            data = ""
            while len(data) == 0 or data[-1] != '\0':
                buf = sock.recv(1024)
                data += buf.decode('utf-8')
            return data[:-1].strip()

In this tutorial, we will be using python's selectors package to handle file events.

.. code-block:: python
    :linenos:

    # Top of file
    import selectors

    sel = selectors.DefaultSelector()


Next we send the command to open the echo antenna to the network and get the response. We parse the response into the id, in file, and out file.

.. code-block:: python
   :linenos:

    data = send_command("create bluetooth_client rw --address {} --port {}".format(bt_add,bt_port))
    ant_id, in_file, out_file = data.split(" ")

We then open the files to the antenna. IMPORTANT - Open Read file first, then write file.

.. code-block:: python
   :linenos:

    # Top of file
    import os

    try:
        in_fh = os.open(in_file, os.O_RDONLY)
        out_fh = os.open(out_file, os.O_WRONLY)
        sel.register(fh_in, selectors.EVENT_READ)
    finally:
        os.close(in_fh)
        os.close(out_fh)
        sel.unregister(in_fh)

Then we send a one through the file pipeline to start the incrementing process.

.. code-block:: python
   :linenos:

    try:
        in_fh = os.open(in_file, os.O_RDONLY)
        out_fh = os.open(out_file, os.O_WRONLY)
        sel.register(fh_in, selectors.EVENT_READ)

        os.write(out_fh, b'1')
    finally:
        os.close(in_fh)
        os.close(out_fh)
        sel.unregister(in_fh)


In this program, we will assume that the only event coming in will be the increment number. As such, we will read in the event, and then print the number, the increment by one and write it back out

.. code-block:: python
   :linenos:

    try:
        fh_in = os.open(in_file, os.O_RDONLY)
        fh_out = os.open(out_file, os.O_WRONLY)
        sel.register(fh_in, selectors.EVENT_READ)

        os.write(fh_out, b'1')

        while True:
            events = sel.select()
            if events:
                buff = os.read(fh_in, 1024)
                if buff:
                    num = int(buff.decode('utf-8'))
                    print(num)
                    os.write(fh_out,str(num + 1).encode('utf-8'))

    finally:
        os.close(in_fh)
        os.close(out_fh)
        sel.unregister(in_fh)


With that, we have completed the program. It will start an echo antenna, then write a one to it and print out the incrementations after.



.. code-block:: python
   :linenos:

    import selectors
    import os

    server_address = "network_command"
    port = 65432

    def send_command(command):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.connect(server_address)
            sock.send(command.encode('utf-8') + b'\0')
            data = ""
            while len(data) == 0 or data[-1] != '\0':
                buf = sock.recv(1024)
                data += buf.decode('utf-8')
            return data[:-1].strip()

    def main():
        data = send_command("create bluetooth_client rw --address {} --port {}".format(bt_add,bt_port))
        ant_id, in_file, out_file = data.split(" ")


        sel = selectors.DefaultSelector()
        try:
            fh_in = os.open(in_file, os.O_RDONLY)
            fh_out = os.open(out_file, os.O_WRONLY)
            sel.register(fh_in, selectors.EVENT_READ)

            os.write(fh_out, b'1')

            while True:
                events = sel.select()
                if events:
                    buff = os.read(fh_in, 1024)
                    if buff:
                        num = int(buff.decode('utf-8'))
                        print(num)
                        os.write(fh_out,str(num + 1).encode('utf-8'))

        finally:
            os.close(in_fh)
            os.close(out_fh)
            sel.unregister(in_fh)

    if __name__ == "__main__":
        main()
