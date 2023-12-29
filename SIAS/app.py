import random
#from tkinter import S, Y
from flask import Flask, redirect, render_template, request, flash
from flask_ngrok import run_with_ngrok
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import struct
import enum
import serial
import time
import threading

app = Flask(__name__,static_url_path='', static_folder='static')
run_with_ngrok(app)
app.config['SECRET_KEY'] = "#$Geg4535%^%tERDFHd4@%$#"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATION'] = True
socketio = SocketIO(app)
sockets = {}
db = SQLAlchemy(app)
migrate = Migrate(app, db)
class StorageColumn(db.Model):
    _id = db.Column("id",db.Integer, primary_key = True)
    type = db.Column(db.String(50))
    bound = db.Column(db.Integer)
    filled_cells = db.Column(db.Integer)
    def __init__(self, type):
        super().__init__()
        self.type = type
        self.filled_cells = 0
        self.bound = 0
        self.oid = 0
        db.session.commit()
    def Removetools(self):
        filled_cells = self.query.filter_by(_id= self._id).first().filled_cells
        if filled_cells >= 1:
            return True
        else:
            return False
    def Addtools(self, addedtools):
        self.filled_cells += addedtools
class Template(db.Model):
    _id = db.Column("id",db.Integer, primary_key = True)
    name = db.Column(db.String(50))
    rid= db.Column(db.Integer)
    spatula = db.Column(db.Integer)
    knife = db.Column(db.Integer)
    scissors = db.Column(db.Integer)
    def __init__(self, name, spatula, knife, scissors):
        super().__init__()
        self.name = name
        self.spatula = spatula
        self.knife = knife
        self.scissors = scissors
        c_column = StorageColumn.query.filter_by(bound = 0).first()
        c_column.bound = 1
        self.rid = c_column._id
        db.session.commit()
        
    def __str__(self):
        return self.name
EV3_1 = None
Ev3_2 = None
def random_int(low, high):
    return int(random.random()*(high-low) + low)        
def printMessage(s):
    return ' '.join("{:02x}".format(c) for c in s)

class MessageType(enum.Enum):
    Text = 0
    Numeric = 1
    Logic = 2
def fEV3_2(Ev3_2,EV3_1):
    while True:
        n = Ev3_2.inWaiting()
        if n!= 0: 
            s=Ev3_2.read(n)
            mail,value,s = decodeMessage(s,MessageType.Text)
            if value == 'R' :
                print('R')
                m = encodeMessage(MessageType.Text, 'raspiSays', value)
                EV3_1.write(m)
        else:
            time.sleep(0.1)
def fEv3_1(EV3_1,Ev3_2):
    messageReceived = False  
    while not messageReceived:
        n = EV3_1.inWaiting()
        if n!= 0:
            s=EV3_1.read(n)
            mail,value,s = decodeMessage(s,MessageType.Text)
            c = encodeMessage(MessageType.Text,'raspiSays', 'S')
            Ev3_2.write(c)
            time.sleep(0.2)
            if value == 'S':
                m = encodeMessage(MessageType.Numeric, 'raspiSays0', 0)
                Ev3_2.write(m)
                time.sleep(1)
                Template_1 = StorageColumn.query.filter_by(type="Template_1").first()
                filled_cells = Template_1.filled_cells
                y = encodeMessage(MessageType.Numeric, 'raspiSays1', 3 - filled_cells)
                Ev3_2.write(y)
                print(str(3 - filled_cells))
                Template_1.filled_cells += 1
                db.session.commit()
            elif value == 'N':
                m = encodeMessage(MessageType.Numeric, 'raspiSays0', 1)
                Ev3_2.write(m)
                time.sleep(1)
                print('1')
                Template_2 = StorageColumn.query.filter_by(type="Template_2").first()
                filled_cells = Template_2.filled_cells
                y = encodeMessage(MessageType.Numeric, 'raspiSays1', 3 - filled_cells )
                Ev3_2.write(y)
                print(str(3 - filled_cells))
                Template_2.filled_cells += 1 
                db.session.commit()
            elif value == 'P':
                m = encodeMessage(MessageType.Numeric, 'raspiSays0', 2)
                Ev3_2.write(m)
                time.sleep(1)
                print('2')
                Template_3 = StorageColumn.query.filter_by(type="Template_3").first()
                filled_cells = Template_3.filled_cells
                y = encodeMessage(MessageType.Numeric, 'raspiSays1', 3 - filled_cells )
                Ev3_2.write(y)
                print(str(3 - filled_cells))
                Template_3.filled_cells += 1
                db.session.commit()
            m2 = False
            while not m2:
                n = EV3_1.inWaiting()
                if n != 0:
                    s=EV3_1.read(n)
                    mail,value,s = decodeMessage(s,MessageType.Text)
                    if value == 'D':
                        m2 = True
                else : 
                    time.sleep(0.1)

        else:
            time.sleep(0.1)
