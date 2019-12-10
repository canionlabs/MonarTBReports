function WebSocketAPI(device_token, device_id, startTs, endTs) {
    var token = device_token;
    var entityId = device_id;
    var webSocket = new WebSocket("ws://platform.canionlabs.io:9090/api/ws/plugins/telemetry?token="+token);

    webSocket.onopen = function () {
        var object = {
            historyCmds: [
              {
                  cmdId: 1,
                  entityType: "DEVICE",
                  entityId: entityId,
                  keys: "t0,h0",
                  startTs: startTs,
                  endTs: endTs
              }
            ]
        };
        var data = JSON.stringify(object);
        webSocket.send(data);
    };

    webSocket.onmessage = function (event) {
        var received_msg = JSON.parse(event.data);

        var bigger = 0;
        var smaller = 100;

        for (key in received_msg.data){
          for (var index = 0; index < received_msg.data[key].length; index+=1) {
            if(smaller>received_msg.data[key][index][1]){
              smaller = received_msg.data[key][index][1];
            } 
            if(bigger<received_msg.data[key][index][1]){
              bigger = received_msg.data[key][index][1];
            }
          }
        }
        
        var average = (parseFloat(bigger)+parseFloat(smaller))/2;

        console.log(received_msg);
        console.log("Maior: "+bigger+" Menor: "+smaller+" Média: "+average);
    };

    webSocket.onclose = function (event) {
        console.log("Connection is closed!");
    };
}