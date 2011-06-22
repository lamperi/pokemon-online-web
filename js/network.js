Network = {
    init: function(handler) {
        this.handler = handler;

        /* var */ ws = new WebSocket("ws://localhost:8080/test");
        ws.onmessage = function(evt) {
            try {
                var data = JSON.parse(evt.data)
                $('#output').text(data.type);
                if (!handler[data.type]) {
                    console.log('Unknown event: ' + data.type);
                    return;
                }
                handler[data.type](data);
            } catch(e) {
                alert("Couldn't parse '" + evt.data + "': "+e);
            }
        }
    
        ws.onopen = function(evt) {
            $('#conn_status').html('<b>Connected</b>');
            ws.send(JSON.stringify({type: 'Login', name: 'Lamp'+String(Math.random()).substring(0,4)}));
        }
        ws.onerror = function(evt) {
            $('#conn_status').html('<b>Error</b>');
        }
        ws.onclose = function(evt) {
            $('#conn_status').html('<b>Closed</b>');
        }
    },
}

$(document).ready(function() {
    var handler = new UI.Handler();
    Network.init(handler)
});