def decodeMessage(s, msgType):
    payloadSize = struct.unpack_from('<H', s, 0)[0]
    
    if payloadSize < 5:       # includes the mailSize
        raise BufferError('Payload size is too small')
    
    a,b,c,d = struct.unpack_from('<4B', s, 2)
    if a != 1 or b != 0 or c != 0x81 or d != 0x9e:
        raise BufferError('Header is not correct.  Expecting 01 00 81 9e')
    
    mailSize = struct.unpack_from('<B', s, 6)[0]
    
    if payloadSize < (5 + mailSize):  # includes the valueSize
        raise BufferError('Payload size is too small')
    
    mailBytes = struct.unpack_from('<' + str(mailSize) + 's', s, 7)[0]
    mail = mailBytes.decode('ascii')[:-1]
    
    valueSize = struct.unpack_from('<H', s, 7 + mailSize)[0]
    if payloadSize < (7 + mailSize + valueSize):  # includes the valueSize
        raise BufferError('Payload size does not match the packet')

    if msgType == MessageType.Logic:
        if valueSize != 1:
            raise BufferError('Value size is not one byte required for Logic Type')
        valueBytes = struct.unpack_from('<B', s, 9 + mailSize)[0]
        value = True if valueBytes != 0 else False
    elif msgType == MessageType.Numeric:
        if valueSize != 4:
            raise BufferError('Value size is not four bytes required for Numeric Type')
        value = struct.unpack_from('<f', s, 9 + mailSize)[0]
    else:
        valueBytes = struct.unpack_from('<' + str(valueSize) + 's', s, 9 + mailSize)[0]
        value = valueBytes.decode('ascii')[:-1]
        if len(s) > (payloadSize + 2):
            remnant = None
        else:
            remnant = s[(payloadSize) + 2:]
        
    return (mail, value, remnant)

def encodeMessage(msgType, mail, value):
    mail = mail + '\x00'
    mailBytes = mail.encode('ascii') 
    mailSize = len(mailBytes)
    fmt = '<H4BB' + str(mailSize) + 'sH'
    
    if msgType == MessageType.Logic:
        valueSize = 1
        valueBytes = 1 if value is True else 0
        fmt += 'B'
    elif msgType == MessageType.Numeric:
        valueSize = 4
        valueBytes = float(value)
        fmt += 'f'
    else:
        value = value + '\x00'
        valueBytes = value.encode('ascii')
        valueSize = len(valueBytes)
        fmt += str(valueSize) + 's'
    
    payloadSize = 7 + mailSize + valueSize
    s = struct.pack(fmt, payloadSize, 0x01, 0x00, 0x81, 0x9e, mailSize, mailBytes, valueSize, valueBytes)
    return s



@app.route("/")
def home():
    currently_stored = StorageColumn.query.all()
    print(currently_stored)
    return render_template("home.html", templates = Template.query.all(), currently_stored = currently_stored)

if not db.session.query(StorageColumn).first():
    Template_1 = StorageColumn('Template_1')
    Template_2 = StorageColumn('Template_2')
    Template_3 = StorageColumn('Template_3')
    db.session.add(Template_1)
    db.session.add(Template_2)
    db.session.add(Template_3)
    db.session.commit()
    
@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == "POST":
        if len(Template.query.all()) >= 3:
            return redirect("/")
        Name = request.form["floatingInput"]
        spatula = request.form["spatula"]
        if not spatula:
            spatula = 0
        knife = request.form["knife"]
        if not knife:
            knife = 0
        scissors = request.form["scissors"]
        if not scissors:
            scissors = 0
        template = Template(Name, spatula, knife, scissors)
        db.session.add(template)
        db.session.commit()
        return redirect("/")
    else:
        return render_template("create.html")

@app.route("/about")
def about():
    return render_template("about.html")
    
@socketio.on('order')
def retrieve_template(id):
    template_id = int(id)
    
    found_template = Template.query.filter_by(_id=template_id+1).first()
    print(found_template)
    c_column = StorageColumn.query.filter_by(_id = found_template.rid).first()
    print(c_column)
    if c_column.Removetools():
        print(template_id)
        
        sockets[request.sid].emit('order-response', {'accepted':True})
        s = encodeMessage(MessageType.Text, 'raspiSays', 'O')
        print(Ev3_2)
        Ev3_2.write(s)
        time.sleep(0.2)
        g = encodeMessage(MessageType.Numeric, 'raspiSays0', c_column._id -1)
        Ev3_2.write(g)
        time.sleep(0.2)
        x = encodeMessage(MessageType.Numeric, 'raspiSays1', 4 - c_column.filled_cells)
        Ev3_2.write(x)
        c_column.filled_cells -= 1
        db.session.commit()
        time.sleep(1)
    else: 
        sockets[request.sid].emit('order-response',{'accepted':False})
    
@socketio.on('connected')
def connected():
    print( "%s connected" % (request.sid))
    sockets[request.sid] = Socket(request.sid)
    
@socketio.on('disconnect')
def disconnect():
    print( "%s disconnected" % (request.sid))
    del sockets[request.sid]

class Socket:
    def __init__(self, sid):
        self.sid = sid
        self.connected = True

    # Emits data to a socket's unique room 
    def emit(self, event, data = None):
        socketio.emit(event, data, room=self.sid)
        
        
if __name__ == '__main__':
    db.create_all()
    EV3_1 = serial.Serial('/dev/rfcomm0')
    Ev3_2 = serial.Serial('/dev/rfcomm1')
    t1 = threading.Thread(target = fEV3_2, args = (Ev3_2,EV3_1,))
    t1.start()
    t2 = threading.Thread(target = fEv3_1, args = (EV3_1,Ev3_2,))
    t2.start()
    socketio.run(app,host='localhost')