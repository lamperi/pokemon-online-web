/*global SockJS,location,console,alert,document,UI,$*/
var Network = {
    init: function(handler) {

        this.handler = handler;
        var sock = new SockJS('http://' + location.hostname + ':8081');
        this.sock = sock;
        sock.onmessage = function(evt) {
            try {
                var data = JSON.parse(evt.data);
                $('#output').text(data.type);
                console.log('Got event of data type ' + data.type + ": " + evt.data);
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
        };
    
        sock.onopen = function(evt) {
            $('#conn_status').html('<b>Connected</b>');
        };
        sock.onerror = function(evt) {
            $('#conn_status').html('<b>Error</b>');
        };
        sock.onclose = function(evt) {
            $('#conn_status').html('<b>Closed</b>');
        };
    },

    disconnect: function() {
        this.sock.close();
    },

    sendJSON: function(o) {
        this.sock.send(JSON.stringify(o));
    },

    sendConnect: function(ip, port) {
        this.sendJSON({type: 'Connect', ip: ip, port: parseInt(port,10)});
    },

    sendLogin: function(name) {
        this.sendJSON({type: 'Login', name: name ? name : 'Lamp'+String(Math.random()).substring(0,4)});
    },

    sendChannelMessage: function(chanId, message) {
        this.sendJSON({type: 'ChannelMessage', chanId: chanId, message: message});
    },

    sendJoinChannel: function(chanName) {
        this.sendJSON({type: 'JoinChannel', chanName: chanName});
    },

    sendLeaveChannel: function(chanId) {
        this.sendJSON({type: 'LeaveChannel', chanId: chanId});
    },
    
    sendRegister: function() {
        this.sendJSON({type: 'Register'});
    },

    sendAskForPass: function(password, salt) {
        this.sendJSON({type: 'AskForPass', password: password, salt: salt});
    },

    sendSendPM: function(playerId, message) {
        this.sendJSON({type: 'SendPM', playerId: playerId, message: message});
    },

    sendChallengeStuff: function(info) {
        this.sendJSON({type: 'ChallengeStuff', info: info});
    },

    sendBattleCommand: function(id, choice) {
        this.sendJSON({type: 'BattleCommand', id: id, choice: choice});
    },

    sendBattleFinished: function(id, result) {
        this.sendJSON({type: 'BattleFinished', battleid: id, result: result});
    }
};

$(document).ready(function() {
    var handler = new UI.Handler();
    Network.init(handler);
});
