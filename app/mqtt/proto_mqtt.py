import logging
from logging import ERROR, handlers
import paho.mqtt.client as mqtt
import json
from ..settings import PATH_FILE_LOG

# Setup logger
PATH_FILE_LOG += "logs/"
formatter = logging.Formatter(
    "%(asctime)s::%(levelname)s::%(filename)s::%(lineno)d %(message)s"
)
logger = logging.getLogger("mqtt")


# time logger
handler = handlers.TimedRotatingFileHandler(
    PATH_FILE_LOG + "mqtt/mqtt.log",
    when="midnight",
    backupCount=10,
    interval=1,
)
handler.setFormatter(formatter)
logger.addHandler(handler)

class MQTTProto:
    """
    mqtt class
    """
    def __init__(self, settings, loglevel="DEBUG"):
        """ mqtt client initialise """
        # print("proto_mqtt.py class MQTTProto init")
        self._broker_address = settings["connection"]["broker_address"]
        self._user_id = settings["connection"]["user_id"]
        self._password = settings["connection"]["password"]
        self._port = settings["connection"]["port"]

        logger.setLevel(loglevel)

        self._hb_topic = settings["channel"]["HB_pub"]
        try:
            self._client = mqtt.Client()
            logger.debug("started mqtt client!")
            print("!!! started mqtt client.....")
        except Exception as e:
            logger.error(e)

        self.dump_que = None
        self.initialise_que()

    def initialise_que(self):
        """ que of subscribe data topic + data """
        self.bs_config_que = []

    def connection(self, sub_topic):
        """
        Args:
            sub_topic (object): initialise subscribe topic lists with QoS
            [('topic1', 0),('topic2', 1)...(topic, Qos)]

        Returns:

        """
        self._subscribe_topics = sub_topic
        self._client.on_connect = self.on_connect
        self._client.on_message = self.on_message
        try:
            self._client.connect(self._broker_address, self._port)
            self._client.username_pw_set(self._user_id, self._password)
            logger.debug("login mqtt : " + str(self._broker_address) + " " +str(self._port) + " User : "+str(self._user_id))
           
        except Exception as e:
            logger.error(e)

    def on_connect(self, mqttc, obj, flags, rc):
        """ _subscribe_topics subscribe one or more topics with QoS
        [('topic1', 0),('topic2', 1)...(topic, Qos)]
        """
        self._client.subscribe(self._subscribe_topics)

    def on_message(self, mqttc, obj, msg):
        """
        mqtt msg read and insert into message que
        and msg payload convert bytes to string
        """
        data = (msg.payload).decode("utf-8")
        try:
            logger.debug(str(msg.topic) + "-$-" + str(data))
            # print("message topic=",msg.topic)
            # print("message qos=",msg.qos)
            # print("message retain flag=",msg.retain)
            
            message = {"topic":"mqtt","type":None,"data": json.loads(data)}            
            self.dump_que(message)            
            # print("msg in mqtt queue >",message)
            
            return
        except:
            logger.warn("while subscribe topic {} msg json format".format(str(msg.topic)))

    def message_que(self):
        """
        pop the msg from subscribe data by FIFO method
        when if available in que
        Returns:

        """
        pop_bs_msg = ""
        if len(self.bs_config_que) > 0:
            pop_bs_msg = self.bs_config_que.pop(0)

        return pop_bs_msg

    def message_que_pop(self, pop=False):
        """
        message que for discard data

        Args:
            pop (object):
        """
        pop_bs_msg = ""
        if len(self.bs_config_que) > 0 and pop == False:

            pop_bs_msg = self.bs_config_que[0]
        elif pop:
            """ 
            for discard message from que 
            """
            pop_bs_msg = self.bs_config_que.pop(0)

        return pop_bs_msg

    def start_loop(self):
        """
        start the loop of mqtt subscribe and in call of publish data
        Returns:

        """
        self._client.loop_start()

    def stop_loop(self):
        """
        Stop the mqtt loop of subscribe topic
        Returns:

        """
        self._client.loop_stop()

    def subscribe(self, sub_topic):
        """
        sub_topic is lists of subscribe topic with QoS
        [('topic1', 0),('topic2', 1)...(topic, Qos)]
        """
        self._subscribe_topics = sub_topic
        self._client.subscribe(self._subscribe_topics, 1)
        logger.debug("subscribe topic : "+str(self._subscribe_topics))

    def publish(self, pub_topic, pub_payload=None, qos=0, retain=False):
        """

        Args:
            pub_topic: publish topic name
            pub_data: publish data
            qos:
            retain:

        Returns:

        """
        try:
            logger.info("{} debug {}".format(pub_topic,str(pub_payload)))
            # print("{} debug {}".format(pub_topic,str(pub_payload)))
            self._client.publish(pub_topic, str(pub_payload), qos, retain)
        except Exception as e:
            logger.warning("while publish transaction : {}".format(str(e)))

    def heartbeat(self, pub_payload, pub_topic=None, qos=1, retain=False):
        try:
            if pub_topic is None:
                pub_topic = self._hb_topic
            self._client.publish("HeartBeat", str(pub_payload), qos, retain)
            logger.debug("topic : "+ pub_topic +", data publish : "+str(pub_payload) + " Heartbeat On " + str(pub_topic))
        except Exception as e:
            logger.error(str(e))

    def disconnect(self):
        """
        closing connection of mqtt client
        Returns:

        """
        self._client.disconnect()

"""
how to use
subscribe
mq1 = itekMQTT(self.mqttbroker_address)
mq1.initialise_que()
mq1.connection(self.config_sub_topic)
mq1.start_loop()
mq1.subscribe(self.config_sub_topic)
mqtt_msg = mq1.message_que_pop()

publish
pubdata = itekMQTT(self.mqttbroker_address)
pubdata.connection(self.config_sub_topic)
pubdata.start_loop()
pubdata.publish(topic, str(pub_data))
pubdata.stop_loop()
pubdata.disconnect()

"""