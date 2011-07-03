Network = {
    init: function(handler) {
        var ws;

        this.handler = handler;
        ws = this.ws = new WebSocket("ws://localhost:8080/test");
        ws.onmessage = function(evt) {
            try {
                var data = JSON.parse(evt.data)
                $('#output').text(data.type);
                if (!handler[data.type]) {
                    console.log('Unknown event: ' + data.type);
                    return;
                }
                try {
                    handler[data.type](data);
                } catch(e) {
                    alert("Handler for " + data.type + " returned error: " + e);
                }
            } catch(e) {
                alert("Couldn't parse '" + evt.data + "': "+e);
            }
        }
    
        ws.onopen = function(evt) {
            $('#conn_status').html('<b>Connected</b>');
        }
        ws.onerror = function(evt) {
            $('#conn_status').html('<b>Error</b>');
        }
        ws.onclose = function(evt) {
            $('#conn_status').html('<b>Closed</b>');
        }
    },

    disconnect: function() {
        this.ws.close();
    },

    sendJSON: function(o) {
        this.ws.send(JSON.stringify(o));
    },

    sendConnect: function(ip, port) {
        this.sendJSON({type: 'Connect', ip: ip, port: parseInt(port)});
    },

    sendLogin: function(name) {
        this.sendJSON({type: 'Login', name: name ? name : 'Lamp'+String(Math.random()).substring(0,4)});
    },

    sendChannelMessage: function(chanId, message) {
        this.sendJSON({type: 'ChannelMessage', chanId: chanId, message: message});
    },

    sendJoinChannel: function(chanName) {
        this.sendJSON({type: 'JoinChannel', chanName: chanName})
    },

    sendLeaveChannel: function(chanId) {
        this.sendJSON({type: 'LeaveChannel', chanId: chanId})
    },
    
    sendRegister: function() {
        this.sendJSON({type: 'Register'});
    },

    sendAskForPass: function(password, salt) {
        this.sendJSON({type: 'AskForPass', password: password, salt: salt});
    },

    sendSendPM: function(playerId, message) {
        this.sendJSON({type: 'SendPM', playerId: playerId, message: message})
    }
}

$(document).ready(function() {
    var handler = new UI.Handler();
    Network.init(handler)
});
