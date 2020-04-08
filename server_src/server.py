# Basic
import os,sys,subprocess,csv

# For main server
import socketio
from flask import Flask, render_template

# For handling terminal and files
import pty, select
import termios, struct, fcntl


# File Watcher
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pwd import getpwuid


app = Flask(__name__)
sio = socketio.Server(async_mode='threading')
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)

# Initialize Filesystem and add Users
def on_startup():
    print("on_startup()-------------------------------------")
    bot_users = []
    with open("/app/users.csv", newline='') as csvfile:
        reader = csv.DictReader(csvfile)    
        for row in reader:
            # print(row['first_name'], row['last_name'])
            bot_users.append((row['USER_ID'],row['DISC_NAME']))
            print(row['USER_ID'],row['DISC_NAME'])

    # Create directories and such
    os.mkdir("/tmp/upload_to_discord")
    os.system("chmod -R a+r /app")
    os.system("chmod -R a+rw /tmp/upload_to_discord")
    os.system("chmod -R ugo+rx /app/shared")
    os.system("echo -e \"\n* hard nproc 1000\" >> /etc/security/limits.conf")

    # Add all users
    os.system('groupadd discord_members')

    start_uid = 2000
    for user_id,disc_name in bot_users:
        os.system("useradd -g discord_members --badnames" + \
        " -m " + user_id + \
        " -u " + str(start_uid) + \
        " --skel " + "/app/skel")
        start_uid += 1    


# Shell sutff
running_shells = {}

class Shell():
    def __init__(self,discord_id: int):
        print("[INFO]startshell(",discord_id,")---------------------------")
        self.user_name = str(discord_id)
        child_pid,child_fd = pty.fork()
        if child_pid == 0:
            # Inside child process
            os.system("sudo -u " + self.user_name + " /bin/bash")
            quit()
        self.pid,self.fd = child_pid,child_fd
        self.set_winsize(5,100)
        self.screen = ""
    def input(self,text):
        command = text.encode()
        os.write(self.fd,text.encode())

    def output(self,data):
        # Could be a bit better
        sio.emit("shell_output",[self.user_name,data])
    
    def set_winsize(self, row, col, xpix=0, ypix=0):
        winsize = struct.pack("HHHH", row, col, xpix, ypix)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, winsize)


# Socket-io Server
@sio.on('connect')
def connect(sid,environ):
    print("Connected:",sid)

@sio.on('shell')
def shell(sid,args):
    input_str = args['input'] + "\n"
    user_name = args['id']
    if int(user_name) in running_shells.keys():
        running_shells[user_name].input(input_str)
    else:
        running_shells[user_name] = Shell(user_name)
        running_shells[user_name].input(input_str)
    sio.emit('info','trying')

@sio.on('shell_reset')
def shell_reset(sid,args):
    if int(args['id']) in running_shells.keys():
        del running_shells[args['id']]


# Background Function that reads output from each shell fd:
def emit_shell_output():
    # This will check fd of all open shells for input
    max_read_bytes = 500
    while True:
        sio.sleep(0.5)
        for uname,u_shell in running_shells.items():
            child_fd = u_shell.fd
            (data_ready, _, _) = select.select([child_fd], [], [], 0)
            if data_ready:
                read_data = os.read(child_fd, max_read_bytes).decode()
                print("----------------")
                print(read_data)
                print("----------------")

                running_shells[uname].output(read_data)

def check_and_upload():
    # Watches files in /tmp/upload_to_discord directory then uploads it
    
    my_event_handler = FileSystemEventHandler()
    def _file_unlocked(file_name):
        x = open(file_name, 'w+')
        try:
            fcntl.flock(x, fcntl.LOCK_EX | fcntl.LOCK_NB)
            x.close()
            return True
        except:
            close(x)
            return False
    def on_created(event):
        while True:
            try:
                fcntl.flock(open(event.src_path,"rb"),fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except:
                sio.sleep(0.5)

        with open(event.src_path,'rb') as f:
            file_name    = os.path.basename(event.src_path)
            owner        = getpwuid(os.stat(event.src_path).st_uid).pw_name
            data_to_send = f.read()
            send_file    = {"dat":data_to_send,"user":owner,"file_name":file_name}

            print(f"[INFO]sending_file({file_name})")
            sio.emit('dispatch_discord_file',send_file)

        os.remove(event.src_path)

    my_event_handler.on_created = on_created
    my_observer = Observer()
    my_observer.schedule(my_event_handler, "/tmp/upload_to_discord")
    my_observer.start()

    while True:
        sio.sleep(0.5)

def main():
    on_startup()
    
    sio.start_background_task(target=emit_shell_output)
    sio.start_background_task(target=check_and_upload)

    app.run(host='0.0.0.0',port='5000',threaded=True)

main()