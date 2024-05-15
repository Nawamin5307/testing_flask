from flask import Flask , render_template , request , jsonify
from flask_socketio import SocketIO , emit
from flask_mqtt import Mqtt
from flask_mysqldb import MySQL
import math
import re

# ========== Variable ============
# global distance
# global angle
# global count
# global palate

distance = []
angle  = []
count = 0

palate = [
    "AA001" ,
    "AA002" ,
    "AA003" ,
    "AA004" ,
    "AA005" ,
    "AA006" ,
    "AA007" ,
    "AA008" ,
    "AA009" ,
    "AA010" ,
    "AA011" ,
    "AA012" ,
    "AA013" ,
    "AA014" ,
    "AA015" ,
    "AA016" ,
    "AA017" ,
    "AA018" ,
    "AA019" ,
    "AA020" ,
    "AA021" ,
    "AA022" ,
    "AA023" ,
    "AA024" ,
    "AA025" ,
    "AA026" ,
    "AA027" ,
    "AA028" ,
    "AA029" ,
    "AA030" ,
    "AA031" ,
    "AA032"
]

# ================================

app = Flask(__name__ , template_folder='www/')
app.config['SECRET_KEY'] = 'secret_key'
socketio = SocketIO(app)

app.config['MQTT_BROKER_URL'] = '192.168.50.214'  
app.config['MQTT_BROKER_PORT'] = 1883  
app.config['MQTT_USERNAME'] = ''  
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 300 
app.config['MQTT_TLS_ENABLED'] = False
topic = "+"
mqtt = Mqtt(app)

# # MySQL Configure
# mysql = MySQL(app)
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = 'dew2533449'
# app.config['MYSQL_DB'] = 'esp_data'

def send_pallet_to_web(np):
    return {
        "pallet_v" : np
    }

def send_point_to_web(dt):
    return {
        'point': dt
    }

def send_all_zero():
    return {
        'pallet_v' : 0 ,
        'point' : 0
    }

def show_palate(index):
    return palate[index]

def clear_data(input_str):
    new_data = re.findall(r'[-+]?\d*\.\d+|\d+', input_str)
    return new_data

def convert_angle(input_angle):
    return float(input_angle*(math.pi/180))


def collected_data(input_str):
    angle.append(clear_data(input_str)[1])
    distance.append(clear_data(input_str)[2])

def cal_pallet():
    result = 0
    i = 0
    for i in range(0 , len(distance)):
        sum = 0
        sum = float(distance[i]) * round(math.cos(convert_angle(float(angle[i]))))
        # print("sum = " + str(sum))
        result = result + sum

    return math.floor(((15*len(distance)) - result) / 1.2)


# MQTT
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("connect with result code" + str(rc))
    client.subscribe(topic)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global msg
    global count
    msg = message.payload.decode()
    print(message.topic + " " + str(msg))
    if  clear_data(msg)[0] == "1":
        if message.topic == "measure":
            angle.append(clear_data(msg)[1])
            distance.append(clear_data(msg)[2])
            print("angle : " + str(angle))
            print("distance : " + str(distance))
            send_point_to_web(distance)
            if len(distance) == 1 :
                socketio.emit('send_point_1' , send_point_to_web(distance[0]) , namespace='/')
            elif len(distance) == 2 :
                socketio.emit('send_point_2' , send_point_to_web(distance[1]) , namespace='/')
            elif len(distance) == 3 :
                socketio.emit('send_point_3' , send_point_to_web(distance[2]) , namespace='/')
            elif len(distance) == 4 :
                socketio.emit('send_point_4' , send_point_to_web(distance[3]) , namespace='/')
            elif len(distance) == 5 :
                socketio.emit('send_point_5' , send_point_to_web(distance[4]) , namespace='/')

        elif message.topic == "next":
            global num_palate
            num_pallet = cal_pallet()
            print(str(show_palate(count)) + " : " + str(num_pallet))
            distance.clear()
            angle.clear()
            count = count + 1 

            socketio.emit('send_pallet' , send_pallet_to_web(num_pallet) , namespace='/' )

        elif message.topic == "reset":
            count = count - 1
            print(show_palate(count))
            # socketio.emit('send_palate' , function() , namespace='/' )
            distance.clear()
            angle.clear()

            socketio.emit('set_zero' , send_all_zero() , namespace='/') #set all 0


@socketio.on('connect')
def handle_connect():
    print('Client connected')
    socketio.emit('message', 'Connected to server')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    socketio.emit('message', 'state: disconnected')

@socketio.on('message')
def handle_message(message):
    print('Received message:', message)
    
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, host='0.0.0.0' , port=5000)