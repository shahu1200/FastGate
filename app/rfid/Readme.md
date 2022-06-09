# **i-Tek Retail Gamma - RFID Service**

## **Introduction**
---------------
This service handles RFID tasks like connect, disconnect, close etc. It also has most of the business logic implemented in it like scancount, encoding etc.
This service uses redis-pubsub for inter-process communication.

## **Dependencies**
---------------
### Packages
---
#### Python
- python>=3.5
- toml==0.10.1
- redis==3.5.3
- pyserial==3.5
- itek_feig>=0.0.1.dev8
> NOTE:- To install these run: **pip3 install -r requirements.txt**

#### Other
- redis-server

### PUBSUB Topics
---
1. PUBLISH
    - belt-application = send rfid response
2. SUBSCRIBE
    - belt-emergency = listen for any emergency event
    - belt-rfid = listen for rfid request/command

## **Messages**
---
Below are general **request** and **response** message format for communication between this service and the application.

REQUEST message :-
```
{
    'command': 'setup',
    'data': <optional-data>
}
```

RESPONSE message :-
```
1. Success
{
    'command': 'setup',
    'status': 'success',
    'reason': '',
    'data': <optional-data>
}

2. Running/In-progress
{
    'command': 'setup',
    'status': 'running',
    'reason': '',
    'data': <optional-data>
}

3. Any error
{
    'command': 'setup',
    'status': 'error',
    'reason': <reason>,
    'data': <optional-data>
}
```

> NOTE: If NO 'data' is present, set it to **None**.

### **Reader Configuration/Setup**
---
This message is used to configure and connect the reader.

REQUEST message :-
```
{
    'command': 'setup',
    'data': None
}
```

RESPONSE message :-
```
1. Success
{
    'command': 'setup',
    'status': 'success',
    'reason': '',
    'data': None
}

2. Connect failed
{
    'command': 'setup',
    'status': 'error',
    'reason': 'CONNECT_FAILED',
    'data': None
}

3. Comm timeout
{
    'command': 'setup',
    'status': 'error',
    'reason': 'COMM_TIMEOUT',
    'data': None
}

4. Invalid reader
{
    'command': 'setup',
    'status': 'error',
    'reason': 'INVALID_READER',
    'data': None
}
```

### **Reader disconnect/close**
---
TODO

### **Reader diagnostic**
---
TODO

### **Scan Count**
---
This message is used to read **ALL** tags in the feild.

REQUEST message :-
```
{
    'command': 'scancount',
    'data': None
}
```

RESPONSE message :-
```
1. Success
{
	'command': 'scancount',
	'status': 'success',
	'reason': '',
	'data': {
		'eanList': {
			'890759431061': 73,
			'NON_ENCODED': 2,
		},
		'tagList': {
			'e28011702000016a4fe309ea': {
				'epc': '30361fad281e55574877e757',
				'tid': 'e28011702000016a4fe309ea',
				'antennas': [
					{'antno': '1', 'rssi': '56', 'phase_angle': '19'},
					{'antno': '2', 'rssi': '81', 'phase_angle': '23'}
				],
				'first_seen': 1606802382.990956,
				'last_seen': 1606802388.2394295,
				'seen_count': 4,
				'ean': '890759431061',
				'serialNo': '100000065367',
				'hard_tag': True
			},
			'e200341201351800024b6e0d': {
				'epc': '3c3c3c3c3c3c3c3cdbededed',
				'tid': 'e200341201351800024b6e0d',
				'antennas': [
					{'antno': '2', 'rssi': '77', 'phase_angle': '83'}
				],
				'first_seen': 1606802384.381227,
				'last_seen': 1606802384.381227,
				'seen_count': 1,
				'ean': 'NON_ENCODED',
				'serialNo': '',
				'hard_tag': True
			}
		}
	}
}

2. Running or In-progress
{
	'command': 'scancount',
	'status': 'running',
	'reason': '',
	'data': {
		'eanList': {
			'890759431061': 72,
			'NON_ENCODED': 2,
		},
		'tagList': None
	}
}

3. Reader NOT connected
{
    'command': 'scancount',
    'status': 'error',
    'reason': 'READER_NOT_CONNECTED',
    'data': None
}

4. Reader BRM mode error
{
    'command': 'scancount',
    'status': 'error',
    'reason': 'READER_BRM_MODE',
    'data': None
}
```

### **Encode**
---
This message is used for writing SGTIN(EPC) onto the tags.
> TODO: Add encoding process

REQUEST message :-
```
{
	'command': 'encode',
	'data': {
		'tagList': [
            # Format: [tid, epc, antno]
			['e28011702000016a4fe309ea', '30361FAD281E55574877E78A', 1],
			['e2003412013502000aa789b7', '30361FAD281E55574877E7D9', 2]
		],
		'password': [
			'12345678', '00000000', '88888888'
		]
	}
}

```

RESPONSE message :-
```
1. Success
{
	'command': 'encode',
	'status': 'success',
	'reason': '',
	'data': {
		'count': 72,
		'tagList': [
            # Format: [tid, epc, antno, status]
			['e28011702000016a4fe309ea', '30361FAD281E55574877E78A', 1, True],
			['e2003412013502000aa789b7', '30361FAD281E55574877E7D9', 2, False]
		]
	}
}

2. Running or In-progress
{
    'command': 'encode',
    'status': 'running',
    'reason': '',
    'data': {
		'count': 64,  # number of tags successfully written/update
		'tagList': None
    }
}

3. Reader NOT connected
{
    'command': 'encode',
    'status': 'error',
    'reason': 'READER_NOT_CONNECTED',
    'data': None
}

4. Invalid Data passed in REQUEST 'data'
{
    'command': 'encode',
    'status': 'error',
    'reason': 'INVALID_DATA',
    'data': None
}

5. Reader HOST mode error
{
    'command': 'encode',
    'status': 'error',
    'reason': 'READER_HOST_MODE',
    'data': None
}
```


### **Decode**
---
TODO
