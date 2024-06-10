from flask import Flask , render_template , request , jsonify
from flask_socketio import SocketIO , emit
from flask_mqtt import Mqtt
from flask_cors import CORS , cross_origin
import math
import re
from datetime import datetime
import mysql.connector

# ========== Variable ============
# global distance
# global angle
# global count
# global palate

distance = []
angle_x  = []
angle_y  = []
count = 0
MAX_RANGE = 15 #m.

pallet = [
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

def create_app():
    app = Flask(__name__ , template_folder='www/')
    app.config['SECRET_KEY'] = 'secret_key'

    # MySQL Configure
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'dew2533449'
    app.config['MYSQL_DB'] = 'mydb'
    return app

app = create_app()

socketio = SocketIO(app)
cors = CORS(app)

app.config['MQTT_BROKER_URL'] = '192.168.44.1'  
app.config['MQTT_BROKER_PORT'] = 1883  
app.config['MQTT_USERNAME'] = ''  
app.config['MQTT_PASSWORD'] = ''
app.config['MQTT_KEEPALIVE'] = 300 
app.config['MQTT_TLS_ENABLED'] = False
topic = "+"
mqtt = Mqtt(app)


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

def send_point_zero():
    return {
        'point' : 0
    }

def send_c_row(row):
    return {
        'c_row_v' : row
    }

def send_row(row):
    return {
        'row_v' : row
    }

def show_pallet(index):
    return pallet[index]

def clear_data(input_str):
    new_data = re.findall(r'[-+]?\d*\.\d+|\d+', input_str)
    return new_data

# convert degree to radian
def convert_angle(input_angle):
    return float(input_angle*(math.pi/180))


def collected_data(input_str):
    angle_x.append(clear_data(input_str)[0])
    angle_y.append(clear_data(input_str)[1])
    distance.append(clear_data(input_str)[2])


def cal_pallet():
    result = 0
    i = 0
    for i in range(0 , len(distance)):
        sum = 0
        sum = (float(distance[i]) * math.cos(convert_angle(float(angle_y[i])))) * math.cos(convert_angle(float(angle_x[i])))
        result = result + math.floor(sum)

    return math.floor(((MAX_RANGE*len(distance)) - result) / 1.2)
    # return round(((15*len(distance)) - result) / 1.2)

# MySQL
def send_db(row_name , distance , angle_x , angle_y):
    try:
        with app.app_context():
            connection = mysql.connector.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DB']
            )
            if connection.is_connected():
                current_time = datetime.now()
                date = current_time.strftime("%Y-%m-%d %H:%M:%S")
                cur = connection.cursor()
                cur.execute("INSERT INTO check_log(row_name, distance , x , y ,update_date) VALUES (%s ,%s ,%s ,%s ,%s)", (row_name, distance, angle_x, angle_y, date))
                connection.commit()
                print("Insert data")
                cur.close()

    except Exception as e:
        print(e)
        return "error"

def send_delete(row_name):
    try:
        with app.app_context():
            connection = mysql.connector.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DB']
            )
            if connection.is_connected():
                cur = connection.cursor()
                cur.execute("set SQL_SAFE_UPDATES = 0")
                cur.execute(f"delete from mydb.check_log WHERE row_name = '{row_name}' ")
                cur.execute(f"delete from stock WHERE row_name = '{row_name}' ")
                connection.commit()
                print("DELETE data")
                cur.close()

    except Exception as e:
        print(e)
        return "error"
    
def send_pallet(row_name, pallet):
    try:
        with app.app_context():
            connection = mysql.connector.connect(
                host=app.config['MYSQL_HOST'],
                user=app.config['MYSQL_USER'],
                password=app.config['MYSQL_PASSWORD'],
                database=app.config['MYSQL_DB']
            )
            if connection.is_connected():
                cur = connection.cursor()
                cur.execute("set SQL_SAFE_UPDATES = 0")
                cur.execute("INSERT INTO stock(row_name, pallet) VALUES (%s ,%s)", (row_name, pallet))
                connection.commit()
                print("Insert pallet")
                cur.close()

    except Exception as e:
        print(e)
        return "error"
    
# MQTT
@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    print("connect with result code " + str(rc))
    client.subscribe(topic)

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global msg
    global count
    msg = message.payload.decode()
    print(message.topic + " " + str(msg))
    socketio.emit('send_c_row' , send_c_row(show_pallet(count)) , namespace='/')

    if message.topic == "measure":
        collected_data(msg)
        print("angle x : " + str(angle_x))
        print("angle y : " + str(angle_y))
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

        #Send to Database
        send_db(show_pallet(count) ,distance[len(distance)-1] , angle_x[len(angle_x)-1] , angle_y[len(angle_y)-1])

    elif message.topic == "next":
        global num_pallet
        num_pallet = cal_pallet()
        print(str(show_pallet(count)) + " : " + str(num_pallet))
        send_pallet(show_pallet(count) , num_pallet)
        distance.clear()
        angle_x.clear()
        angle_y.clear()
        count = count + 1 
        socketio.emit('send_c_row' , send_c_row(show_pallet(count)) , namespace='/')
        socketio.emit('send_row' , send_row(show_pallet(count-1)) , namespace='/')
        socketio.emit('send_pallet' , send_pallet_to_web(num_pallet) , namespace='/' )
        socketio.emit('set_point_zero' , send_point_zero() , namespace='/')

    elif message.topic == "reset":
        count = count - 1
        send_delete(show_pallet(count))
        print(show_pallet(count))
        distance.clear()
        angle_x.clear()
        angle_y.clear()
        socketio.emit('send_c_row' , send_c_row(show_pallet(count)) , namespace='/')
        socketio.emit('set_zero' , send_all_zero() , namespace='/')
            
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
@cross_origin()
def index():
    return render_template("index.html")


if __name__ == "__main__":
    socketio.run(app , host='0.0.0.0' , port=5000)